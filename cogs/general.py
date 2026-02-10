import discord
from discord import app_commands
from discord.ext import commands

class General(commands.Cog):
    """通用指令"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # 創建指令組
    general_group = app_commands.Group(name="一般", description="一般功能指令")
    
    @general_group.command(name="延遲檢查", description="檢查機器人延遲")
    async def ping(self, interaction: discord.Interaction):
        """Ping指令 - 顯示機器人延遲"""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'🏓 Pong! 延遲: {latency}ms')
    
    @general_group.command(name="打招呼", description="打個招呼")
    async def hello(self, interaction: discord.Interaction):
        """Say hello"""
        await interaction.response.send_message(f'👋 你好, {interaction.user.mention}!')
    
    @general_group.command(name="查看用戶資訊", description="查看用戶資訊")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """顯示用戶資訊"""
        member = member or interaction.user
        
        embed = discord.Embed(
            title=f"{member.name} 的資訊",
            color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📛 用戶名", value=str(member), inline=True)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 加入時間", value=discord.utils.format_dt(member.joined_at, style='R'), inline=False)
        embed.add_field(name="📅 帳號創建時間", value=discord.utils.format_dt(member.created_at, style='R'), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(General(bot))
