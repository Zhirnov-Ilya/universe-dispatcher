import abc
from datetime import datetime

class BaseNewsAdapter(abc.ABC):

    def __init__(self, name, source_code):
        self.name = name
        self.source_code = source_code
        self.last_check = None

    def __str__(self):
        return f"Адаптер: {self.name} ({self.source_code})"

    @abc.abstractmethod
    async def fetch_news(self):
        pass

    @abc.abstractmethod
    async def fetch_new_news(self):
        pass

    @abc.abstractmethod
    def build_news_id(self, raw_news):
        pass

    def format_for_notification(self, news_item):

        return {
            'id': news_item['id'],
            
        }
    
    def update_last_check_time(self):
        self.last_check = datetime.now()
