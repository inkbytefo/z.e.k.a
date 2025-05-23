# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# MCP Entegrasyon Test Modülü

import os
import sys
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

# Proje kök dizinini ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.mcp_integration import MCPIntegration, discover_mcp_servers, register_mcp_server
from src.core.vector_database import VectorDatabase
from src.core.exceptions import MCPError


class TestMCPIntegration(unittest.TestCase):
    """MCP entegrasyonu testleri."""
    
    def setUp(self):
        """Test öncesi hazırlık."""
        # Mock vektör veritabanı
        self.mock_vector_db = MagicMock()
        
        # Test verileri
        self.test_server_name = "Test MCP Server"
        self.test_server_url = "http://localhost:8765"
    
    @patch("mcp.server.fastmcp.FastMCP")
    def test_init(self, mock_fastmcp):
        """Başlatma testi."""
        # Mock FastMCP
        mock_server = MagicMock()
        mock_fastmcp.return_value = mock_server
        
        # MCP entegrasyonunu başlat
        integration = MCPIntegration(
            server_name=self.test_server_name,
            vector_db=self.mock_vector_db,
            enable_telemetry=False
        )
        
        self.assertIsNotNone(integration)
        self.assertEqual(integration.server, mock_server)
        self.assertFalse(integration.is_server_running)
        self.assertIsNone(integration.client)
        self.assertEqual(integration.metrics["total_requests"], 0)
        
        # FastMCP'nin doğru parametrelerle çağrıldığını doğrula
        mock_fastmcp.assert_called_once()
        args, kwargs = mock_fastmcp.call_args
        self.assertEqual(kwargs["enable_telemetry"], False)
    
    @patch("mcp.server.fastmcp.FastMCP")
    async def async_test_start_server(self, mock_fastmcp):
        """Sunucu başlatma testi."""
        # Mock FastMCP
        mock_server = MagicMock()
        mock_server.run = AsyncMock()
        mock_fastmcp.return_value = mock_server
        
        # MCP entegrasyonunu başlat
        integration = MCPIntegration(server_name=self.test_server_name)
        
        # _wait_for_server_ready metodunu mock'la
        integration._wait_for_server_ready = AsyncMock()
        
        # Sunucuyu başlat
        server_task = await integration.start_server(
            host="localhost",
            port=8765,
            timeout=1.0
        )
        
        self.assertTrue(integration.is_server_running)
        self.assertIsNotNone(server_task)
        
        # Sunucu run metodunun çağrıldığını doğrula
        mock_server.run.assert_called_once_with(host="localhost", port=8765)
        
        # _wait_for_server_ready metodunun çağrıldığını doğrula
        integration._wait_for_server_ready.assert_called_once_with("localhost", 8765)
    
    @patch("mcp.client.MCPClient")
    async def async_test_connect_to_server(self, mock_mcp_client):
        """Sunucuya bağlanma testi."""
        # Mock MCPClient
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_mcp_client.return_value = mock_client
        
        # MCP entegrasyonunu başlat
        integration = MCPIntegration(server_name=self.test_server_name)
        
        # Sunucuya bağlan
        result = await integration.connect_to_server(
            server_url=self.test_server_url,
            server_name="Test Client",
            server_type="local",
            timeout=1.0
        )
        
        self.assertTrue(result)
        self.assertEqual(integration.client, mock_client)
        
        # Bağlı sunucular listesinde olduğunu doğrula
        self.assertIn(self.test_server_url, integration.connected_servers)
        self.assertEqual(integration.connected_servers[self.test_server_url]["name"], "Test Client")
        
        # connect metodunun çağrıldığını doğrula
        mock_client.connect.assert_called_once()
    
    @patch("mcp.client.MCPClient")
    async def async_test_execute_tool(self, mock_mcp_client):
        """Araç çalıştırma testi."""
        # Mock MCPClient
        mock_client = MagicMock()
        mock_client.execute_tool = AsyncMock(return_value="Test result")
        mock_mcp_client.return_value = mock_client
        
        # MCP entegrasyonunu başlat
        integration = MCPIntegration(server_name=self.test_server_name)
        
        # Sunucuya bağlan
        integration.client = mock_client
        
        # Aracı çalıştır
        result = await integration.execute_tool(
            tool_name="test_tool",
            param1="value1",
            param2="value2"
        )
        
        self.assertEqual(result, "Test result")
        self.assertEqual(integration.metrics["total_tool_calls"], 1)
        
        # execute_tool metodunun doğru parametrelerle çağrıldığını doğrula
        mock_client.execute_tool.assert_called_once_with(
            "test_tool",
            param1="value1",
            param2="value2"
        )
    
    @patch("mcp.client.MCPClient")
    async def async_test_get_resource(self, mock_mcp_client):
        """Kaynak getirme testi."""
        # Mock MCPClient
        mock_client = MagicMock()
        mock_client.get_resource = AsyncMock(return_value="Test content")
        mock_mcp_client.return_value = mock_client
        
        # MCP entegrasyonunu başlat
        integration = MCPIntegration(server_name=self.test_server_name)
        
        # Sunucuya bağlan
        integration.client = mock_client
        
        # Kaynağı getir
        content = await integration.get_resource(
            resource_uri="test://resource",
            timeout=1.0
        )
        
        self.assertEqual(content, "Test content")
        self.assertEqual(integration.metrics["total_resource_requests"], 1)
        
        # get_resource metodunun çağrıldığını doğrula
        mock_client.get_resource.assert_called_once_with("test://resource")
    
    @patch("aiohttp.ClientSession.get")
    async def async_test_discover_mcp_servers(self, mock_get):
        """MCP sunucuları keşfetme testi."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "servers": [
                {"url": "http://server1.example.com", "name": "Server 1"},
                {"url": "http://server2.example.com", "name": "Server 2"}
            ]
        })
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Sunucuları keşfet
        servers = await discover_mcp_servers(
            discovery_url="http://test.example.com/servers",
            timeout=1.0
        )
        
        self.assertEqual(len(servers), 2)
        self.assertEqual(servers[0]["url"], "http://server1.example.com")
        self.assertEqual(servers[1]["name"], "Server 2")
        
        # get metodunun çağrıldığını doğrula
        mock_get.assert_called_once_with("http://test.example.com/servers", timeout=1.0)
    
    @patch("aiohttp.ClientSession.post")
    async def async_test_register_mcp_server(self, mock_post):
        """MCP sunucusu kaydetme testi."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Sunucuyu kaydet
        result = await register_mcp_server(
            server_url="http://test.example.com",
            server_name="Test Server",
            server_type="community",
            registry_url="http://registry.example.com/register",
            timeout=1.0
        )
        
        self.assertTrue(result)
        
        # post metodunun çağrıldığını doğrula
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://registry.example.com/register")
        self.assertEqual(kwargs["json"]["url"], "http://test.example.com")
        self.assertEqual(kwargs["json"]["name"], "Test Server")
    
    def test_all(self):
        """Tüm asenkron testleri çalıştır."""
        loop = asyncio.get_event_loop()
        
        # Tüm asenkron testleri çalıştır
        loop.run_until_complete(self.async_test_start_server())
        loop.run_until_complete(self.async_test_connect_to_server())
        loop.run_until_complete(self.async_test_execute_tool())
        loop.run_until_complete(self.async_test_get_resource())
        loop.run_until_complete(self.async_test_discover_mcp_servers())
        loop.run_until_complete(self.async_test_register_mcp_server())


if __name__ == "__main__":
    unittest.main()
