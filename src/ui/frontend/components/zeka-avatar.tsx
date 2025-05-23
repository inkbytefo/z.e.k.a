"use client"

import { useRef, useEffect } from "react"

export default function ZekaAvatar() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas dimensions
    const size = 120
    canvas.width = size
    canvas.height = size

    // Animation variables
    let animationFrame: number
    const particles: Particle[] = []
    let hue = 230 // Blue base color
    let frame = 0

    // Particle class
    class Particle {
      x: number
      y: number
      size: number
      speedX: number
      speedY: number
      color: string
      life: number
      maxLife: number

      constructor() {
        this.x = size / 2
        this.y = size / 2
        this.size = Math.random() * 3 + 1
        const angle = Math.random() * Math.PI * 2
        const speed = Math.random() * 1 + 0.5
        this.speedX = Math.cos(angle) * speed
        this.speedY = Math.sin(angle) * speed
        this.color = `hsla(${hue}, 100%, 70%, 1)`
        this.maxLife = Math.random() * 100 + 50
        this.life = this.maxLife
      }

      update() {
        this.x += this.speedX
        this.y += this.speedY
        this.life--

        // Slowly move back to center
        if (Math.random() > 0.95) {
          const angle = Math.atan2(size / 2 - this.y, size / 2 - this.x)
          this.speedX += Math.cos(angle) * 0.1
          this.speedY += Math.sin(angle) * 0.1
        }

        // Limit speed
        const maxSpeed = 1.5
        const currentSpeed = Math.sqrt(this.speedX * this.speedX + this.speedY * this.speedY)
        if (currentSpeed > maxSpeed) {
          this.speedX = (this.speedX / currentSpeed) * maxSpeed
          this.speedY = (this.speedY / currentSpeed) * maxSpeed
        }
      }

      draw() {
        const alpha = this.life / this.maxLife
        ctx.fillStyle = this.color.replace("1)", `${alpha})`)
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    // Animation function
    const animate = () => {
      // Clear canvas with slight transparency for trail effect
      ctx.fillStyle = "rgba(0, 0, 0, 0.1)"
      ctx.fillRect(0, 0, size, size)

      // Update and draw particles
      for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update()
        particles[i].draw()

        // Remove dead particles
        if (particles[i].life <= 0) {
          particles.splice(i, 1)
        }
      }

      // Add new particles
      if (frame % 2 === 0) {
        particles.push(new Particle())
      }

      // Slowly shift hue
      if (frame % 10 === 0) {
        hue = 230 + Math.sin(frame * 0.01) * 20 // Shift between blue shades
      }

      // Draw center core
      const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 4)
      gradient.addColorStop(0, "rgba(30, 64, 255, 0.8)")
      gradient.addColorStop(1, "rgba(16, 32, 128, 0)")
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(size / 2, size / 2, size / 4, 0, Math.PI * 2)
      ctx.fill()

      frame++
      animationFrame = requestAnimationFrame(animate)
    }

    // Start animation
    animate()

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrame)
    }
  }, [])

  return (
    <div className="relative w-[120px] h-[120px] flex items-center justify-center">
      <div className="absolute inset-0 rounded-full bg-blue-900/10 backdrop-blur-sm border border-blue-500/20 shadow-[0_0_15px_rgba(30,64,255,0.2)]"></div>
      <div className="absolute inset-0 rounded-full animate-pulse-ring border-2 border-blue-500/30"></div>
      <canvas
        ref={canvasRef}
        className="absolute inset-0 rounded-full"
        style={{ filter: "blur(1px)" }}
        width="120"
        height="120"
      ></canvas>
      <div className="z-10 text-blue-300 text-sm font-mono flex flex-col items-center">
        <span className="font-bold tracking-wider">Z.E.K.A</span>
        <span className="text-[8px] text-blue-400/70 mt-1">ACTIVE</span>
      </div>
    </div>
  )
}
