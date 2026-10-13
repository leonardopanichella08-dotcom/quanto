import React, { useEffect, useRef } from 'react'

/** Sfondo del hero: onde morbide di giallo QUANTO su fondo chiaro, generate da uno shader (three.js, caricato solo qui e solo quando serve).
 *  Reagisce piano al mouse, si ferma fuori schermo e con «riduci movimento» disegna un solo fotogramma. Senza WebGL resta il fondo CSS. */
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
  p += (uMouse - 0.5) * vec2(0.18, 0.12);
  float t = uTime * 0.06;
  vec2 q = vec2(fbm(p*1.2 + t), fbm(p*1.2 + vec2(5.2,1.3) - t));
  vec2 r = vec2(fbm(p*1.4 + 2.0*q + vec2(1.7,9.2) + 1.2*t), fbm(p*1.4 + 2.0*q + vec2(8.3,2.8) - t));
  float f = fbm(p*1.1 + 2.2*r);
  vec3 cream = vec3(0.980, 0.965, 0.914);
  vec3 white = vec3(1.0, 0.995, 0.97);
  vec3 yellow = vec3(0.945, 0.886, 0.106);
  vec3 soft = vec3(0.99, 0.94, 0.55);
  vec3 col = mix(cream, white, smoothstep(0.25, 0.6, f));
  float y = smoothstep(0.38, 0.70, f + 0.15*length(q));
  col = mix(col, soft, y);
  col = mix(col, yellow, smoothstep(0.55, 0.85, f + 0.25*r.x));
  float fade = smoothstep(0.0, 0.55, uv.x) * 0.55 + 0.45;           // a sinistra più chiaro: il titolo resta leggibile
  col = mix(cream, col, fade);
  col = mix(col, cream, smoothstep(0.62, 0.05, uv.y) * 0.85);        // sfuma nel fondo chiaro della pagina
  col += (hash(gl_FragCoord.xy + uTime) - 0.5) * 0.018;
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
        uniforms.uRes.value.copy(renderer.getDrawingBufferSize(new THREE.Vector2()))
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
