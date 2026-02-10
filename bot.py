import discord
from discord.ext import commands
import os
import asyncio
import sys
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
        
        # 啟動終端輸入監聽
        self.loop.create_task(self.handle_terminal_input())
    
    async def on_ready(self):
        print(f'✅ 機器人已登錄: {self.user.name} (ID: {self.user.id})')
        print(f'✅ 在 {len(self.guilds)} 個伺服器中')
        print('─' * 40)
        print('💡 終端命令: restart(重啟) | stop(關閉) | status(狀態) | help(幫助)')
        print('─' * 40)
    
    async def handle_terminal_input(self):
        """處理終端輸入命令"""
        def get_input():
            return sys.stdin.readline().strip()
        
        while True:
            try:
                # 在另一個執行緒中讀取輸入，避免阻塞事件循環
                command = await asyncio.get_event_loop().run_in_executor(None, get_input)
                
                if not command:
                    continue
                
                # 處理命令
                if command.lower() in ['restart', '重啟', 'restat']:
                    print('🔄 正在重啟機器人...')
                    await self.close()
                    # 重新啟動
                    os.execv(sys.executable, ['python'] + sys.argv)
                
                elif command.lower() in ['stop', '關閉', 'quit', 'exit']:
                    print('🛑 正在關閉機器人...')
                    await self.web_server.stop()
                    await self.close()
                    sys.exit(0)
                
                elif command.lower() in ['status', '狀態']:
                    print('─' * 40)
                    print(f'📊 機器人狀態:')
                    print(f'  • 名稱: {self.user.name}')
                    print(f'  • ID: {self.user.id}')
                    print(f'  • 伺服器數: {len(self.guilds)}')
                    print(f'  • 延遲: {round(self.latency * 1000)}ms')
                    print(f'  • 網頁端口: {WEB_PORT}')
                    print('─' * 40)
                
                elif command.lower() in ['help', '幫助', 'h']:
                    print('─' * 40)
                    print('📋 可用終端命令:')
                    print('  • restart/重啟  - 重新啟動機器人')
                    print('  • stop/關閉     - 關閉機器人')
                    print('  • status/狀態   - 顯示機器人狀態')
                    print('  • help/幫助     - 顯示此幫助訊息')
                    print('─' * 40)
                
                else:
                    print(f'❌ 未知命令: {command}')
                    print('💡 輸入 help 查看可用命令')
            
            except Exception as e:
                print(f'❌ 處理命令時發生錯誤: {e}')
                await asyncio.sleep(0.1)

def main():
    bot = MyBot()
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
