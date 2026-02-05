import os
from pathlib import Path
from dotenv import load_dotenv

class Config:

    def __init__(self):

        self.config_dir = Path("config")
        
        if not self.config_dir.exists():
            self.config_dir = Path(".")
        
        env_path = self.config_dir / ".env"
        load_dotenv(env_path)

    def load_config(self, section):
        
        try:
            if section == 'telegram':
                return {
                    'bot_token' : os.getenv('BOT_TOKEN'),
                    'chat_id': os.getenv('CHAT_ID')
                }
            elif section == 'hr_portal':
                return {
                    'base_url': os.getenv('HR_BASE_URL'),
                    'api_url': os.getenv('HR_API_URL'),
                    'username': os.getenv('HR_USERNAME'),
                    'password': os.getenv('HR_PASSWORD'),
                    'api_token': os.getenv('HR_API_TOKEN')
                }
            return {}

        except Exception as ex:
            print(f"Ошиюка конфигурации: {ex}")

if __name__ == "__main__":

    config = Config()
    data = config.load_config('telegram')
    print("Содержимое .env: ", data['bot_token'])