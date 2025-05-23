# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Özel Hata Sınıfları Modülü

"""
Bu modül, ZEKA asistanı için özel hata sınıflarını tanımlar.
Hata yönetimini daha tutarlı ve bilgilendirici hale getirmek için kullanılır.
"""

class ZEKAError(Exception):
    """ZEKA asistanı için temel hata sınıfı."""

    def __init__(self, message: str = "ZEKA asistanında bir hata oluştu", code: str = "ZEKA_ERROR"):
        """Temel hata sınıfı başlatıcısı.

        Args:
            message: Hata mesajı
            code: Hata kodu
        """
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.code}] {self.message}"


# API ve İletişim Hataları

class APIError(ZEKAError):
    """API istekleri sırasında oluşan hatalar için temel sınıf."""

    def __init__(self, message: str = "API isteği sırasında bir hata oluştu", code: str = "API_ERROR"):
        super().__init__(message, code)


class OpenRouterAPIError(APIError):
    """OpenRouter API istekleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "OpenRouter API isteği sırasında bir hata oluştu", code: str = "OPENROUTER_API_ERROR"):
        super().__init__(message, code)


class ModelError(APIError):
    """Dil modeli işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "Dil modeli işlemi sırasında bir hata oluştu", code: str = "MODEL_ERROR", model_name: str = None):
        self.model_name = model_name
        message_with_model = f"{message} (Model: {model_name})" if model_name else message
        super().__init__(message_with_model, code)


class MCPError(APIError):
    """MCP (Model Context Protocol) işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "MCP işlemi sırasında bir hata oluştu", code: str = "MCP_ERROR"):
        super().__init__(message, code)


class CommunicationError(ZEKAError):
    """Ajanlar arası iletişim sırasında oluşan hatalar."""

    def __init__(self, message: str = "Ajanlar arası iletişim sırasında bir hata oluştu", code: str = "COMMUNICATION_ERROR"):
        super().__init__(message, code)


# Veri ve Bellek Hataları

class MemoryManagerError(ZEKAError):
    """Bellek yönetimi sırasında oluşan hatalar."""

    def __init__(self, message: str = "Bellek yönetimi sırasında bir hata oluştu", code: str = "MEMORY_ERROR"):
        super().__init__(message, code)


class VectorDBError(ZEKAError):
    """Vektör veritabanı işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "Vektör veritabanı işlemi sırasında bir hata oluştu", code: str = "VECTORDB_ERROR"):
        super().__init__(message, code)


class DataValidationError(ZEKAError):
    """Veri doğrulama sırasında oluşan hatalar."""

    def __init__(self, message: str = "Veri doğrulama sırasında bir hata oluştu", code: str = "DATA_VALIDATION_ERROR"):
        super().__init__(message, code)


# Ajan ve Görev Hataları

class AgentError(ZEKAError):
    """Ajan işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "Ajan işlemi sırasında bir hata oluştu", code: str = "AGENT_ERROR", agent_id: str = None):
        self.agent_id = agent_id
        message_with_id = f"{message} (Ajan: {agent_id})" if agent_id else message
        super().__init__(message_with_id, code)


class TaskError(ZEKAError):
    """Görev işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "Görev işlemi sırasında bir hata oluştu", code: str = "TASK_ERROR", task_id: str = None):
        self.task_id = task_id
        message_with_id = f"{message} (Görev: {task_id})" if task_id else message
        super().__init__(message_with_id, code)


class TaskAssignmentError(TaskError):
    """Görev atama sırasında oluşan hatalar."""

    def __init__(self, message: str = "Görev atama sırasında bir hata oluştu", code: str = "TASK_ASSIGNMENT_ERROR", task_id: str = None):
        super().__init__(message, code, task_id)


class TaskExecutionError(TaskError):
    """Görev yürütme sırasında oluşan hatalar."""

    def __init__(self, message: str = "Görev yürütme sırasında bir hata oluştu", code: str = "TASK_EXECUTION_ERROR", task_id: str = None):
        super().__init__(message, code, task_id)


# Güvenlik Hataları

class SecurityError(ZEKAError):
    """Güvenlik işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "Güvenlik işlemi sırasında bir hata oluştu", code: str = "SECURITY_ERROR"):
        super().__init__(message, code)


class AuthenticationError(SecurityError):
    """Kimlik doğrulama sırasında oluşan hatalar."""

    def __init__(self, message: str = "Kimlik doğrulama sırasında bir hata oluştu", code: str = "AUTHENTICATION_ERROR"):
        super().__init__(message, code)


class AuthorizationError(SecurityError):
    """Yetkilendirme sırasında oluşan hatalar."""

    def __init__(self, message: str = "Yetkilendirme sırasında bir hata oluştu", code: str = "AUTHORIZATION_ERROR"):
        super().__init__(message, code)


# Yapılandırma Hataları

class ConfigurationError(ZEKAError):
    """Yapılandırma işlemleri sırasında oluşan hatalar."""

    def __init__(self, message: str = "Yapılandırma işlemi sırasında bir hata oluştu", code: str = "CONFIGURATION_ERROR"):
        super().__init__(message, code)


class ResourceNotFoundError(ZEKAError):
    """Kaynak bulunamadığında oluşan hatalar."""

    def __init__(self, message: str = "İstenen kaynak bulunamadı", code: str = "RESOURCE_NOT_FOUND", resource_type: str = None, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id

        if resource_type and resource_id:
            message = f"{resource_type} bulunamadı: {resource_id}"
        elif resource_type:
            message = f"{resource_type} bulunamadı"

        super().__init__(message, code)
