# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Bellek Yönetim Modülü

from datetime import datetime, timedelta
import json
import os
import asyncio
import aiofiles
from typing import Dict, List, Any, Optional, Union, Set
import time

from .logging_manager import get_logger
from .exceptions import MemoryManagerError

class MemoryManager:
    """Kullanıcı etkileşimlerini ve bilgileri depolayan bellek yönetim sınıfı.

    Bu sınıf, kullanıcı etkileşimlerini, öğrenilen bilgileri ve tercihleri depolamak ve
    erişmek için vektör veritabanı kullanır. Semantik arama yetenekleri sunar.
    """

    def __init__(self, storage_path: str = "./data/memory", vector_db_enabled: bool = False):
        """Bellek yöneticisi başlatıcısı.

        Args:
            storage_path: Bellek verilerinin depolanacağı dizin yolu
            vector_db_enabled: Vektör veritabanı kullanılsın mı?
        """
        self.storage_path = storage_path
        self.vector_db = None  # İlerleyen aşamalarda vektör veritabanı bağlantısı eklenecek
        self.vector_db_enabled = vector_db_enabled
        self.logger = get_logger("memory_manager")
        self.write_lock = asyncio.Lock()  # Eşzamanlı yazma işlemleri için kilit
        self.read_cache = {}  # Okuma performansı için önbellek
        self.cache_ttl = 300  # Önbellek süresi (saniye)
        self.cache_last_cleanup = time.time()

        # Depolama dizinini oluştur
        self._ensure_storage_exists()

        self.logger.info(f"Bellek yöneticisi başlatıldı: {storage_path}")

        # Vektör veritabanı etkinse başlat
        self.vector_db_initialized = False
        if vector_db_enabled:
            # _init_vector_db asenkron olduğu için burada çağrılamaz
            # Bunun yerine ilk kullanımda başlatılacak
            pass

    def _ensure_storage_exists(self) -> None:
        """Depolama dizininin var olduğundan emin olur."""
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            self.logger.debug(f"Depolama dizini oluşturuldu: {self.storage_path}")
        except Exception as e:
            self.logger.error(f"Depolama dizini oluşturulurken hata: {str(e)}", exc_info=True)
            raise MemoryManagerError(f"Depolama dizini oluşturulamadı: {str(e)}")

    async def _init_vector_db(self) -> None:
        """Vektör veritabanını başlatır."""
        try:
            from .vector_database import VectorDatabase

            vector_db_path = os.path.join(self.storage_path, "vector_db")
            self.vector_db = VectorDatabase(persist_directory=vector_db_path)

            # Etkileşimler koleksiyonunu oluştur
            await self.vector_db.create_collection("interactions")

            self.logger.info("Vektör veritabanı başlatıldı")
        except ImportError:
            self.logger.warning("VectorDatabase modülü bulunamadı, vektör veritabanı devre dışı bırakıldı")
            self.vector_db_enabled = False
        except Exception as e:
            self.logger.error(f"Vektör veritabanı başlatılırken hata: {str(e)}", exc_info=True)
            self.vector_db_enabled = False

    async def store_interaction(
        self,
        user_input: Union[str, Dict],
        system_response: Union[str, Dict],
        agent_id: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Kullanıcı-sistem etkileşimini depolar.

        Args:
            user_input: Kullanıcı girdisi (metin veya sözlük)
            system_response: Sistem yanıtı (metin veya sözlük)
            agent_id: Yanıtı üreten ajanın ID'si
            metadata: Ek meta veriler
        """
        try:
            if metadata is None:
                metadata = {}

            # Etkileşim zamanı
            timestamp = datetime.now()

            # Etkileşim kaydı oluştur
            interaction = {
                "timestamp": timestamp.isoformat(),
                "user_input": user_input,
                "system_response": system_response,
                "agent_id": agent_id,
                "metadata": metadata
            }

            # Dosya tabanlı depolama
            await self._store_to_file(interaction)

            # Vektör veritabanı depolama
            if self.vector_db_enabled and self.vector_db:
                await self._store_to_vector_db(interaction)

            self.logger.debug(f"Etkileşim kaydedildi: {agent_id}")

        except Exception as e:
            self.logger.error(f"Etkileşim kaydedilirken hata: {str(e)}", exc_info=True)
            raise MemoryManagerError(f"Etkileşim kaydedilemedi: {str(e)}")

    async def _store_to_file(self, interaction: Dict[str, Any]) -> None:
        """Etkileşimi dosya sistemine kaydeder.

        Args:
            interaction: Kaydedilecek etkileşim verisi
        """
        try:
            # Tarih bazlı dosya adı oluştur
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.storage_path, f"interactions_{date_str}.jsonl")

            # Eşzamanlı yazma işlemleri için kilit kullan
            async with self.write_lock:
                # Asenkron dosya yazma
                async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
                    await f.write(json.dumps(interaction, ensure_ascii=False) + "\n")

            # Önbelleği temizle
            cache_key = f"interactions_{date_str}"
            if cache_key in self.read_cache:
                del self.read_cache[cache_key]

        except Exception as e:
            self.logger.error(f"Etkileşim dosyaya kaydedilirken hata: {str(e)}", exc_info=True)
            raise MemoryManagerError(f"Etkileşim dosyaya kaydedilemedi: {str(e)}")

    async def _store_to_vector_db(self, interaction: Dict[str, Any]) -> None:
        """Etkileşimi vektör veritabanına kaydeder.

        Args:
            interaction: Kaydedilecek etkileşim verisi
        """
        try:
            # Vektör veritabanı etkin değilse veya başlatılmamışsa
            if not self.vector_db_enabled:
                return

            # Vektör veritabanı başlatılmamışsa başlat
            if not self.vector_db_initialized:
                await self._init_vector_db()
                self.vector_db_initialized = True

            if not self.vector_db:
                return

            # Etkileşim metinlerini birleştir
            user_input = interaction["user_input"]
            system_response = interaction["system_response"]

            if isinstance(user_input, dict):
                user_input = json.dumps(user_input, ensure_ascii=False)
            if isinstance(system_response, dict):
                system_response = json.dumps(system_response, ensure_ascii=False)

            combined_text = f"User: {user_input}\nAssistant: {system_response}"

            # Metadata'yı düzleştir - ChromaDB sadece basit veri tiplerini kabul eder
            flattened_metadata = self._flatten_metadata(interaction)

            # Vektör veritabanına ekle
            await self.vector_db.add_documents(
                collection_name="interactions",
                documents=[combined_text],
                metadatas=[flattened_metadata],
                ids=[f"interaction_{interaction['timestamp']}"]
            )

            self.logger.debug("Etkileşim vektör veritabanına kaydedildi")

        except Exception as e:
            self.logger.error(f"Etkileşim vektör veritabanına kaydedilirken hata: {str(e)}", exc_info=True)
            # Vektör veritabanı hatası kritik değil, devam et

    async def retrieve(self, query: str, limit: int = 5, use_vector_search: bool = True) -> List[Dict[str, Any]]:
        """Sorguya en uygun etkileşimleri getirir.

        Args:
            query: Arama sorgusu
            limit: Getirilecek maksimum sonuç sayısı
            use_vector_search: Vektör arama kullanılsın mı?

        Returns:
            List[Dict[str, Any]]: İlgili etkileşimler listesi
        """
        try:
            # Önce vektör veritabanında ara
            if use_vector_search and self.vector_db_enabled:
                try:
                    self.logger.debug(f"Vektör arama yapılıyor: {query}")
                    vector_results = await self._search_vector_db(query, limit)
                    if vector_results:
                        return vector_results
                except Exception as e:
                    self.logger.error(f"Vektör arama sırasında hata: {str(e)}", exc_info=True)

            # Vektör arama başarısız olursa veya etkin değilse dosya tabanlı arama yap
            self.logger.debug(f"Dosya tabanlı arama yapılıyor: {query}")
            return await self._search_files(query, limit)

        except Exception as e:
            self.logger.error(f"Arama sırasında hata: {str(e)}", exc_info=True)
            raise MemoryManagerError(f"Arama yapılamadı: {str(e)}")

    async def _search_files(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Dosya tabanlı arama yapar.

        Args:
            query: Arama sorgusu
            limit: Maksimum sonuç sayısı

        Returns:
            List[Dict[str, Any]]: Bulunan etkileşimler
        """
        results = []
        query_lower = query.lower()

        # Son 5 günlük etkileşimleri kontrol et
        for i in range(5):
            date = datetime.now().date()
            date_str = (date - timedelta(days=i)).strftime("%Y-%m-%d")
            file_path = os.path.join(self.storage_path, f"interactions_{date_str}.jsonl")

            # Önbellekte var mı kontrol et
            cache_key = f"interactions_{date_str}"
            if cache_key in self.read_cache:
                cache_data = self.read_cache[cache_key]
                cache_time, interactions = cache_data

                # Önbellek geçerli mi?
                if time.time() - cache_time < self.cache_ttl:
                    self.logger.debug(f"Önbellekten okunuyor: {cache_key}")
                    # Önbellekten oku ve filtrele
                    for interaction in interactions:
                        if self._match_interaction(interaction, query_lower):
                            results.append(interaction)
                            if len(results) >= limit:
                                return results
                    continue

            # Dosyadan oku
            if os.path.exists(file_path):
                try:
                    interactions = []
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                        async for line in f:
                            interaction = json.loads(line)
                            interactions.append(interaction)

                            # Arama sorgusu ile eşleşiyor mu?
                            if self._match_interaction(interaction, query_lower):
                                results.append(interaction)
                                if len(results) >= limit:
                                    break

                    # Önbelleğe ekle
                    self.read_cache[cache_key] = (time.time(), interactions)

                    # Önbellek temizliği
                    self._cleanup_cache()

                    if len(results) >= limit:
                        return results

                except Exception as e:
                    self.logger.error(f"Dosya okuma hatası ({file_path}): {str(e)}", exc_info=True)

        return results

    def _flatten_metadata(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Etkileşim verisini ChromaDB için uygun düzleştirilmiş metadata formatına dönüştürür.

        ChromaDB sadece basit veri tiplerini (str, int, float, bool, None) kabul eder.
        İç içe sözlükler ve listeler düzleştirilir.

        Args:
            interaction: Düzleştirilecek etkileşim verisi

        Returns:
            Dict[str, Any]: Düzleştirilmiş metadata
        """
        flattened = {}

        # Timestamp
        flattened["timestamp"] = interaction.get("timestamp", "")

        # Agent ID
        flattened["agent_id"] = interaction.get("agent_id", "")

        # Metadata alanını düzleştir
        metadata = interaction.get("metadata", {})
        self._flatten_dict(metadata, flattened, prefix="metadata_")

        # Kullanıcı girdisi ve sistem yanıtını ekle (metin olarak)
        user_input = interaction.get("user_input", "")
        system_response = interaction.get("system_response", "")

        if isinstance(user_input, dict):
            flattened["user_input_type"] = "dict"
            flattened["user_input"] = json.dumps(user_input, ensure_ascii=False)
        else:
            flattened["user_input_type"] = "text"
            flattened["user_input"] = str(user_input)

        if isinstance(system_response, dict):
            flattened["system_response_type"] = "dict"
            flattened["system_response"] = json.dumps(system_response, ensure_ascii=False)
        else:
            flattened["system_response_type"] = "text"
            flattened["system_response"] = str(system_response)

        return flattened

    def _flatten_dict(self, d: Dict[str, Any], result: Dict[str, Any], prefix: str = "") -> None:
        """Sözlüğü düzleştirir ve sonuç sözlüğüne ekler.

        Args:
            d: Düzleştirilecek sözlük
            result: Sonuçların ekleneceği sözlük
            prefix: Anahtar öneki
        """
        for key, value in d.items():
            # Anahtar adını oluştur
            flat_key = f"{prefix}{key}"

            # Değer tipine göre işlem yap
            if isinstance(value, (str, int, float, bool)) or value is None:
                # Basit veri tiplerini doğrudan ekle
                result[flat_key] = value
            elif isinstance(value, dict):
                # İç içe sözlükleri düzleştir
                self._flatten_dict(value, result, f"{flat_key}_")
            elif isinstance(value, (list, tuple)):
                # Listeleri JSON string'e dönüştür
                result[flat_key] = json.dumps(value, ensure_ascii=False)
            else:
                # Diğer karmaşık veri tiplerini JSON string'e dönüştür
                result[flat_key] = json.dumps(value, ensure_ascii=False)

    def _match_interaction(self, interaction: Dict[str, Any], query_lower: str) -> bool:
        """Etkileşimin arama sorgusu ile eşleşip eşleşmediğini kontrol eder.

        Args:
            interaction: Kontrol edilecek etkileşim
            query_lower: Küçük harfli arama sorgusu

        Returns:
            bool: Eşleşme varsa True
        """
        # Kullanıcı girdisi ve sistem yanıtında ara
        user_input = interaction.get("user_input", "")
        system_response = interaction.get("system_response", "")

        # Sözlük ise metin olarak dönüştür
        if isinstance(user_input, dict):
            user_input = json.dumps(user_input, ensure_ascii=False)
        if isinstance(system_response, dict):
            system_response = json.dumps(system_response, ensure_ascii=False)

        # Metin eşleşmesi
        if (isinstance(user_input, str) and query_lower in user_input.lower()) or \
           (isinstance(system_response, str) and query_lower in system_response.lower()):
            return True

        # Metadata'da ara
        metadata = interaction.get("metadata", {})
        if metadata:
            metadata_str = json.dumps(metadata, ensure_ascii=False).lower()
            if query_lower in metadata_str:
                return True

        return False

    async def _search_vector_db(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Vektör veritabanında semantik arama yapar.

        Args:
            query: Arama sorgusu
            limit: Maksimum sonuç sayısı

        Returns:
            List[Dict[str, Any]]: Bulunan etkileşimler
        """
        # Vektör veritabanı etkin değilse
        if not self.vector_db_enabled:
            return []

        # Vektör veritabanı başlatılmamışsa başlat
        if not self.vector_db_initialized:
            await self._init_vector_db()
            self.vector_db_initialized = True

        if not self.vector_db:
            return []

        # Vektör arama yap
        results = await self.vector_db.search(
            collection_name="interactions",
            query=query,
            n_results=limit
        )

        # Sonuçları dönüştür
        interactions = []
        if results and "metadatas" in results and results["metadatas"]:
            for flattened_metadata in results["metadatas"][0]:
                # Düzleştirilmiş metadataları orijinal formata dönüştür
                interaction = self._unflatten_metadata(flattened_metadata)
                interactions.append(interaction)

        return interactions

    def _unflatten_metadata(self, flattened_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Düzleştirilmiş metadataları orijinal etkileşim formatına dönüştürür.

        Args:
            flattened_metadata: Düzleştirilmiş metadata

        Returns:
            Dict[str, Any]: Orijinal etkileşim formatı
        """
        interaction = {}

        # Temel alanları ekle
        interaction["timestamp"] = flattened_metadata.get("timestamp", "")
        interaction["agent_id"] = flattened_metadata.get("agent_id", "")

        # Metadata alanını yeniden oluştur
        metadata = {}
        metadata_keys = {}

        # Önce tüm metadata anahtarlarını grupla
        for key, value in flattened_metadata.items():
            if key.startswith("metadata_"):
                parts = key[len("metadata_"):].split("_")
                current_level = metadata_keys

                # Son parça hariç tüm parçaları işle
                for part in parts[:-1]:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

                # Son parçayı ekle
                current_level[parts[-1]] = value

        # Şimdi metadata'yı yeniden oluştur
        self._rebuild_nested_dict(metadata_keys, metadata)
        interaction["metadata"] = metadata

        # Kullanıcı girdisi ve sistem yanıtını yeniden oluştur
        user_input_type = flattened_metadata.get("user_input_type", "text")
        user_input = flattened_metadata.get("user_input", "")

        if user_input_type == "dict" and user_input:
            try:
                interaction["user_input"] = json.loads(user_input)
            except:
                interaction["user_input"] = user_input
        else:
            interaction["user_input"] = user_input

        system_response_type = flattened_metadata.get("system_response_type", "text")
        system_response = flattened_metadata.get("system_response", "")

        if system_response_type == "dict" and system_response:
            try:
                interaction["system_response"] = json.loads(system_response)
            except:
                interaction["system_response"] = system_response
        else:
            interaction["system_response"] = system_response

        return interaction

    def _rebuild_nested_dict(self, keys_dict: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Düzleştirilmiş anahtarlardan iç içe sözlük yapısını yeniden oluşturur.

        Args:
            keys_dict: Düzleştirilmiş anahtarlar sözlüğü
            result: Sonuç sözlüğü
        """
        for key, value in keys_dict.items():
            if isinstance(value, dict):
                # İç içe sözlük
                result[key] = {}
                self._rebuild_nested_dict(value, result[key])
            else:
                # Değer
                # JSON string ise parse et
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                    try:
                        result[key] = json.loads(value)
                    except:
                        result[key] = value
                else:
                    result[key] = value

    def _cleanup_cache(self) -> None:
        """Önbelleği temizler."""
        # Her 5 dakikada bir temizlik yap
        current_time = time.time()
        if current_time - self.cache_last_cleanup < 300:  # 5 dakika
            return

        self.cache_last_cleanup = current_time

        # Süresi dolmuş önbellek öğelerini temizle
        expired_keys = []
        for key, (cache_time, _) in self.read_cache.items():
            if current_time - cache_time > self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.read_cache[key]

        self.logger.debug(f"{len(expired_keys)} önbellek öğesi temizlendi")

    async def store_user_preference(self, preference_type: str, preference_value: Any) -> None:
        """Kullanıcı tercihini depolar.

        Args:
            preference_type: Tercih türü
            preference_value: Tercih değeri
        """
        try:
            preferences_file = os.path.join(self.storage_path, "user_preferences.json")

            # Eşzamanlı yazma işlemleri için kilit kullan
            async with self.write_lock:
                # Mevcut tercihleri yükle
                preferences = {}
                if os.path.exists(preferences_file):
                    async with aiofiles.open(preferences_file, "r", encoding="utf-8") as f:
                        content = await f.read()
                        if content:
                            preferences = json.loads(content)

                # Tercihi güncelle
                preferences[preference_type] = preference_value

                # Tercihleri kaydet
                async with aiofiles.open(preferences_file, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(preferences, ensure_ascii=False, indent=2))

            self.logger.debug(f"Kullanıcı tercihi kaydedildi: {preference_type}")

        except Exception as e:
            self.logger.error(f"Kullanıcı tercihi kaydedilirken hata: {str(e)}", exc_info=True)
            raise MemoryManagerError(f"Kullanıcı tercihi kaydedilemedi: {str(e)}")

    async def get_user_preferences(self, preference_type: Optional[str] = None) -> Union[Dict[str, Any], Any, None]:
        """Kullanıcı tercihlerini getirir.

        Args:
            preference_type: Tercih türü. None ise tüm tercihler getirilir.

        Returns:
            Union[Dict[str, Any], Any, None]: İstenen tercih(ler)
        """
        try:
            preferences_file = os.path.join(self.storage_path, "user_preferences.json")

            # Dosya yoksa boş değer döndür
            if not os.path.exists(preferences_file):
                return {} if preference_type is None else None

            # Dosyadan oku
            async with aiofiles.open(preferences_file, "r", encoding="utf-8") as f:
                content = await f.read()
                if not content:
                    return {} if preference_type is None else None

                preferences = json.loads(content)

            # İstenen tercihi veya tüm tercihleri döndür
            if preference_type is None:
                return preferences
            return preferences.get(preference_type)

        except Exception as e:
            self.logger.error(f"Kullanıcı tercihleri getirilirken hata: {str(e)}", exc_info=True)
            return {} if preference_type is None else None

    async def cleanup(self) -> None:
        """Bellek yöneticisini temizler ve kapatır."""
        try:
            self.logger.info("Bellek yöneticisi temizleniyor...")

            # Önbelleği temizle
            self.read_cache.clear()

            # Vektör veritabanını kapat
            if self.vector_db_enabled and self.vector_db:
                # Vektör veritabanı kapatma işlemi
                if hasattr(self.vector_db, "client") and hasattr(self.vector_db.client, "persist"):
                    self.vector_db.client.persist()
                    self.logger.debug("Vektör veritabanı kalıcı hale getirildi")

            self.logger.info("Bellek yöneticisi başarıyla temizlendi")

        except Exception as e:
            self.logger.error(f"Bellek yöneticisi temizlenirken hata: {str(e)}", exc_info=True)

    def get_access_interface(self) -> 'MemoryManager':
        """Bellek erişim arayüzünü döndürür.

        Returns:
            MemoryManager: Bellek erişim arayüzü
        """
        return self