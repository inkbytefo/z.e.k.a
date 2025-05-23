import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'
import { v4 as uuidv4 } from 'uuid'

// MCP config dosya yolu
const MCP_CONFIG_PATH = path.join(process.cwd(), '..', 'data', 'mcp', 'mcp_config.json')

// MCP config dosyasını oku
async function readMCPConfig() {
  try {
    // Dosya yoksa boş bir yapılandırma oluştur
    if (!fs.existsSync(MCP_CONFIG_PATH)) {
      return { mcpServers: {} }
    }
    
    const data = await fs.promises.readFile(MCP_CONFIG_PATH, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('MCP yapılandırması okunurken hata:', error)
    return { mcpServers: {} }
  }
}

// MCP config dosyasını yaz
async function writeMCPConfig(config: any) {
  try {
    const dirPath = path.dirname(MCP_CONFIG_PATH)
    
    // Dizin yoksa oluştur
    if (!fs.existsSync(dirPath)) {
      await fs.promises.mkdir(dirPath, { recursive: true })
    }
    
    await fs.promises.writeFile(
      MCP_CONFIG_PATH, 
      JSON.stringify(config, null, 2),
      'utf8'
    )
    return true
  } catch (error) {
    console.error('MCP yapılandırması yazılırken hata:', error)
    return false
  }
}

// GET: MCP sunucularını listele
export async function GET(request: NextRequest) {
  try {
    const config = await readMCPConfig()
    return NextResponse.json(config)
  } catch (error) {
    console.error('MCP sunucuları listelenirken hata:', error)
    return NextResponse.json(
      { error: 'MCP sunucuları listelenirken bir hata oluştu' },
      { status: 500 }
    )
  }
}

// POST: Yeni MCP sunucusu ekle
export async function POST(request: NextRequest) {
  try {
    const serverConfig = await request.json()
    
    // Gerekli alanları kontrol et
    if (!serverConfig.name || !serverConfig.command || !serverConfig.args) {
      return NextResponse.json(
        { error: 'Geçersiz sunucu yapılandırması. name, command ve args alanları gereklidir.' },
        { status: 400 }
      )
    }
    
    // Mevcut yapılandırmayı oku
    const config = await readMCPConfig()
    
    // Sunucu ID'si oluştur (veya mevcut adı kullan)
    const serverId = serverConfig.name.toLowerCase().replace(/\s+/g, '-')
    
    // Aynı ID'ye sahip sunucu var mı kontrol et
    if (config.mcpServers[serverId]) {
      return NextResponse.json(
        { error: `"${serverId}" ID'sine sahip bir sunucu zaten mevcut.` },
        { status: 409 }
      )
    }
    
    // Yeni sunucuyu ekle
    config.mcpServers[serverId] = {
      command: serverConfig.command,
      args: serverConfig.args,
      ...(serverConfig.env && { env: serverConfig.env }),
      ...(serverConfig.disabled !== undefined && { disabled: serverConfig.disabled }),
      ...(serverConfig.autoApprove && { autoApprove: serverConfig.autoApprove }),
      ...(serverConfig.fromGalleryId && { fromGalleryId: serverConfig.fromGalleryId })
    }
    
    // Yapılandırmayı kaydet
    await writeMCPConfig(config)
    
    return NextResponse.json({ 
      success: true, 
      id: serverId,
      message: `"${serverConfig.name}" sunucusu başarıyla eklendi.`
    })
  } catch (error) {
    console.error('MCP sunucusu eklenirken hata:', error)
    return NextResponse.json(
      { error: 'MCP sunucusu eklenirken bir hata oluştu' },
      { status: 500 }
    )
  }
}
