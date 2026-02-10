import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from web.server import WebServer

# 載入環境變數
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WEB_PORT = int(os.getenv('WEB_PORT', 8080))  # 網頁端口，預設8080

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # 初始化網頁伺服器
        self.web_server = WebServer(self, port=WEB_PORT)
    
    async def setup_hook(self):
        # 啟動網頁控制台
        await self.web_server.start()
        
        # 載入所有cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ 已載入 {filename}')
        
        # 同步slash commands
        await self.tree.sync()
        print('✅ Slash commands已同步')
    
    async def on_ready(self):
        print(f'✅ 機器人已登錄: {self.user.name} (ID: {self.user.id})')
        print(f'✅ 在 {len(self.guilds)} 個伺服器中')
        print('─' * 40)

def main():
    bot = MyBot()
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
