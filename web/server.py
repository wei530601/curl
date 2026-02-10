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
        self.app.router.add_get('/select-server', self.select_server)
        self.app.router.add_get('/dashboard/{guild_id}', self.dashboard)
        self.app.router.add_get('/logout', self.logout)
        self.app.router.add_get('/api/guilds', self.api_guilds)
        self.app.router.add_get('/api/stats/{guild_id}', self.api_stats)
        self.app.router.add_get('/api/data/{guild_id}/{data_type}', self.api_data)
        self.app.router.add_post('/api/welcome/{guild_id}/toggle', self.api_toggle_welcome)
    
    async def index(self, request):
        """主頁"""
        session = await get_session(request)
        user = session.get('user')
        
        if user:
            # 已登錄，重定向到伺服器選擇頁面
            raise web.HTTPFound('/select-server')
        
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
        
        raise web.HTTPFound('/select-server')
    
    async def select_server(self, request):
        """伺服器選擇頁面"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            raise web.HTTPFound('/login')
        
        with open('web/select_server.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # 替換用戶資訊
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
        
        html = html.replace('{USERNAME}', user['username'])
        html = html.replace('{AVATAR_URL}', avatar_url)
        
        return web.Response(text=html, content_type='text/html')
    
    async def api_guilds(self, request):
        """API：獲取用戶的伺服器列表"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        access_token = session.get('access_token')
        
        # 獲取用戶的 Discord 伺服器
        async with ClientSession() as client_session:
            headers = {'Authorization': f"Bearer {access_token}"}
            async with client_session.get('https://discord.com/api/users/@me/guilds', headers=headers) as resp:
                if resp.status != 200:
                    return web.json_response({'error': 'Failed to fetch guilds'}, status=500)
                user_guilds = await resp.json()
        
        # 獲取機器人所在的伺服器
        bot_guild_ids = {str(guild.id) for guild in self.bot.guilds}
        
        # 過濾有管理權限且機器人也在的伺服器
        accessible_guilds = []
        for guild in user_guilds:
            permissions = int(guild.get('permissions', 0))
            guild_id = guild['id']
            
            # 檢查管理員權限或管理伺服器權限
            if (permissions & 0x8 or permissions & 0x20) and guild_id in bot_guild_ids:
                # 獲取伺服器圖標
                icon_url = None
                if guild.get('icon'):
                    icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{guild['icon']}.png"
                
                # 獲取成員數量
                bot_guild = self.bot.get_guild(int(guild_id))
                member_count = bot_guild.member_count if bot_guild else 0
                
                accessible_guilds.append({
                    'id': guild_id,
                    'name': guild['name'],
                    'icon': icon_url,
                    'member_count': member_count
                })
        
        return web.json_response({'guilds': accessible_guilds})
    
    async def api_stats(self, request):
        """API：特定伺服器統計數據"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        # 獲取伺服器
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return web.json_response({'error': 'Guild not found'}, status=404)
        
        # 收集統計數據
        stats = {
            'guild_name': guild.name,
            'member_count': guild.member_count,
            'channel_count': len(guild.channels),
            'role_count': len(guild.roles),
            'text_channels': len(guild.text_channels),
            'voice_channels': len(guild.voice_channels),
            'categories': len(guild.categories),
        }
        
        return web.json_response(stats)
    
    async def api_data(self, request):
        """API：讀取伺服器數據文件"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        data_type = request.match_info.get('data_type')
        
        # 驗證數據類型
        allowed_types = ['levels', 'welcome', 'reaction_roles', 'daily', 'birthdays', 'birthday_settings', 'game_stats', 'statistics']
        if data_type not in allowed_types:
            return web.json_response({'error': 'Invalid data type'}, status=400)
        
        # 讀取數據文件
        data_file = os.path.join('data', guild_id, f'{data_type}.json')
        
        if not os.path.exists(data_file):
            return web.json_response({'data': {}, 'exists': False})
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return web.json_response({'data': data, 'exists': True})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_toggle_welcome(self, request):
        """API：切換歡迎系統開關"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            # 獲取請求數據
            data = await request.json()
            toggle_type = data.get('type')  # 'welcome' 或 'leave'
            enabled = data.get('enabled')  # True 或 False
            
            if toggle_type not in ['welcome', 'leave']:
                return web.json_response({'error': 'Invalid type'}, status=400)
            
            # 讀取現有設定
            data_file = os.path.join('data', guild_id, 'welcome.json')
            
            if not os.path.exists(data_file):
                # 創建預設設定
                os.makedirs(os.path.dirname(data_file), exist_ok=True)
                settings = {
                    'welcome_enabled': False,
                    'leave_enabled': False,
                    'welcome_channel': None,
                    'leave_channel': None,
                    'welcome_message': '歡迎 {user} 加入 {server}！',
                    'leave_message': '{username} 離開了伺服器'
                }
            else:
                with open(data_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # 更新設定
            if toggle_type == 'welcome':
                settings['welcome_enabled'] = enabled
            else:
                settings['leave_enabled'] = enabled
            
            # 儲存設定
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return web.json_response({
                'success': True,
                'settings': settings
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def dashboard(self, request):
        """儀表板"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            raise web.HTTPFound('/login')
        
        guild_id = request.match_info.get('guild_id')
        
        # 驗證用戶是否有權限訪問此伺服器
        access_token = session.get('access_token')
        async with ClientSession() as client_session:
            headers = {'Authorization': f"Bearer {access_token}"}
            async with client_session.get('https://discord.com/api/users/@me/guilds', headers=headers) as resp:
                if resp.status != 200:
                    raise web.HTTPFound('/select-server')
                user_guilds = await resp.json()
        
        # 檢查用戶是否在此伺服器且有管理權限
        has_access = False
        guild_name = "Unknown Server"
        for guild in user_guilds:
            if guild['id'] == guild_id:
                permissions = int(guild.get('permissions', 0))
                if permissions & 0x8 or permissions & 0x20:  # 管理員或管理伺服器
                    has_access = True
                    guild_name = guild['name']
                    break
        
        if not has_access:
            return web.Response(text="您沒有權限訪問此伺服器", status=403)
        
        with open('web/dashboard.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # 替換用戶資訊
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
        
        html = html.replace('{USERNAME}', user['username'])
        html = html.replace('{AVATAR_URL}', avatar_url)
        html = html.replace('{GUILD_ID}', guild_id)
        html = html.replace('{GUILD_NAME}', guild_name)
        
        return web.Response(text=html, content_type='text/html')
    
    async def logout(self, request):
        """登出"""
        session = await get_session(request)
        session.clear()
        raise web.HTTPFound('/')
    
    async def start(self):
        """啟動 Web 伺服器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f'🌐 網頁控制台已啟動: http://{self.host}:{self.port}')
        print(f'   本地訪問: http://localhost:{self.port}')
