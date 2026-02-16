from aiohttp import web
import asyncio

async def handle(request):
    if request.method == 'GET':
        print("🔍 Получен GET-запрос (проверка от Яндекса)")
        return web.Response(text='OK', status=200)
        
    data = await request.json()
    print("✅ Получено:", data)
    return web.Response(text='OK')

app = web.Application()
app.router.add_post('/webhook', handle)

if __name__ == '__main__':
    web.run_app(app, port=8080)