import asyncio
from telegram import Bot
from config_loader import Config
from telegram.constants import ParseMode

class TelegramDelivery:

    def __init__(self, bot_token, default_chat_id=None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.bot = Bot(token=bot_token)

    def _format_notification(self, news_item):

        title = self._escape_html(news_item['title'])
        content = self._escape_html(news_item['content'])
        rubric = self._escape_html(news_item['rubric'])
        link = self._escape_html(news_item['link'])

        rubric_emojis = {
            'Anniversary time': '🎉',
            'Career upgrade': '🚀',
            'день рождения': '🎂',
            'Без рубрики': '📰'
        }
    
        emoji = rubric_emojis.get(rubric, '📌')

        message = (
            f"{emoji} <b>{title}</b>\n\n"
            f"{content}\n\n"
            f"🏷️ <i>Рубрика: {rubric}</i>\n"
            f"🔗 <a href='{link}'>Читать полностью</a>"
        )

        return message
    
    def _escape_html(self, text):
        if not text:
            return ""
        
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', "&qout;").replace("'", '&#39')
        return text
        


    async def send_notification(self, text, chat_id=None):
        target_chat = chat_id or self.default_chat_id
        print(target_chat)

        if not target_chat:
            print("Не указан chat_id для отправки")
            return False

        try:
            # message = self._format_notification(news_item)
            await self.bot.send_message(
                chat_id = target_chat,
                text = text,
                parse_mode = ParseMode.HTML,
                disable_web_page_preview = True
            )

            return True

        except Exception as e:
            print(f"Ошибка отправки в Telegram: {e}")
            return False

    async def send_to_many(self, text, chat_ids):
        
        try:
            tasks = []
            for chat_id in chat_ids:
                task = self.send_notification(text, chat_id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = 0
            failed = 0

            print(f"Отправлено в Telegram!")
            for result in results:
                if isinstance(result, bool) and result:
                    successful += 1
                else:
                    failed += 1
            
            print(f"Результат отпрвки: успешно - {successful}, неудачно - {failed}")
            return successful

        except Exception as ex:
            print("Ошибка в send_to_many: ", ex)

async def main():
    config = Config()
    BOT_TOKEN = config.load_config('telegram')['bot_token']
    CHAT_ID = config.load_config('telegram')['chat_id']
    print(CHAT_ID)
    TEST_NEWS = {
    'id': 'hr_266',
    'title': 'Anniversary time: Барсов Кирилл!',
    'content': 'Сегодня год в компании отмечает @Барсов Кирилл...',
    'rubric': 'Anniversary time',
    'link': 'https://universe-data.ismyteam.ru/news/detail/266'
    }       
    telegram = TelegramDelivery(BOT_TOKEN, CHAT_ID)
    try:
        await telegram.send_notification(TEST_NEWS)

    except Exception as ex:
        print(f"Ошибка отправки сообщения: {ex}")

if __name__ == "__main__":
    asyncio.run(main())