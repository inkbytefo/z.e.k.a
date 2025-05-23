# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Proaktif Öneri API Rotaları

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from pydantic import BaseModel

from core.vector_database import VectorDatabase
from core.user_profile import UserProfile
from core.behavior_tracker import UserBehaviorTracker, InteractionType
from core.proactive_assistant import ProactiveAssistant, SuggestionType
from config import PROFILES_PATH

# Router oluştur
router = APIRouter(
    prefix="/api/proactive",
    tags=["proactive"],
    responses={404: {"description": "Not found"}},
)

# Modelleri tanımla
class TrackInteractionRequest(BaseModel):
    user_id: str
    interaction_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class TrackInteractionResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class SuggestionResponse(BaseModel):
    id: Optional[str] = None
    content: str
    type: str
    confidence: float
    reason: str
    metadata: Optional[Dict[str, Any]] = None

class SuggestionsResponse(BaseModel):
    success: bool
    suggestions: List[SuggestionResponse]
    message: Optional[str] = None

class NextActionRequest(BaseModel):
    user_id: str
    context: Optional[str] = None

class NextActionResponse(BaseModel):
    success: bool
    suggestion: Optional[SuggestionResponse] = None
    message: Optional[str] = None

# Proaktif asistanlar için önbellek
proactive_assistants: Dict[str, ProactiveAssistant] = {}

# Yardımcı fonksiyonlar
async def get_proactive_assistant(user_id: str) -> ProactiveAssistant:
    """Kullanıcı için proaktif asistanı getirir veya oluşturur.
    
    Args:
        user_id: Kullanıcı ID'si
        
    Returns:
        ProactiveAssistant: Proaktif asistan
    """
    if user_id in proactive_assistants:
        return proactive_assistants[user_id]
    
    # Vektör veritabanını al
    vector_db = VectorDatabase.get_instance()
    
    # Kullanıcı profilini al
    user_profile = UserProfile(user_id, storage_path=PROFILES_PATH)
    
    # Davranış izleyiciyi oluştur
    behavior_tracker = UserBehaviorTracker(user_id, vector_db)
    
    # Proaktif asistanı oluştur
    assistant = ProactiveAssistant(user_id, vector_db, user_profile, behavior_tracker)
    
    # Asistanı başlat
    await assistant.initialize()
    
    # Önbelleğe ekle
    proactive_assistants[user_id] = assistant
    
    return assistant

@router.post("/track", response_model=TrackInteractionResponse)
async def track_interaction(request: TrackInteractionRequest):
    """Kullanıcı etkileşimini kaydeder.
    
    Args:
        request: Etkileşim bilgileri
        
    Returns:
        TrackInteractionResponse: İşlem sonucu
    """
    try:
        # Proaktif asistanı al
        assistant = await get_proactive_assistant(request.user_id)
        
        # Etkileşimi kaydet
        success = await assistant.behavior_tracker.track_interaction(
            interaction_type=request.interaction_type,
            content=request.content,
            metadata=request.metadata
        )
        
        if success:
            return {
                "success": True,
                "message": "Etkileşim başarıyla kaydedildi"
            }
        else:
            return {
                "success": False,
                "message": "Etkileşim kaydedilemedi"
            }
    except Exception as e:
        logging.error(f"Etkileşim kaydedilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Etkileşim kaydedilemedi: {str(e)}"
        )

@router.get("/suggestions/time", response_model=SuggestionsResponse)
async def get_time_based_suggestions(user_id: str, top_n: int = 3):
    """Zamana dayalı öneriler getirir.
    
    Args:
        user_id: Kullanıcı ID'si
        top_n: Maksimum öneri sayısı
        
    Returns:
        SuggestionsResponse: Öneri listesi
    """
    try:
        # Proaktif asistanı al
        assistant = await get_proactive_assistant(user_id)
        
        # Zamana dayalı önerileri al
        suggestions = await assistant.get_suggestions_by_time(top_n=top_n)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": f"{len(suggestions)} zamana dayalı öneri bulundu"
        }
    except Exception as e:
        logging.error(f"Zamana dayalı öneriler getirilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Zamana dayalı öneriler getirilemedi: {str(e)}"
        )

@router.get("/suggestions/context", response_model=SuggestionsResponse)
async def get_context_based_suggestions(user_id: str, context: str, top_n: int = 3):
    """Bağlama dayalı öneriler getirir.
    
    Args:
        user_id: Kullanıcı ID'si
        context: Bağlam metni
        top_n: Maksimum öneri sayısı
        
    Returns:
        SuggestionsResponse: Öneri listesi
    """
    try:
        # Proaktif asistanı al
        assistant = await get_proactive_assistant(user_id)
        
        # Bağlama dayalı önerileri al
        suggestions = await assistant.get_suggestions_by_context(context=context, top_n=top_n)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": f"{len(suggestions)} bağlama dayalı öneri bulundu"
        }
    except Exception as e:
        logging.error(f"Bağlama dayalı öneriler getirilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bağlama dayalı öneriler getirilemedi: {str(e)}"
        )

@router.get("/suggestions/pattern", response_model=SuggestionsResponse)
async def get_pattern_based_suggestions(user_id: str, top_n: int = 3):
    """Davranış örüntüsüne dayalı öneriler getirir.
    
    Args:
        user_id: Kullanıcı ID'si
        top_n: Maksimum öneri sayısı
        
    Returns:
        SuggestionsResponse: Öneri listesi
    """
    try:
        # Proaktif asistanı al
        assistant = await get_proactive_assistant(user_id)
        
        # Davranış örüntüsüne dayalı önerileri al
        suggestions = await assistant.get_suggestions_by_pattern(top_n=top_n)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": f"{len(suggestions)} davranış örüntüsüne dayalı öneri bulundu"
        }
    except Exception as e:
        logging.error(f"Davranış örüntüsüne dayalı öneriler getirilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Davranış örüntüsüne dayalı öneriler getirilemedi: {str(e)}"
        )

@router.post("/next-action", response_model=NextActionResponse)
async def suggest_next_action(request: NextActionRequest):
    """Kullanıcının bir sonraki olası eylemini önerir.
    
    Args:
        request: İstek bilgileri
        
    Returns:
        NextActionResponse: Öneri
    """
    try:
        # Proaktif asistanı al
        assistant = await get_proactive_assistant(request.user_id)
        
        # Bir sonraki eylemi öner
        suggestion = await assistant.suggest_next_action(context=request.context)
        
        if suggestion:
            return {
                "success": True,
                "suggestion": suggestion,
                "message": "Bir sonraki eylem önerisi bulundu"
            }
        else:
            return {
                "success": False,
                "suggestion": None,
                "message": "Bir sonraki eylem önerisi bulunamadı"
            }
    except Exception as e:
        logging.error(f"Bir sonraki eylem önerilirken hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bir sonraki eylem önerilemedi: {str(e)}"
        )
