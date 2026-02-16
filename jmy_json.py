import json

login = "universe-dispetcher@universe-data.ru"

callback_data = {
    "data": login 
    }

btn = json.dumps([{
        "text": "Подписаться на новости",
        "callback_data": callback_data
        },
        {
        "text": "Отписаться от новостей",
        "callback_data": callback_data
        },
        {
        "text": "Доступные команды",
        "callback_data": callback_data
        },], indent=4, ensure_ascii=False)
print(btn)