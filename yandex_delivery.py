import aiohttp
from aiohttp import web
import asyncio
from config_loader import Config
import json
from dataclasses import dataclass
from webhook_server import WebhookServer
from storage import NewsStorage
from yandex_adapter import YandexAdapter

class BotCommand():
    SUBSCRIBE_TG = "Подписаться на рассылку в Telegram"
    UNSUBSCRIBE_TG = "Отписаться от рассылки в Telegram"
    SUBSCRIBE_YX = "Подписаться на рассылку в Яндекс Мессенджере"
    UNSUBSCRIBE_YX = "Отписаться от рассылки в Яндекс Мессенджере"
    CURRENT_SUB = "Текущие подписки"
    LINK_TELEGRAM = "Привязать Telegram-аккаунт"

@dataclass
class YandexBotConfig:
    bot_token: str
    base_url: str
    webhook_url: str
    send_message_url: str
    send_image_url: str
    disk_token: str
    default_chat_id: str

    @classmethod
    def from_config(cls, config: Config):
        yandex_config = config.load_config('yandex')
        server_config = config.load_config('server')

        return cls(
            bot_token=yandex_config['bot_token'],
            base_url = yandex_config['base_url'],
            webhook_url = yandex_config['set_webhook'],
            send_message_url = yandex_config['send_message_url'],
            send_image_url = yandex_config['send_image_url'],
            disk_token = yandex_config['disk_token'],
            default_chat_id = yandex_config['user_id']
        )

class YandexDeliveryBot:

    WELCOME_MESSAGE = """✨ Добро пожаловать в **Яндекс Бот**!

     Здесь вы можете настроить доставку 
     корпоративных новостей прямо в Telegram.
    """
    THIN_SPACE = '\u2009'
    BUTTON_WIDTH = 60
    
    def __init__(self, config: YandexBotConfig, storage):
        self.count = 0
        self.config = config
        self.storage = storage
        self._session = None
        self._setup_ui_texts()
        self._setup_headers()

    def _setup_ui_texts(self):

        thin_space = self.THIN_SPACE
        width = self.BUTTON_WIDTH

        # self.subscribe_tg = f"{BotCommand.SUBSCRIBE_TG:{thin_space}^{width+19}}"
        # self.unsubscribe_tg = f"{BotCommand.UNSUBSCRIBE_TG:{thin_space}^{width+22}}"
        # self.subscribe_yx = f"{BotCommand.SUBSCRIBE_YX:{thin_space}^{width}}"
        # self.unsubscribe_yx = f"{BotCommand.UNSUBSCRIBE_YX:{thin_space}^{width+2}}"
        # self.current_sub = f"{BotCommand.CURRENT_SUB:{thin_space}^{width+44}}"
        # self.link_telegram = f"{BotCommand.LINK_TELEGRAM:{thin_space}^{width+32}}"

        self.subscribe_tg = f"{BotCommand.SUBSCRIBE_TG}"
        self.unsubscribe_tg = f"{BotCommand.UNSUBSCRIBE_TG}"
        self.subscribe_yx = f"{BotCommand.SUBSCRIBE_YX}"
        self.unsubscribe_yx = f"{BotCommand.UNSUBSCRIBE_YX}"
        self.current_sub = f"{BotCommand.CURRENT_SUB}"
        self.link_telegram = f"{BotCommand.LINK_TELEGRAM}"

        self.keyboard = [{"text": btn} for btn in [
            self.subscribe_tg,
            self.unsubscribe_tg,
            self.subscribe_yx,
            self.unsubscribe_yx,
            self.current_sub,
        ]]

        self.keyboard.append({"text": self.link_telegram, "url": "https://t.me/universe_data_bot" })
    
    def _setup_headers(self):
        self.headers = {"Authorization": f"OAuth {self.config.bot_token}"}
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(self, method: str, url: str, **kwargs):
        try:
            session = await self._get_session()
            kwargs['headers'] = self.headers

            async with session.request(method, url, **kwargs) as response:
                return await response.json()
        except Exception as ex:
            print("Ошибка: ", ex)
    
    async def send_message_with_buttons(self, login: str, text: str, btn=None):
        if btn is None:
            btn = self.keyboard
        return await self._make_request(
            'POST',
            self.config.send_message_url,
            json={
                "login": login,
                "text": text,
                "inline_keyboard": btn
            }
        )

    async def send_image(self, login: str, image: bytes):
        url = self.config.send_image_url
        data = aiohttp.FormData()
        data.add_field('login', login)
        data.add_field('image', image)
        
        session = await self._get_session()
        async with session.post(url, headers=self.headers, data=data) as resp:
            return await resp.json()

    async def send_message(self, login: str, text: str):
        return await self._make_request(
        'POST',
        self.config.send_message_url,
        json={
            "login": login,
            "text": text
        }
    )

    async def send_welcome(self, login: str):
        return await self.send_message_with_buttons(login, self.WELCOME_MESSAGE)


    async def set_webhook(self, webhook_url):
        return await self._make_request(
            "POST",
            self.config.webhook_url,
            json={"webhook_url": webhook_url})
    
    async def handle_webhook(self, request):
        try:
            print("Новый веб-хук!")
            data = await request.json()

            asyncio.create_task(self._process_webhook_data(data))
            return web.json_response({'ok': True}, status=200)
            # print(json.dumps(data, indent=2, ensure_ascii=False))

        except Exception as ex:
            print(f"Ошибка обработки вебхука: {ex}")
            return web.Response(text='Error', status=500)
    
    async def _process_webhook_data(self, data):
        if 'updates' not in data:
                return web.Response(text='No updates', status=200)
        else:
            for update in data['updates']:
                await self._process_update(update)
                
    async def _process_update(self, update):

        try:
            text = update.get('text')
            if not text and 'forwarded_messages' in update:
                text = update['forwarded_messages'][0].get('text')
            
            images_itog = []
            if 'images' in update and update['images']:
                images = update['images']
                for image in images:
                    images_itog.append(image[-1]['file_id'])
            elif 'forwarded_messages' in update:
                forwarded = update['forwarded_messages'][0]
                if 'images' in forwarded and forwarded['images']:
                    for image in forwarded['images']:
                        images_itog.append(image[-1]['file_id'])
            
            print("images_itog", images_itog)

            user_login = update['from']['login']
            type_chat = update['chat']['type']

            if type_chat == "private":
                if text == "/start":
                    await self.handle_start(user_login)
                elif text == "/link":
                    await self.send_warning(user_login)
                elif text == "/help":
                    await self.send_help(user_login)
                elif text == "/subscribe_tg" or text == self.subscribe_tg:
                    await self.handle_subscribe_tg(user_login)
                elif text == "/unsubscribe_tg" or text == self.unsubscribe_tg:
                    await self.handle_unsubscribe_tg(user_login)
                elif text == "/subscribe_yx" or text == self.subscribe_yx:
                    await self.handle_subscribe_yx(user_login)
                elif text == "/unsubscribe_yx" or text == self.unsubscribe_yx:
                    await self.handle_unsubscribe_yx(user_login)
                elif text == "/status" or text == self.current_sub:
                    await self.handle_status(user_login)
                else:
                    await self.send_help(user_login)
            elif type_chat == "group":
                if images_itog:
                    tasks = []
                    for file_id in images_itog:
                        tasks.append(self.download_file_by_id(file_id))
                    
                    files_bytes = await asyncio.gather(*tasks)
                    for file_bytes in files_bytes:
                        if file_bytes:
                            await self.send_image(user_login, file_bytes)
                await self.send_message(user_login, text)
        except Exception as ex:
            print(f"Ошибка обработки вебхука {ex}")


    async def download_file_by_id(self, file_id: str):
        url = "https://botapi.messenger.yandex.net/bot/v1/messages/getFile/"
        headers = {"Authorization": f"OAuth {self.config.bot_token}"}
        data = {"file_id": file_id}
    
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status != 200:
                    print(f"Ошибка скачивания файла: {resp.status}")
                    return None
                return await asyncio.wait_for(resp.read(), timeout = 10.0)
        except Exception as ex:
            print(f"Ошибка при скачивании: {ex}")
            return None

    async def send_help(self, login: str):
        if not await self.storage.check_exist_yx_login(login):
             await self.storage.add_user_yx(login)
        return await self.send_message_with_buttons(login, "Доступные команды")

    async def send_warning(self, login: str):
        return await self.send_message_with_buttons(login, f"Для использования бота необходимо привязать telegram-аккаунт! \nВаш логин: {login}")
    
    async def check_link(self, login: str):
        tg_id = await self.storage.get_tg_id_by_yx(login)

        if not tg_id:
            await self.send_warning(login) 

        return tg_id

    async def handle_start(self, login: str):
        if not await self.storage.check_exist_yx_login(login):
             await self.storage.add_user_yx(login)
        tg_id = await self.check_link(login)
        if tg_id:
            await self.storage.add_user_yx(login)
            await self.send_welcome(login)
    
    async def handle_subscribe_tg(self, login: str):
        tg_id = await self.check_link(login)
        if tg_id:
            await self.storage.subscribe_user_tg(tg_id)
            await self.send_message_with_buttons(login, "✅ Вы подписались на рассылку в Telegram!")

    async def handle_unsubscribe_tg(self, login: str):
        tg_id = await self.check_link(login)
        if tg_id:
            await self.storage.unsubscribe_user_tg(tg_id)
            await self.send_message_with_buttons(login, "❌ Вы отписались от рассылки в Telegram")
    
    async def handle_status(self, login: str):
        tg_id = await self.check_link(login)
        if tg_id:
            active_tg = "активна! ✅" if await self.storage.check_active_tg(tg_id) else "неактивна ❌"
            active_yx = "активна! ✅" if await self.storage.check_active_yx(login) else "неактивна ❌"

            
            await self.send_message_with_buttons(login, f'''Ваши подписки: \n\nTelegram: Подписка {active_tg}\nЯндекс Мессенджер: Подписка {active_yx}
                                            ''')
         
    async def handle_subscribe_yx(self, login: str):
        tg_id = await self.check_link(login)
        print(tg_id)
        if tg_id:
            await self.storage.subscribe_user_yx(login)
            await self.send_message_with_buttons(login, "✅ Вы подписались на рассылку в Яндекс Мессенджере!")
        
    async def handle_unsubscribe_yx(self, login: str):
        tg_id = await self.check_link(login)
        if tg_id:
            await self.storage.unsubscribe_user_yx(login)
            await self.send_message_with_buttons(login, "❌ Вы отписались от рассылки в Яндекс Мессенджере")

    def _format_notification(self, news_item):

        title = news_item['title']
        content = news_item['content']
        rubric = news_item['rubric']
        link = news_item['link']

        rubric_emojis = {
            'Anniversary time': '🎉',
            'Career upgrade': '🚀',
            'день рождения': '🎂',
            'Без рубрики': '📰'
        }
    
        emoji = rubric_emojis.get(rubric, '📌')

        message = (
            f"{emoji} **{title}**\n\n"
            f"{content}\n\n"
            f"🏷️ Рубрика: __{rubric}__\n"
            f"🔗 [Читать полностью]({link})"
        )

        return message
    
    
    async def send_notification(self, news_item, login):

        try:
            message = self._format_notification(news_item)
            await self.send_message(login, message)

            return True

        except Exception as ex:
            print(f"Ошибка отправки в Яндекс Мессенджер: {ex}")
            return False

    async def send_to_many(self, news_item, logins):
        try:
            tasks = []
            for login in logins:
                task = self.send_notification(news_item, login)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = 0
            failed = 0

            print(f"Отправлено в Яндекс Мессенджер: {news_item['title']}")
            for result in results:
                if isinstance(result, bool) and result:
                    successful += 1
                else:
                    failed += 1
            
            print(f"Результат отпрвки: успешно - {successful}, неудачно - {failed}")
            return successful

        except Exception as ex:
            print("Ошибка в send_to_many: ", ex)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()
        print("Сессия закрыта")




async def main():
    bot = None
    try:
        async with NewsStorage() as storage:
            config = Config()
            bot_config = YandexBotConfig.from_config(config)

            bot = YandexDeliveryBot(bot_config, storage)
            
            await bot.send_welcome(bot_config.default_chat_id)

            TEST_NEWS = {
            'id': 'hr_266',
            'title': 'Anniversary time: Барсов Кирилл!',
            'content': 'Сегодня год в компании отмечает @Барсов Кирилл...',
            'rubric': 'Anniversary time',
            'link': 'https://universe-data.ismyteam.ru/news/detail/266'
            }  
            logins = await storage.get_all_activate_users_yx()
            print(logins)
            await bot.send_to_many(TEST_NEWS, logins)
            server = WebhookServer(bot, "0.0.0.0", 8080)
            await server.start()
            webhook = await bot.set_webhook(config.load_config('server')['base_url'])
            print(json.dumps(webhook, indent=2, ensure_ascii=False))
            await asyncio.Event().wait()
    except Exception as ex:
        print("Ошибка: ",ex)
    finally:
        if bot:
            await bot.close()
            print("Ссесия закрыта")



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        print("Сервер отключен")