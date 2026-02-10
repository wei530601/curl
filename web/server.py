from aiohttp import web, ClientSession
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
import os
import base64
import json

class WebServer:
    """網頁後台控制器"""
    
    def __init__(self, bot, host='0.0.0.0', port=8080):
        self.bot = bot
        self.host = host
        self.port = port
        
        # Discord OAuth2 設定
        self.client_id = os.getenv('DISCORD_CLIENT_ID')
        self.client_secret = os.getenv('DISCORD_CLIENT_SECRET')
        self.redirect_uri = os.getenv('DISCORD_REDIRECT_URI', f'http://localhost:{port}/callback')
        
        # Session 密鑰
        session_secret = os.getenv('SESSION_SECRET', fernet.Fernet.generate_key().decode())
        secret_key = base64.urlsafe_b64decode(session_secret.encode() if len(session_secret) == 44 else base64.urlsafe_b64encode(session_secret.encode()[:32]))
        
        # 創建應用
        self.app = web.Application(middlewares=[session_middleware(EncryptedCookieStorage(secret_key))])
        self.setup_routes()
    
    def setup_routes(self):
        """設定路由"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/login', self.login)
        self.app.router.add_get('/callback', self.callback)
        self.app.router.add_get('/dashboard', self.dashboard)
        self.app.router.add_get('/logout', self.logout)
        self.app.router.add_get('/api/stats', self.api_stats)
    
    async def index(self, request):
        """主頁"""
        session = await get_session(request)
        user = session.get('user')
        
        if user:
            # 已登錄，重定向到儀表板
            raise web.HTTPFound('/dashboard')
        
        with open('web/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        return web.Response(text=html, content_type='text/html')
    
    async def login(self, request):
        """Discord 登錄"""
        oauth_url = (
            f"https://discord.com/api/oauth2/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=identify%20guilds"
        )
        raise web.HTTPFound(oauth_url)
    
    async def callback(self, request):
        """OAuth2 回調"""
        code = request.query.get('code')
        
        if not code:
            return web.Response(text="錯誤：未提供授權碼", status=400)
        
        # 交換 access token
        async with ClientSession() as session:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri
            }
            
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            async with session.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as resp:
                if resp.status != 200:
                    return web.Response(text="登錄失敗", status=400)
                
                token_data = await resp.json()
                access_token = token_data['access_token']
            
            # 獲取用戶資訊
            headers = {'Authorization': f"Bearer {access_token}"}
            async with session.get('https://discord.com/api/users/@me', headers=headers) as resp:
                user_data = await resp.json()
            
            # 儲存 session
            session = await get_session(request)
            session['user'] = {
                'id': user_data['id'],
                'username': user_data['username'],
                'avatar': user_data.get('avatar'),
                'discriminator': user_data.get('discriminator', '0')
            }
            session['access_token'] = access_token
        
        raise web.HTTPFound('/dashboard')
    
    async def dashboard(self, request):
        """儀表板"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            raise web.HTTPFound('/login')
        
        with open('web/dashboard.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # 替換用戶資訊
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
        
        html = html.replace('{USERNAME}', user['username'])
        html = html.replace('{AVATAR_URL}', avatar_url)
        
        return web.Response(text=html, content_type='text/html')
    
    async def logout(self, request):
        """登出"""
        session = await get_session(request)
        session.clear()
        raise web.HTTPFound('/')
    
    async def api_stats(self, request):
        """API：統計數據"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # 收集統計數據
        stats = {
            'guilds': len(self.bot.guilds),
            'users': sum(guild.member_count for guild in self.bot.guilds),
            'channels': sum(len(guild.channels) for guild in self.bot.guilds),
            'uptime': str(self.bot.uptime) if hasattr(self.bot, 'uptime') else 'N/A'
        }
        
        return web.json_response(stats)
    
    async def start(self):
        """啟動 Web 伺服器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f'🌐 網頁控制台已啟動: http://{self.host}:{self.port}')
        print(f'   本地訪問: http://localhost:{self.port}')
