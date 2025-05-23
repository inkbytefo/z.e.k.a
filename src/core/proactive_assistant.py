# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Proaktif Öneri Modülü

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import logging
import random

from .vector_database import VectorDatabase
from .behavior_tracker import UserBehaviorTracker, InteractionType
from .logging_manager import get_logger
from .user_profile import UserProfile

class SuggestionType(Enum):
    """Öneri tipleri."""
    TIME_BASED = "time_based"  # Zamana dayalı öneri
    CONTEXT_BASED = "context_based"  # Bağlama dayalı öneri
    INTEREST_BASED = "interest_based"  # İlgi alanına dayalı öneri
    PATTERN_BASED = "pattern_based"  # Davranış örüntüsüne dayalı öneri
    REMINDER = "reminder"  # Hatırlatıcı
    TASK = "task"  # Görev önerisi
    INFORMATION = "information"  # Bilgi önerisi
    ACTION = "action"  # Eylem önerisi

class ProactiveAssistant:
    """Proaktif öneri sistemi.
    
    Bu sınıf, kullanıcının davranışlarını analiz ederek
    proaktif öneriler sunar. Zamana, bağlama, ilgi alanlarına
    ve davranış örüntülerine dayalı öneriler oluşturur.
    """
    
    def __init__(
        self,
        user_id: str,
        vector_db: VectorDatabase,
        user_profile: Optional[UserProfile] = None,
        behavior_tracker: Optional[UserBehaviorTracker] = None
    ):
        """ProactiveAssistant başlatıcısı.
        
        Args:
            user_id: Kullanıcı ID'si
            vector_db: Vektör veritabanı
            user_profile: Kullanıcı profili (opsiyonel)
            behavior_tracker: Davranış izleyici (opsiyonel)
        """
        self.user_id = user_id
        self.vector_db = vector_db
        self.user_profile = user_profile
        self.behavior_tracker = behavior_tracker or UserBehaviorTracker(user_id, vector_db)
        self.collection_name = f"user_behavior_{user_id}"
        self.logger = get_logger("proactive_assistant")
        
        # Öneri geçmişi
        self.suggestion_history: List[Dict[str, Any]] = []
        self.max_history_size = 50
        
        # Öneri ayarları
        self.min_similarity_threshold = 0.7
        self.max_suggestions_per_type = 3
        self.suggestion_cooldown = timedelta(hours=1)  # Aynı öneriyi tekrar sunmadan önce geçmesi gereken süre
        
    async def initialize(self) -> bool:
        """Proaktif asistanı başlatır.
        
        Returns:
            bool: Başlatma başarılı ise True
        """
        try:
            # Davranış izleyiciyi başlat
            if not await self.behavior_tracker.initialize():
                self.logger.error("Davranış izleyici başlatılamadı")
                return False
            
            self.logger.info(f"Proaktif asistan başlatıldı: {self.user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Proaktif asistan başlatılamadı: {str(e)}")
            return False
    
    async def get_suggestions_by_time(
        self,
        top_n: int = 3,
        hour_range: int = 1,
        day_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """Zamana dayalı öneriler oluşturur.
        
        Günün bu saatinde genellikle ne yapıldığını bulur.
        
        Args:
            top_n: Maksimum öneri sayısı
            hour_range: Saat aralığı (±)
            day_filter: Haftanın günü filtresini uygula
            
        Returns:
            List[Dict[str, Any]]: Öneri listesi
        """
        try:
            # Günün bu saatinde genellikle ne yapıldığını bul
            current_time = datetime.now()
            current_hour = current_time.hour
            current_day = current_time.strftime("%A")
            
            # Filtreleme koşulları
            where = {
                "user_id": self.user_id,
                "hour_of_day": {"$gte": current_hour - hour_range, "$lte": current_hour + hour_range}
            }
            
            # Haftanın günü filtresi
            if day_filter:
                where["day_of_week"] = current_day
            
            # Vektör veritabanından sorgula
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query="",  # Boş sorgu, sadece filtreleme yapılacak
                n_results=top_n * 2,  # Daha fazla sonuç al, sonra filtreleme yap
                where=where
            )
            
            # Sonuçları düzenle
            suggestions = []
            
            if results["ids"] and results["ids"][0]:
                for i, (doc_id, document, metadata) in enumerate(zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0]
                )):
                    # Öneri geçmişinde var mı kontrol et
                    if not self._is_recently_suggested(document):
                        suggestions.append({
                            "id": doc_id,
                            "content": document,
                            "metadata": metadata,
                            "type": SuggestionType.TIME_BASED.value,
                            "confidence": 0.8,  # Zamana dayalı önerilerin güven skoru
                            "reason": f"Bu saatlerde genellikle bunu yapıyorsunuz ({metadata.get('interaction_type', 'etkileşim')})"
                        })
                    
                    # Maksimum öneri sayısına ulaşıldıysa dur
                    if len(suggestions) >= top_n:
                        break
            
            # Öneri geçmişine ekle
            for suggestion in suggestions:
                self._add_to_suggestion_history(suggestion)
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Zamana dayalı öneriler oluşturulamadı: {str(e)}")
            return []
    
    async def get_suggestions_by_context(
        self,
        context: str,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """Bağlama dayalı öneriler oluşturur.
        
        Verilen bağlama benzer etkileşimleri bulur.
        
        Args:
            context: Bağlam metni
            top_n: Maksimum öneri sayısı
            
        Returns:
            List[Dict[str, Any]]: Öneri listesi
        """
        try:
            # Vektör veritabanından sorgula
            results = await self.vector_db.search(
                collection_name=self.collection_name,
                query=context,
                n_results=top_n * 2,  # Daha fazla sonuç al, sonra filtreleme yap
                where={"user_id": self.user_id}
            )
            
            # Sonuçları düzenle
            suggestions = []
            
            if results["ids"] and results["ids"][0]:
                for i, (doc_id, document, metadata, similarity) in enumerate(zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["similarities"][0] if "similarities" in results else [0.7] * len(results["ids"][0])
                )):
                    # Benzerlik eşiğini kontrol et
                    if similarity < self.min_similarity_threshold:
                        continue
                        
                    # Öneri geçmişinde var mı kontrol et
                    if not self._is_recently_suggested(document):
                        suggestions.append({
                            "id": doc_id,
                            "content": document,
                            "metadata": metadata,
                            "type": SuggestionType.CONTEXT_BASED.value,
                            "confidence": similarity,
                            "reason": f"Bu bağlamda benzer bir etkileşim yaptınız ({metadata.get('interaction_type', 'etkileşim')})"
                        })
                    
                    # Maksimum öneri sayısına ulaşıldıysa dur
                    if len(suggestions) >= top_n:
                        break
            
            # Öneri geçmişine ekle
            for suggestion in suggestions:
                self._add_to_suggestion_history(suggestion)
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Bağlama dayalı öneriler oluşturulamadı: {str(e)}")
            return []
    
    async def get_suggestions_by_pattern(
        self,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """Davranış örüntüsüne dayalı öneriler oluşturur.
        
        Son etkileşimleri analiz ederek örüntüler bulur.
        
        Args:
            top_n: Maksimum öneri sayısı
            
        Returns:
            List[Dict[str, Any]]: Öneri listesi
        """
        try:
            # Son etkileşimleri getir
            recent_interactions = await self.behavior_tracker.get_recent_interactions(limit=20)
            
            if not recent_interactions:
                return []
            
            # Etkileşim tiplerini say
            interaction_counts = {}
            for interaction in recent_interactions:
                interaction_type = interaction["metadata"].get("interaction_type")
                if interaction_type:
                    interaction_counts[interaction_type] = interaction_counts.get(interaction_type, 0) + 1
            
            # En sık kullanılan etkileşim tiplerini bul
            top_interactions = sorted(
                interaction_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            # Her bir etkileşim tipi için öneriler oluştur
            suggestions = []
            
            for interaction_type, count in top_interactions:
                # Bu tipteki etkileşimleri getir
                type_interactions = await self.behavior_tracker.get_recent_interactions(
                    limit=5,
                    interaction_type=interaction_type
                )
                
                if type_interactions:
                    # Rastgele bir etkileşim seç
                    interaction = random.choice(type_interactions)
                    
                    # Öneri geçmişinde var mı kontrol et
                    if not self._is_recently_suggested(interaction["content"]):
                        suggestions.append({
                            "id": interaction["id"],
                            "content": interaction["content"],
                            "metadata": interaction["metadata"],
                            "type": SuggestionType.PATTERN_BASED.value,
                            "confidence": min(0.9, count / 20),  # Sıklığa dayalı güven skoru
                            "reason": f"Son zamanlarda sık sık '{interaction_type}' tipinde etkileşimler yapıyorsunuz"
                        })
                
                # Maksimum öneri sayısına ulaşıldıysa dur
                if len(suggestions) >= top_n:
                    break
            
            # Öneri geçmişine ekle
            for suggestion in suggestions:
                self._add_to_suggestion_history(suggestion)
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Davranış örüntüsüne dayalı öneriler oluşturulamadı: {str(e)}")
            return []
    
    async def suggest_next_action(self, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Kullanıcının bir sonraki olası eylemini önerir.
        
        Farklı öneri tiplerini birleştirerek en iyi öneriyi seçer.
        
        Args:
            context: Bağlam metni (opsiyonel)
            
        Returns:
            Optional[Dict[str, Any]]: En iyi öneri veya None
        """
        try:
            suggestions = []
            
            # Zamana dayalı öneriler
            time_suggestions = await self.get_suggestions_by_time(top_n=self.max_suggestions_per_type)
            suggestions.extend(time_suggestions)
            
            # Bağlama dayalı öneriler (eğer bağlam varsa)
            if context:
                context_suggestions = await self.get_suggestions_by_context(
                    context=context,
                    top_n=self.max_suggestions_per_type
                )
                suggestions.extend(context_suggestions)
            
            # Davranış örüntüsüne dayalı öneriler
            pattern_suggestions = await self.get_suggestions_by_pattern(top_n=self.max_suggestions_per_type)
            suggestions.extend(pattern_suggestions)
            
            if not suggestions:
                return None
            
            # En iyi öneriyi seç (güven skoruna göre)
            best_suggestion = max(suggestions, key=lambda x: x["confidence"])
            
            return best_suggestion
        except Exception as e:
            self.logger.error(f"Bir sonraki eylem önerilemedi: {str(e)}")
            return None
    
    def _is_recently_suggested(self, content: str) -> bool:
        """İçeriğin yakın zamanda önerilip önerilmediğini kontrol eder.
        
        Args:
            content: Öneri içeriği
            
        Returns:
            bool: Yakın zamanda önerilmişse True
        """
        current_time = datetime.now()
        
        for suggestion in self.suggestion_history:
            # İçerik eşleşiyor mu kontrol et
            if suggestion["content"] == content:
                # Zaman aşımı kontrolü
                suggestion_time = datetime.fromisoformat(suggestion["timestamp"])
                if current_time - suggestion_time < self.suggestion_cooldown:
                    return True
        
        return False
    
    def _add_to_suggestion_history(self, suggestion: Dict[str, Any]) -> None:
        """Öneriyi geçmişe ekler.
        
        Args:
            suggestion: Öneri
        """
        # Zaman damgası ekle
        suggestion["timestamp"] = datetime.now().isoformat()
        
        # Geçmişe ekle
        self.suggestion_history.append(suggestion)
        
        # Geçmiş boyutunu kontrol et
        if len(self.suggestion_history) > self.max_history_size:
            # En eski öneriyi sil
            self.suggestion_history.pop(0)
    
    async def close(self) -> bool:
        """Proaktif asistanı kapatır.
        
        Returns:
            bool: Kapatma başarılı ise True
        """
        try:
            # Davranış izleyiciyi kapat
            await self.behavior_tracker.close()
            
            self.logger.info(f"Proaktif asistan kapatıldı: {self.user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Proaktif asistan kapatılamadı: {str(e)}")
            return False
