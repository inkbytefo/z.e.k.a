"use client"

import { useState, useEffect } from "react"
import { Server, PlusCircle, Trash2, RefreshCw, Power, PowerOff, ExternalLink, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import MCPServerModal, { MCPServerConfig } from "./mcp-server-modal"

interface MCPServerManagerProps {
  className?: string
}

interface MCPServer {
  id: string
  name: string
  command: string
  args: string[]
  env?: Record<string, string>
  disabled?: boolean
  status?: "online" | "offline" | "error"
  lastConnected?: string
}

export default function MCPServerManager({ className }: MCPServerManagerProps) {
  const [servers, setServers] = useState<MCPServer[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedServer, setSelectedServer] = useState<MCPServer | null>(null)

  // Fetch MCP servers from config
  useEffect(() => {
    const fetchServers = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // API'den MCP sunucularını al
        const response = await fetch('/api/mcp/servers')

        if (!response.ok) {
          throw new Error(`Sunucular yüklenirken hata: ${response.status}`)
        }

        const data = await response.json()

        // Transform the data to our format
        const serverList: MCPServer[] = Object.entries(data.mcpServers || {}).map(([id, config]: [string, any]) => ({
          id,
          name: id,
          command: config.command,
          args: config.args || [],
          env: config.env,
          disabled: config.disabled || false,
          status: config.disabled ? "offline" : "online"
        }))

        setServers(serverList)
      } catch (err) {
        console.error("MCP sunucuları yüklenirken hata:", err)
        setError("MCP sunucuları yüklenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
      } finally {
        setIsLoading(false)
      }
    }

    fetchServers()
  }, [])

  // Save MCP server to config
  const saveMCPServer = async (serverConfig: MCPServerConfig) => {
    try {
      setIsLoading(true)
      setError(null)

      // API'ye MCP sunucusu ekle
      const response = await fetch('/api/mcp/servers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(serverConfig)
      })

      if (!response.ok) {
        throw new Error(`Sunucu kaydedilirken hata: ${response.status}`)
      }

      const data = await response.json()

      // Add the new server to our list
      const newServer: MCPServer = {
        id: data.id || serverConfig.name,
        name: serverConfig.name,
        command: serverConfig.command,
        args: serverConfig.args,
        env: serverConfig.env,
        disabled: serverConfig.disabled || false,
        status: "offline"
      }

      setServers(prev => [...prev, newServer])

      console.log("MCP sunucusu başarıyla eklendi:", serverConfig.name)
    } catch (err) {
      console.error("MCP sunucusu kaydedilirken hata:", err)
      setError("MCP sunucusu kaydedilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
    } finally {
      setIsLoading(false)
    }
  }

  // Toggle server status (enable/disable)
  const toggleServerStatus = async (serverId: string) => {
    try {
      const server = servers.find(s => s.id === serverId)
      if (!server) return

      // API'ye durum değişikliği gönder
      const newStatus = server.status === "online" ? "offline" : "online"

      // API çağrısı (gerçek uygulamada)
      // const response = await fetch(`/api/mcp/servers/${serverId}`, {
      //   method: 'PUT',
      //   headers: {
      //     'Content-Type': 'application/json'
      //   },
      //   body: JSON.stringify({ disabled: newStatus === "offline" })
      // })

      // Update the server in our list
      setServers(prev => prev.map(s =>
        s.id === serverId ? { ...s, status: newStatus } : s
      ))

      console.log(`MCP sunucusu ${newStatus === "online" ? "etkinleştirildi" : "devre dışı bırakıldı"}:`, server.name)
    } catch (err) {
      console.error("MCP sunucusu durumu değiştirilirken hata:", err)
      setError("MCP sunucusu durumu değiştirilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
    }
  }

  // Delete server from config
  const deleteServer = async (serverId: string) => {
    try {
      if (!confirm("Bu MCP sunucusunu silmek istediğinizden emin misiniz?")) {
        return
      }

      setIsLoading(true)
      setError(null)

      // API'den MCP sunucusunu sil
      const response = await fetch(`/api/mcp/servers/${serverId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error(`Sunucu silinirken hata: ${response.status}`)
      }

      // Remove the server from our list
      setServers(prev => prev.filter(s => s.id !== serverId))

      console.log("MCP sunucusu başarıyla silindi:", serverId)
    } catch (err) {
      console.error("MCP sunucusu silinirken hata:", err)
      setError("MCP sunucusu silinirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-sky-400 flex items-center">
          <Server size={16} className="mr-2" />
          MCP Sunucuları
        </h3>
        <button
          onClick={() => setIsModalOpen(true)}
          className="text-xs bg-sky-900/30 hover:bg-sky-800/40 px-2 py-1 rounded-md text-sky-300 transition-colors border border-sky-700/30"
        >
          <PlusCircle size={12} className="inline mr-1" /> Ekle
        </button>
      </div>

      {error && (
        <div className="bg-rose-900/30 border border-rose-700/30 rounded-md p-3 text-rose-300 text-sm flex items-start">
          <AlertCircle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center items-center py-4">
          <RefreshCw size={20} className="animate-spin text-sky-400" />
        </div>
      ) : servers.length === 0 ? (
        <div className="text-center py-4 text-slate-400 text-sm">
          <p>Henüz MCP sunucusu eklenmemiş.</p>
          <p className="mt-1">Yeni bir MCP sunucusu eklemek için "Ekle" butonuna tıklayın.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {servers.map(server => (
            <div
              key={server.id}
              className="p-2 border border-sky-900/20 rounded-md bg-sky-900/10 hover:bg-sky-900/20 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="text-sm text-white font-medium">{server.name}</div>
                  {server.status && (
                    <div className="ml-2 flex items-center">
                      <div className={cn(
                        "w-2 h-2 rounded-full mr-1",
                        server.status === "online" ? "bg-emerald-400" :
                        server.status === "offline" ? "bg-slate-400" : "bg-rose-400"
                      )}></div>
                      <span className={cn(
                        "text-xs",
                        server.status === "online" ? "text-emerald-400" :
                        server.status === "offline" ? "text-slate-400" : "text-rose-400"
                      )}>
                        {server.status === "online" ? "Çevrimiçi" :
                         server.status === "offline" ? "Çevrimdışı" : "Hata"}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => toggleServerStatus(server.id)}
                    className="p-1 text-slate-400 hover:text-sky-400 transition-colors"
                    title={server.status === "online" ? "Devre Dışı Bırak" : "Etkinleştir"}
                  >
                    {server.status === "online" ? <PowerOff size={14} /> : <Power size={14} />}
                  </button>
                  <button
                    onClick={() => window.open(`http://localhost:8000/mcp/${server.id}`, '_blank')}
                    className="p-1 text-slate-400 hover:text-sky-400 transition-colors"
                    title="Sunucuya Git"
                    disabled={server.status !== "online"}
                  >
                    <ExternalLink size={14} className={server.status !== "online" ? "opacity-50" : ""} />
                  </button>
                  <button
                    onClick={() => deleteServer(server.id)}
                    className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                    title="Sil"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {server.command} {server.args.join(' ')}
              </div>
            </div>
          ))}
        </div>
      )}

      <MCPServerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={saveMCPServer}
      />
    </div>
  )
}
