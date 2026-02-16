from base_adapter import BaseNewsAdapter
import asyncio

class YandexAdapter():
    def __init__(message):
        self.message = message
    
    async def format_message(self, message=None):
        if message == None:
            message = self.message
        text = message["text"]


    