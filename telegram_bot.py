from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.types import BotCommand, BotCommandScopeDefault
from storage import NewsStorage
import asyncio
from config_loader import Config
from aiogram.fsm.state import State, StatesGroup

class LinkState(StatesGroup):
    waiting_for_yandex_login = State()

class Messages:
    """Тексты сообщений бота"""
    START = (
        "✨ Вы подписаны на новости HR-портала!\n\n"
        "Команды:\n"
        "/subscribe - подписаться\n"
        "/unsubscribe - отписаться\n"
        "/help - помощь"
    )
    SUBSCRIBED = "✅ Вы подписались на рассылку!"
    UNSUBSCRIBED = "❌ Вы отписались от рассылки"
    HELP = (
        "<b>Доступные команды:</b>\n\n"
        "/start - Начать работу и подписаться\n"
        "/subscribe - Подписаться на новости\n"
        "/unsubscribe - Отписаться от новостей\n"
        "/link_yandex - Привязать Яндекс Мессенджер"
        "/help - Команды\n\n"
        "📰 Новости автоматически приходят из HR-портала"
    )
    LINK_YX = ("🔗 Введите ваш логин (email) от Яндекс Мессенджера:\n"
               "Пример: ivan.ivanov@example.ru")

class NewsBot:

    def __init__(self, token , storage):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.storage = storage

        self.dp.message(Command("start"))(self.start_handler)
        self.dp.message(Command("subscribe"))(self.subscribe_handler)
        self.dp.message(Command("unsubscribe"))(self.unsubscribe_handler)
        self.dp.message(Command("link_yandex"))(self.link_yandex_start)
        self.dp.message(StateFilter(LinkState.waiting_for_yandex_login))(self.link_yandex_finish)
        self.dp.message(Command("help"))(self.help_handler)

        self.dp.startup.register(self.set_commands)
        

    async def set_commands(self):

        commands = [
            BotCommand(command="start", description="Начать работу"),
            BotCommand(command="subscribe", description="Подписаться на рассылку"),
            BotCommand(command="unsubscribe", description="Отписаться от рассылки"),
            BotCommand(command="link_yandex", description="Привязать Яндекс Мессенджер"),
            BotCommand(command="help", description="Помощь и информация"),
        ]
        await self.bot.set_my_commands(commands, BotCommandScopeDefault())

    async def help_handler(self, message):

        help_text = (Messages.HELP)
        await message.answer(help_text, parse_mode="HTML")

    async def start_handler(self, message):
        user = message.from_user

        await self.storage.add_user_tg(
            user_id = user.id,
            chat_id = message.chat.id,
            user_name = user.username
        )

        await message.answer(Messages.START)

    async def subscribe_handler(self, message):

        await self.storage.subscribe_user_tg(message.from_user.id)
        await message.answer(Messages.SUBSCRIBED)
    
    async def unsubscribe_handler(self, message):
        await self.storage.unsubsribe_user_tg(message.from_user.id)
        await message.answer(Messages.UNSUBSCRIBED)
    
    async def link_yandex_start(self, message, state):
        await message.answer(Messages.LINK_YX, parse_mode='HTML')
        await state.set_state(LinkState.waiting_for_yandex_login)
    
    async def link_yandex_finish(self, message, state):
        yandex_login = message.text.strip()
        if await self.storage.check_exist_yx_login(yandex_login):
            await self.storage.link_accounts(message.from_user.id, yandex_login)
            await message.answer(f"✅ Яндекс Мессенджер {yandex_login} привязан!")
            await state.clear()
        else:
            await message.answer(f"❌ Логин {yandex_login} не найден!\nСначала напишите боту в Яндекс Мессенджере")
            await state.clear()

    async def run(self):
        try:
            print("Бот запущен")
            await self.dp.start_polling(self.bot)
        except Exception as ex:
            print("Ошибка запуска бота: ", ex)
        finally:
            await self.bot.session.close()
            print("Сессия бота закрыта")

async def main():

    async with NewsStorage() as storage:
        config = Config()
        token = config.load_config('telegram')['bot_token']
        bot = NewsBot(token, storage)
        await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот отключен")
        