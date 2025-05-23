import { Suspense } from "react"
import ZekaInterface from "@/components/zeka-interface"
import Loading from "@/components/loading"

export default function Home() {
  return (
    <main className="w-full h-screen bg-black overflow-hidden">
      <Suspense fallback={<Loading />}>
        <ZekaInterface />
      </Suspense>
    </main>
  )
}
