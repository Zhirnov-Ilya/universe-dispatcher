from aiogram import Bot
from base_adapter import BaseNewsAdapter
import asyncio
import json
from config_loader import Config
from bs4 import BeautifulSoup

class TelegramChannelAdapter():
    def __init__(self, bot_token, channel_username):
        self.bot = Bot(token=bot_token)
        self.channel = channel_username

    async def fetch_new_news(self):
        offset = 0
        await self.bot.delete_webhook()
        while True:
            try:
                updates = await self.bot.get_updates(offset=offset, timeout=30)

                print(f"Проверка updates:")
                if updates:
                    print(f"Get updates {len(updates)}")
                    for update in updates:
                        msg = update.message
                        offset = update.update_id + 1
                        updates_dict = []
                        if msg and msg.forward_from_chat:
                            await self.handle_and_forward(update)
                            print(f"ID: {msg.message_id}")
                            print(f"Text: {msg.text}")
                            print(f"Date: {msg.date}")
                            print(f"Caption: {msg.caption}")
                            print(msg.html_text)
                            print('\n\n\n\n')
                            await self._parser_for_yandex(msg.html_text)
                            updates_dict.append(update.model_dump())
                            with open("tg_data.json", 'w', encoding='utf-8') as file:
                                json.dump(updates_dict, file, indent=2, ensure_ascii=False)      
                            print("Данные сохранены!")               
            except Exception as ex:
                print(f"Eroor: {ex}")
            finally:
                await self.bot.session.close()

    async def handle_and_forward(self, update):
        message = update.message

        await self.bot.copy_message(
            chat_id = "5671771943",
            from_chat_id = message.chat.id,
            message_id = message.message_id
        )

    async def _parser_for_yandex(self, html_content):
        
        if not html_content: return ""

        try:

            soup = BeautifulSoup(html_content, 'html.parser')
            for tag in soup.find_all("i"):
                tag.replace_with(f"__{tag.get_text()}__")

            for tag in soup.find_all("tg-emoji"):
                tag.replace_with(f"{tag.get_text()}")
            
            for tag in soup.find_all("b"):
                tag.replace_with(f"**{tag.get_text()}**")
            
            for link in soup.find_all("a"):
                href = link.get('href')
                text = link.get_text()
                link.replace_with(f"[{text}]({href})")
                

            print(soup)
        except Exception as ex:
            print(f"Ошибка парсинга tg_html: {ex}")


async def main():
    config = Config()
    bot_token = config.load_config('telegram')['bot_token']
    adapter = TelegramChannelAdapter(bot_token, "test_universe_dispatcher")
    await adapter.fetch_new_news()

if __name__ == "__main__":
    asyncio.run(main())

