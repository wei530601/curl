from aiohttp import web
import aiohttp
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import os
import json
from cryptography import fernet
from dotenv import load_dotenv
import base64

load_dotenv()

class WebServer:
    """網頁後台控制器"""
    
    def __init__(self, bot, host='0.0.0.0', port=8080):
        self.bot = bot
        self.host = host
        self.port = port
        
        # Discord OAuth2 設定
        self.client_id = os.getenv('DISCORD_CLIENT_ID')
        self.client_secret = os.getenv('DISCORD_CLIENT_SECRET')
        self.redirect_uri = os.getenv('DISCORD_REDIRECT_URI')
        
        # 創建應用
        self.app = web.Application()
        
        # 設定加密 session
        secret_key = fernet.Fernet.generate_key()
        setup(self.app, EncryptedCookieStorage(secret_key))
        
        self.setup_routes()
    
    def setup_routes(self):
        """設定路由"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/login', self.login)
        self.app.router.add_get('/callback', self.callback)
        self.app.router.add_get('/logout', self.logout)
        self.app.router.add_get('/dashboard', self.dashboard)
        self.app.router.add_get('/api/bot-info', self.api_bot_info)
        self.app.router.add_get('/api/servers', self.api_servers)
        # 如果 static 目錄存在才添加靜態文件路由
        if os.path.exists('web/static'):
            self.app.router.add_static('/static', 'web/static')
    
    async def index(self, request):
        """主頁"""
        session = await get_session(request)
        user = session.get('user')
        
        if user:
            # 已登錄，跳轉到控制台
            raise web.HTTPFound('/dashboard')
        
        with open('web/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return web.Response(text=html_content, content_type='text/html')
    
    async def login(self, request):
        """Discord OAuth2 登錄"""
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
            return web.Response(text="登錄失敗：缺少授權碼", status=400)
        
        # 交換 access token
        async with aiohttp.ClientSession() as session_http:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri
            }
            
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            async with session_http.post('https://discord.com/api/oauth2/token', data=data, headers=headers) as resp:
                token_data = await resp.json()
            
            if 'access_token' not in token_data:
                return web.Response(text="登錄失敗：無法獲取 access token", status=400)
            
            access_token = token_data['access_token']
            
            # 獲取用戶信息
            headers = {'Authorization': f"Bearer {access_token}"}
            async with session_http.get('https://discord.com/api/users/@me', headers=headers) as resp:
                user_data = await resp.json()
            
            # 保存 session
            session = await get_session(request)
            session['user'] = {
                'id': user_data['id'],
                'username': user_data['username'],
                'discriminator': user_data.get('discriminator', '0'),
                'avatar': user_data.get('avatar'),
                'access_token': access_token
            }
            
            raise web.HTTPFound('/dashboard')
    
    async def logout(self, request):
        """登出"""
        session = await get_session(request)
        session.clear()
        raise web.HTTPFound('/')
    
    async def dashboard(self, request):
        """控制台主頁"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            raise web.HTTPFound('/')
        
        with open('web/dashboard.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return web.Response(text=html_content, content_type='text/html')
    
    async def api_bot_info(self, request):
        """API: 獲取機器人信息"""
        session = await get_session(request)
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        data = {
            'username': self.bot.user.name,
            'avatar': str(self.bot.user.display_avatar.url),
            'server_count': len(self.bot.guilds),
            'user_count': sum(g.member_count for g in self.bot.guilds),
            'status': 'online'
        }
        
        return web.json_response(data)
    
    async def api_servers(self, request):
        """API: 獲取伺服器列表"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        servers = []
        for guild in self.bot.guilds:
            # 檢查用戶是否在此伺服器中
            member = guild.get_member(int(user['id']))
            if member:
                servers.append({
                    'id': str(guild.id),
                    'name': guild.name,
                    'icon': str(guild.icon.url) if guild.icon else None,
                    'member_count': guild.member_count,
                    'is_admin': member.guild_permissions.administrator
                })
        
        return web.json_response({'servers': servers})
    
    async def start(self):
        """啟動 Web 伺服器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f'🌐 網頁控制台已啟動: http://{self.host}:{self.port}')
        print(f'   本地訪問: http://localhost:{self.port}')
