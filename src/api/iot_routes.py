# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# IoT API Rotaları

import os
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.iot import (
    IoTDeviceManager,
    DeviceType,
    DevicePlatform,
    DeviceCapability
)
from config import IOT_CONFIG

# Router oluştur
router = APIRouter(
    prefix="/api/iot",
    tags=["iot"],
    responses={404: {"description": "Not found"}},
)

# Modelleri tanımla
class DeviceResponse(BaseModel):
    device_id: str
    name: str
    device_type: str
    platform: str
    capabilities: List[str]
    state: Dict[str, Any]
    last_updated: Optional[str] = None
    available: bool

class DevicesResponse(BaseModel):
    devices: List[DeviceResponse]

class DeviceStateResponse(BaseModel):
    device_id: str
    state: Dict[str, Any]
    last_updated: Optional[str] = None

class DeviceControlRequest(BaseModel):
    command: str
    params: Optional[Dict[str, Any]] = None

class DeviceControlResponse(BaseModel):
    success: bool
    device_id: str
    message: Optional[str] = None

class DeviceStateChangeMessage(BaseModel):
    device_id: str
    state: Dict[str, Any]
    timestamp: str

# IoT cihaz yöneticisi
device_manager = None

# WebSocket bağlantıları
websocket_connections: List[WebSocket] = []

# Yardımcı fonksiyonlar
async def get_device_manager() -> IoTDeviceManager:
    """IoT cihaz yöneticisini getirir veya oluşturur.
    
    Returns:
        IoTDeviceManager: IoT cihaz yöneticisi
    """
    global device_manager
    
    if device_manager is None:
        # IoT yapılandırmasını al
        config = IOT_CONFIG
        
        # Cihaz yöneticisini oluştur
        device_manager = IoTDeviceManager(config)
        
        # Cihaz yöneticisini başlat
        await device_manager.initialize()
        
        # Durum değişikliği callback'ini kaydet
        await device_manager.register_state_change_callback(on_device_state_change)
    
    return device_manager

async def on_device_state_change(device_id: str, state: Dict[str, Any]) -> None:
    """Cihaz durumu değiştiğinde çağrılır.
    
    Args:
        device_id: Cihaz ID'si
        state: Yeni durum
    """
    # Bağlı WebSocket'lere bildir
    if websocket_connections:
        # Cihazı al
        dm = await get_device_manager()
        device = await dm.get_device(device_id)
        
        if device and device.last_updated:
            # Mesajı oluştur
            message = DeviceStateChangeMessage(
                device_id=device_id,
                state=state,
                timestamp=device.last_updated.isoformat()
            )
            
            # Tüm bağlantılara gönder
            for connection in websocket_connections:
                try:
                    await connection.send_json(message.dict())
                except Exception:
                    pass

@router.get("/devices", response_model=DevicesResponse)
async def get_devices(
    device_type: Optional[str] = None,
    platform: Optional[str] = None,
    capability: Optional[str] = None
):
    """Cihazları listeler.
    
    Args:
        device_type: Cihaz tipi filtresi (opsiyonel)
        platform: Platform filtresi (opsiyonel)
        capability: Yetenek filtresi (opsiyonel)
        
    Returns:
        DevicesResponse: Cihaz listesi
    """
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()
        
        # Cihazları getir
        devices = await dm.get_devices(device_type, platform, capability)
        
        # Yanıt oluştur
        response_devices = []
        for device in devices:
            response_devices.append(DeviceResponse(
                device_id=device.device_id,
                name=device.name,
                device_type=device.device_type.value,
                platform=device.platform.value,
                capabilities=[cap.value for cap in device.capabilities],
                state=device.state,
                last_updated=device.last_updated.isoformat() if device.last_updated else None,
                available=device.available
            ))
        
        return {"devices": response_devices}
    except Exception as e:
        logging.error(f"Cihazlar listelenirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cihazlar listelenirken hata: {str(e)}"
        )

@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str):
    """Belirli bir cihazı getirir.
    
    Args:
        device_id: Cihaz ID'si
        
    Returns:
        DeviceResponse: Cihaz bilgileri
    """
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()
        
        # Cihazı getir
        device = await dm.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cihaz bulunamadı: {device_id}"
            )
        
        # Yanıt oluştur
        return DeviceResponse(
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type.value,
            platform=device.platform.value,
            capabilities=[cap.value for cap in device.capabilities],
            state=device.state,
            last_updated=device.last_updated.isoformat() if device.last_updated else None,
            available=device.available
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Cihaz getirilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cihaz getirilirken hata: {str(e)}"
        )

@router.get("/devices/{device_id}/state", response_model=DeviceStateResponse)
async def get_device_state(device_id: str):
    """Belirli bir cihazın durumunu getirir.
    
    Args:
        device_id: Cihaz ID'si
        
    Returns:
        DeviceStateResponse: Cihaz durumu
    """
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()
        
        # Cihazı getir
        device = await dm.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cihaz bulunamadı: {device_id}"
            )
        
        # Cihaz durumunu getir
        state = await dm.get_device_state(device_id)
        
        # Yanıt oluştur
        return DeviceStateResponse(
            device_id=device_id,
            state=state or {},
            last_updated=device.last_updated.isoformat() if device.last_updated else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Cihaz durumu getirilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cihaz durumu getirilirken hata: {str(e)}"
        )

@router.post("/devices/{device_id}/control", response_model=DeviceControlResponse)
async def control_device(device_id: str, request: DeviceControlRequest):
    """Bir cihazı kontrol eder.
    
    Args:
        device_id: Cihaz ID'si
        request: Kontrol isteği
        
    Returns:
        DeviceControlResponse: Kontrol sonucu
    """
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()
        
        # Cihazı getir
        device = await dm.get_device(device_id)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cihaz bulunamadı: {device_id}"
            )
        
        # Cihazı kontrol et
        success = await dm.control_device(device_id, request.command, request.params)
        
        if success:
            return DeviceControlResponse(
                success=True,
                device_id=device_id,
                message=f"Cihaz başarıyla kontrol edildi: {request.command}"
            )
        else:
            return DeviceControlResponse(
                success=False,
                device_id=device_id,
                message=f"Cihaz kontrol edilemedi: {request.command}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Cihaz kontrol edilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cihaz kontrol edilirken hata: {str(e)}"
        )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint'i.
    
    Bu endpoint, cihaz durumu değişikliklerini gerçek zamanlı olarak almak için kullanılır.
    """
    await websocket.accept()
    
    # Bağlantıyı listeye ekle
    websocket_connections.append(websocket)
    
    try:
        # Cihaz yöneticisini al
        dm = await get_device_manager()
        
        # Bağlantı durumu mesajı
        await websocket.send_json({
            "type": "connection_status",
            "status": "connected",
            "message": "IoT WebSocket bağlantısı kuruldu"
        })
        
        # Mesajları dinle
        while True:
            data = await websocket.receive_text()
            
            # Mesajı işle (gelecekte kullanılabilir)
            await websocket.send_json({
                "type": "echo",
                "data": data
            })
            
    except WebSocketDisconnect:
        logging.info("WebSocket bağlantısı kapatıldı")
    except Exception as e:
        logging.error(f"WebSocket hatası: {str(e)}")
    finally:
        # Bağlantıyı listeden çıkar
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
