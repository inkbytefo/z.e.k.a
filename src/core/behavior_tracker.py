# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Kullanıcı Davranış İzleme Modülü

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging

from .vector_database import VectorDatabase
from .logging_manager import get_logger

class InteractionType(Enum):
    """Kullanıcı etkileşim tipleri."""
    QUERY = "query"  # Kullanıcı sorgusu
    COMMAND = "command"  # Komut çalıştırma
    FEEDBACK = "feedback"  # Geri bildirim
    PREFERENCE = "preference"  # Tercih değişikliği
    NAVIGATION = "navigation"  # Sayfa gezinme
    SEARCH = "search"  # Arama yapma
    VOICE = "voice"  # Sesli komut
    TASK = "task"  # Görev oluşturma/tamamlama
    SCHEDULE = "schedule"  # Zamanlama
    REMINDER = "reminder"  # Hatırlatıcı
    OTHER = "other"  # Diğer

class UserBehaviorTracker:
    """Kullanıcı davranışlarını izleyen ve kaydeden sınıf.
    
    Bu sınıf, kullanıcının etkileşimlerini izler, kaydeder ve
    vektör veritabanında saklar. Bu veriler, proaktif öneriler
    ve kişiselleştirme için kullanılır.
    """
    
    def __init__(self, user_id: str, vector_db: VectorDatabase):
        """UserBehaviorTracker başlatıcısı.
        
        Args:
            user_id: Kullanıcı ID'si
            vector_db: Vektör veritabanı
        """
        self.user_id = user_id
        self.vector_db = vector_db
        self.collection_name = f"user_behavior_{user_id}"
        self.logger = get_logger("behavior_tracker")
        
        # Disk önbelleği için dizin
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "behavior_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Eşzamanlı yazma işlemleri için kilit
        self.lock = asyncio.Lock()
        
        # Önbellek
        self._cache: List[Dict[str, Any]] = []
        self.max_cache_size = 100
        self.flush_threshold = 20
        
    async def initialize(self) -> bool:
        """Davranış izleyiciyi başlatır.
        
        Returns:
            bool: Başlatma başarılı ise True
        """
        try:
            # Koleksiyonu oluştur
            await self.vector_db.create_collection(self.collection_name)
            
            # Disk önbelleğini yükle
            await self._load_cache_from_disk()
            
            self.logger.info(f"Davranış izleyici başlatıldı: {self.user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Davranış izleyici başlatılamadı: {str(e)}")
            return False
    
    async def track_interaction(
        self,
        interaction_type: Union[InteractionType, str],
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Kullanıcı etkileşimini kaydeder.
        
        Args:
            interaction_type: Etkileşim tipi
            content: Etkileşim içeriği
            metadata: Ek meta veriler
            
        Returns:
            bool: Kaydetme başarılı ise True
        """
        try:
            # InteractionType enum'dan string'e dönüştür
            if isinstance(interaction_type, InteractionType):
                interaction_type = interaction_type.value
                
            # Metadata oluştur
            current_time = datetime.now()
            interaction_metadata = metadata or {}
            interaction_metadata.update({
                "user_id": self.user_id,
                "timestamp": current_time.isoformat(),
                "interaction_type": interaction_type,
                "day_of_week": current_time.strftime("%A"),
                "hour_of_day": current_time.hour,
                "date": current_time.strftime("%Y-%m-%d")
            })
            
            # Önbelleğe ekle
            async with self.lock:
                self._cache.append({
                    "content": content,
                    "metadata": interaction_metadata
                })
                
                # Önbellek eşiği aşıldıysa veritabanına aktar
                if len(self._cache) >= self.flush_threshold:
                    await self._flush_cache_to_db()
            
            self.logger.debug(f"Etkileşim kaydedildi: {interaction_type}")
            return True
        except Exception as e:
            self.logger.error(f"Etkileşim kaydedilemedi: {str(e)}")
            return False
    
    async def _flush_cache_to_db(self) -> bool:
        """Önbellekteki etkileşimleri veritabanına aktarır.
        
        Returns:
            bool: Aktarma başarılı ise True
        """
        if not self._cache:
            return True
            
        try:
            # Önbellekteki verileri hazırla
            documents = []
            metadatas = []
            
            for item in self._cache:
                documents.append(item["content"])
                metadatas.append(item["metadata"])
            
            # Vektör veritabanına ekle
            await self.vector_db.add_documents(
                collection_name=self.collection_name,
                documents=documents,
                metadatas=metadatas
            )
            
            # Önbelleği temizle
            self._cache = []
            
            # Disk önbelleğini güncelle
            await self._save_cache_to_disk()
            
            self.logger.info(f"{len(documents)} etkileşim veritabanına aktarıldı")
            return True
        except Exception as e:
            self.logger.error(f"Önbellek veritabanına aktarılamadı: {str(e)}")
            
            # Disk önbelleğine kaydet (hata durumunda veri kaybını önlemek için)
            await self._save_cache_to_disk()
            
            return False
    
    async def _save_cache_to_disk(self) -> bool:
        """Önbelleği diske kaydeder.
        
        Returns:
            bool: Kaydetme başarılı ise True
        """
        try:
            cache_path = os.path.join(self.cache_dir, f"{self.user_id}_cache.json")
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            self.logger.error(f"Önbellek diske kaydedilemedi: {str(e)}")
            return False
    
    async def _load_cache_from_disk(self) -> bool:
        """Önbelleği diskten yükler.
        
        Returns:
            bool: Yükleme başarılı ise True
        """
        try:
            cache_path = os.path.join(self.cache_dir, f"{self.user_id}_cache.json")
            
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                
                # Önbellek eşiği aşıldıysa veritabanına aktar
                if len(self._cache) >= self.flush_threshold:
                    await self._flush_cache_to_db()
                    
                self.logger.info(f"{len(self._cache)} etkileşim diskten yüklendi")
                return True
            
            return True
        except Exception as e:
            self.logger.error(f"Önbellek diskten yüklenemedi: {str(e)}")
            return False
    
    async def get_recent_interactions(
        self,
        limit: int = 10,
        interaction_type: Optional[Union[InteractionType, str]] = None
    ) -> List[Dict[str, Any]]:
        """Son etkileşimleri getirir.
        
        Args:
            limit: Maksimum sonuç sayısı
            interaction_type: Etkileşim tipi filtresi
            
        Returns:
            List[Dict[str, Any]]: Etkileşim listesi
        """
        try:
            # Önbellekteki verileri veritabanına aktar
            await self._flush_cache_to_db()
            
            # Filtreleme koşulları
            where = {"user_id": self.user_id}
            
            # Etkileşim tipi filtresi
            if interaction_type:
                if isinstance(interaction_type, InteractionType):
                    interaction_type = interaction_type.value
                where["interaction_type"] = interaction_type
            
            # Vektör veritabanından sorgula
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query="",  # Boş sorgu, sadece filtreleme yapılacak
                n_results=limit,
                where=where
            )
            
            # Sonuçları düzenle
            interactions = []
            
            if results["ids"] and results["ids"][0]:
                for i, (doc_id, document, metadata) in enumerate(zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0]
                )):
                    interactions.append({
                        "id": doc_id,
                        "content": document,
                        "metadata": metadata
                    })
            
            return interactions
        except Exception as e:
            self.logger.error(f"Son etkileşimler getirilemedi: {str(e)}")
            return []
    
    async def close(self) -> bool:
        """Davranış izleyiciyi kapatır.
        
        Returns:
            bool: Kapatma başarılı ise True
        """
        try:
            # Önbellekteki verileri veritabanına aktar
            await self._flush_cache_to_db()
            
            self.logger.info(f"Davranış izleyici kapatıldı: {self.user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Davranış izleyici kapatılamadı: {str(e)}")
            return False
