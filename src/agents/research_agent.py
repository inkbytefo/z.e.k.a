# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Araştırma Ajanı Modülü

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import asyncio
import json

from ..core.agent_base import Agent
from ..core.communication import MessageType, TaskStatus, TaskPriority

class ResearchAgent(Agent):
    """İnternet araştırması ve bilgi toplama için uzmanlaşmış ajan.

    Bu ajan, kullanıcının sorularına yanıt bulmak için internet araştırması yapar,
    bilgileri toplar, analiz eder ve özetler.
    """

    def __init__(self, agent_id="research_agent", name="Araştırma Ajanı", description="İnternet araştırması ve bilgi analizi yapan ajan"):
        """Araştırma ajanı başlatıcısı.

        Args:
            agent_id: Ajan ID'si
            name: Ajan adı
            description: Ajan açıklaması
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities={
                "web_research",
                "data_analysis",
                "content_summarization",
                "fact_checking",
                "source_verification"
            }
        )
        self.search_engines = {}
        self.knowledge_sources = {}
        self.cache = {}
        self.nlp_processor = None
        self.fact_checker = None
        self.max_search_results = 10
        self.max_summary_length = 500
        self.cache_ttl = 3600  # 1 saat

    async def add_search_engine(
        self,
        engine_name: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Arama motoru ekler.

        Args:
            engine_name: Arama motoru adı
            api_key: API anahtarı
            config: Yapılandırma

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        try:
            if engine_name in self.search_engines:
                return {
                    "success": False,
                    "message": "Bu arama motoru zaten ekli",
                    "error": "DUPLICATE_ENGINE"
                }

            self.search_engines[engine_name] = {
                "api_key": api_key,
                "config": config or {},
                "status": "active",
                "added_at": datetime.now().isoformat()
            }

            return {
                "success": True,
                "message": f"{engine_name} arama motoru eklendi",
                "engine": engine_name
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Arama motoru ekleme başarısız: {str(e)}",
                "error": str(e)
            }

    async def add_knowledge_source(
        self,
        source_name: str,
        source_url: Optional[str] = None,
        source_type: str = "web",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Bilgi kaynağı ekler.

        Args:
            source_name: Kaynak adı
            source_url: Kaynak URL'si
            source_type: Kaynak türü (web, api, database)
            config: Ek yapılandırma

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        try:
            if source_name in self.knowledge_sources:
                return {
                    "success": False,
                    "message": "Bu kaynak zaten ekli",
                    "error": "DUPLICATE_SOURCE"
                }

            self.knowledge_sources[source_name] = {
                "url": source_url,
                "type": source_type,
                "config": config or {},
                "status": "active",
                "added_at": datetime.now().isoformat()
            }

            return {
                "success": True,
                "message": f"{source_name} bilgi kaynağı eklendi",
                "source": source_name
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Kaynak ekleme başarısız: {str(e)}",
                "error": str(e)
            }

    async def process_task(
        self,
        task_id: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bir görevi işler.

        Args:
            task_id: Görev ID'si
            description: Görev açıklaması
            metadata: Görev meta verileri

        Returns:
            Dict[str, Any]: Görev sonucu
        """
        intent = metadata.get("intent")
        entities = metadata.get("entities", {})
        action = entities.get("action", "unknown")

        try:
            # Kullanıcı tercihlerini ve belleği kontrol et
            preferences = self.get_user_preferences("research")
            relevant_memory = self.get_relevant_memory(description)

            # İşlem türüne göre yönlendir
            if action == "search":
                result = await self._search_information(description, entities, preferences)
            elif action == "summarize":
                result = await self._summarize_information(description, entities, preferences)
            elif action == "compare":
                result = await self._compare_information(description, entities, preferences)
            elif action == "analyze":
                result = await self._analyze_information(description, entities, preferences)
            elif action == "verify":
                result = await self._verify_information(description, entities, preferences)
            else:
                result = {
                    "success": False,
                    "message": "Araştırma isteğinizi tam olarak anlayamadım. Lütfen daha açık bir ifade kullanın.",
                    "action_needed": "clarification"
                }

            # Başarılı sonuçları önbelleğe al
            if result.get("success", False):
                self._cache_result(task_id, result)

            return result

        except Exception as e:
            return {
                "success": False,
                "message": f"İşlem sırasında bir hata oluştu: {str(e)}",
                "error": str(e)
            }

    async def _search_information(
        self,
        description: str,
        entities: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bilgi araştırması yapar.

        Args:
            description: Araştırma konusu
            entities: İstekten çıkarılan varlıklar
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        try:
            # Önbellekte ara
            cache_key = f"search_{description}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Arama kriterlerini belirle
            keywords = await self._extract_keywords(description)
            engines = entities.get("engines", list(self.search_engines.keys()))
            limit = entities.get("limit", self.max_search_results)

            # Paralel arama yap
            search_tasks = []
            for engine in engines:
                if engine in self.search_engines:
                    task = self._search_with_engine(engine, keywords, limit)
                    search_tasks.append(task)

            results = await asyncio.gather(*search_tasks)

            # Sonuçları birleştir ve sırala
            combined_results = self._merge_search_results(results)

            # Kaynak güvenilirliğini kontrol et
            if self.fact_checker:
                reliability_scores = await self.fact_checker.check_sources(combined_results)
            else:
                reliability_scores = {}

            return {
                "success": True,
                "message": "Araştırma tamamlandı",
                "results": combined_results,
                "keywords": keywords,
                "reliability_scores": reliability_scores,
                "total_sources": len(combined_results)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Araştırma başarısız: {str(e)}",
                "error": str(e)
            }

    async def _summarize_information(
        self,
        description: str,
        entities: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bilgileri özetler.

        Args:
            description: Özetlenecek içerik
            entities: İstekten çıkarılan varlıklar
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        if not self.nlp_processor:
            return {
                "success": False,
                "message": "NLP işlemcisi ayarlanmamış",
                "error": "NLP_PROCESSOR_NOT_SET"
            }

        try:
            # Önbellekte ara
            cache_key = f"summary_{description}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Özetleme parametrelerini belirle
            max_length = entities.get("max_length", self.max_summary_length)
            style = entities.get("style", "informative")

            # İçeriği özetle
            summary = await self.nlp_processor.summarize(
                description,
                max_length=max_length,
                style=style
            )

            return {
                "success": True,
                "message": "Özet oluşturuldu",
                "summary": summary,
                "original_length": len(description),
                "summary_length": len(summary),
                "style": style
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Özetleme başarısız: {str(e)}",
                "error": str(e)
            }

    async def _compare_information(
        self,
        description: str,
        entities: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bilgileri karşılaştırır.

        Args:
            description: Karşılaştırma isteği
            entities: İstekten çıkarılan varlıklar
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        try:
            # Karşılaştırılacak öğeleri belirle
            items = entities.get("items", [])
            criteria = entities.get("criteria", [])

            if not items or len(items) < 2:
                return {
                    "success": False,
                    "message": "Karşılaştırılacak öğeler belirtilmemiş",
                    "error": "MISSING_ITEMS"
                }

            # Her öğe için bilgi topla
            item_data = []
            for item in items:
                search_result = await self._search_information(item, {}, preferences)
                if search_result.get("success"):
                    item_data.append(search_result["results"])

            # Karşılaştırma yap
            comparison = await self._analyze_differences(item_data, criteria)

            return {
                "success": True,
                "message": "Karşılaştırma tamamlandı",
                "comparison": comparison,
                "items": items,
                "criteria": criteria
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Karşılaştırma başarısız: {str(e)}",
                "error": str(e)
            }

    async def _analyze_information(
        self,
        description: str,
        entities: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bilgileri analiz eder.

        Args:
            description: Analiz isteği
            entities: İstekten çıkarılan varlıklar
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        if not self.nlp_processor:
            return {
                "success": False,
                "message": "NLP işlemcisi ayarlanmamış",
                "error": "NLP_PROCESSOR_NOT_SET"
            }

        try:
            # Analiz parametrelerini belirle
            analysis_type = entities.get("analysis_type", "general")
            depth = entities.get("depth", "detailed")

            # Önce bilgi topla
            search_result = await self._search_information(description, entities, preferences)
            if not search_result.get("success"):
                return search_result

            # Analiz yap
            analysis = await self.nlp_processor.analyze(
                search_result["results"],
                analysis_type=analysis_type,
                depth=depth
            )

            # Güvenilirlik kontrolü
            if self.fact_checker:
                reliability = await self.fact_checker.verify_analysis(analysis)
            else:
                reliability = None

            return {
                "success": True,
                "message": "Analiz tamamlandı",
                "analysis": analysis,
                "reliability": reliability,
                "type": analysis_type,
                "depth": depth
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Analiz başarısız: {str(e)}",
                "error": str(e)
            }

    async def _verify_information(
        self,
        description: str,
        entities: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bilgileri doğrular.

        Args:
            description: Doğrulama isteği
            entities: İstekten çıkarılan varlıklar
            preferences: Kullanıcı tercihleri

        Returns:
            Dict[str, Any]: İşlem sonucu
        """
        if not self.fact_checker:
            return {
                "success": False,
                "message": "Doğrulama sistemi ayarlanmamış",
                "error": "FACT_CHECKER_NOT_SET"
            }

        try:
            # Doğrulama kriterlerini belirle
            claim = entities.get("claim", description)
            sources = entities.get("sources", [])

            # Kaynakları topla
            if not sources:
                search_result = await self._search_information(claim, entities, preferences)
                if search_result.get("success"):
                    sources = search_result["results"]

            # Doğrulama yap
            verification = await self.fact_checker.verify_claim(claim, sources)

            return {
                "success": True,
                "message": "Doğrulama tamamlandı",
                "claim": claim,
                "verification": verification,
                "confidence": verification.get("confidence", 0),
                "sources_used": len(sources)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Doğrulama başarısız: {str(e)}",
                "error": str(e)
            }

    async def _extract_keywords(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri çıkarır.

        Args:
            text: İşlenecek metin

        Returns:
            List[str]: Anahtar kelimeler listesi
        """
        if self.nlp_processor:
            try:
                return await self.nlp_processor.extract_keywords(text)
            except:
                pass

        # Yedek basit yaklaşım
        words = text.lower().split()
        stopwords = {"ve", "veya", "ile", "için", "gibi", "kadar", "bu", "şu", "o"}
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        return list(set(keywords))

    async def _search_with_engine(
        self,
        engine: str,
        keywords: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Belirli bir arama motoruyla arama yapar.

        Args:
            engine: Arama motoru adı
            keywords: Arama anahtar kelimeleri
            limit: Maksimum sonuç sayısı

        Returns:
            List[Dict[str, Any]]: Arama sonuçları
        """
        engine_config = self.search_engines[engine]
        # Burada gerçek arama API'si kullanılacak
        return []

    def _merge_search_results(
        self,
        results: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Farklı kaynaklardan gelen sonuçları birleştirir.

        Args:
            results: Kaynaklardan gelen sonuçlar

        Returns:
            List[Dict[str, Any]]: Birleştirilmiş sonuçlar
        """
        # Sonuçları birleştir ve tekrarları kaldır
        merged = {}
        for source_results in results:
            for result in source_results:
                url = result.get("url")
                if url and url not in merged:
                    merged[url] = result

        # Alakalılık sırasına göre sırala
        return sorted(
            merged.values(),
            key=lambda x: x.get("relevance", 0),
            reverse=True
        )

    def _cache_result(self, key: str, result: Dict[str, Any]) -> None:
        """Sonucu önbelleğe alır.

        Args:
            key: Önbellek anahtarı
            result: Önbelleğe alınacak sonuç
        """
        # Eski önbellek girişlerini temizle
        now = datetime.now().timestamp()
        self.cache = {
            k: v for k, v in self.cache.items()
            if v.get("timestamp", 0) + self.cache_ttl > now
        }

        # Yeni sonucu ekle
        result["timestamp"] = now
        self.cache[key] = result
