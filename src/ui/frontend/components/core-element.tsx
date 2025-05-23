"use client"

import { useRef } from "react"
import { useFrame } from "@react-three/fiber"
import { Sphere, MeshDistortMaterial } from "@react-three/drei"
import type * as THREE from "three"

export default function CoreElement() {
  const sphereRef = useRef<THREE.Mesh>(null)
  const lightRef = useRef<THREE.PointLight>(null)

  useFrame(({ clock }) => {
    if (sphereRef.current) {
      // Enhanced pulsing effect - more visible but still gentle
      const t = clock.getElapsedTime()
      sphereRef.current.scale.set(
        1 + Math.sin(t * 0.25) * 0.05,
        1 + Math.sin(t * 0.25) * 0.05,
        1 + Math.sin(t * 0.25) * 0.05,
      )
    }

    if (lightRef.current) {
      // Moving light effect - optimized for visibility
      const t = clock.getElapsedTime()
      lightRef.current.position.x = Math.sin(t * 0.25) * 3.5
      lightRef.current.position.y = Math.cos(t * 0.25) * 3.5
      lightRef.current.intensity = 4 + Math.sin(t * 0.4) * 1.5
    }
  })

  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight ref={lightRef} position={[0, 0, 5]} intensity={4} color="#0078D7" />

      <Sphere ref={sphereRef} args={[1.5, 64, 64]} position={[0, 0, 0]}>
        <MeshDistortMaterial
          color="#0078D7"
          attach="material"
          distort={0.25}
          speed={1.2}
          roughness={0.25}
          metalness={0.8}
        />
      </Sphere>

      {/* Enhanced particles - increased count and visibility */}
      {Array.from({ length: 25 }).map((_, i) => (
        <mesh
          key={i}
          position={[(Math.random() - 0.5) * 14, (Math.random() - 0.5) * 14, (Math.random() - 0.5) * 14]}
          scale={0.04}
        >
          <sphereGeometry args={[1, 8, 8]} />
          <meshBasicMaterial color="#0078D7" transparent opacity={0.5} />
        </mesh>
      ))}

      {/* Orbital rings - more visible */}
      <RingElement radius={2.5} thickness={0.02} color="#0078D7" opacity={0.3} />
      <RingElement radius={3.2} thickness={0.02} color="#0078D7" opacity={0.25} />
      <RingElement radius={3.9} thickness={0.02} color="#0078D7" opacity={0.2} />
    </>
  )
}

// Separate component for rings to avoid ref issues
function RingElement({
  radius,
  thickness,
  color,
  opacity,
}: {
  radius: number
  thickness: number
  color: string
  opacity: number
}) {
  const ringRef = useRef<THREE.Mesh>(null)

  useFrame(({ clock }) => {
    if (ringRef.current) {
      // Optimized rotation speed for better visibility
      ringRef.current.rotation.z = clock.getElapsedTime() * 0.15
      // Add slight x-axis rotation for more dynamic effect
      ringRef.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.1) * 0.1
    }
  })

  return (
    <mesh ref={ringRef}>
      <torusGeometry args={[radius, thickness, 16, 100]} />
      <meshBasicMaterial color={color} transparent opacity={opacity} />
    </mesh>
  )
}
