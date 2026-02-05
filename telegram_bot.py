from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault
from storage import NewsStorage
import asyncio
from storage import NewsStorage
from config_loader import Config

class NewsBot:

    def __init__(self, token , storage):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.storage = storage

        self.dp.message(Command("start"))(self.start_handler)
        self.dp.message(Command("subscribe"))(self.subscribe_handler)
        self.dp.message(Command("unsubscribe"))(self.unsubcribe_handler)
        self.dp.message(Command("help"))(self.help_handler)

        self.dp.startup.register(self.set_commands)
        

    async def set_commands(self, bot):

        commands = [
            BotCommand(command="start", description="Начать работу"),
            BotCommand(command="subscribe", description="Подписаться на рассылку"),
            BotCommand(command="unsubscribe", description="Отписаться от рассылки"),
            BotCommand(command="help", description="Помощь и информация"),
        ]
        await bot.set_my_commands(commands, BotCommandScopeDefault())

    async def help_handler(self, message):

        help_text = (
            "<b>Доступные команды:</b>\n\n"
            "/start - Начать работу и подписаться\n"
            "/subscribe - Подписаться на новости\n"
            "/unsubscribe - Отписаться от новостей\n"
            "/help - Команды\n\n"
            "📰 Новости автоматически приходят из HR-портала"
        )
        await message.answer(help_text, parse_mode="HTML")

    async def start_handler(self, message):
        user = message.from_user

        await self.storage.add_user(
            user_id = user.id,
            chat_id = message.chat.id,
            user_name = user.username
        )

        await message.answer(
            "✨Вы подписаны на новости HR-портала!\n\n"
            "Команды:\n"
            "/subscribe - подписаться\n"
            "/unsubscribe - отписаться\n"
            "/help\n"
        )

    async def subscribe_handler(self, message):

        await self.storage.subscribe_user(message.from_user.id)
        await message.answer("✅Вы подписались на рассылку!")
    
    async def unsubcribe_handler(self, message):
        await self.storage.unsubsribe_user(message.from_user.id)
        await message.answer("❌Вы отписались от рассылки")

    async def run(self):
        try:
            print("Бот запущен")
            await self.dp.start_polling(self.bot)
        except Exception as ex:
            print("Ошибка запуска бота: ", ex)

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
        