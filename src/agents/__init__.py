# ZEKA - Kişiselleştirilmiş Çoklu Ajanlı Yapay Zeka Asistanı
# Ajanlar paketi

from .conversation_agent import ConversationAgent
from .desktop_agent import DesktopAgent

__all__ = [
    'ConversationAgent',
    'DesktopAgent'
    # İlerleyen aşamalarda diğer ajanlar eklenecek
    # 'CalendarAgent',
    # 'EmailAgent',
    # 'ResearchAgent',
    # 'CodingAgent'
]