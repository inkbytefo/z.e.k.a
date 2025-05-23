"use client"

import { useState } from "react"
import { X, Server, Info } from "lucide-react"
import { cn } from "@/lib/utils"

interface MCPServerModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (serverConfig: MCPServerConfig) => void
}

export interface MCPServerConfig {
  name: string
  command: string
  args: string[]
  env?: Record<string, string>
  disabled?: boolean
  autoApprove?: string[]
  fromGalleryId?: string
}

export default function MCPServerModal({ isOpen, onClose, onSave }: MCPServerModalProps) {
  const [serverName, setServerName] = useState("")
  const [command, setCommand] = useState("npx")
  const [args, setArgs] = useState("")
  const [envVars, setEnvVars] = useState("")
  const [galleryId, setGalleryId] = useState("")
  const [configJson, setConfigJson] = useState("")
  const [useJsonMode, setUseJsonMode] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens
  const resetForm = () => {
    setServerName("")
    setCommand("npx")
    setArgs("")
    setEnvVars("")
    setGalleryId("")
    setConfigJson("")
    setUseJsonMode(false)
    setError(null)
  }

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    try {
      if (useJsonMode) {
        // Parse JSON configuration
        try {
          const config = JSON.parse(configJson)
          if (!config.name || !config.command || !config.args) {
            setError("JSON yapılandırması geçersiz. 'name', 'command' ve 'args' alanları gereklidir.")
            return
          }

          onSave(config)
          onClose()
          resetForm()
        } catch (err) {
          setError("Geçersiz JSON formatı. Lütfen kontrol edin.")
        }
      } else {
        // Form mode
        if (!serverName.trim()) {
          setError("Sunucu adı gereklidir.")
          return
        }

        if (!command.trim()) {
          setError("Komut gereklidir.")
          return
        }

        if (!args.trim()) {
          setError("Argümanlar gereklidir.")
          return
        }

        // Parse environment variables
        const env: Record<string, string> = {}
        if (envVars.trim()) {
          envVars.split("\n").forEach(line => {
            const [key, value] = line.split("=").map(part => part.trim())
            if (key && value) {
              env[key] = value
            }
          })
        }

        // Create server config
        const serverConfig: MCPServerConfig = {
          name: serverName,
          command: command,
          args: args.split(" ").filter(arg => arg.trim() !== ""),
          env: Object.keys(env).length > 0 ? env : undefined,
          fromGalleryId: galleryId.trim() || undefined
        }

        onSave(serverConfig)
        onClose()
        resetForm()
      }
    } catch (err) {
      setError(`Bir hata oluştu: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-slate-900 border border-sky-700/30 rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-sky-700/30">
          <h2 className="text-lg font-medium text-sky-400 flex items-center">
            <Server size={18} className="mr-2" />
            MCP Sunucusu Ekle
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Toggle between form and JSON mode */}
          <div className="flex justify-end mb-2">
            <button
              type="button"
              onClick={() => setUseJsonMode(!useJsonMode)}
              className="text-xs bg-sky-900/30 hover:bg-sky-800/40 px-2 py-1 rounded-md text-sky-300 transition-colors border border-sky-700/30"
            >
              {useJsonMode ? "Form Moduna Geç" : "JSON Moduna Geç"}
            </button>
          </div>

          {error && (
            <div className="bg-rose-900/30 border border-rose-700/30 rounded-md p-3 text-rose-300 text-sm">
              {error}
            </div>
          )}

          {useJsonMode ? (
            <div className="space-y-2">
              <label className="block text-sm text-slate-300">
                JSON Yapılandırması
                <textarea
                  value={configJson}
                  onChange={(e) => setConfigJson(e.target.value)}
                  className="mt-1 w-full h-64 bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50 font-mono text-sm"
                  placeholder={`{\n  "name": "my-server",\n  "command": "npx",\n  "args": ["-y", "my-mcp-package"],\n  "env": {\n    "API_KEY": "your-api-key"\n  },\n  "disabled": false,\n  "autoApprove": ["function1", "function2"]\n}`}
                />
              </label>

              <div className="flex items-start text-xs text-slate-400">
                <Info size={14} className="mr-1 mt-0.5 text-sky-400" />
                <p>
                  JSON yapılandırması, MCP sunucusunun tüm özelliklerini içermelidir.
                  En azından "name", "command" ve "args" alanları gereklidir.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm text-slate-300">
                  Sunucu Adı
                  <input
                    type="text"
                    value={serverName}
                    onChange={(e) => setServerName(e.target.value)}
                    className="mt-1 w-full bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
                    placeholder="my-server"
                  />
                </label>
              </div>

              <div className="space-y-2">
                <label className="block text-sm text-slate-300">
                  Komut
                  <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    className="mt-1 w-full bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
                    placeholder="npx"
                  />
                </label>
              </div>

              <div className="space-y-2">
                <label className="block text-sm text-slate-300">
                  Argümanlar (boşlukla ayrılmış)
                  <input
                    type="text"
                    value={args}
                    onChange={(e) => setArgs(e.target.value)}
                    className="mt-1 w-full bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
                    placeholder="-y my-mcp-package"
                  />
                </label>
              </div>

              <div className="space-y-2">
                <label className="block text-sm text-slate-300">
                  Ortam Değişkenleri (her satırda bir KEY=VALUE)
                  <textarea
                    value={envVars}
                    onChange={(e) => setEnvVars(e.target.value)}
                    className="mt-1 w-full h-20 bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
                    placeholder="API_KEY=your-api-key\nDEBUG=true"
                  />
                </label>
                <div className="flex items-start text-xs text-slate-400">
                  <Info size={14} className="mr-1 mt-0.5 text-sky-400" />
                  <p>
                    Örnek: API_KEY=your-api-key, MEMORY_FILE_PATH=C:\path\to\file.json
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm text-slate-300">
                  Galeri ID (opsiyonel)
                  <input
                    type="text"
                    value={galleryId}
                    onChange={(e) => setGalleryId(e.target.value)}
                    className="mt-1 w-full bg-slate-800/70 border border-sky-700/30 rounded-md px-3 py-2 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500/50"
                    placeholder="author.package-name"
                  />
                </label>
                <div className="flex items-start text-xs text-slate-400">
                  <Info size={14} className="mr-1 mt-0.5 text-sky-400" />
                  <p>
                    Örnek: GLips.Figma-Context-MCP, kazuph.mcp-taskmanager
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-sky-900/30">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800/70 hover:bg-slate-700/70 rounded-md text-slate-300 transition-colors border border-slate-700/30"
            >
              İptal
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-sky-600 hover:bg-sky-700 rounded-md text-white transition-colors"
            >
              Kaydet
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
