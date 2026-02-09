import aiosqlite
import asyncio
from datetime import datetime
import os
import pathlib 
from pathlib import Path

class NewsStorage:

    def __init__(self, db_name = "news.db"):

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        self.db_path = str(data_dir/db_name)
        self.connection = None
        self.db_name = db_name


    async def connect(self):
        if self.connection is None:
            self.connection = await aiosqlite.connect(self.db_path)
            await self._create_table()
            await self.initialize_last_id("hr_portal", "hr_275")
            print("Подключение к БД выполнено")

    async def _create_table(self):

        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS sent_news (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("В базе данных создана таблица sent_news")

        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER UNIQUE NOT NULL,
            user_name TEXT,
            is_active BOOLEAN DEFAULT 1)        
        ''')
        print("В базе данных создана таблица users")


        await self.connection.commit()
    
    async def initialize_last_id(self, source_code, default_id="hr_0"):
        async with self.connection.execute(
            "SELECT COUNT(*) FROM sent_news WHERE source = ?", (source_code,)
        ) as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                await self.connection.execute(
                    "INSERT INTO sent_news (id, source) VALUES (?, ?)",
                    (default_id, source_code)
                )
                await self.connection.commit()
                print(f"Вставка начального значаения hr_id = {default_id}")

    async def add_user(self, user_id, chat_id, user_name):
        try:
            await self.connection.execute('''
            INSERT OR REPLACE INTO users
            (user_id, chat_id, user_name, is_active)
            VALUES (?, ?, ?, 1)
            ''', (user_id, chat_id, user_name))

            await self.connection.commit()
        except Exception as ex:
            print("Ошибка добавления пользователя: ", ex)
            return False

    async def get_all_activate_users(self):

        try:
            async with self.connection.execute('''
                SELECT chat_id from users WHERE is_active = 1
            ''') as cursor:
                
                results = await cursor.fetchall()
                return [row[0] for row in results] if results else []
        except Exception as ex:
            print("Ошибка получения chat_id", ex)
    
    async def subscribe_user(self, user_id):
        try:
            await self.connection.execute(
                "UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,)
            )
            await self.connection.commit()
            return True
        except Exception as ex:
            print("Ошибка подпсики: ", ex)
            return False
    
    async def unsubsribe_user(self, user_id):

        try:
            await self.connection.execute(
                "UPDATE users SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            return False
    
    async def get_last_id(self, source_code):
        try:
            async with self.connection.execute(
                "SELECT MAX(id) FROM sent_news  WHERE source = ?", (source_code,)
            ) as cursor:

                result = await cursor.fetchone()
                return result[0] if result else None

        except Exception as ex:
            print("Ошибка получения id: ", ex)

    async def update_id(self, source_code, new_id, last_id):
        try:
            await self.connection.execute(
                """UPDATE sent_news SET id = ?
                   WHERE id = ? AND source = ?
            """, (new_id, last_id, source_code)
            )
            await self.connection.commit()
            print(f"Обновлен last_id для {source_code}: {new_id}")
        except Exception as ex:
            print("Ошибка обновления id: ", ex)


    async def close(self):
        if self.connection:
            await self.connection.close()
            print("Соединение с БД закрыто")
    


    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

async def main():
    async with NewsStorage() as storage:
        chat_ids = await storage.get_all_activate_users()
        print(chat_ids)
        await storage.add_user(15, 100, "Ilya")
        await storage.unsubsribe_user(15)
        await storage.subscribe_user(15)
        last_id = await storage.get_last_id('hr_portal')
        print(last_id)
        chat_id = await storage.get_all_activate_users()
        print(chat_id)

if __name__ == "__main__":
    asyncio.run(main())


    





    




