import os
from pathlib import Path
from dotenv import load_dotenv

class Config:

    def __init__(self):

        self.config_dir = Path("config")
        
        env_path = self.config_dir / ".env"
        load_dotenv(env_path)

    def load_config(self, section):
        
        try:
            if section == 'telegram':
                return {
                    'bot_token' : os.getenv('TG_BOT_TOKEN'),
                    'chat_id': os.getenv('TG_CHAT_ID')
                }
            elif section == 'hr_portal':
                return {
                    'base_url': os.getenv('HR_BASE_URL'),
                    'api_url': os.getenv('HR_API_URL'),
                    'username': os.getenv('HR_USERNAME'),
                    'password': os.getenv('HR_PASSWORD'),
                    'api_token': os.getenv('HR_API_TOKEN')
                }
            elif section == 'yandex':
                return { 
                    'base_url': os.getenv('YX_BASE_URL'),
                    'bot_token': os.getenv('YX_BOT_TOKEN'),
                    'user_id': os.getenv('YX_LOGIN')
                }

        except Exception as ex:
            print(f"Ошибка конфигурации: {ex}")

if __name__ == "__main__":

    config = Config()
    data = config.load_config('telegram')
    print("Содержимое .env: ", data['bot_token'])