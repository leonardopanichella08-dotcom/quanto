import React, { useEffect, useRef } from 'react'

/** Sfondo del hero: «liquido» ambra generato da uno shader (three.js, caricato solo qui e solo quando serve). Reagisce al mouse, si ferma fuori schermo
 *  e con «riduci movimento» disegna un solo fotogramma. Senza WebGL resta il gradiente CSS dietro. */
const FRAG = `
precision highp float;
uniform float uTime; uniform vec2 uRes; uniform vec2 uMouse;
float hash(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y); }
float fbm(vec2 p){ float v=0.0, a=0.5; for(int i=0;i<5;i++){ v+=a*noise(p); p=p*2.02+vec2(3.1,1.7); a*=0.5; } return v; }
void main(){
  vec2 uv = gl_FragCoord.xy / uRes;
  vec2 p = (gl_FragCoord.xy - 0.5*uRes) / uRes.y;
  p += (uMouse - 0.5) * vec2(0.22, 0.14);
  float t = uTime * 0.07;
  vec2 q = vec2(fbm(p*1.3 + t), fbm(p*1.3 + vec2(5.2,1.3) - t));
  vec2 r = vec2(fbm(p*1.5 + 2.0*q + vec2(1.7,9.2) + 1.3*t), fbm(p*1.5 + 2.0*q + vec2(8.3,2.8) - t));
  float f = fbm(p*1.2 + 2.3*r);
  vec3 dark = vec3(0.027, 0.027, 0.035);
  vec3 c1 = vec3(0.86, 0.36, 0.03);
  vec3 c2 = vec3(1.00, 0.76, 0.22);
  vec3 c3 = vec3(1.00, 0.97, 0.62);
  vec3 col = mix(dark, c1, smoothstep(0.34, 0.66, f));
  col = mix(col, c2, smoothstep(0.52, 0.80, f + 0.18*length(q)));
  col = mix(col, c3, smoothstep(0.78, 0.98, f + 0.25*r.x));
  float edge = smoothstep(0.0, 0.5, uv.x);               // a sinistra più scuro: il titolo resta leggibile
  col *= mix(0.22, 1.0, edge);
  col *= smoothstep(1.35, 0.25, length((uv - 0.5) * vec2(1.25, 1.0)));
  col *= smoothstep(0.0, 0.18, uv.y) * 0.5 + 0.5;
  float g = hash(gl_FragCoord.xy + uTime) - 0.5;
  col += g * 0.025;
  gl_FragColor = vec4(col, 1.0);
}`
const VERT = 'void main(){ gl_Position = vec4(position.xy, 0.0, 1.0); }'

export default function LiquidHero({ reduce }) {
  const host = useRef(null)
  useEffect(() => {
    let disposed = false
    let cleanup = () => {}
    ;(async () => {
      let THREE
      try { THREE = await import('three') } catch { return }
      if (disposed || !host.current) return
      let renderer
      try { renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false, powerPreference: 'low-power' }) } catch { return }
      const el = host.current
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5))
      el.appendChild(renderer.domElement)
      Object.assign(renderer.domElement.style, { width: '100%', height: '100%', display: 'block' })
      const scene = new THREE.Scene()
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)
      const uniforms = { uTime: { value: 0 }, uRes: { value: new THREE.Vector2(1, 1) }, uMouse: { value: new THREE.Vector2(0.5, 0.5) } }
      const mat = new THREE.ShaderMaterial({ uniforms, vertexShader: VERT, fragmentShader: FRAG })
      const geo = new THREE.PlaneGeometry(2, 2)
      scene.add(new THREE.Mesh(geo, mat))

      const resize = () => {
        const w = el.clientWidth || 1, h = el.clientHeight || 1
        renderer.setSize(w, h, false)
        const size = renderer.getDrawingBufferSize(new THREE.Vector2())
        uniforms.uRes.value.copy(size)
      }
      resize()
      const ro = new ResizeObserver(resize)
      ro.observe(el)

      const target = new THREE.Vector2(0.5, 0.5)
      const onMove = (e) => { const r = el.getBoundingClientRect(); target.set((e.clientX - r.left) / r.width, 1 - (e.clientY - r.top) / r.height) }
      window.addEventListener('pointermove', onMove, { passive: true })

      let visible = true
      const io = new IntersectionObserver(([en]) => { visible = en.isIntersecting }, { threshold: 0 })
      io.observe(el)

      let raf = 0
      const t0 = performance.now()
      const frame = () => {
        raf = requestAnimationFrame(frame)
        if (!visible || document.hidden) return
        uniforms.uTime.value = (performance.now() - t0) / 1000
        uniforms.uMouse.value.lerp(target, 0.04)
        renderer.render(scene, camera)
      }
      if (reduce) { uniforms.uTime.value = 6; renderer.render(scene, camera) } else frame()

      cleanup = () => {
        cancelAnimationFrame(raf); ro.disconnect(); io.disconnect()
        window.removeEventListener('pointermove', onMove)
        geo.dispose(); mat.dispose(); renderer.dispose()
        renderer.domElement.remove()
      }
    })()
    return () => { disposed = true; cleanup() }
  }, [reduce])
  return <div ref={host} className="liquid-hero" aria-hidden="true" />
}
