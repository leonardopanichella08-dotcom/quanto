// Archivio ZIP costruito nel browser (senza compressione): i file restano così come sono e non servono librerie.
// Si fa qui e non sul server perché Vercel limita a 4,5 MB la risposta di una singola chiamata.

const TABLE = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n += 1) {
    let c = n
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[n] = c >>> 0
  }
  return t
})()

export function crc32(bytes) {
  let c = 0xffffffff
  for (let i = 0; i < bytes.length; i += 1) c = TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}

function dosDateTime(d) {
  const time = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1)
  const date = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()
  return [time & 0xffff, date & 0xffff]
}

/** files: [{ name: 'Cartella/file.pdf', data: Uint8Array }] → Blob application/zip */
export function createZip(files, now = new Date()) {
  const enc = new TextEncoder()
  const [time, date] = dosDateTime(now)
  const parts = []
  const central = []
  let offset = 0
  for (const f of files) {
    const name = enc.encode(f.name)
    const crc = crc32(f.data)
    const local = new DataView(new ArrayBuffer(30))
    local.setUint32(0, 0x04034b50, true); local.setUint16(4, 20, true); local.setUint16(6, 0x0800, true)     // 0x0800: nomi in UTF-8
    local.setUint16(8, 0, true); local.setUint16(10, time, true); local.setUint16(12, date, true)
    local.setUint32(14, crc, true); local.setUint32(18, f.data.length, true); local.setUint32(22, f.data.length, true)
    local.setUint16(26, name.length, true); local.setUint16(28, 0, true)
    parts.push(local.buffer, name, f.data)
    const cen = new DataView(new ArrayBuffer(46))
    cen.setUint32(0, 0x02014b50, true); cen.setUint16(4, 20, true); cen.setUint16(6, 20, true); cen.setUint16(8, 0x0800, true)
    cen.setUint16(10, 0, true); cen.setUint16(12, time, true); cen.setUint16(14, date, true)
    cen.setUint32(16, crc, true); cen.setUint32(20, f.data.length, true); cen.setUint32(24, f.data.length, true)
    cen.setUint16(28, name.length, true); cen.setUint32(42, offset, true)
    central.push(cen.buffer, name)
    offset += 30 + name.length + f.data.length
  }
  const centralSize = central.reduce((s, p) => s + (p.byteLength ?? p.length), 0)
  const end = new DataView(new ArrayBuffer(22))
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true)
  end.setUint32(12, centralSize, true); end.setUint32(16, offset, true)
  return new Blob([...parts, ...central, end.buffer], { type: 'application/zip' })
}

/** Rende unico un nome dentro l'archivio: «a.pdf», «a (2).pdf»… */
export function uniqueName(name, used) {
  if (!used.has(name)) { used.add(name); return name }
  const dot = name.lastIndexOf('.')
  const base = dot > 0 ? name.slice(0, dot) : name
  const ext = dot > 0 ? name.slice(dot) : ''
  for (let n = 2; ; n += 1) {
    const candidate = `${base} (${n})${ext}`
    if (!used.has(candidate)) { used.add(candidate); return candidate }
  }
}
