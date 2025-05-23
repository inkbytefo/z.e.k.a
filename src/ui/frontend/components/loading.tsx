import { Loader2 } from "lucide-react"

export default function Loading() {
  return (
    <div className="w-full h-screen flex flex-col items-center justify-center bg-black">
      <div className="relative">
        <div className="w-24 h-24 rounded-full border-4 border-blue-500/20 animate-pulse"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-12 h-12 text-blue-400 animate-spin" />
        </div>
      </div>
      <h2 className="mt-6 text-blue-400 font-light tracking-wider text-xl">Z.E.K.A INITIALIZING</h2>
      <p className="text-blue-500/60 mt-2 font-mono text-sm">Zenginleştirilmiş Etkileşimli Kişisel Asistan</p>
    </div>
  )
}
