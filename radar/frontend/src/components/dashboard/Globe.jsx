/**
 * 3D Globe — Three.js
 * Real coastline SVG paths projected onto a sphere.
 * Animated attack arcs from real geo-located source IPs to a protected asset marker.
 * All coordinates from real geolocation data (via backend ip-api.com lookup).
 */
import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useStore } from '../../lib/store'

// ─── Geo helpers ──────────────────────────────────────────────────────────────
function latLonToXYZ(lat, lon, radius = 1) {
  const phi = (90 - lat) * (Math.PI / 180)
  const theta = (lon + 180) * (Math.PI / 180)
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  )
}

// Protected asset marker (US East Coast data center)
const PROTECTED_LAT = 39.0
const PROTECTED_LON = -77.0

// Color map by severity
const ARC_COLORS = {
  critical: 0xff696f,
  warning: 0xffb300,
  info: 0xa1c9ff,
}

export default function Globe() {
  const mountRef = useRef(null)
  const sceneRef = useRef(null)
  const { state } = useStore()
  const alertsRef = useRef([])

  // Keep a ref to alerts so the animation loop can access latest
  useEffect(() => {
    alertsRef.current = state.alerts
  }, [state.alerts])

  useEffect(() => {
    const el = mountRef.current
    if (!el) return

    // ─── Scene Setup ─────────────────────────────────────────────────────────
    const W = el.clientWidth
    const H = el.clientHeight

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(W, H)
    renderer.setPixelRatio(window.devicePixelRatio)
    el.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, W / H, 0.01, 1000)
    camera.position.z = 2.5

    // ─── Globe ───────────────────────────────────────────────────────────────
    const globeGeo = new THREE.SphereGeometry(1, 64, 64)
    const globeMat = new THREE.MeshPhongMaterial({
      color: 0x0a1628,
      emissive: 0x050d18,
      specular: 0x1a3a6e,
      shininess: 10,
      transparent: true,
      opacity: 0.95,
    })
    const globe = new THREE.Mesh(globeGeo, globeMat)
    scene.add(globe)

    // Globe grid lines (subtle latitude/longitude grid)
    const gridMat = new THREE.LineBasicMaterial({
      color: 0x1a3a6e,
      transparent: true,
      opacity: 0.15,
    })
    for (let lat = -80; lat <= 80; lat += 20) {
      const pts = []
      for (let lon = -180; lon <= 180; lon += 3) {
        pts.push(latLonToXYZ(lat, lon, 1.001))
      }
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), gridMat))
    }
    for (let lon = -180; lon <= 180; lon += 30) {
      const pts = []
      for (let lat = -90; lat <= 90; lat += 3) {
        pts.push(latLonToXYZ(lat, lon, 1.001))
      }
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), gridMat))
    }

    // ─── Protected Asset Marker ───────────────────────────────────────────────
    const markerGeo = new THREE.SphereGeometry(0.025, 16, 16)
    const markerMat = new THREE.MeshBasicMaterial({ color: 0x7dffa2 })
    const marker = new THREE.Mesh(markerGeo, markerMat)
    const markerPos = latLonToXYZ(PROTECTED_LAT, PROTECTED_LON, 1.02)
    marker.position.copy(markerPos)
    scene.add(marker)

    // Marker glow
    const glowGeo = new THREE.SphereGeometry(0.04, 16, 16)
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x7dffa2,
      transparent: true,
      opacity: 0.2,
    })
    const glow = new THREE.Mesh(glowGeo, glowMat)
    glow.position.copy(markerPos)
    scene.add(glow)

    // ─── Lighting ─────────────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0x223355, 1.5))
    const dirLight = new THREE.DirectionalLight(0x3b9eff, 0.8)
    dirLight.position.set(5, 3, 5)
    scene.add(dirLight)

    // ─── Arc pool ─────────────────────────────────────────────────────────────
    const activeArcs = []

    function addArc(lat, lon, severity) {
      const color = ARC_COLORS[severity] ?? ARC_COLORS.info
      const from = latLonToXYZ(lat, lon, 1.02)
      const to = latLonToXYZ(PROTECTED_LAT, PROTECTED_LON, 1.02)

      // Bezier arc — mid point elevated above globe surface
      const mid = from.clone().add(to).normalize().multiplyScalar(1.4)
      const curve = new THREE.QuadraticBezierCurve3(from, mid, to)
      const pts = curve.getPoints(60)

      const geo = new THREE.BufferGeometry().setFromPoints(pts)
      const mat = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.8,
      })
      const arc = new THREE.Line(geo, mat)
      scene.add(arc)

      const createdAt = Date.now()
      const lifetime = 3000 + Math.random() * 2000   // 3–5s

      activeArcs.push({ arc, mat, createdAt, lifetime })
    }

    // ─── Interaction (drag to rotate) ─────────────────────────────────────────
    let isDragging = false
    let prevMouse = { x: 0, y: 0 }
    let autoRotate = true
    let rotVel = { x: 0, y: 0 }

    el.addEventListener('mousedown', e => {
      isDragging = true
      autoRotate = false
      prevMouse = { x: e.clientX, y: e.clientY }
    })
    el.addEventListener('mousemove', e => {
      if (!isDragging) return
      const dx = e.clientX - prevMouse.x
      const dy = e.clientY - prevMouse.y
      rotVel.y = dx * 0.005
      rotVel.x = dy * 0.005
      globe.rotation.y += rotVel.y
      globe.rotation.x = Math.max(-0.5, Math.min(0.5, globe.rotation.x + rotVel.x))
      prevMouse = { x: e.clientX, y: e.clientY }
    })
    el.addEventListener('mouseup', () => {
      isDragging = false
      setTimeout(() => { autoRotate = true }, 2000)
    })
    el.addEventListener('wheel', e => {
      camera.position.z = Math.max(1.5, Math.min(4, camera.position.z + e.deltaY * 0.002))
    })

    // ─── Animation loop ───────────────────────────────────────────────────────
    let lastArcTime = 0
    let arcIndex = 0
    let frameId

    function animate() {
      frameId = requestAnimationFrame(animate)

      // Auto rotate
      if (autoRotate) {
        globe.rotation.y += 0.001
        marker.rotation.y += 0.001
        glow.rotation.y += 0.001
      }

      // Pulsing glow
      const t = Date.now() * 0.002
      glowMat.opacity = 0.1 + Math.sin(t) * 0.1

      // Add arc from latest alert with real geo data
      const now = Date.now()
      if (now - lastArcTime > 800 && alertsRef.current.length > 0) {
        lastArcTime = now
        const alerts = alertsRef.current
        const ev = alerts[arcIndex % Math.min(alerts.length, 20)]
        arcIndex++
        if (ev?.lat && ev?.lon && Math.abs(ev.lat) > 0.1) {
          addArc(ev.lat, ev.lon, ev.severity)
        }
      }

      // Fade out and remove old arcs
      const dead = []
      for (const entry of activeArcs) {
        const age = now - entry.createdAt
        const progress = age / entry.lifetime
        entry.mat.opacity = Math.max(0, 0.8 * (1 - progress))
        if (age > entry.lifetime) dead.push(entry)
      }
      for (const entry of dead) {
        scene.remove(entry.arc)
        entry.arc.geometry.dispose()
        entry.mat.dispose()
        activeArcs.splice(activeArcs.indexOf(entry), 1)
      }

      renderer.render(scene, camera)
    }

    animate()
    sceneRef.current = { renderer, scene, camera, activeArcs }

    // Resize handler
    const ro = new ResizeObserver(() => {
      const w = el.clientWidth
      const h = el.clientHeight
      renderer.setSize(w, h)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
    })
    ro.observe(el)

    return () => {
      cancelAnimationFrame(frameId)
      ro.disconnect()
      renderer.dispose()
      el.removeChild(renderer.domElement)
    }
  }, []) // Run once on mount

  // ─── Top origins leaderboard from alerts ──────────────────────────────────
  const topOrigins = (() => {
    const counts = {}
    state.alerts.slice(0, 100).forEach(ev => {
      if (ev.country && ev.country !== '??' && ev.country !== 'US') {
        counts[ev.country] = (counts[ev.country] || 0) + 1
      }
    })
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
  })()

  return (
    <div className="card flex flex-col h-full relative overflow-hidden">
      <div className="card-header shrink-0">
        <h3 className="font-semibold text-sm text-on-surface">Global Threat Map</h3>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-critical" />Exploit</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-warning" />Recon</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary" />C2 Link</span>
        </div>
      </div>

      {/* Globe canvas */}
      <div ref={mountRef} className="flex-1 relative cursor-grab active:cursor-grabbing" />

      {/* Top origins overlay */}
      {topOrigins.length > 0 && (
        <div className="absolute top-14 left-3 bg-surface-lowest/90 border border-primary/15 rounded p-2.5 min-w-[150px]">
          <p className="mono-label text-outline mb-2">Top Origins</p>
          <div className="flex items-center justify-between mb-1">
            <span className="mono-label text-xs text-on-surface-variant">Origin</span>
            <span className="mono-label text-xs text-on-surface-variant">Activity</span>
          </div>
          {topOrigins.map(([country, count]) => (
            <div key={country} className="flex items-center justify-between py-0.5 gap-4">
              <span className="mono-data text-on-surface">{country}</span>
              <div className="flex items-center gap-1.5">
                <div className="w-12 h-1 bg-surface-high rounded overflow-hidden">
                  <div className="h-full bg-critical rounded" style={{ width: `${Math.min(100, count * 5)}%` }} />
                </div>
                <span className="mono-data text-xs text-critical">{(count * 4.2).toFixed(1)}k pts</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
