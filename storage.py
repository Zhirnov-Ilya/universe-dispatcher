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
            await self.initialize_last_id("hr_portal", "hr_0")
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
        CREATE TABLE IF NOT EXISTS users_tg (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER UNIQUE NOT NULL,
            user_name TEXT,
            is_active BOOLEAN DEFAULT 1)        
        ''')
        print("В базе данных создана таблица users_tg")

        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS users_yx (
            login TEXT PRIMARY KEY,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        print("В базе данных создана таблица users_yx")

        await self.connection.execute('''
        CREATE TABLE IF NOT EXISTS user_tg_yx (
        tg_id INTEGER,
        yx_id TEXT,
        FOREIGN KEY (tg_id) REFERENCES users_tg (user_id) ON DELETE CASCADE,
        FOREIGN KEY (yx_id) REFERENCES users_yx (login) ON DELETE CASCADE,
        PRIMARY KEY (tg_id, yx_id)
        )
        ''')

        await self.connection.commit()
    
    async def initialize_last_id(self, source_code, default_id):
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

    async def link_accounts(self, tg_id, yx_id):
        await self.connection.execute('''
        INSERT INTO user_tg_yx(tg_id, yx_id)
        VALUES (?, ?)
        ''', (tg_id, yx_id))
        await self.connection.commit()
    
    async def get_tg_id_by_yx(self, yx_id):
        async with self.connection.execute('''
            SELECT tg_id FROM user_tg_yx WHERE yx_id = ?
        ''', (yx_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def add_user_yx(self, login):
        try:
            await self.connection.execute('''
            INSERT OR REPLACE INTO users_yx
            (login, is_active)
            VALUES(?, 1)
            ''', (login,))

            await self.connection.commit()
        
        except Exception as ex:
            print("Ошибка добавления пользователя: ", ex)
            return False 
    
    async def get_all_activate_users_yx(self):
        try:
            async with self.connection.execute('''
                SELECT login from users_yx WHERE is_active = 1
            ''') as cursor:
                results = await cursor.fetchall()
                return [row[0] for row in results] if results else []
        except Exception as ex:
            print("Ошибка получения chat_id", ex)

    async def subscribe_user_yx(self, login):
            try:
                await self.connection.execute(
                    "UPDATE users_yx SET is_active = 1 WHERE login = ?", (login,)
                )
                await self.connection.commit()
                return True
            except Exception as ex:
                print("Ошибка подпсики: ", ex)
                return False
    
    async def unsubscribe_user_yx(self, login):

        try:
            await self.connection.execute(
                "UPDATE users_yx SET is_active = 0 WHERE login = ?",
                (login,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            return False
    
    async def check_active_yx(self, login):
        try:
            async with self.connection.execute('''
            SELECT is_active FROM users_yx WHERE login = ?
            ''', (login, )) as cursor:

                result = await cursor.fetchone()
                if result:
                    return True if result[0] == 1 else False
                else: return False
        except Exception as ex:
            print("Ошибка проверки: ", ex)
            return False
    
    async def check_exist_yx_login(self, login):
        try:
            async with self.connection.execute('''
            SELECT is_active FROM users_yx WHERE login = ?
            ''', (login, )) as cursor:

                result = await cursor.fetchone()
                if result:
                    return True 
                else: return False
        except Exception as ex:
            print("Ошибка проверки: ", ex)
            return False



    async def add_user_tg(self, user_id, chat_id, user_name):
        try:
            await self.connection.execute('''
            INSERT OR REPLACE INTO users_tg
            (user_id, chat_id, user_name, is_active)
            VALUES (?, ?, ?, 1)
            ''', (user_id, chat_id, user_name))

            await self.connection.commit()
        except Exception as ex:
            print("Ошибка добавления пользователя: ", ex)
            return False

    async def get_all_activate_users_tg(self):

        try:
            async with self.connection.execute('''
                SELECT chat_id from users_tg WHERE is_active = 1
            ''') as cursor:
                
                results = await cursor.fetchall()
                return [row[0] for row in results] if results else []
        except Exception as ex:
            print("Ошибка получения chat_id", ex)
    
    async def subscribe_user_tg(self, user_id):
        try:
            await self.connection.execute(
                "UPDATE users_tg SET is_active = 1 WHERE user_id = ?", (user_id,)
            )
            await self.connection.commit()
            return True
        except Exception as ex:
            print("Ошибка подпсики: ", ex)
            return False
    
    async def unsubscribe_user_tg(self, user_id):

        try:
            await self.connection.execute(
                "UPDATE users_tg SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            return False
    
    async def check_active_tg(self, user_id):
        try:
            async with self.connection.execute('''
            SELECT is_active FROM users_tg WHERE user_id = ?
            ''', (user_id, )) as cursor:

                result = await cursor.fetchone()
                if result:
                    return True if result[0] == 1 else False
                else: return False
        except Exception as ex:
            print("Ошибка проверки: ", ex)
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
        await storage.add_user_yx("Ilya")
        # result = await storage.unsubscribe_user_tg(15)
        chat_id = await storage.check_exist_yx_login("Ilya")
        print(chat_id)

if __name__ == "__main__":
    asyncio.run(main())


    





    




