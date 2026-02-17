from aiohttp import web, ClientSession
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
import discord
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
        
        # 開發者 ID 列表
        dev_ids = os.getenv('DEV_ID', '')
        self.dev_ids = [int(id.strip()) for id in dev_ids.split(',') if id.strip()]
        
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
        self.app.router.add_get('/my-tickets', self.my_tickets)
        self.app.router.add_get('/logout', self.logout)
        self.app.router.add_get('/api/guilds', self.api_guilds)
        self.app.router.add_get('/api/my-tickets', self.api_my_tickets)
        self.app.router.add_get('/api/stats/{guild_id}', self.api_stats)
        self.app.router.add_get('/api/data/{guild_id}/{data_type}', self.api_data)
        self.app.router.add_post('/api/welcome/{guild_id}/toggle', self.api_toggle_welcome)
        self.app.router.add_post('/api/welcome/{guild_id}/update', self.api_update_welcome)
        
        # 自定義命令 API
        self.app.router.add_get('/api/custom-commands/{guild_id}', self.api_get_custom_commands)
        self.app.router.add_post('/api/custom-commands/{guild_id}', self.api_add_custom_command)
        self.app.router.add_put('/api/custom-commands/{guild_id}/{command_name}', self.api_edit_custom_command)
        self.app.router.add_delete('/api/custom-commands/{guild_id}/{command_name}', self.api_delete_custom_command)
        
        # 臨時語音頻道 API
        self.app.router.add_get('/api/temp-voice/{guild_id}', self.api_get_temp_voice_config)
        self.app.router.add_post('/api/temp-voice/{guild_id}', self.api_update_temp_voice_config)
        self.app.router.add_get('/api/channels/{guild_id}', self.api_get_channels)
        
        # 警告系統 API
        self.app.router.add_get('/api/warnings/{guild_id}', self.api_get_warnings)
        self.app.router.add_delete('/api/warnings/{guild_id}/{user_id}', self.api_clear_warnings)
        self.app.router.add_delete('/api/warnings/{guild_id}/{user_id}/latest', self.api_remove_latest_warning)
        self.app.router.add_delete('/api/warnings/{guild_id}/{user_id}/{index}', self.api_remove_warning_by_index)
        
        # 成就系統 API
        self.app.router.add_get('/api/achievements/{guild_id}', self.api_get_achievements)
        self.app.router.add_post('/api/achievements/{guild_id}/{user_id}/{achievement_id}', self.api_grant_achievement)
        self.app.router.add_delete('/api/achievements/{guild_id}/{user_id}/{achievement_id}', self.api_revoke_achievement)
        
        # 客服單系統 API
        self.app.router.add_get('/api/tickets/{guild_id}', self.api_get_tickets)
        self.app.router.add_post('/api/tickets/{guild_id}/settings', self.api_update_ticket_settings)
        self.app.router.add_post('/api/tickets/{guild_id}/{ticket_id}/close', self.api_close_ticket)
        self.app.router.add_get('/api/tickets/{guild_id}/{ticket_id}/transcript', self.api_get_ticket_transcript)
        self.app.router.add_post('/api/tickets/{guild_id}/create-panel', self.api_create_ticket_panel)
        
        # 自動回覆系統 API
        self.app.router.add_get('/api/auto-reply/{guild_id}', self.api_get_auto_replies)
        self.app.router.add_post('/api/auto-reply/{guild_id}', self.api_add_auto_reply)
        self.app.router.add_put('/api/auto-reply/{guild_id}/{rule_id}', self.api_update_auto_reply)
        self.app.router.add_delete('/api/auto-reply/{guild_id}/{rule_id}', self.api_delete_auto_reply)
        self.app.router.add_post('/api/auto-reply/{guild_id}/toggle', self.api_toggle_auto_reply_system)
        self.app.router.add_post('/api/auto-reply/{guild_id}/{rule_id}/toggle', self.api_toggle_auto_reply_rule)
        
        # 安全系統 API
        self.app.router.add_get('/api/security/{guild_id}', self.api_get_security)
        self.app.router.add_post('/api/security/{guild_id}', self.api_update_security)
        self.app.router.add_post('/api/security/{guild_id}/banned-words', self.api_add_banned_word)
        self.app.router.add_delete('/api/security/{guild_id}/banned-words', self.api_delete_banned_word)
        
        # 開發者面板路由
        self.app.router.add_get('/dev-panel', self.dev_panel)
        self.app.router.add_get('/api/dev/all-guilds', self.api_dev_all_guilds)
        self.app.router.add_get('/api/dev/guild-config/{guild_id}', self.api_dev_guild_config)
    
    def is_developer(self, user_id):
        """檢查用戶是否為開發者"""
        return int(user_id) in self.dev_ids
    
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
        
        # 如果是開發者，顯示開發者面板按鈕
        if self.is_developer(user['id']):
            html = html.replace('{DEV_BUTTON}', '<a href="/dev-panel" class="dev-btn">🔧 開發者面板</a>')
        else:
            html = html.replace('{DEV_BUTTON}', '')
        
        return web.Response(text=html, content_type='text/html')
    
    async def my_tickets(self, request):
        """我的客服單頁面"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            raise web.HTTPFound('/login')
        
        with open('web/my-tickets.html', 'r', encoding='utf-8') as f:
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
    
    async def api_update_welcome(self, request):
        """API：更新歡迎系統設定"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            # 獲取請求數據
            data = await request.json()
            
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
            
            # 更新設定（只更新提供的字段）
            if 'welcome_channel' in data:
                settings['welcome_channel'] = data['welcome_channel']
            if 'leave_channel' in data:
                settings['leave_channel'] = data['leave_channel']
            if 'welcome_message' in data:
                settings['welcome_message'] = data['welcome_message']
            if 'leave_message' in data:
                settings['leave_message'] = data['leave_message']
            
            # 儲存設定
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return web.json_response({
                'success': True,
                'settings': settings
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_get_custom_commands(self, request):
        """API：獲取自定義命令列表"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        data_file = os.path.join('data', guild_id, 'custom_commands.json')
        
        if not os.path.exists(data_file):
            return web.json_response({'commands': {}})
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                commands = json.load(f)
            return web.json_response({'commands': commands})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_add_custom_command(self, request):
        """API：添加自定義命令"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            data = await request.json()
            command_name = data.get('name')
            response = data.get('response')
            
            if not command_name or not response:
                return web.json_response({'error': 'Missing name or response'}, status=400)
            
            data_file = os.path.join('data', guild_id, 'custom_commands.json')
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            
            # 讀取現有命令
            commands = {}
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    commands = json.load(f)
            
            # 檢查命令是否已存在
            if command_name in commands:
                return web.json_response({'error': 'Command already exists'}, status=400)
            
            # 添加命令
            from datetime import datetime
            commands[command_name] = {
                'response': response,
                'created_by': session.get('user')['id'],
                'created_at': datetime.utcnow().isoformat(),
                'uses': 0
            }
            
            # 儲存
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(commands, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'commands': commands})
        
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_edit_custom_command(self, request):
        """API：編輯自定義命令"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        command_name = request.match_info.get('command_name')
        
        try:
            data = await request.json()
            new_response = data.get('response')
            
            if not new_response:
                return web.json_response({'error': 'Missing response'}, status=400)
            
            data_file = os.path.join('data', guild_id, 'custom_commands.json')
            
            if not os.path.exists(data_file):
                return web.json_response({'error': 'Commands file not found'}, status=404)
            
            with open(data_file, 'r', encoding='utf-8') as f:
                commands = json.load(f)
            
            if command_name not in commands:
                return web.json_response({'error': 'Command not found'}, status=404)
            
            # 更新命令
            from datetime import datetime
            commands[command_name]['response'] = new_response
            commands[command_name]['edited_by'] = session.get('user')['id']
            commands[command_name]['edited_at'] = datetime.utcnow().isoformat()
            
            # 儲存
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(commands, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'commands': commands})
        
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_delete_custom_command(self, request):
        """API：刪除自定義命令"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        command_name = request.match_info.get('command_name')
        
        try:
            data_file = os.path.join('data', guild_id, 'custom_commands.json')
            
            if not os.path.exists(data_file):
                return web.json_response({'error': 'Commands file not found'}, status=404)
            
            with open(data_file, 'r', encoding='utf-8') as f:
                commands = json.load(f)
            
            if command_name not in commands:
                return web.json_response({'error': 'Command not found'}, status=404)
            
            # 刪除命令
            del commands[command_name]
            
            # 儲存
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(commands, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'commands': commands})
        
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_get_temp_voice_config(self, request):
        """API：獲取臨時語音配置"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        data_file = os.path.join('data', guild_id, 'temp_voice.json')
        
        if not os.path.exists(data_file):
            return web.json_response({
                'config': {
                    'enabled': False,
                    'trigger_channel_id': None,
                    'category_id': None,
                    'channel_name_format': '{username} 的頻道',
                    'user_limit': 0,
                    'default_bitrate': 64000
                }
            })
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return web.json_response({'config': config})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_update_temp_voice_config(self, request):
        """API：更新臨時語音配置"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            data = await request.json()
            
            data_file = os.path.join('data', guild_id, 'temp_voice.json')
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
            
            # 讀取現有配置
            config = {
                'enabled': False,
                'trigger_channel_id': None,
                'category_id': None,
                'channel_name_format': '{username} 的頻道',
                'user_limit': 0,
                'default_bitrate': 64000
            }
            
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新配置
            if 'enabled' in data:
                config['enabled'] = data['enabled']
            if 'trigger_channel_id' in data:
                # 將字符串 ID 轉換為整數（如果不為 None）
                try:
                    config['trigger_channel_id'] = int(data['trigger_channel_id']) if data['trigger_channel_id'] else None
                except (ValueError, TypeError):
                    config['trigger_channel_id'] = None
            if 'category_id' in data:
                # 將字符串 ID 轉換為整數（如果不為 None）
                try:
                    config['category_id'] = int(data['category_id']) if data['category_id'] else None
                except (ValueError, TypeError):
                    config['category_id'] = None
            if 'channel_name_format' in data:
                config['channel_name_format'] = data['channel_name_format']
            if 'user_limit' in data:
                config['user_limit'] = data['user_limit']
            if 'default_bitrate' in data:
                config['default_bitrate'] = data['default_bitrate']
            
            # 儲存
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'config': config})
        
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_get_channels(self, request):
        """API：獲取伺服器頻道列表"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            guild = self.bot.get_guild(int(guild_id))
            
            if not guild:
                return web.json_response({'error': 'Guild not found'}, status=404)
            
            # 獲取各類頻道
            text_channels = []
            voice_channels = []
            categories = []
            
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text_channels.append({
                        'id': str(channel.id),
                        'name': channel.name,
                        'position': channel.position
                    })
                elif isinstance(channel, discord.VoiceChannel):
                    voice_channels.append({
                        'id': str(channel.id),
                        'name': channel.name,
                        'position': channel.position
                    })
                elif isinstance(channel, discord.CategoryChannel):
                    categories.append({
                        'id': str(channel.id),
                        'name': channel.name,
                        'position': channel.position
                    })
            
            return web.json_response({
                'text_channels': sorted(text_channels, key=lambda x: x['position']),
                'voice_channels': sorted(voice_channels, key=lambda x: x['position']),
                'categories': sorted(categories, key=lambda x: x['position'])
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
    
    async def api_get_warnings(self, request):
        """獲取警告數據"""
        guild_id = request.match_info['guild_id']
        
        try:
            file_path = f'./data/{guild_id}/warnings.json'
            if not os.path.exists(file_path):
                return web.json_response({'warnings': {}})
            
            with open(file_path, 'r', encoding='utf-8') as f:
                warnings_data = json.load(f)
            
            # 獲取用戶信息
            guild = self.bot.get_guild(int(guild_id))
            enriched_warnings = {}
            
            if guild:
                for user_id, warnings in warnings_data.items():
                    member = guild.get_member(int(user_id))
                    enriched_warnings[user_id] = {
                        'username': member.name if member else '未知用戶',
                        'display_name': member.display_name if member else '未知用戶',
                        'avatar': str(member.display_avatar.url) if member else None,
                        'warnings': warnings,
                        'warn_count': len(warnings)
                    }
            else:
                enriched_warnings = {uid: {'username': '未知', 'warnings': warns, 'warn_count': len(warns)} 
                                   for uid, warns in warnings_data.items()}
            
            return web.json_response({'warnings': enriched_warnings})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_clear_warnings(self, request):
        """清除用戶所有警告"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        user_id = request.match_info['user_id']
        
        try:
            file_path = f'./data/{guild_id}/warnings.json'
            if not os.path.exists(file_path):
                return web.json_response({'success': True, 'message': '沒有警告記錄'})
            
            with open(file_path, 'r', encoding='utf-8') as f:
                warnings_data = json.load(f)
            
            if user_id in warnings_data:
                warn_count = len(warnings_data[user_id])
                del warnings_data[user_id]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(warnings_data, f, ensure_ascii=False, indent=4)
                
                return web.json_response({
                    'success': True, 
                    'message': f'已清除 {warn_count} 次警告'
                })
            else:
                return web.json_response({'success': True, 'message': '沒有警告記錄'})
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_remove_latest_warning(self, request):
        """移除用戶最近一次警告"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        user_id = request.match_info['user_id']
        
        try:
            file_path = f'./data/{guild_id}/warnings.json'
            if not os.path.exists(file_path):
                return web.json_response({'success': False, 'message': '沒有警告記錄'})
            
            with open(file_path, 'r', encoding='utf-8') as f:
                warnings_data = json.load(f)
            
            if user_id in warnings_data and len(warnings_data[user_id]) > 0:
                removed = warnings_data[user_id].pop()
                
                if len(warnings_data[user_id]) == 0:
                    del warnings_data[user_id]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(warnings_data, f, ensure_ascii=False, indent=4)
                
                return web.json_response({
                    'success': True, 
                    'message': f'已移除警告',
                    'removed_warning': removed
                })
            else:
                return web.json_response({'success': False, 'message': '沒有警告記錄'})
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_remove_warning_by_index(self, request):
        """移除用戶指定索引的警告"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        user_id = request.match_info['user_id']
        index = int(request.match_info['index'])
        
        try:
            file_path = f'./data/{guild_id}/warnings.json'
            if not os.path.exists(file_path):
                return web.json_response({'success': False, 'message': '沒有警告記錄'})
            
            with open(file_path, 'r', encoding='utf-8') as f:
                warnings_data = json.load(f)
            
            if user_id in warnings_data and len(warnings_data[user_id]) > index >= 0:
                removed = warnings_data[user_id].pop(index)
                
                if len(warnings_data[user_id]) == 0:
                    del warnings_data[user_id]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(warnings_data, f, ensure_ascii=False, indent=4)
                
                return web.json_response({
                    'success': True, 
                    'message': '已移除警告',
                    'removed_warning': removed
                })
            else:
                return web.json_response({'success': False, 'message': '警告不存在'})
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_get_achievements(self, request):
        """獲取成就數據"""
        guild_id = request.match_info['guild_id']
        
        try:
            file_path = f'./data/{guild_id}/achievements.json'
            if not os.path.exists(file_path):
                return web.json_response({'achievements': {}})
            
            with open(file_path, 'r', encoding='utf-8') as f:
                achievements_data = json.load(f)
            
            # 獲取用戶信息和成就定義
            guild = self.bot.get_guild(int(guild_id))
            achievements_cog = self.bot.get_cog('Achievements')
            
            enriched_achievements = {}
            
            if guild and achievements_cog:
                achievement_defs = achievements_cog.achievement_definitions
                
                for user_id, user_achievements in achievements_data.items():
                    member = guild.get_member(int(user_id))
                    
                    # 豐富成就信息
                    enriched_list = []
                    for ach_id in user_achievements:
                        if ach_id in achievement_defs:
                            ach_def = achievement_defs[ach_id]
                            enriched_list.append({
                                'id': ach_id,
                                'name': ach_def['name'],
                                'description': ach_def['description'],
                                'rarity': ach_def['rarity'],
                                'category': ach_def['category']
                            })
                    
                    enriched_achievements[user_id] = {
                        'username': member.name if member else '未知用戶',
                        'display_name': member.display_name if member else '未知用戶',
                        'avatar': str(member.display_avatar.url) if member else None,
                        'achievements': enriched_list,
                        'achievement_count': len(enriched_list)
                    }
            else:
                enriched_achievements = {uid: {'username': '未知', 'achievements': achs, 'achievement_count': len(achs)} 
                                        for uid, achs in achievements_data.items()}
            
            return web.json_response({'achievements': enriched_achievements})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_grant_achievement(self, request):
        """授予成就"""
        guild_id = request.match_info['guild_id']
        user_id = request.match_info['user_id']
        achievement_id = request.match_info['achievement_id']
        
        try:
            file_path = f'./data/{guild_id}/achievements.json'
            
            # 載入數據
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    achievements_data = json.load(f)
            else:
                achievements_data = {}
            
            # 添加成就
            if user_id not in achievements_data:
                achievements_data[user_id] = []
            
            if achievement_id not in achievements_data[user_id]:
                achievements_data[user_id].append(achievement_id)
                
                # 保存
                os.makedirs(f'./data/{guild_id}', exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(achievements_data, f, ensure_ascii=False, indent=4)
                
                return web.json_response({
                    'success': True, 
                    'message': '成就已授予'
                })
            else:
                return web.json_response({
                    'success': False, 
                    'message': '用戶已擁有此成就'
                })
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_revoke_achievement(self, request):
        """撤銷成就"""
        guild_id = request.match_info['guild_id']
        user_id = request.match_info['user_id']
        achievement_id = request.match_info['achievement_id']
        
        try:
            file_path = f'./data/{guild_id}/achievements.json'
            if not os.path.exists(file_path):
                return web.json_response({'success': False, 'message': '沒有成就記錄'})
            
            with open(file_path, 'r', encoding='utf-8') as f:
                achievements_data = json.load(f)
            
            if user_id in achievements_data and achievement_id in achievements_data[user_id]:
                achievements_data[user_id].remove(achievement_id)
                
                if len(achievements_data[user_id]) == 0:
                    del achievements_data[user_id]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(achievements_data, f, ensure_ascii=False, indent=4)
                
                return web.json_response({
                    'success': True, 
                    'message': '成就已撤銷'
                })
            else:
                return web.json_response({
                    'success': False, 
                    'message': '用戶沒有此成就'
                })
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_get_tickets(self, request):
        """API：獲取客服單數據"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        
        try:
            file_path = f'./data/{guild_id}/tickets.json'
            if not os.path.exists(file_path):
                return web.json_response({
                    'exists': False,
                    'data': {
                        'enabled': False,
                        'category_id': None,
                        'support_role_id': None,
                        'log_channel_id': None,
                        'tickets': {},
                        'ticket_count': 0
                    }
                })
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 豐富客服單信息（添加用戶名等）
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                for ticket_id, ticket in data['tickets'].items():
                    user = guild.get_member(int(ticket['user_id']))
                    ticket['user_name'] = user.name if user else '未知用戶'
                    ticket['user_avatar'] = str(user.avatar.url) if user and user.avatar else None
                    
                    if ticket.get('closed_by'):
                        closer = guild.get_member(int(ticket['closed_by']))
                        ticket['closer_name'] = closer.name if closer else '未知用戶'
            
            return web.json_response({'exists': True, 'data': data})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_update_ticket_settings(self, request):
        """API：更新客服單設定"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        
        try:
            body = await request.json()
            file_path = f'./data/{guild_id}/tickets.json'
            
            # 讀取現有數據
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    'enabled': False,
                    'category_id': None,
                    'support_role_id': None,
                    'log_channel_id': None,
                    'tickets': {},
                    'ticket_count': 0
                }
            
            # 更新設定
            if 'enabled' in body:
                data['enabled'] = body['enabled']
            if 'category_id' in body:
                data['category_id'] = body['category_id']
            if 'support_role_id' in body:
                data['support_role_id'] = body['support_role_id']
            if 'log_channel_id' in body:
                data['log_channel_id'] = body['log_channel_id']
            if 'panel_channel_id' in body:
                data['panel_channel_id'] = body['panel_channel_id']
            
            # 保存數據
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            return web.json_response({'success': True, 'message': '設定已更新'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_close_ticket(self, request):
        """API：關閉客服單（已禁用）"""
        return web.json_response({
            'success': False, 
            'message': '網頁後台不支援關閉客服單，請使用 Discord 內的關閉按鈕'
        }, status=403)
    
    async def api_my_tickets(self, request):
        """API：獲取當前用戶的所有客服單"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        user_id = user['id']
        
        try:
            all_tickets = []
            server_map = {}
            
            # 遍歷所有伺服器，找出用戶的客服單
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                file_path = f'./data/{guild_id}/tickets.json'
                
                if not os.path.exists(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 找出屬於該用戶的客服單
                    for ticket_id, ticket in data.get('tickets', {}).items():
                        if str(ticket.get('user_id')) == str(user_id):
                            ticket_info = {
                                'ticket_id': ticket_id,
                                'guild_id': guild_id,
                                'channel_name': ticket.get('channel_name', '未知'),
                                'channel_id': ticket.get('channel_id'),
                                'status': ticket.get('status', 'unknown'),
                                'created_at': ticket.get('created_at', ''),
                                'closed_at': ticket.get('closed_at'),
                                'closed_reason': ticket.get('close_reason')
                            }
                            all_tickets.append(ticket_info)
                            server_map[guild_id] = guild.name
                
                except Exception as e:
                    print(f"讀取伺服器 {guild.name} 的客服單時發生錯誤: {e}")
                    continue
            
            return web.json_response({
                'tickets': all_tickets,
                'servers': server_map
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_get_ticket_transcript(self, request):
        """API：獲取客服單聊天記錄HTML"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        ticket_id = request.match_info['ticket_id']
        
        try:
            # 獲取客服單數據
            file_path = f'./data/{guild_id}/tickets.json'
            if not os.path.exists(file_path):
                return web.json_response({'error': '找不到客服單'}, status=404)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if ticket_id not in data['tickets']:
                return web.json_response({'error': '客服單不存在'}, status=404)
            
            ticket = data['tickets'][ticket_id]
            
            # 檢查權限：只有客服單創建者或管理員可以查看
            user_id = user['id']
            is_ticket_owner = str(ticket.get('user_id')) == str(user_id)
            
            # 檢查是否為管理員（從 access_token 獲取用戶的公團權限）
            is_admin = False
            access_token = session.get('access_token')
            if access_token:
                async with ClientSession() as client_session:
                    headers = {'Authorization': f"Bearer {access_token}"}
                    async with client_session.get('https://discord.com/api/users/@me/guilds', headers=headers) as resp:
                        if resp.status == 200:
                            user_guilds = await resp.json()
                            for guild in user_guilds:
                                if str(guild['id']) == str(guild_id):
                                    permissions = int(guild.get('permissions', 0))
                                    is_admin = (permissions & 0x8) == 0x8
                                    break
            
            if not (is_ticket_owner or is_admin):
                return web.json_response({'error': '無權查看此客服單'}, status=403)
            
            # 獲取HTML文件
            channel_name = ticket.get('channel_name', f"客服單-{ticket_id}")
            transcript_path = f'./data/{guild_id}/ticket/{channel_name}-{ticket_id}.html'
            
            if not os.path.exists(transcript_path):
                return web.json_response({'error': '找不到聊天記錄'}, status=404)
            
            with open(transcript_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return web.Response(text=html_content, content_type='text/html')
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_create_ticket_panel(self, request):
        """API：創建客服單面板"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info['guild_id']
        
        try:
            body = await request.json()
            channel_id = body.get('channel_id')
            
            if not channel_id:
                return web.json_response({'error': '缺少頻道ID'}, status=400)
            
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                return web.json_response({'error': '找不到伺服器'}, status=404)
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return web.json_response({'error': '找不到頻道'}, status=404)
            
            # 獲取tickets cog
            tickets_cog = self.bot.get_cog('Tickets')
            if not tickets_cog:
                return web.json_response({'error': '客服單系統未啟動'}, status=500)
            
            # 創建嵌入消息
            embed = discord.Embed(
                title="🎫 客服單系統",
                description="需要幫助嗎？點擊下方按鈕創建客服單\n\n"
                           "📋 創建客服單後，我們的支持團隊會盡快回覆您\n"
                           "⏱️ 請耐心等待，我們會盡快處理您的問題",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"{guild.name} 客服支持")
            
            # 導入TicketPanelView
            from cogs.tickets import TicketPanelView
            view = TicketPanelView(tickets_cog)
            
            # 發送面板
            message = await channel.send(embed=embed, view=view)
            
            # 保存面板訊息ID
            file_path = f'./data/{guild_id}/tickets.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    'enabled': False,
                    'category_id': None,
                    'support_role_id': None,
                    'log_channel_id': None,
                    'panel_channel_id': None,
                    'panel_message_id': None,
                    'tickets': {},
                    'ticket_count': 0
                }
            
            data['panel_channel_id'] = str(channel_id)
            data['panel_message_id'] = str(message.id)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            return web.json_response({
                'success': True,
                'message': '已創建客服單面板',
                'channel_id': str(channel_id),
                'message_id': str(message.id)
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    # ===== 自動回覆系統 API =====
    
    async def api_get_auto_replies(self, request):
        """API：獲取自動回覆規則"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        file_path = f'./data/{guild_id}/auto_reply.json'
        
        if not os.path.exists(file_path):
            return web.json_response({
                'enabled': True,
                'rules': []
            })
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 獲取伺服器頻道和角色信息
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                # 添加頻道和角色名稱
                for rule in data.get('rules', []):
                    # 添加頻道名稱
                    if 'channel_ids' in rule:
                        channels = []
                        for ch_id in rule['channel_ids']:
                            channel = guild.get_channel(int(ch_id))
                            if channel:
                                channels.append({'id': ch_id, 'name': channel.name})
                        rule['channels'] = channels
                    
                    # 添加角色名稱
                    if 'role_ids' in rule:
                        roles = []
                        for role_id in rule['role_ids']:
                            role = guild.get_role(int(role_id))
                            if role:
                                roles.append({'id': role_id, 'name': role.name})
                        rule['roles'] = roles
            
            return web.json_response(data)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_add_auto_reply(self, request):
        """API：添加自動回覆規則"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            data_input = await request.json()
            
            # 載入現有數據
            file_path = f'./data/{guild_id}/auto_reply.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'enabled': True, 'rules': []}
            
            # 創建新規則
            new_rule = {
                'id': max([r.get('id', 0) for r in data.get('rules', [])] + [0]) + 1,
                'trigger': data_input.get('trigger', ''),
                'reply': data_input.get('reply', ''),
                'match_type': data_input.get('match_type', 'contains'),
                'reply_type': data_input.get('reply_type', 'message'),
                'enabled': data_input.get('enabled', True),
                'case_sensitive': data_input.get('case_sensitive', False),
                'mention_user': data_input.get('mention_user', False),
                'trigger_once': data_input.get('trigger_once', False),
                'channel_ids': data_input.get('channel_ids', []),
                'role_ids': data_input.get('role_ids', []),
                'reaction': data_input.get('reaction', '👍'),
                'triggered_count': 0,
                'created_at': datetime.now().isoformat(),
                'created_by': session.get('user', {}).get('id')
            }
            
            data.setdefault('rules', []).append(new_rule)
            
            # 保存
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'rule': new_rule})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_update_auto_reply(self, request):
        """API：更新自動回覆規則"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        rule_id = int(request.match_info.get('rule_id'))
        
        try:
            data_input = await request.json()
            
            file_path = f'./data/{guild_id}/auto_reply.json'
            if not os.path.exists(file_path):
                return web.json_response({'error': '找不到自動回覆數據'}, status=404)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找並更新規則
            found = False
            for rule in data.get('rules', []):
                if rule['id'] == rule_id:
                    rule['trigger'] = data_input.get('trigger', rule['trigger'])
                    rule['reply'] = data_input.get('reply', rule['reply'])
                    rule['match_type'] = data_input.get('match_type', rule['match_type'])
                    rule['reply_type'] = data_input.get('reply_type', rule['reply_type'])
                    rule['enabled'] = data_input.get('enabled', rule['enabled'])
                    rule['case_sensitive'] = data_input.get('case_sensitive', rule.get('case_sensitive', False))
                    rule['mention_user'] = data_input.get('mention_user', rule.get('mention_user', False))
                    rule['trigger_once'] = data_input.get('trigger_once', rule.get('trigger_once', False))
                    rule['channel_ids'] = data_input.get('channel_ids', rule.get('channel_ids', []))
                    rule['role_ids'] = data_input.get('role_ids', rule.get('role_ids', []))
                    rule['reaction'] = data_input.get('reaction', rule.get('reaction', '👍'))
                    rule['updated_at'] = datetime.now().isoformat()
                    found = True
                    break
            
            if not found:
                return web.json_response({'error': '找不到指定規則'}, status=404)
            
            # 保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_delete_auto_reply(self, request):
        """API：刪除自動回覆規則"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        rule_id = int(request.match_info.get('rule_id'))
        
        try:
            file_path = f'./data/{guild_id}/auto_reply.json'
            if not os.path.exists(file_path):
                return web.json_response({'error': '找不到自動回覆數據'}, status=404)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 刪除規則
            original_length = len(data.get('rules', []))
            data['rules'] = [r for r in data.get('rules', []) if r['id'] != rule_id]
            
            if len(data['rules']) == original_length:
                return web.json_response({'error': '找不到指定規則'}, status=404)
            
            # 保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_toggle_auto_reply_system(self, request):
        """API：開關自動回覆系統"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        
        try:
            data_input = await request.json()
            enabled = data_input.get('enabled', True)
            
            file_path = f'./data/{guild_id}/auto_reply.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'enabled': True, 'rules': []}
            
            data['enabled'] = enabled
            
            # 保存
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'enabled': enabled})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_toggle_auto_reply_rule(self, request):
        """API：開關特定自動回覆規則"""
        session = await get_session(request)
        
        if not session.get('user'):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        guild_id = request.match_info.get('guild_id')
        rule_id = int(request.match_info.get('rule_id'))
        
        try:
            data_input = await request.json()
            enabled = data_input.get('enabled', True)
            
            file_path = f'./data/{guild_id}/auto_reply.json'
            if not os.path.exists(file_path):
                return web.json_response({'error': '找不到自動回覆數據'}, status=404)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新規則狀態
            found = False
            for rule in data.get('rules', []):
                if rule['id'] == rule_id:
                    rule['enabled'] = enabled
                    found = True
                    break
            
            if not found:
                return web.json_response({'error': '找不到指定規則'}, status=404)
            
            # 保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'enabled': enabled})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    # ==================== 安全系統 API ====================
    
    async def api_get_security(self, request):
        """獲取安全系統設定"""
        try:
            guild_id = request.match_info['guild_id']
            
            # 檢查權限
            session = await get_session(request)
            user = session.get('user')
            if not user:
                return web.json_response({'error': '未登入'}, status=401)
            
            # 獲取數據
            filepath = f"./data/{guild_id}/security.json"
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "enabled": True,
                    "banned_words": [],
                    "timeout_duration": 60,
                    "action_type": "timeout",
                    "whitelist_roles": [],
                    "whitelist_channels": [],
                    "case_sensitive": False,
                    "match_type": "contains"
                }
            
            return web.json_response(data)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_update_security(self, request):
        """更新安全系統設定"""
        try:
            guild_id = request.match_info['guild_id']
            
            # 檢查權限
            session = await get_session(request)
            user = session.get('user')
            if not user:
                return web.json_response({'error': '未登入'}, status=401)
            
            # 讀取請求數據
            data = await request.json()
            
            # 驗證數據
            if 'timeout_duration' in data:
                timeout = data['timeout_duration']
                if not isinstance(timeout, int) or timeout < 1 or timeout > 2419200:
                    return web.json_response({'error': '超時時長必須在 1-2419200 秒之間'}, status=400)
            
            if 'action_type' in data:
                if data['action_type'] not in ['timeout', 'delete', 'warn']:
                    return web.json_response({'error': '無效的處罰類型'}, status=400)
            
            if 'match_type' in data:
                if data['match_type'] not in ['contains', 'exact', 'regex']:
                    return web.json_response({'error': '無效的匹配模式'}, status=400)
            
            # 保存數據
            folder = f"./data/{guild_id}"
            os.makedirs(folder, exist_ok=True)
            
            filepath = f"{folder}/security.json"
            
            # 讀取現有數據或創建新數據
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {
                    "enabled": True,
                    "banned_words": [],
                    "timeout_duration": 60,
                    "action_type": "timeout",
                    "whitelist_roles": [],
                    "whitelist_channels": [],
                    "case_sensitive": False,
                    "match_type": "contains"
                }
            
            # 更新數據
            existing_data.update(data)
            
            # 保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'data': existing_data})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_add_banned_word(self, request):
        """添加違禁詞"""
        try:
            guild_id = request.match_info['guild_id']
            
            # 檢查權限
            session = await get_session(request)
            user = session.get('user')
            if not user:
                return web.json_response({'error': '未登入'}, status=401)
            
            # 讀取請求數據
            data = await request.json()
            word = data.get('word', '').strip()
            
            if not word:
                return web.json_response({'error': '違禁詞不能為空'}, status=400)
            
            # 讀取現有數據
            folder = f"./data/{guild_id}"
            os.makedirs(folder, exist_ok=True)
            filepath = f"{folder}/security.json"
            
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    security_data = json.load(f)
            else:
                security_data = {
                    "enabled": True,
                    "banned_words": [],
                    "timeout_duration": 60,
                    "action_type": "timeout",
                    "whitelist_roles": [],
                    "whitelist_channels": [],
                    "case_sensitive": False,
                    "match_type": "contains"
                }
            
            # 檢查是否已存在
            if word in security_data['banned_words']:
                return web.json_response({'error': '該違禁詞已存在'}, status=400)
            
            # 添加違禁詞
            security_data['banned_words'].append(word)
            
            # 保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(security_data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'word': word, 'banned_words': security_data['banned_words']})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def api_delete_banned_word(self, request):
        """刪除違禁詞"""
        try:
            guild_id = request.match_info['guild_id']
            
            # 檢查權限
            session = await get_session(request)
            user = session.get('user')
            if not user:
                return web.json_response({'error': '未登入'}, status=401)
            
            # 讀取請求數據
            data = await request.json()
            word = data.get('word', '').strip()
            
            if not word:
                return web.json_response({'error': '違禁詞不能為空'}, status=400)
            
            # 讀取現有數據
            filepath = f"./data/{guild_id}/security.json"
            if not os.path.exists(filepath):
                return web.json_response({'error': '安全系統數據不存在'}, status=404)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                security_data = json.load(f)
            
            # 檢查是否存在
            if word not in security_data['banned_words']:
                return web.json_response({'error': '該違禁詞不存在'}, status=404)
            
            # 移除違禁詞
            security_data['banned_words'].remove(word)
            
            # 保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(security_data, f, ensure_ascii=False, indent=2)
            
            return web.json_response({'success': True, 'word': word, 'banned_words': security_data['banned_words']})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def dev_panel(self, request):
        """開發者面板"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user:
            raise web.HTTPFound('/login')
        
        # 檢查開發者權限
        if not self.is_developer(user['id']):
            return web.Response(text='<h1>403 Forbidden</h1><p>您沒有權限訪問開發者面板</p>', status=403, content_type='text/html')
        
        with open('web/dev-panel.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # 替換用戶資訊
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
        
        html = html.replace('{USERNAME}', user['username'])
        html = html.replace('{AVATAR_URL}', avatar_url)
        
        return web.Response(text=html, content_type='text/html')
    
    async def api_dev_all_guilds(self, request):
        """API：獲取所有伺服器列表（開發者專用）"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user or not self.is_developer(user['id']):
            return web.json_response({'error': 'Unauthorized'}, status=403)
        
        guilds_data = []
        
        for guild in self.bot.guilds:
            # 獲取伺服器圖標
            icon_url = str(guild.icon.url) if guild.icon else None
            
            # 獲取擁有者資訊
            owner = guild.owner
            owner_info = {
                'id': str(owner.id),
                'name': owner.name,
                'avatar': str(owner.avatar.url) if owner.avatar else None
            } if owner else None
            
            guilds_data.append({
                'id': str(guild.id),
                'name': guild.name,
                'icon': icon_url,
                'member_count': guild.member_count,
                'created_at': guild.created_at.isoformat(),
                'owner': owner_info,
                'features': guild.features,
                'text_channels': len(guild.text_channels),
                'voice_channels': len(guild.voice_channels),
                'roles': len(guild.roles),
                'emojis': len(guild.emojis)
            })
        
        return web.json_response({
            'total': len(guilds_data),
            'guilds': guilds_data
        })
    
    async def api_dev_guild_config(self, request):
        """API：獲取指定伺服器的完整配置（開發者專用）"""
        session = await get_session(request)
        user = session.get('user')
        
        if not user or not self.is_developer(user['id']):
            return web.json_response({'error': 'Unauthorized'}, status=403)
        
        guild_id = request.match_info.get('guild_id')
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({'error': 'Guild not found'}, status=404)
        
        # 讀取所有配置文件
        config_data = {}
        data_dir = f"./data/{guild_id}"
        
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            config_data[filename[:-5]] = json.load(f)
                    except Exception as e:
                        config_data[filename[:-5]] = {'error': str(e)}
        
        # 獲取伺服器詳細資訊
        guild_info = {
            'id': str(guild.id),
            'name': guild.name,
            'icon': str(guild.icon.url) if guild.icon else None,
            'owner_id': str(guild.owner_id),
            'member_count': guild.member_count,
            'created_at': guild.created_at.isoformat(),
            'features': guild.features,
            'verification_level': str(guild.verification_level),
            'premium_tier': guild.premium_tier,
            'channels': {
                'text': [{'id': str(c.id), 'name': c.name, 'category': c.category.name if c.category else None} for c in guild.text_channels],
                'voice': [{'id': str(c.id), 'name': c.name, 'category': c.category.name if c.category else None} for c in guild.voice_channels],
                'categories': [{'id': str(c.id), 'name': c.name} for c in guild.categories]
            },
            'roles': [{'id': str(r.id), 'name': r.name, 'color': str(r.color), 'position': r.position, 'members': len(r.members)} for r in guild.roles],
            'emojis': [{'id': str(e.id), 'name': e.name, 'animated': e.animated} for e in guild.emojis]
        }
        
        return web.json_response({
            'guild': guild_info,
            'config': config_data
        })
    
    async def start(self):
        """啟動 Web 伺服器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f'🌐 網頁控制台已啟動: http://{self.host}:{self.port}')
        print(f'   本地訪問: http://localhost:{self.port}')
