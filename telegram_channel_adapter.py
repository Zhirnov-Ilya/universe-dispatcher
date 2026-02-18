from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
from base_adapter import BaseNewsAdapter
import asyncio
import json
from config_loader import Config
from bs4 import BeautifulSoup
from yandex_delivery import YandexDeliveryBot, YandexBotConfig
from storage import NewsStorage

class TelegramChannelAdapter():

    def __init__(self, bot_token, channel_username, storage, yx_bot):
        self.bot = Bot(token=bot_token)
        self.bot_token = bot_token
        self.channel = channel_username
        self.storage = storage
        self.yx_bot = yx_bot

    async def fetch_new_news(self):
        offset = 0
        media_groups = []

        while True:
            try:
                updates = await self.bot.get_updates(offset=offset, timeout=30)

                print(f"Проверка updates:")
                updates_dict = []
                if updates:
                    print(f"Get updates {len(updates)}")

                    for update in updates:
                        offset = update.update_id + 1
                        msg = update.message

                        if msg and msg.media_group_id:
                            group_id = msg.media_group_id
                            media_groups.append(msg)
                            print(f"Добавлено медиа в группу, всего: {len(media_groups)}")

                        elif msg:
                            if media_groups:
                                await self.send_media_group(media_groups)
                                media_groups = []
 
                            await self.handle_and_forward(update)
                            await self._send_yandex(msg)

                    if media_groups:
                        await self.send_media_group(media_groups)
                        media_groups = []

                    # with open("tg_data.json", 'w', encoding='utf-8') as file:
                    #     json.dump(updates_dict, file, indent=2, ensure_ascii=False)      
                    # print("Данные сохранены!")               
            except Exception as ex:
                print(f"Eroor: {ex}")

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
                text = ' '.join(tag.get_text().split())
                tag.replace_with(f"__{text}__")

            for tag in soup.find_all("tg-emoji"):
                text = ' '.join(tag.get_text().split())
                tag.replace_with(f"{text}")
            
            for tag in soup.find_all("b"):
                text = ' '.join(tag.get_text().split())
                tag.replace_with(f"**{text}**")
            
            for tag in soup.find_all("s"):
                text = ' '.join(tag.get_text().split())
                tag.replace_with(f"~~{text}~~")

            for link in soup.find_all("a"):
                href = link.get('href')
                text = link.get_text()
                link.replace_with(f"[{text}]({href})")
            
            
            return str(soup)

        except Exception as ex:
            print(f"Ошибка парсинга tg_html: {ex}")

    async def _send_yandex(self, message):
        try:
            logins = await self.storage.get_all_activate_users_yx()
            text = await self._parser_for_yandex(message.html_text)

            wrong_text = ["__", "**", "~~"]
            for i in wrong_text:
                if i in text:
                    text = message.caption if message.caption else message.text
                    break

            await self.yx_bot.send_to_many(logins, text)
        except Exception as ex:
            print(f"Ошибка отправки в ЯМ: {ex}")


    async def send_media_group(self, messages):
    
        media = []
        caption_added = False
        msg_caption = ""

        for msg in messages:
            if msg.photo:
                file_id = msg.photo[-1].file_id
                
                if msg.caption and not caption_added:
                    media.append(InputMediaPhoto(
                        media=file_id,
                        caption=msg.caption,
                        parse_mode='HTML'
                    ))
                    msg_caption = msg
                    caption_added = True
                else:
                    media.append(InputMediaPhoto(media=file_id))
        
            elif msg.video:
                file_id = msg.video.file_id
                
                if msg.caption and not caption_added:
                    media.append(InputMediaVideo(
                        media=file_id,
                        caption=msg.caption,
                        parse_mode='HTML'
                    ))
                    msg_caption = msg
                    caption_added = True
                else:
                    media.append(InputMediaVideo(media=file_id))
        
        if caption_added:
            await self._send_yandex(msg_caption)


        await self.bot.send_media_group(
            chat_id="5671771943",
            media=media
        )



async def main():
    
    async with NewsStorage() as storage:
        config = Config()
        bot_config = YandexBotConfig.from_config(config)
        yx_bot = YandexDeliveryBot(bot_config, storage)
        bot_token = config.load_config('telegram')['bot_token']
        adapter = TelegramChannelAdapter(bot_token, "test_universe_dispatcher", storage, yx_bot)
        await adapter.fetch_new_news()

if __name__ == "__main__":
    asyncio.run(main())

