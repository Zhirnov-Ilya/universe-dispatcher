import aiohttp
import asyncio
import json
from bs4 import BeautifulSoup
from datetime import datetime
from base_adapter import BaseNewsAdapter
from storage import NewsStorage
from config_loader import Config

class HRPortalAdapter(BaseNewsAdapter):

    def __init__(self, base_url, api_url, username, password, api_token=None):

        super().__init__(
            name = "HR Портал МояКоманада",
            source_code = "hr_portal"
        )

        self.api_url = api_url
        self.base_url = base_url
        self.username = username
        self.password = password
        self.api_token = api_token
        self._login_needed = False

        self.session = None

        if api_token:
            self.headers = {'Authorization': f'Bearer {api_token}'}
        else:
            self.headers = {}
            self._login_needed = True

    async def connect(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

    async def _login(self):

        try:
            login_url = f"{self.base_url}/api/login"
            login_data = {
                'email': self.username,
                'password': self.password
            }

            if self.session is None:
                await self.connect()

            async with self.session.post(login_url, data = login_data) as response:

                if response.status == 200:
                    print("Успешная авторизация")
                    self._login_needed = False
                    return True
                else:
                    print(f"Ошибка авторизации: {response.status}")
                    return False

        except Exception as e:
            print(f" Ошибка при логине: {e}")
            return False

        
    async def _make_api_request(self):

        try:
            print(f"Запрос к {self.api_url}")
            
            if self._login_needed and not self.api_token:
                if not await self._login():
                    return None

            if self.session is None:
                await self.connect()

            async with self.session.get(
                self.api_url,
                headers=self.headers if self.api_token else {},
                timeout=10
            ) as response:

                if response.status == 200:
                    print("Успешно. Код ответа 200.")
                    data = await response.json()
                    return data
                else:
                    print(f"Ошибка. Код овтета {response.status}")
                    return None
        
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            return None
    
    async def fetch_news(self):
        print("Попытка получения новостей.")
        data = await self._make_api_request()

        if data:
            with open('hr_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                print("Данные сохранены в hr_data.json")

                items = data['data']['items']
                parsed_items = []
                for item in items:
                    parsed = self._parse_news_item(item)
                    parsed = self._simple_truncate(parsed)
                    parsed_items.append(parsed)
                return parsed_items

        else:
            print("Ошибка получния данных.")
            return None
    
    async def fetch_new_news(self, last_id):
        print("Получение новой новости")
        items = await self.fetch_news()
        
        if not items:
            return []

        new_items = []

        for item in items:
            if self.rebuild_news_id(item['id']) > self.rebuild_news_id(last_id):
                new_items.append(item)
        
        print("Найдно новых новостей: ", len(new_items))
        return sorted(new_items, key = lambda item: item['id'])

    def build_news_id(self, row_id):
        return f"hr_{row_id}"
    
    def rebuild_news_id(self, row_id):
        return int(row_id[3:])
    
    def _create_news_link(self, news_id):
        return f"{self.base_url}/news/detail/{news_id[3:]}"

    def _make_absolute_url(self, url):

        if not url:
            return None
        
        return f"{self.base_url}{url}"
    def _parse_news_item(self, item):
       
       content_html = item.get('content', '')
       clean_content = self._extract_text_from_html(content_html)
       news_id = self.build_news_id(item['id'])
       image_url = self._make_absolute_url(item.get('imagePreview'))


       return {
        'id': news_id,
        'title': item['title'],
        'content': clean_content,
        'rubric': item.get('category', 'Без рубрики'),
        'link': self._create_news_link(news_id),
        'published_at': item.get('createdAt', 'unknown')
       }


    def _extract_text_from_html(self, html_content):

        if not html_content: return ""

        try:

            soup = BeautifulSoup(html_content, 'html.parser')

            for tag in soup.find_all(['script', 'style', 'img', 'frame', 'video']):
                tag.decompose()

            for span in soup.find_all('span', class_='an1'):
                emoji = span.get('char', '') or span.get_text(strip=True)
                if emoji:
                    span.replace_with(emoji)
                else:
                    span.decompose()
            
            for mention in soup.find_all('mention'):
                user_name = mention.get('label', '') or mention.get_text(strip=True)
                if user_name:
                    mention.replace_with(f"@{user_name}")
                else:
                    mention.decompose()
            
            for br in soup.find_all('br'):
                br.replace_with('\n')

            for tag in soup.find_all(['span', 'em', 'strong', 'b', 'i', 'u']):
                tag.replace_with(tag.get_text()) 
            
            for p in soup.find_all('p'):
                if not p.get_text(strip=True):
                    p.decompose()

            text = soup.get_text(separator=' ', strip=True)

            text = ' '.join(text.split())

        except Exception as e:
            text = f"Ошибка парсинга HTML: {e}"

        return text

    def _simple_truncate(self, item, max_length = 200):
        text = item.get('content', '')
        if len(text) <= max_length:
            return item

        trunced = text[:max_length]
        last_space = trunced.rfind(' ')

        if last_space > 0:
            item['content'] = trunced[:last_space] + "..."
        else:
            item['content'] = trunced + "..."            
        return item

    async def get_last_news_id(self):

        try:
            items= await self.fetch_news()

            if not items:
                print("Новости отсутствуют")
                return None
            
            last_news =  items[0]
            last_id = last_news['id']

            print("Получен последний ID на портале: ", last_id)
            return last_id
        
        except Exception as e:
            print("Ошибка получения id: ", e)
            return None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()
            print('Сессия закрыта')

    async def __aenter__(self):
        await self.connect()
        return self

    @staticmethod
    def print_format_item(item):
        for row in item:
            print(f"{row}: {item[row]}")
    
    

    
if __name__ == "__main__":

    async def main():
        
        config = Config()

        async with NewsStorage() as storage:
        
            base_url = config.load_config('hr_portal')['base_url']
            api_url = config.load_config('hr_portal')['api_url']
            username = config.load_config('hr_portal')['username']
            password = config.load_config('hr_portal')['password']
            token = config.load_config('hr_portal')['api_token']

            async with HRPortalAdapter(base_url, api_url, username, password, token) as adapter:
            
            
                last_id_on_portal = await adapter.get_last_news_id()
                print(last_id_on_portal)

                last_id_in_bd = await storage.get_last_id('hr_portal')
                print(last_id_in_bd) 

                items = await adapter.fetch_news()
                
                for item in items:
                    HRPortalAdapter.print_format_item(item)
    
    asyncio.run(main())



