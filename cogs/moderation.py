import discord
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    """管理指令"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # 創建指令組
    mod_group = app_commands.Group(name="管理", description="管理功能指令")
    
    @mod_group.command(name="踢出用戶", description="踢出用戶")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無理由"):
        """踢出成員"""
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="✅ 成員已踢出",
                description=f"{member.mention} 已被踢出",
                color=discord.Color.orange()
            )
            embed.add_field(name="理由", value=reason)
            embed.set_footer(text=f"操作者: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 我沒有權限踢出此用戶", ephemeral=True)
    
    @mod_group.command(name="封鎖用戶", description="封鎖用戶")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無理由"):
        """封鎖成員"""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 成員已封鎖",
                description=f"{member.mention} 已被封鎖",
                color=discord.Color.red()
            )
            embed.add_field(name="理由", value=reason)
            embed.set_footer(text=f"操作者: {interaction.user}")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ 我沒有權限封鎖此用戶", ephemeral=True)
    
    @mod_group.command(name="清除訊息", description="清除訊息")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        """清除指定數量的訊息"""
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ 請輸入1-100之間的數字", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ 已刪除 {len(deleted)} 則訊息", ephemeral=True)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
