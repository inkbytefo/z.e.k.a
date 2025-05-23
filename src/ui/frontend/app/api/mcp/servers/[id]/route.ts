import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

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

// GET: Belirli bir MCP sunucusunu getir
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    const config = await readMCPConfig()
    
    if (!config.mcpServers[id]) {
      return NextResponse.json(
        { error: `"${id}" ID'sine sahip sunucu bulunamadı.` },
        { status: 404 }
      )
    }
    
    return NextResponse.json({
      id,
      ...config.mcpServers[id]
    })
  } catch (error) {
    console.error('MCP sunucusu alınırken hata:', error)
    return NextResponse.json(
      { error: 'MCP sunucusu alınırken bir hata oluştu' },
      { status: 500 }
    )
  }
}

// PUT: MCP sunucusunu güncelle
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    const serverConfig = await request.json()
    
    // Mevcut yapılandırmayı oku
    const config = await readMCPConfig()
    
    // Sunucu var mı kontrol et
    if (!config.mcpServers[id]) {
      return NextResponse.json(
        { error: `"${id}" ID'sine sahip sunucu bulunamadı.` },
        { status: 404 }
      )
    }
    
    // Sunucuyu güncelle
    config.mcpServers[id] = {
      ...config.mcpServers[id],
      ...(serverConfig.command && { command: serverConfig.command }),
      ...(serverConfig.args && { args: serverConfig.args }),
      ...(serverConfig.env && { env: serverConfig.env }),
      ...(serverConfig.disabled !== undefined && { disabled: serverConfig.disabled }),
      ...(serverConfig.autoApprove && { autoApprove: serverConfig.autoApprove }),
      ...(serverConfig.fromGalleryId && { fromGalleryId: serverConfig.fromGalleryId })
    }
    
    // Yapılandırmayı kaydet
    await writeMCPConfig(config)
    
    return NextResponse.json({ 
      success: true, 
      id,
      message: `"${id}" sunucusu başarıyla güncellendi.`
    })
  } catch (error) {
    console.error('MCP sunucusu güncellenirken hata:', error)
    return NextResponse.json(
      { error: 'MCP sunucusu güncellenirken bir hata oluştu' },
      { status: 500 }
    )
  }
}

// DELETE: MCP sunucusunu sil
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    
    // Mevcut yapılandırmayı oku
    const config = await readMCPConfig()
    
    // Sunucu var mı kontrol et
    if (!config.mcpServers[id]) {
      return NextResponse.json(
        { error: `"${id}" ID'sine sahip sunucu bulunamadı.` },
        { status: 404 }
      )
    }
    
    // Sunucuyu sil
    delete config.mcpServers[id]
    
    // Yapılandırmayı kaydet
    await writeMCPConfig(config)
    
    return NextResponse.json({ 
      success: true, 
      message: `"${id}" sunucusu başarıyla silindi.`
    })
  } catch (error) {
    console.error('MCP sunucusu silinirken hata:', error)
    return NextResponse.json(
      { error: 'MCP sunucusu silinirken bir hata oluştu' },
      { status: 500 }
    )
  }
}
