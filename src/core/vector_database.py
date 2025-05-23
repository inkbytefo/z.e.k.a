# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Vektör Veritabanı Entegrasyon Modülü

import os
import json
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from .logging_manager import get_logger
from .exceptions import VectorDBError

class VectorDatabase:
    """Vektör veritabanı entegrasyonu.

    Bu sınıf, ChromaDB vektör veritabanını kullanarak
    semantik arama ve bellek yönetimi sağlar.
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls, **kwargs):
        """Singleton instance getter."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls, **kwargs):
        """Singleton instance reset."""
        cls._instance = cls(**kwargs)
        return cls._instance

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_function_name: str = "sentence_transformer",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        collection_metadata: Optional[Dict[str, Any]] = None
    ):
        """Vektör veritabanı başlatıcısı.

        Args:
            persist_directory: Veritabanı dosyalarının saklanacağı dizin.
            embedding_function_name: Gömme fonksiyonu adı (openai, sentence_transformer, huggingface, cohere).
            embedding_model_name: Gömme modeli adı (sentence_transformer için).
            collection_metadata: Varsayılan koleksiyon meta verileri.
        """
        # Loglama
        self.logger = get_logger("vector_database")

        # Depolama yolu
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "vector_db"
        )
        os.makedirs(self.persist_directory, exist_ok=True)

        # Thread havuzu (asenkron işlemler için)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Kilit (eşzamanlı yazma işlemleri için)
        self.lock = asyncio.Lock()

        try:
            # ChromaDB istemcisi oluştur
            self.client = chromadb.Client(Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))

            # Gömme fonksiyonu
            self.embedding_function_name = embedding_function_name
            self.embedding_model_name = embedding_model_name
            self.embedding_function = self._get_embedding_function(embedding_function_name, embedding_model_name)

            # Koleksiyonlar
            self.collections = {}
            self.collection_metadata = collection_metadata or {
                "description": "ZEKA Asistanı vektör veritabanı koleksiyonu",
                "created_at": datetime.now().isoformat()
            }

            self.logger.info(f"Vektör veritabanı başlatıldı: {self.persist_directory}")
        except Exception as e:
            self.logger.error(f"Vektör veritabanı başlatılırken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Vektör veritabanı başlatılamadı: {str(e)}")

    def _get_embedding_function(self, name: str, model_name: Optional[str] = None) -> Any:
        """Gömme fonksiyonu oluşturur.

        Args:
            name: Gömme fonksiyonu adı.
            model_name: Gömme modeli adı.

        Returns:
            Any: Gömme fonksiyonu.
        """
        try:
            if name == "openai":
                # OpenAI gömme fonksiyonu
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    self.logger.warning("OPENAI_API_KEY çevre değişkeni bulunamadı")
                    raise ValueError("OPENAI_API_KEY çevre değişkeni gereklidir")

                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=model_name or "text-embedding-ada-002"
                )
            elif name == "sentence_transformer":
                # Yerel SentenceTransformer gömme fonksiyonu
                model = model_name or "all-MiniLM-L6-v2"

                # Özel SentenceTransformer gömme fonksiyonu
                class SentenceTransformerEmbeddingFunction(embedding_functions.EmbeddingFunction):
                    def __init__(self, model_name: str):
                        self.model = SentenceTransformer(model_name)

                    def __call__(self, texts: List[str]) -> List[List[float]]:
                        embeddings = self.model.encode(texts, convert_to_numpy=True)
                        return embeddings.tolist()

                self.logger.info(f"SentenceTransformer gömme fonksiyonu oluşturuluyor: {model}")
                return SentenceTransformerEmbeddingFunction(model)

            elif name == "huggingface":
                # HuggingFace gömme fonksiyonu
                api_key = os.getenv("HUGGINGFACE_API_KEY")
                if not api_key:
                    self.logger.warning("HUGGINGFACE_API_KEY çevre değişkeni bulunamadı")
                    raise ValueError("HUGGINGFACE_API_KEY çevre değişkeni gereklidir")

                return embedding_functions.HuggingFaceEmbeddingFunction(
                    api_key=api_key,
                    model_name=model_name or "sentence-transformers/all-MiniLM-L6-v2"
                )
            elif name == "cohere":
                # Cohere gömme fonksiyonu
                api_key = os.getenv("COHERE_API_KEY")
                if not api_key:
                    self.logger.warning("COHERE_API_KEY çevre değişkeni bulunamadı")
                    raise ValueError("COHERE_API_KEY çevre değişkeni gereklidir")

                return embedding_functions.CohereEmbeddingFunction(
                    api_key=api_key,
                    model_name=model_name or "embed-english-v2.0"
                )
            else:
                # Varsayılan olarak SentenceTransformer gömme fonksiyonu
                self.logger.warning(f"Bilinmeyen gömme fonksiyonu: {name}, SentenceTransformer kullanılıyor.")
                return self._get_embedding_function("sentence_transformer", model_name)
        except Exception as e:
            self.logger.error(f"Gömme fonksiyonu oluşturulurken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Gömme fonksiyonu oluşturulamadı: {str(e)}")

    async def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Yeni bir koleksiyon oluşturur.

        Args:
            name: Koleksiyon adı.
            metadata: Koleksiyon meta verileri.

        Returns:
            Any: Oluşturulan koleksiyon.
        """
        async with self.lock:
            try:
                # Önbellekte varsa getir
                if name in self.collections:
                    self.logger.debug(f"Koleksiyon önbellekte bulundu: {name}")
                    return self.collections[name]

                # Koleksiyon oluştur (thread havuzunda çalıştır)
                def _create_collection():
                    return self.client.create_collection(
                        name=name,
                        metadata=metadata or self.collection_metadata,
                        embedding_function=self.embedding_function
                    )

                try:
                    # Asenkron olarak koleksiyon oluştur
                    collection = await asyncio.get_event_loop().run_in_executor(
                        self.executor, _create_collection
                    )

                    # Koleksiyonu önbelleğe ekle
                    self.collections[name] = collection

                    self.logger.info(f"Koleksiyon oluşturuldu: {name}")
                    return collection
                except Exception as e:
                    # Koleksiyon zaten varsa getir
                    if "already exists" in str(e):
                        self.logger.info(f"Koleksiyon zaten var: {name}")
                        return await self.get_collection(name)
                    else:
                        raise
            except Exception as e:
                self.logger.error(f"Koleksiyon oluşturulurken hata: {str(e)}", exc_info=True)
                raise VectorDBError(f"Koleksiyon oluşturulamadı: {str(e)}")

    async def get_collection(self, name: str) -> Any:
        """Var olan bir koleksiyonu getirir.

        Args:
            name: Koleksiyon adı.

        Returns:
            Any: Koleksiyon.
        """
        try:
            # Önbellekte varsa getir
            if name in self.collections:
                return self.collections[name]

            # Koleksiyonu getir (thread havuzunda çalıştır)
            def _get_collection():
                return self.client.get_collection(
                    name=name,
                    embedding_function=self.embedding_function
                )

            # Asenkron olarak koleksiyon getir
            collection = await asyncio.get_event_loop().run_in_executor(
                self.executor, _get_collection
            )

            # Koleksiyonu önbelleğe ekle
            self.collections[name] = collection

            self.logger.info(f"Koleksiyon getirildi: {name}")
            return collection
        except Exception as e:
            self.logger.error(f"Koleksiyon getirilirken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Koleksiyon getirilemedi: {str(e)}")

    async def list_collections(self) -> List[str]:
        """Tüm koleksiyonları listeler.

        Returns:
            List[str]: Koleksiyon adları listesi.
        """
        try:
            # Thread havuzunda çalıştır
            def _list_collections():
                return self.client.list_collections()

            # Asenkron olarak koleksiyonları listele
            collections = await asyncio.get_event_loop().run_in_executor(
                self.executor, _list_collections
            )

            collection_names = [collection.name for collection in collections]
            self.logger.debug(f"Koleksiyonlar listelendi: {len(collection_names)} adet")
            return collection_names
        except Exception as e:
            self.logger.error(f"Koleksiyonlar listelenirken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Koleksiyonlar listelenemedi: {str(e)}")

    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> List[str]:
        """Belgeleri koleksiyona ekler.

        Args:
            collection_name: Koleksiyon adı.
            documents: Belge metinleri.
            metadatas: Belge meta verileri.
            ids: Belge ID'leri.
            batch_size: Toplu ekleme için parti boyutu.

        Returns:
            List[str]: Eklenen belge ID'leri.
        """
        try:
            # Koleksiyonu getir veya oluştur
            collection = await self.get_collection(collection_name)

            # ID'ler yoksa oluştur
            if ids is None:
                timestamp = datetime.now().timestamp()
                ids = [f"doc_{i}_{timestamp}" for i in range(len(documents))]

            # Meta veriler yoksa oluştur
            if metadatas is None:
                timestamp = datetime.now().isoformat()
                metadatas = [{"timestamp": timestamp, "source": "zeka_assistant"} for _ in range(len(documents))]

            # Belgeleri partiler halinde ekle
            added_ids = []

            # Belge sayısı çok fazla ise partiler halinde ekle
            if len(documents) > batch_size:
                self.logger.info(f"Belgeler {batch_size} adetlik partiler halinde eklenecek: {len(documents)} belge")

                for i in range(0, len(documents), batch_size):
                    batch_docs = documents[i:i+batch_size]
                    batch_metas = metadatas[i:i+batch_size]
                    batch_ids = ids[i:i+batch_size]

                    # Thread havuzunda çalıştır
                    def _add_batch():
                        return collection.add(
                            documents=batch_docs,
                            metadatas=batch_metas,
                            ids=batch_ids
                        )

                    # Asenkron olarak belgeleri ekle
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, _add_batch
                    )

                    added_ids.extend(batch_ids)
                    self.logger.debug(f"Parti eklendi: {len(batch_docs)} belge ({i+1} / {(len(documents) // batch_size) + 1})")
            else:
                # Thread havuzunda çalıştır
                def _add_documents():
                    return collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )

                # Asenkron olarak belgeleri ekle
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, _add_documents
                )

                added_ids = ids

            self.logger.info(f"{len(documents)} belge eklendi: {collection_name}")
            return added_ids
        except Exception as e:
            self.logger.error(f"Belgeler eklenirken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Belgeler eklenemedi: {str(e)}")

    async def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Semantik arama yapar.

        Args:
            collection_name: Koleksiyon adı.
            query: Arama sorgusu.
            n_results: Maksimum sonuç sayısı.
            where: Meta veri filtreleme koşulları.
            where_document: Belge içeriği filtreleme koşulları.
            include_embeddings: Gömme vektörlerini dahil et.
            include_distances: Benzerlik mesafelerini dahil et.

        Returns:
            Dict[str, Any]: Arama sonuçları.
        """
        try:
            # Koleksiyonu getir
            collection = await self.get_collection(collection_name)

            # Thread havuzunda çalıştır
            def _search():
                return collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where,
                    where_document=where_document
                )

            # Asenkron olarak arama yap
            start_time = datetime.now()
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor, _search
            )
            elapsed_time = (datetime.now() - start_time).total_seconds()

            # Sonuç sayısını hesapla
            result_count = len(results["ids"][0]) if results["ids"] and results["ids"][0] else 0

            self.logger.info(f"Arama yapıldı: '{query}' ({collection_name}) - {result_count} sonuç ({elapsed_time:.3f}s)")

            # Sonuçları daha kullanışlı bir formata dönüştür
            if result_count > 0 and "distances" in results:
                # Benzerlik skorlarını hesapla (mesafe değil)
                similarities = []
                for distances in results["distances"]:
                    # Mesafeyi benzerliğe dönüştür (1 - mesafe)
                    similarities.append([1 - distance for distance in distances])
                results["similarities"] = similarities

            return results
        except Exception as e:
            self.logger.error(f"Arama yapılırken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Arama yapılamadı: {str(e)}")

    async def update_document(
        self,
        collection_name: str,
        document_id: str,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Belgeyi günceller.

        Args:
            collection_name: Koleksiyon adı.
            document_id: Belge ID'si.
            document: Yeni belge metni.
            metadata: Yeni belge meta verileri.

        Returns:
            bool: Güncelleme başarılı ise True.
        """
        try:
            # Koleksiyonu getir
            collection = await self.get_collection(collection_name)

            # Meta veri yoksa oluştur
            if metadata is None:
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "updated": True,
                    "update_source": "zeka_assistant"
                }

            # Thread havuzunda çalıştır
            def _update_document():
                return collection.update(
                    ids=[document_id],
                    documents=[document],
                    metadatas=[metadata]
                )

            # Asenkron olarak belgeyi güncelle
            await asyncio.get_event_loop().run_in_executor(
                self.executor, _update_document
            )

            self.logger.info(f"Belge güncellendi: {document_id} ({collection_name})")
            return True
        except Exception as e:
            self.logger.error(f"Belge güncellenirken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Belge güncellenemedi: {str(e)}")

    async def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> bool:
        """Belgeyi siler.

        Args:
            collection_name: Koleksiyon adı.
            document_id: Belge ID'si.

        Returns:
            bool: Silme başarılı ise True.
        """
        try:
            # Koleksiyonu getir
            collection = await self.get_collection(collection_name)

            # Thread havuzunda çalıştır
            def _delete_document():
                return collection.delete(ids=[document_id])

            # Asenkron olarak belgeyi sil
            await asyncio.get_event_loop().run_in_executor(
                self.executor, _delete_document
            )

            self.logger.info(f"Belge silindi: {document_id} ({collection_name})")
            return True
        except Exception as e:
            self.logger.error(f"Belge silinirken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Belge silinemedi: {str(e)}")

    async def delete_collection(self, collection_name: str) -> bool:
        """Koleksiyonu siler.

        Args:
            collection_name: Koleksiyon adı.

        Returns:
            bool: Silme başarılı ise True.
        """
        async with self.lock:
            try:
                # Thread havuzunda çalıştır
                def _delete_collection():
                    return self.client.delete_collection(collection_name)

                # Asenkron olarak koleksiyonu sil
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, _delete_collection
                )

                # Önbellekten kaldır
                if collection_name in self.collections:
                    del self.collections[collection_name]

                self.logger.info(f"Koleksiyon silindi: {collection_name}")
                return True
            except Exception as e:
                self.logger.error(f"Koleksiyon silinirken hata: {str(e)}", exc_info=True)
                raise VectorDBError(f"Koleksiyon silinemedi: {str(e)}")

    async def update_embedding_function(
        self,
        embedding_function_name: str,
        embedding_model_name: str
    ) -> bool:
        """Gömme fonksiyonunu günceller.

        Args:
            embedding_function_name: Yeni gömme fonksiyonu adı.
            embedding_model_name: Yeni gömme modeli adı.

        Returns:
            bool: Güncelleme başarılı ise True.
        """
        async with self.lock:
            try:
                # Yeni gömme fonksiyonunu oluştur
                new_embedding_function = self._get_embedding_function(
                    embedding_function_name,
                    embedding_model_name
                )

                # Mevcut koleksiyonları yeni gömme fonksiyonu ile güncelle
                collection_names = await self.list_collections()

                for collection_name in collection_names:
                    # Önbellekten kaldır
                    if collection_name in self.collections:
                        del self.collections[collection_name]

                    # Koleksiyonu yeni gömme fonksiyonu ile yeniden getir
                    def _get_collection():
                        return self.client.get_collection(
                            name=collection_name,
                            embedding_function=new_embedding_function
                        )

                    # Asenkron olarak koleksiyon getir
                    collection = await asyncio.get_event_loop().run_in_executor(
                        self.executor, _get_collection
                    )

                    # Koleksiyonu önbelleğe ekle
                    self.collections[collection_name] = collection

                    self.logger.info(f"Koleksiyon '{collection_name}' yeni embedding fonksiyonu ile güncellendi")

                # Varsayılan gömme fonksiyonunu güncelle
                self.embedding_function = new_embedding_function
                self.embedding_function_name = embedding_function_name
                self.embedding_model_name = embedding_model_name

                self.logger.info(f"Embedding fonksiyonu güncellendi: {embedding_function_name}/{embedding_model_name}")
                return True
            except Exception as e:
                self.logger.error(f"Embedding fonksiyonu güncellenirken hata: {str(e)}", exc_info=True)
                raise VectorDBError(f"Embedding fonksiyonu güncellenemedi: {str(e)}")

    async def get_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Belgeyi getirir.

        Args:
            collection_name: Koleksiyon adı.
            document_id: Belge ID'si.

        Returns:
            Optional[Dict[str, Any]]: Belge bilgileri veya None.
        """
        try:
            # Koleksiyonu getir
            collection = await self.get_collection(collection_name)

            # Thread havuzunda çalıştır
            def _get_document():
                return collection.get(
                    ids=[document_id]
                )

            # Asenkron olarak belgeyi getir
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _get_document
            )

            # Sonuç var mı kontrol et
            if not result["ids"]:
                self.logger.warning(f"Belge bulunamadı: {document_id} ({collection_name})")
                return None

            self.logger.info(f"Belge getirildi: {document_id} ({collection_name})")

            # Sonuç formatını düzenle
            return {
                "id": result["ids"][0],
                "document": result["documents"][0] if result["documents"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else None,
                "embedding": result["embeddings"][0] if "embeddings" in result and result["embeddings"] else None
            }
        except Exception as e:
            self.logger.error(f"Belge getirilirken hata: {str(e)}", exc_info=True)
            raise VectorDBError(f"Belge getirilemedi: {str(e)}")

# Test kodu
async def test_vector_db():
    """Vektör veritabanını test eder."""
    try:
        print("Vektör veritabanı testi başlatılıyor...")

        # Vektör veritabanını başlat
        db = VectorDatabase(
            embedding_function_name="sentence_transformer",
            embedding_model_name="all-MiniLM-L6-v2"
        )

        # Koleksiyon oluştur
        collection_name = "test_collection"
        await db.create_collection(collection_name)
        print(f"Koleksiyon oluşturuldu: {collection_name}")

        # Belgeler ekle
        documents = [
            "Yapay zeka, insan zekasını taklit eden ve öğrenebilen bilgisayar sistemleridir.",
            "Makine öğrenimi, yapay zekanın bir alt dalıdır ve verilerden öğrenen algoritmaları içerir.",
            "Derin öğrenme, çok katmanlı yapay sinir ağlarını kullanan bir makine öğrenimi tekniğidir.",
            "Doğal dil işleme, bilgisayarların insan dilini anlama ve işleme yeteneğidir.",
            "Bilgisayarlı görü, bilgisayarların görüntüleri anlama ve işleme yeteneğidir."
        ]

        metadatas = [
            {"category": "ai", "difficulty": "beginner", "source": "test"},
            {"category": "ai", "difficulty": "intermediate", "source": "test"},
            {"category": "ai", "difficulty": "advanced", "source": "test"},
            {"category": "nlp", "difficulty": "intermediate", "source": "test"},
            {"category": "cv", "difficulty": "intermediate", "source": "test"}
        ]

        # Belgeleri ekle
        doc_ids = await db.add_documents(collection_name, documents, metadatas)
        print(f"{len(doc_ids)} belge eklendi")

        # Arama yap
        print("\nArama yapılıyor: 'yapay zeka nedir?'")
        results = await db.search(
            collection_name=collection_name,
            query="yapay zeka nedir?",
            n_results=3,
            include_distances=True
        )

        # Sonuçları göster
        print("\nArama sonuçları:")
        if results["ids"] and results["ids"][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                similarity = 1 - distance
                print(f"{i+1}. {doc}")
                print(f"   Kategori: {metadata['category']}, Zorluk: {metadata['difficulty']}")
                print(f"   Benzerlik: {similarity:.4f}")
        else:
            print("Sonuç bulunamadı")

        # Belge getir
        if doc_ids:
            print(f"\nBelge getiriliyor: {doc_ids[0]}")
            document = await db.get_document(collection_name, doc_ids[0])
            if document:
                print(f"Belge içeriği: {document['document']}")
                print(f"Belge meta verileri: {document['metadata']}")
            else:
                print("Belge bulunamadı")

        # Belge güncelle
        if doc_ids:
            print(f"\nBelge güncelleniyor: {doc_ids[0]}")
            await db.update_document(
                collection_name=collection_name,
                document_id=doc_ids[0],
                document="Yapay zeka (AI), insan zekasını simüle etmek için tasarlanmış bilgisayar sistemleridir.",
                metadata={"category": "ai", "difficulty": "beginner", "updated": True}
            )

            # Güncellenmiş belgeyi getir
            updated_doc = await db.get_document(collection_name, doc_ids[0])
            print(f"Güncellenmiş belge: {updated_doc['document']}")

        # Koleksiyonları listele
        collections = await db.list_collections()
        print(f"\nKoleksiyonlar: {collections}")

        # Test koleksiyonunu sil
        print(f"\nKoleksiyon siliniyor: {collection_name}")
        await db.delete_collection(collection_name)

        # Koleksiyonları tekrar listele
        collections = await db.list_collections()
        print(f"Kalan koleksiyonlar: {collections}")

        print("\nVektör veritabanı testi başarıyla tamamlandı")
    except Exception as e:
        print(f"Test sırasında hata oluştu: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test fonksiyonunu çalıştır
    asyncio.run(test_vector_db())
