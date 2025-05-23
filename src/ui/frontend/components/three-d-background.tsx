"use client"

import { Canvas } from "@react-three/fiber"
import { Environment } from "@react-three/drei"
import CoreElement from "@/components/core-element"

export default function ThreeDBackground() {
  return (
    <Canvas>
      <Environment preset="night" />
      <CoreElement />
    </Canvas>
  )
}
