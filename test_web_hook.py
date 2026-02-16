
import requests
import json
from config_loader import Config

config = Config()
token = config.load_config('telegram')['bot_token']

# Сброс вебхука (важно!)
requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")

# Получаем обновления
url = f"https://api.telegram.org/bot{token}/getUpdates?timeout=30"
response = requests.get(url)
data = response.json()

print(json.dumps(data, indent=2, ensure_ascii=False))