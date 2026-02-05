import asyncio
from storage import NewsStorage
from hr_portal_adapter import HRPortalAdapter
from dispatcher import Dispatcher
from config_loader import Config
from telegram_delivery import TelegramDelivery
from telegram_bot import NewsBot

async def run_all():

    print("Запуск Universe Dispatch")

    config = Config()


    async with NewsStorage() as storage:

        news_bot = NewsBot(
            token=config.load_config('telegram')['bot_token'],
            storage=storage
        )

        bot_task = asyncio.create_task(news_bot.run())

        async with HRPortalAdapter(
        base_url = config.load_config('hr_portal')['base_url'],
        api_url = config.load_config('hr_portal')['api_url'],
        username = config.load_config('hr_portal')['username'],
        password = config.load_config('hr_portal')['password'],
        api_token = config.load_config('hr_portal')['api_token']) as hr_adapter:

            telegram = TelegramDelivery(
                bot_token=config.load_config('telegram')['bot_token'],
                default_chat_id = config.load_config('telegram')['chat_id']
            )

            dispatcher = Dispatcher(
                adapter= hr_adapter,
                storage = storage,
                telegram= telegram,
                check_interval=60
            )

            await dispatcher.run_forever()
            try:
                await dispatcher.run_forever()
            finally:
                bot_task.cancel()
                try:
                    await bot_task
                except asyncio.CancelledError:
                    pass


if __name__ == "__main__":
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("Диспетчер остановлен")
