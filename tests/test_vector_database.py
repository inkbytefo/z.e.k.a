# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Vektör Veritabanı Test Modülü

import os
import sys
import asyncio
import unittest
import tempfile
from pathlib import Path

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.vector_database import VectorDatabase
from src.core.exceptions import VectorDBError


class TestVectorDatabase(unittest.TestCase):
    """Vektör veritabanı testleri."""
    
    def setUp(self):
        """Test öncesi hazırlık."""
        # Geçici dizin oluştur
        self.temp_dir = tempfile.TemporaryDirectory()
        self.persist_directory = self.temp_dir.name
        
        # Test verileri
        self.test_documents = [
            "Yapay zeka, insan zekasını taklit eden ve öğrenebilen bilgisayar sistemleridir.",
            "Makine öğrenimi, yapay zekanın bir alt dalıdır ve verilerden öğrenen algoritmaları içerir.",
            "Derin öğrenme, çok katmanlı yapay sinir ağlarını kullanan bir makine öğrenimi tekniğidir.",
            "Doğal dil işleme, bilgisayarların insan dilini anlama ve işleme yeteneğidir.",
            "Bilgisayarlı görü, bilgisayarların görüntüleri anlama ve işleme yeteneğidir."
        ]
        
        self.test_metadatas = [
            {"category": "ai", "difficulty": "beginner", "source": "test"},
            {"category": "ai", "difficulty": "intermediate", "source": "test"},
            {"category": "ai", "difficulty": "advanced", "source": "test"},
            {"category": "nlp", "difficulty": "intermediate", "source": "test"},
            {"category": "cv", "difficulty": "intermediate", "source": "test"}
        ]
    
    def tearDown(self):
        """Test sonrası temizlik."""
        # Geçici dizini temizle
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Başlatma testi."""
        # SentenceTransformer ile başlat
        db = VectorDatabase(
            persist_directory=self.persist_directory,
            embedding_function_name="sentence_transformer",
            embedding_model_name="all-MiniLM-L6-v2"
        )
        
        self.assertIsNotNone(db)
        self.assertEqual(db.persist_directory, self.persist_directory)
        self.assertEqual(db.embedding_function_name, "sentence_transformer")
        self.assertEqual(db.embedding_model_name, "all-MiniLM-L6-v2")
    
    async def async_test_create_collection(self):
        """Koleksiyon oluşturma testi."""
        db = VectorDatabase(persist_directory=self.persist_directory)
        
        # Koleksiyon oluştur
        collection_name = "test_collection"
        collection = await db.create_collection(collection_name)
        
        self.assertIsNotNone(collection)
        
        # Koleksiyonları listele
        collections = await db.list_collections()
        self.assertIn(collection_name, collections)
    
    async def async_test_add_documents(self):
        """Belge ekleme testi."""
        db = VectorDatabase(persist_directory=self.persist_directory)
        
        # Koleksiyon oluştur
        collection_name = "test_collection"
        await db.create_collection(collection_name)
        
        # Belgeleri ekle
        doc_ids = await db.add_documents(
            collection_name=collection_name,
            documents=self.test_documents,
            metadatas=self.test_metadatas
        )
        
        self.assertEqual(len(doc_ids), len(self.test_documents))
        
        # İlk belgeyi getir
        document = await db.get_document(collection_name, doc_ids[0])
        self.assertIsNotNone(document)
        self.assertEqual(document["document"], self.test_documents[0])
        self.assertEqual(document["metadata"]["category"], "ai")
    
    async def async_test_search(self):
        """Arama testi."""
        db = VectorDatabase(persist_directory=self.persist_directory)
        
        # Koleksiyon oluştur
        collection_name = "test_collection"
        await db.create_collection(collection_name)
        
        # Belgeleri ekle
        await db.add_documents(
            collection_name=collection_name,
            documents=self.test_documents,
            metadatas=self.test_metadatas
        )
        
        # Arama yap
        results = await db.search(
            collection_name=collection_name,
            query="yapay zeka nedir?",
            n_results=3
        )
        
        self.assertIsNotNone(results)
        self.assertIn("documents", results)
        self.assertIn("metadatas", results)
        self.assertIn("distances", results)
        self.assertIn("ids", results)
        
        # En az bir sonuç olmalı
        self.assertGreater(len(results["documents"][0]), 0)
        
        # İlk sonuç "yapay zeka" içermeli
        self.assertIn("yapay zeka", results["documents"][0][0].lower())
    
    async def async_test_update_document(self):
        """Belge güncelleme testi."""
        db = VectorDatabase(persist_directory=self.persist_directory)
        
        # Koleksiyon oluştur
        collection_name = "test_collection"
        await db.create_collection(collection_name)
        
        # Belgeleri ekle
        doc_ids = await db.add_documents(
            collection_name=collection_name,
            documents=self.test_documents,
            metadatas=self.test_metadatas
        )
        
        # Belgeyi güncelle
        updated_text = "Yapay zeka (AI), insan zekasını simüle etmek için tasarlanmış bilgisayar sistemleridir."
        success = await db.update_document(
            collection_name=collection_name,
            document_id=doc_ids[0],
            document=updated_text,
            metadata={"category": "ai", "difficulty": "beginner", "updated": True}
        )
        
        self.assertTrue(success)
        
        # Güncellenmiş belgeyi getir
        document = await db.get_document(collection_name, doc_ids[0])
        self.assertEqual(document["document"], updated_text)
        self.assertTrue(document["metadata"]["updated"])
    
    async def async_test_delete_document(self):
        """Belge silme testi."""
        db = VectorDatabase(persist_directory=self.persist_directory)
        
        # Koleksiyon oluştur
        collection_name = "test_collection"
        await db.create_collection(collection_name)
        
        # Belgeleri ekle
        doc_ids = await db.add_documents(
            collection_name=collection_name,
            documents=self.test_documents,
            metadatas=self.test_metadatas
        )
        
        # Belgeyi sil
        success = await db.delete_document(
            collection_name=collection_name,
            document_id=doc_ids[0]
        )
        
        self.assertTrue(success)
        
        # Silinen belgeyi getirmeye çalış
        document = await db.get_document(collection_name, doc_ids[0])
        self.assertIsNone(document)
    
    async def async_test_delete_collection(self):
        """Koleksiyon silme testi."""
        db = VectorDatabase(persist_directory=self.persist_directory)
        
        # Koleksiyon oluştur
        collection_name = "test_collection"
        await db.create_collection(collection_name)
        
        # Koleksiyonu sil
        success = await db.delete_collection(collection_name)
        
        self.assertTrue(success)
        
        # Koleksiyonları listele
        collections = await db.list_collections()
        self.assertNotIn(collection_name, collections)
    
    def test_all(self):
        """Tüm asenkron testleri çalıştır."""
        loop = asyncio.get_event_loop()
        
        # Tüm asenkron testleri çalıştır
        loop.run_until_complete(self.async_test_create_collection())
        loop.run_until_complete(self.async_test_add_documents())
        loop.run_until_complete(self.async_test_search())
        loop.run_until_complete(self.async_test_update_document())
        loop.run_until_complete(self.async_test_delete_document())
        loop.run_until_complete(self.async_test_delete_collection())


if __name__ == "__main__":
    unittest.main()
