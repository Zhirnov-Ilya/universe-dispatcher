import time
from telegram_delivery import TelegramDelivery
from yandex_delivery import YandexDeliveryBot
from datetime import datetime
import asyncio

class Dispatcher:

    def __init__(self, adapter, storage, telegram, check_interval, yandex):

        self.adapter = adapter
        self.storage = storage
        self.telegram = telegram
        self.yandex = yandex
        self.check_interval = check_interval
        self.running = False

    async def run_once(self):
        print(f"Проверка в {datetime.now().strftime('%H:%M:%S')}")

        total_new = 0

        last_id = await self.storage.get_last_id(self.adapter.source_code)
        print(f"Последний известный id: {last_id}")

        new_news = await self.adapter.fetch_new_news(last_id)

        if new_news:
            max_id = self.adapter.build_news_id(max(int(n['id'].split('_')[1]) for n in new_news))

            await self.storage.update_id(self.adapter.source_code, max_id, last_id)

            total_new += len(new_news)
            
            chat_ids = await self.storage.get_all_activate_users_tg()
            logins = await self.storage.get_all_activate_users_yx()
            for news in new_news:
                success_tg = await self.telegram.send_to_many(news, chat_ids)
                success_yx = await self.yandex.send_to_many(news, logins)

        return total_new

    async def stop(self):
        self.running = False

    async def run_forever(self):

        self.running = True
        print("Диспетчер запущен в режиме опроса")
        print(f"Интервал проверки: {self.check_interval} секунд")

        try:
            while self.running:
                new_count = await self.run_once()

                if new_count > 0:
                    print(f"Итого новых: {new_count}")

                print(f"Следующая проверка через {self.check_interval} секунд")
                print()
                await asyncio.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("Диспетчер остановлен")
        finally:
            await self.stop()
    



