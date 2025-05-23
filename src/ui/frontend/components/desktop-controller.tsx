"use client"

import { useState, useEffect } from "react"
import {
  Cpu, Monitor, Folder, Terminal, Camera, FileText,
  RefreshCw, Search, X, ChevronDown, ChevronUp,
  Maximize2, Minimize2, Eye, EyeOff, HardDrive,
  Thermometer, Clock, Laptop, ArrowUp,
  File, FolderOpen, Home, HardDriveIcon, FileIcon,
  MoreHorizontal, Trash2, Copy, FilePlus, FolderPlus
} from "lucide-react"
import { MemoryStick } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import {
  captureScreenshot,
  extractTextFromImage,
  executeCommand,
  listDirectory,
  listWindows,
  getSystemInfo,
  createFile,
  createDirectory,
  deleteItem,
  activateWindow,
  terminateProcess,
  type FileInfo,
  type WindowInfo,
  type SystemInfoResponse
} from "@/lib/desktop-api"

export default function DesktopController() {
  const [activeTab, setActiveTab] = useState("system")
  const [expanded, setExpanded] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sistem bilgileri
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse["data"] | null>(null)

  // Dosya gezgini
  const [currentPath, setCurrentPath] = useState("C:\\")
  const [directoryContents, setDirectoryContents] = useState<FileInfo[]>([])

  // Ekran görüntüsü
  const [screenshotData, setScreenshotData] = useState<string | null>(null)
  const [screenshotTimestamp, setScreenshotTimestamp] = useState<string | null>(null)

  // Metin tanıma
  const [extractedText, setExtractedText] = useState<string | null>(null)

  // Terminal
  const [commandInput, setCommandInput] = useState("")
  const [commandOutput, setCommandOutput] = useState<string | null>(null)

  // Pencere listesi
  const [windows, setWindows] = useState<WindowInfo[]>([])

  // Sistem bilgilerini yükle
  const loadSystemInfo = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await getSystemInfo()

      if (response.success) {
        setSystemInfo(response.data)
      } else {
        setError(response.message || "Sistem bilgileri alınamadı")
      }
    } catch (err) {
      console.error("Sistem bilgileri yüklenirken hata:", err)
      setError("Sistem bilgileri yüklenemedi")
    } finally {
      setLoading(false)
    }
  }

  // Dizin içeriğini yükle
  const loadDirectoryContents = async (path: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await listDirectory(path)

      if (response.success) {
        setDirectoryContents(response.data)
        setCurrentPath(path)
      } else {
        setError(response.message || "Dizin içeriği alınamadı")
      }
    } catch (err) {
      console.error("Dizin içeriği yüklenirken hata:", err)
      setError("Dizin içeriği yüklenemedi")
    } finally {
      setLoading(false)
    }
  }

  // Ekran görüntüsü al
  const takeScreenshot = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await captureScreenshot()

      if (response.success && response.data) {
        setScreenshotData(response.data.image_data)
        setScreenshotTimestamp(response.data.timestamp)
      } else {
        setError(response.message || "Ekran görüntüsü alınamadı")
      }
    } catch (err) {
      console.error("Ekran görüntüsü alınırken hata:", err)
      setError("Ekran görüntüsü alınamadı")
    } finally {
      setLoading(false)
    }
  }

  // Ekran görüntüsünden metin çıkar
  const extractText = async () => {
    if (!screenshotData) {
      setError("Önce bir ekran görüntüsü alın")
      return
    }

    try {
      setLoading(true)
      setError(null)

      const response = await extractTextFromImage(screenshotData)

      if (response.success && response.data) {
        setExtractedText(response.data.text)
      } else {
        setError(response.message || "Metin çıkarılamadı")
      }
    } catch (err) {
      console.error("Metin çıkarılırken hata:", err)
      setError("Metin çıkarılamadı")
    } finally {
      setLoading(false)
    }
  }

  // Komut çalıştır
  const runCommand = async () => {
    if (!commandInput.trim()) {
      return
    }

    try {
      setLoading(true)
      setError(null)

      const response = await executeCommand(commandInput)

      if (response.success) {
        setCommandOutput(response.data || "Komut başarıyla çalıştırıldı")
      } else {
        setError(response.message || "Komut çalıştırılamadı")
      }
    } catch (err) {
      console.error("Komut çalıştırılırken hata:", err)
      setError("Komut çalıştırılamadı")
    } finally {
      setLoading(false)
    }
  }

  // Pencereleri listele
  const loadWindows = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await listWindows()

      if (response.success) {
        setWindows(response.data)
      } else {
        setError(response.message || "Pencere listesi alınamadı")
      }
    } catch (err) {
      console.error("Pencere listesi alınırken hata:", err)
      setError("Pencere listesi alınamadı")
    } finally {
      setLoading(false)
    }
  }

  // Dosya boyutunu formatla
  const formatFileSize = (size: number): string => {
    if (size < 1024) {
      return `${size} B`
    } else if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(1)} KB`
    } else if (size < 1024 * 1024 * 1024) {
      return `${(size / (1024 * 1024)).toFixed(1)} MB`
    } else {
      return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`
    }
  }

  // Dosya yolunu panoya kopyala
  const handleCopyFilePath = (path: string) => {
    navigator.clipboard.writeText(path)
      .then(() => {
        // Başarılı kopyalama bildirimi
        setError("Dosya yolu panoya kopyalandı")
        setTimeout(() => setError(null), 2000)
      })
      .catch(err => {
        console.error("Kopyalama hatası:", err)
        setError("Dosya yolu kopyalanamadı")
      })
  }

  // Dosya veya klasör sil
  const handleDeleteItem = async (item: FileInfo) => {
    if (confirm(`"${item.name}" ${item.type === 'directory' ? 'klasörünü' : 'dosyasını'} silmek istediğinizden emin misiniz?`)) {
      try {
        setLoading(true)
        setError(null)

        // API çağrısı
        const response = await deleteItem(item.path, item.type === 'directory')

        if (response.success) {
          // Başarılı olursa dizini yenile
          await loadDirectoryContents(currentPath)
        } else {
          setError(response.message || `${item.name} silinemedi`)
        }
      } catch (err) {
        console.error("Öğe silme hatası:", err)
        setError("Öğe silme hatası")
      } finally {
        setLoading(false)
      }
    }
  }

  // Yeni klasör oluştur
  const handleCreateFolder = async () => {
    const folderName = prompt("Yeni klasör adı:")
    if (folderName) {
      try {
        setLoading(true)
        setError(null)

        // Tam yolu oluştur
        const fullPath = currentPath.endsWith('\\')
          ? `${currentPath}${folderName}`
          : `${currentPath}\\${folderName}`

        // API çağrısı
        const response = await createDirectory(fullPath)

        if (response.success) {
          // Başarılı olursa dizini yenile
          await loadDirectoryContents(currentPath)
        } else {
          setError(response.message || "Klasör oluşturulamadı")
        }
      } catch (err) {
        console.error("Klasör oluşturma hatası:", err)
        setError("Klasör oluşturma hatası")
      } finally {
        setLoading(false)
      }
    }
  }

  // Yeni dosya oluştur
  const handleCreateFile = async () => {
    const fileName = prompt("Yeni dosya adı:")
    if (fileName) {
      try {
        setLoading(true)
        setError(null)

        // Tam yolu oluştur
        const fullPath = currentPath.endsWith('\\')
          ? `${currentPath}${fileName}`
          : `${currentPath}\\${fileName}`

        // API çağrısı
        const response = await createFile(fullPath, "")

        if (response.success) {
          // Başarılı olursa dizini yenile
          await loadDirectoryContents(currentPath)
        } else {
          setError(response.message || "Dosya oluşturulamadı")
        }
      } catch (err) {
        console.error("Dosya oluşturma hatası:", err)
        setError("Dosya oluşturma hatası")
      } finally {
        setLoading(false)
      }
    }
  }

  // Pencereyi etkinleştir
  const handleActivateWindow = async (processId: number) => {
    try {
      setLoading(true)
      setError(null)

      // API çağrısı
      const response = await activateWindow(processId)

      if (response.success) {
        // Başarılı olursa pencere listesini yenile
        await loadWindows()
      } else {
        setError(response.message || "Pencere etkinleştirilemedi")
      }
    } catch (err) {
      console.error("Pencere etkinleştirme hatası:", err)
      setError("Pencere etkinleştirme hatası")
    } finally {
      setLoading(false)
    }
  }

  // İşlemi sonlandır
  const handleTerminateProcess = async (processId: number, processName: string) => {
    if (confirm(`"${processName}" işlemini sonlandırmak istediğinizden emin misiniz?`)) {
      try {
        setLoading(true)
        setError(null)

        // API çağrısı
        const response = await terminateProcess(processId)

        if (response.success) {
          // Başarılı olursa pencere listesini yenile
          await loadWindows()
        } else {
          setError(response.message || "İşlem sonlandırılamadı")
        }
      } catch (err) {
        console.error("İşlem sonlandırma hatası:", err)
        setError("İşlem sonlandırma hatası")
      } finally {
        setLoading(false)
      }
    }
  }

  // Aktif sekmeye göre veri yükle
  useEffect(() => {
    if (activeTab === "system") {
      loadSystemInfo()
    } else if (activeTab === "files") {
      loadDirectoryContents(currentPath)
    } else if (activeTab === "windows") {
      loadWindows()
    }
  }, [activeTab])

  return (
    <Card className="bg-black/40 backdrop-blur-md border-cyan-500/20 rounded-2xl shadow-[inset_0_1px_60px_rgba(0,170,196,0.05)] transition-all duration-300 hover:shadow-[inset_0_1px_80px_rgba(0,170,196,0.1)]">
      <CardHeader className="p-4 pb-2 flex justify-between items-center">
        <CardTitle className="text-cyan-400 text-sm font-medium flex items-center">
          <Laptop size={16} className="mr-2" />
          Masaüstü Denetleyicisi
        </CardTitle>
        <div className="flex space-x-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-400 hover:text-cyan-400 transition-colors"
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="p-4 pt-2">
          <Tabs defaultValue={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid grid-cols-5 mb-4">
              <TabsTrigger value="system" className="text-xs">
                <Cpu size={14} className="mr-1" />
                <span className="hidden sm:inline">Sistem</span>
              </TabsTrigger>
              <TabsTrigger value="files" className="text-xs">
                <Folder size={14} className="mr-1" />
                <span className="hidden sm:inline">Dosyalar</span>
              </TabsTrigger>
              <TabsTrigger value="terminal" className="text-xs">
                <Terminal size={14} className="mr-1" />
                <span className="hidden sm:inline">Terminal</span>
              </TabsTrigger>
              <TabsTrigger value="screenshot" className="text-xs">
                <Camera size={14} className="mr-1" />
                <span className="hidden sm:inline">Ekran</span>
              </TabsTrigger>
              <TabsTrigger value="windows" className="text-xs">
                <Monitor size={14} className="mr-1" />
                <span className="hidden sm:inline">Pencereler</span>
              </TabsTrigger>
            </TabsList>

            {/* Sistem Bilgileri */}
            <TabsContent value="system" className="mt-0">
              {loading ? (
                <div className="flex justify-center py-4">
                  <RefreshCw size={20} className="animate-spin text-cyan-400" />
                </div>
              ) : error ? (
                <div className="text-red-400 text-sm py-2">{error}</div>
              ) : systemInfo ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-black/30 p-2 rounded-lg">
                      <div className="text-xs text-gray-400 mb-1 flex items-center">
                        <Laptop size={12} className="mr-1 text-cyan-400" />
                        İşletim Sistemi
                      </div>
                      <div className="text-sm text-white">{systemInfo.os} {systemInfo.version}</div>
                    </div>
                    <div className="bg-black/30 p-2 rounded-lg">
                      <div className="text-xs text-gray-400 mb-1 flex items-center">
                        <Clock size={12} className="mr-1 text-cyan-400" />
                        Çalışma Süresi
                      </div>
                      <div className="text-sm text-white">
                        {Math.floor(systemInfo.uptime / 3600)} saat {Math.floor((systemInfo.uptime % 3600) / 60)} dk
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="text-xs text-gray-400 flex items-center">
                        <Thermometer size={12} className="mr-1 text-cyan-400" />
                        CPU Kullanımı
                      </div>
                      <div className="text-xs text-white">{systemInfo.cpu_usage.toFixed(1)}%</div>
                    </div>
                    <Progress value={systemInfo.cpu_usage} className="h-1 bg-gray-800" />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="text-xs text-gray-400 flex items-center">
                        <MemoryStick size={12} className="mr-1 text-cyan-400" />
                        Bellek Kullanımı
                      </div>
                      <div className="text-xs text-white">
                        {(systemInfo.memory_usage / 1024).toFixed(1)} GB / {(systemInfo.total_memory / 1024).toFixed(1)} GB
                      </div>
                    </div>
                    <Progress
                      value={(systemInfo.memory_usage / systemInfo.total_memory) * 100}
                      className="h-1 bg-gray-800"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <div className="text-xs text-gray-400 flex items-center">
                        <HardDrive size={12} className="mr-1 text-cyan-400" />
                        Disk Kullanımı
                      </div>
                      <div className="text-xs text-white">
                        {(systemInfo.disk_usage / 1024).toFixed(1)} GB / {(systemInfo.total_disk / 1024).toFixed(1)} GB
                      </div>
                    </div>
                    <Progress
                      value={(systemInfo.disk_usage / systemInfo.total_disk) * 100}
                      className="h-1 bg-gray-800"
                    />
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2 text-xs bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={loadSystemInfo}
                  >
                    <RefreshCw size={12} className="mr-1" />
                    Yenile
                  </Button>
                </div>
              ) : (
                <div className="text-center py-4 text-gray-400 text-sm">
                  Sistem bilgileri yükleniyor...
                </div>
              )}
            </TabsContent>

            {/* Dosya Gezgini */}
            <TabsContent value="files" className="mt-0">
              <div className="space-y-2">
                {/* Dosya yolu ve navigasyon */}
                <div className="flex items-center space-x-2 mb-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={() => loadDirectoryContents(currentPath.split('\\').slice(0, -1).join('\\') || 'C:\\')}
                    disabled={loading || currentPath === 'C:\\'}
                    title="Üst Dizin"
                  >
                    <ArrowUp size={14} />
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={() => loadDirectoryContents('C:\\')}
                    disabled={loading}
                    title="Ana Dizin"
                  >
                    <Home size={14} />
                  </Button>

                  <Input
                    value={currentPath}
                    onChange={(e) => setCurrentPath(e.target.value)}
                    className="flex-1 bg-black/30 border-cyan-500/20 text-white text-xs"
                    onKeyDown={(e) => e.key === 'Enter' && loadDirectoryContents(currentPath)}
                  />

                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={() => loadDirectoryContents(currentPath)}
                    disabled={loading}
                  >
                    {loading ? <RefreshCw size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                  </Button>
                </div>

                {error && <div className="text-red-400 text-xs">{error}</div>}

                {/* Dosya ve klasör listesi */}
                <div className="bg-black/30 rounded-lg border border-gray-800 overflow-hidden">
                  {loading ? (
                    <div className="flex justify-center py-8">
                      <RefreshCw size={20} className="animate-spin text-cyan-400" />
                    </div>
                  ) : directoryContents.length > 0 ? (
                    <div className="max-h-64 overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-black/50 sticky top-0">
                          <tr>
                            <th className="text-left p-2 text-gray-400">Tür</th>
                            <th className="text-left p-2 text-gray-400">Ad</th>
                            <th className="text-right p-2 text-gray-400">Boyut</th>
                            <th className="text-right p-2 text-gray-400">İşlemler</th>
                          </tr>
                        </thead>
                        <tbody>
                          {directoryContents.map((item, index) => (
                            <tr
                              key={index}
                              className="border-t border-gray-800 hover:bg-cyan-950/20 transition-colors"
                            >
                              <td className="p-2">
                                {item.type === 'directory' ? (
                                  <FolderOpen size={16} className="text-yellow-400" />
                                ) : (
                                  <FileIcon size={16} className="text-blue-400" />
                                )}
                              </td>
                              <td
                                className={`p-2 ${item.type === 'directory' ? 'text-yellow-300' : 'text-white'} cursor-pointer`}
                                onClick={() => item.type === 'directory' ? loadDirectoryContents(item.path) : null}
                              >
                                {item.name}
                              </td>
                              <td className="p-2 text-right text-gray-400">
                                {item.type === 'file' && item.size ? formatFileSize(item.size) : ''}
                              </td>
                              <td className="p-2 text-right">
                                <div className="flex justify-end space-x-1">
                                  {item.type === 'file' && (
                                    <button
                                      className="text-gray-400 hover:text-cyan-400 transition-colors"
                                      title="Dosyayı Kopyala"
                                      onClick={() => handleCopyFilePath(item.path)}
                                    >
                                      <Copy size={14} />
                                    </button>
                                  )}
                                  <button
                                    className="text-gray-400 hover:text-red-400 transition-colors"
                                    title="Sil"
                                    onClick={() => handleDeleteItem(item)}
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-400">
                      Bu dizin boş
                    </div>
                  )}
                </div>

                {/* Yeni dosya/klasör oluşturma */}
                <div className="flex justify-between mt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={() => handleCreateFolder()}
                  >
                    <FolderPlus size={14} className="mr-1" />
                    Yeni Klasör
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={() => handleCreateFile()}
                  >
                    <FilePlus size={14} className="mr-1" />
                    Yeni Dosya
                  </Button>
                </div>
              </div>
            </TabsContent>

            {/* Terminal */}
            <TabsContent value="terminal" className="mt-0">
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <Input
                    value={commandInput}
                    onChange={(e) => setCommandInput(e.target.value)}
                    placeholder="Komut girin..."
                    className="flex-1 bg-black/30 border-cyan-500/20 text-white text-xs"
                    onKeyDown={(e) => e.key === 'Enter' && runCommand()}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={runCommand}
                    disabled={loading}
                  >
                    {loading ? <RefreshCw size={14} className="animate-spin" /> : <Terminal size={14} />}
                  </Button>
                </div>

                {error && <div className="text-red-400 text-xs">{error}</div>}

                {commandOutput && (
                  <div className="bg-black/50 border border-gray-800 rounded-md p-2 text-xs text-gray-300 font-mono max-h-32 overflow-y-auto">
                    <pre className="whitespace-pre-wrap">{commandOutput}</pre>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Ekran Görüntüsü */}
            <TabsContent value="screenshot" className="mt-0">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={takeScreenshot}
                    disabled={loading}
                  >
                    {loading ? <RefreshCw size={14} className="mr-1 animate-spin" /> : <Camera size={14} className="mr-1" />}
                    Ekran Görüntüsü Al
                  </Button>

                  {screenshotData && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                      onClick={extractText}
                      disabled={loading}
                    >
                      {loading ? <RefreshCw size={14} className="mr-1 animate-spin" /> : <FileText size={14} className="mr-1" />}
                      Metin Çıkar
                    </Button>
                  )}
                </div>

                {error && <div className="text-red-400 text-xs">{error}</div>}

                {screenshotData && (
                  <div className="space-y-2">
                    <div className="bg-black/30 rounded-md overflow-hidden">
                      <img
                        src={`data:image/png;base64,${screenshotData}`}
                        alt="Ekran görüntüsü"
                        className="w-full h-auto"
                      />
                    </div>

                    {screenshotTimestamp && (
                      <div className="text-xs text-gray-400 text-center">
                        {new Date(screenshotTimestamp).toLocaleString()}
                      </div>
                    )}
                  </div>
                )}

                {extractedText && (
                  <div className="bg-black/50 border border-gray-800 rounded-md p-2 text-xs text-gray-300 font-mono max-h-32 overflow-y-auto">
                    <div className="text-xs text-cyan-400 mb-1">Çıkarılan Metin:</div>
                    <pre className="whitespace-pre-wrap">{extractedText}</pre>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Pencereler */}
            <TabsContent value="windows" className="mt-0">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm text-white font-medium">Açık Pencereler</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-cyan-950/30 border-cyan-500/20 text-cyan-400 hover:bg-cyan-900/30"
                    onClick={loadWindows}
                    disabled={loading}
                  >
                    {loading ? <RefreshCw size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                  </Button>
                </div>

                {error && <div className="text-red-400 text-xs">{error}</div>}

                <div className="bg-black/30 rounded-lg border border-gray-800 overflow-hidden">
                  {loading ? (
                    <div className="flex justify-center py-8">
                      <RefreshCw size={20} className="animate-spin text-cyan-400" />
                    </div>
                  ) : windows.length > 0 ? (
                    <div className="max-h-64 overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-black/50 sticky top-0">
                          <tr>
                            <th className="text-left p-2 text-gray-400">Durum</th>
                            <th className="text-left p-2 text-gray-400">Başlık</th>
                            <th className="text-left p-2 text-gray-400">İşlem</th>
                            <th className="text-right p-2 text-gray-400">İşlemler</th>
                          </tr>
                        </thead>
                        <tbody>
                          {windows.map((window, index) => (
                            <tr
                              key={index}
                              className={`border-t border-gray-800 hover:bg-cyan-950/20 transition-colors ${window.is_active ? 'bg-cyan-950/30' : ''}`}
                            >
                              <td className="p-2">
                                <div className={`w-2 h-2 rounded-full ${window.is_active ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                              </td>
                              <td className="p-2 text-white">
                                {window.title || 'Başlıksız Pencere'}
                              </td>
                              <td className="p-2 text-gray-400">
                                {window.process_name} ({window.process_id})
                              </td>
                              <td className="p-2 text-right">
                                <div className="flex justify-end space-x-1">
                                  <button
                                    className="text-gray-400 hover:text-cyan-400 transition-colors"
                                    title="Pencereyi Etkinleştir"
                                    onClick={() => handleActivateWindow(window.process_id)}
                                  >
                                    <Maximize2 size={14} />
                                  </button>
                                  <button
                                    className="text-gray-400 hover:text-red-400 transition-colors"
                                    title="İşlemi Sonlandır"
                                    onClick={() => handleTerminateProcess(window.process_id, window.process_name)}
                                  >
                                    <X size={14} />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-400">
                      Açık pencere bulunamadı
                    </div>
                  )}
                </div>

                <div className="bg-black/20 rounded-lg p-3 text-xs text-gray-400">
                  <p>Not: Pencere yönetimi işlevleri işletim sistemine ve izinlere bağlı olarak sınırlı olabilir.</p>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      )}
    </Card>
  )
}
