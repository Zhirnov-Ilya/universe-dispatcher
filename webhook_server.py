from aiohttp import web

class WebhookServer:

    def __init__(self, bot, host, port):
        self.bot = bot
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_post('/webhook', self.bot.handle_webhook)
    
    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()
        print(f"Сервер доступен по адресу {self.host}:{self.port}")
    
    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
