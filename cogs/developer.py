import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv

class Developer(commands.Cog):
    """開發者專用指令"""
    
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        # 讀取開發者 ID（支持多個，用逗號分隔）
        dev_ids = os.getenv('DEV_ID', '')
        if dev_ids:
            self.dev_ids = [int(id.strip()) for id in dev_ids.split(',') if id.strip().isdigit()]
        else:
            self.dev_ids = []
    
    def is_developer(self, user_id: int) -> bool:
        """檢查用戶是否為開發者"""
        return user_id in self.dev_ids
    
    async def show_help(self, message):
        """顯示開發者指令幫助"""
        await message.channel.send(
            "🔧 **開發者指令**\n"
            "```\n"
            "?開發 restart  - 重啟機器人\n"
            "?開發 status   - 查看系統狀態\n"
            "?開發 reload   - 重新載入所有 Cogs\n"
            "?開發 eval     - 執行 Python 代碼\n"
            "```"
        )
    
    async def handle_restart(self, message):
        """重啟機器人"""
        embed = discord.Embed(
            title="🔄 重啟機器人",
            description="機器人正在重啟，請稍候...",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"執行者: {message.author.name}")
        
        await message.channel.send(embed=embed)
        
        print(f"\n{'═' * 62}")
        print(f"🔄 開發者 {message.author.name} ({message.author.id}) 執行重啟")
        print(f"{'═' * 62}\n")
        
        # 關閉機器人
        await self.bot.close()
        
        # 重新啟動 (支援 Linux/Windows)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    async def handle_status(self, message):
        """查看系統狀態"""
        # 獲取版本
        try:
            with open('./version.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                version = content.split('=')[1].strip() if '=' in content else content
        except:
            version = "Unknown"
        
        # 計算 Cogs 數量
        cog_count = len(self.bot.cogs)
        
        # 計算命令數量
        command_count = len([cmd for cmd in self.bot.walk_commands()])
        
        embed = discord.Embed(
            title="🔧 系統狀態",
            color=discord.Color.blue()
        )
        embed.add_field(name="版本", value=f"`{version}`", inline=True)
        embed.add_field(name="延遲", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="伺服器數", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="用戶數", value=f"`{sum(g.member_count for g in self.bot.guilds):,}`", inline=True)
        embed.add_field(name="Cogs 數量", value=f"`{cog_count}`", inline=True)
        embed.add_field(name="命令數量", value=f"`{command_count}`", inline=True)
        
        # Python 版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        embed.add_field(name="Python 版本", value=f"`{python_version}`", inline=True)
        embed.add_field(name="Discord.py", value=f"`{discord.__version__}`", inline=True)
        
        embed.set_footer(text=f"執行者: {message.author.name}")
        
        await message.channel.send(embed=embed)
    
    async def handle_reload(self, message):
        """重新載入所有 Cogs"""
        msg = await message.channel.send("🔄 正在重新載入所有 Cogs...")
        
        successful = []
        failed = []
        
        # 獲取所有已載入的 Cogs
        cog_names = list(self.bot.cogs.keys())
        
        for cog_name in cog_names:
            try:
                # 獲取 Cog 對應的模組名
                cog = self.bot.cogs[cog_name]
                module_name = cog.__module__
                
                # 重新載入
                await self.bot.reload_extension(module_name)
                successful.append(cog_name)
            except Exception as e:
                failed.append(f"{cog_name}: {str(e)}")
        
        # 更新結果
        embed = discord.Embed(
            title="🔄 Cogs 重新載入結果",
            color=discord.Color.green() if not failed else discord.Color.orange()
        )
        
        if successful:
            embed.add_field(
                name=f"✅ 成功 ({len(successful)})",
                value="```\n" + "\n".join(successful) + "```",
                inline=False
            )
        
        if failed:
            embed.add_field(
                name=f"❌ 失敗 ({len(failed)})",
                value="```\n" + "\n".join(failed[:5]) + "```",
                inline=False
            )
        
        embed.set_footer(text=f"執行者: {message.author.name}")
        
        await msg.edit(content=None, embed=embed)
    
    async def handle_eval(self, message, code: str):
        """執行 Python 代碼（危險！）"""
        # 移除代碼塊標記
        if code.startswith('```') and code.endswith('```'):
            code = code[3:-3]
            if code.startswith('python'):
                code = code[6:]
        
        try:
            result = eval(code)
            
            embed = discord.Embed(
                title="✅ 執行成功",
                color=discord.Color.green()
            )
            embed.add_field(name="代碼", value=f"```python\n{code[:1000]}\n```", inline=False)
            embed.add_field(name="結果", value=f"```python\n{str(result)[:1000]}\n```", inline=False)
            
            await message.channel.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 執行失敗",
                color=discord.Color.red()
            )
            embed.add_field(name="代碼", value=f"```python\n{code[:1000]}\n```", inline=False)
            embed.add_field(name="錯誤", value=f"```python\n{str(e)[:1000]}\n```", inline=False)
            
            await message.channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽消息並處理開發者指令"""
        # 忽略機器人自己的消息
        if message.author.bot:
            return
        
        # 檢查是否為開發者指令（以 ?開發 開頭）
        if not message.content.startswith('?開發'):
            return
        
        # 檢查權限
        if not self.is_developer(message.author.id):
            msg = await message.channel.send("❌ 此指令僅限開發者使用！")
            await message.delete(delay=5)
            await msg.delete(delay=5)
            return
        
        # 解析指令
        parts = message.content.split(maxsplit=2)
        
        # 只有 ?開發
        if len(parts) == 1:
            await self.show_help(message)
            return
        
        command = parts[1].lower()
        
        # 處理各種指令
        if command in ['restart', '重啟']:
            await self.handle_restart(message)
        
        elif command in ['status', '狀態']:
            await self.handle_status(message)
        
        elif command in ['reload', '重載']:
            await self.handle_reload(message)
        
        elif command == 'eval':
            if len(parts) >= 3:
                code = parts[2]
                await self.handle_eval(message, code)
            else:
                await message.channel.send("❌ 請提供要執行的代碼！\n用法: `?開發 eval <代碼>`")
        
        else:
            await message.channel.send(f"❌ 未知的指令: `{command}`\n使用 `?開發` 查看所有可用指令")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cog 準備就緒"""
        if self.dev_ids:
            print(f'🔧 {self.__class__.__name__} cog已載入 | 開發者: {len(self.dev_ids)} 位')
        else:
            print(f'⚠️  {self.__class__.__name__} cog已載入 | 警告: 未設定開發者ID')

async def setup(bot):
    await bot.add_cog(Developer(bot))
