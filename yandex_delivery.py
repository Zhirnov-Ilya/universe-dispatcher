import aiohttp
import asyncio
from config_loader import Config

class YandexDerlivery:
    
    def __init__(self, bot_token, base_url, default_chat_id=None):
        self.bot_token = bot_token
        self.base_url = base_url
        self.chat_id = default_chat_id
        self.headers = {"Authorization": f"OAuth {self.bot_token}"}

    async def send_message(self, login, text):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}",
                json={"login": login, "text": text},
                headers=self.headers
            ) as resp:
             return await resp.json()

async def main():
    config = Config()
    bot_token = config.load_config('yandex')['bot_token']
    base_url = config.load_config('yandex')['base_url']
    user_id = config.load_config('yandex')['user_id']

    print(bot_token)
    print(base_url)
    print(user_id)
    
    yx_service = YandexDerlivery(bot_token, base_url, user_id)
    print(yx_service.headers)
    print(await yx_service.send_message(user_id, "Новое сообщение!!"))

if __name__ == "__main__":
    asyncio.run(main())