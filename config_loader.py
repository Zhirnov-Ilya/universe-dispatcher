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
                    'user_id': os.getenv('YX_LOGIN'),
                    'set_webhook': os.getenv('YX_API_SET_WEBHOOK'),
                    'send_message_url': os.getenv('YX_API_SEND_MESSAGE_URL'),
                    'send_image_url': os.getenv('YX_API_SEND_IMAGE_URL'),
                    'disk_token': os.getenv('YX_DISK_TOKEN')
                }
            elif section == "server":
                return{
                    'base_url': os.getenv('SR_URL')
                }

        except Exception as ex:
            print(f"Ошибка конфигурации: {ex}")

if __name__ == "__main__":

    config = Config()
    data = config.load_config('server')
    print("Содержимое .env: ", data['base_url'])