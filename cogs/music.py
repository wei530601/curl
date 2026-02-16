"""
音乐系统 - 使用 Lavalink 提供音乐播放功能
"""

import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import asyncio
from typing import cast
import logging

logger = logging.getLogger(__name__)


class Music(commands.Cog):
    """音乐播放系统"""
    
    def __init__(self, bot):
        self.bot = bot
        self.node_connected = False
        
    async def cog_load(self):
        """Cog 加载时连接到 Lavalink"""
        try:
            # 从环境变量获取 Lavalink 配置
            lavalink_uri = self.bot.config.get('LAVALINK_URI', 'http://localhost:2333')
            lavalink_password = self.bot.config.get('LAVALINK_PASSWORD', 'youshallnotpass')
            
            # 连接到 Lavalink 节点
            node: wavelink.Node = wavelink.Node(
                uri=lavalink_uri,
                password=lavalink_password
            )
            
            await wavelink.Pool.connect(client=self.bot, nodes=[node])
            self.node_connected = True
            logger.info(f"✅ 已连接到 Lavalink 节点: {lavalink_uri}")
            
        except Exception as e:
            logger.error(f"❌ 连接 Lavalink 失败: {e}")
            self.node_connected = False
    
    async def cog_unload(self):
        """Cog 卸载时断开 Lavalink 连接"""
        await wavelink.Pool.close()
        logger.info("🔌 已断开 Lavalink 连接")
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """当 Lavalink 节点准备就绪时触发"""
        logger.info(f"🎵 Lavalink 节点已就绪: {payload.node.identifier}")
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """当音轨开始播放时触发"""
        player: wavelink.Player | None = payload.player
        if not player:
            return
        
        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track
        
        embed = discord.Embed(
            title="🎵 正在播放",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.green()
        )
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        
        embed.add_field(name="作者", value=track.author, inline=True)
        embed.add_field(name="時長", value=self._format_duration(track.length), inline=True)
        
        if hasattr(player, 'message_channel') and player.message_channel:
            await player.message_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """当音轨结束播放时触发"""
        player: wavelink.Player | None = payload.player
        if not player:
            return
        
        # 如果队列为空且没有自动播放，5分钟后自动断开
        if player.queue.is_empty and not player.autoplay:
            await asyncio.sleep(300)  # 5分钟
            if player.queue.is_empty and not player.playing:
                await player.disconnect()
                if hasattr(player, 'message_channel') and player.message_channel:
                    await player.message_channel.send("⏹️ 播放队列为空，已自动离开语音频道")
    
    def _format_duration(self, milliseconds: int) -> str:
        """格式化时长"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    async def ensure_voice(self, interaction: discord.Interaction) -> wavelink.Player | None:
        """确保用户在语音频道并连接机器人"""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ 你必須先加入語音頻道！", ephemeral=True)
            return None
        
        channel = interaction.user.voice.channel
        
        # 获取或创建播放器
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            try:
                player = await channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.enabled
                # 保存消息频道用于发送通知
                player.message_channel = interaction.channel
            except Exception as e:
                await interaction.response.send_message(f"❌ 無法連接到語音頻道: {e}", ephemeral=True)
                return None
        elif player.channel.id != channel.id:
            await interaction.response.send_message("❌ 機器人已在其他語音頻道中！", ephemeral=True)
            return None
        
        return player
    
    @app_commands.command(name="播放", description="播放音樂")
    @app_commands.describe(查詢="歌曲名稱、URL 或搜尋關鍵字")
    async def play(self, interaction: discord.Interaction, 查詢: str):
        """播放音乐"""
        if not self.node_connected:
            await interaction.response.send_message("❌ 音樂系統未就緒，請檢查 Lavalink 連接", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        player = await self.ensure_voice(interaction)
        if not player:
            return
        
        # 搜索音轨
        try:
            tracks: wavelink.Search = await wavelink.Playable.search(查詢)
            if not tracks:
                await interaction.followup.send("❌ 找不到相關歌曲")
                return
            
            # 如果是播放列表
            if isinstance(tracks, wavelink.Playlist):
                added: int = await player.queue.put_wait(tracks)
                await interaction.followup.send(
                    f"✅ 已添加播放列表 **{tracks.name}** ({added} 首歌曲)"
                )
            else:
                track: wavelink.Playable = tracks[0]
                await player.queue.put_wait(track)
                
                embed = discord.Embed(
                    title="➕ 已加入隊列",
                    description=f"[{track.title}]({track.uri})",
                    color=discord.Color.blue()
                )
                
                if track.artwork:
                    embed.set_thumbnail(url=track.artwork)
                
                embed.add_field(name="作者", value=track.author, inline=True)
                embed.add_field(name="時長", value=self._format_duration(track.length), inline=True)
                embed.add_field(name="隊列位置", value=str(player.queue.count), inline=True)
                
                await interaction.followup.send(embed=embed)
            
            # 如果没有在播放，开始播放
            if not player.playing:
                await player.play(player.queue.get())
                
        except Exception as e:
            logger.error(f"播放音乐失败: {e}")
            await interaction.followup.send(f"❌ 播放失敗: {str(e)}")
    
    @app_commands.command(name="暫停", description="暫停音樂")
    async def pause(self, interaction: discord.Interaction):
        """暂停音乐"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or not player.playing:
            await interaction.response.send_message("❌ 目前沒有正在播放的音樂", ephemeral=True)
            return
        
        await player.pause(not player.paused)
        
        if player.paused:
            await interaction.response.send_message("⏸️ 已暫停播放")
        else:
            await interaction.response.send_message("▶️ 繼續播放")
    
    @app_commands.command(name="停止", description="停止音樂並清空隊列")
    async def stop(self, interaction: discord.Interaction):
        """停止音乐"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
            return
        
        await player.disconnect()
        await interaction.response.send_message("⏹️ 已停止播放並離開語音頻道")
    
    @app_commands.command(name="跳過", description="跳過當前歌曲")
    async def skip(self, interaction: discord.Interaction):
        """跳过当前歌曲"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or not player.playing:
            await interaction.response.send_message("❌ 目前沒有正在播放的音樂", ephemeral=True)
            return
        
        await player.skip(force=True)
        await interaction.response.send_message("⏭️ 已跳過當前歌曲")
    
    @app_commands.command(name="隊列", description="顯示播放隊列")
    async def queue(self, interaction: discord.Interaction):
        """显示播放队列"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
            return
        
        if player.queue.is_empty and not player.current:
            await interaction.response.send_message("📝 播放隊列為空", ephemeral=True)
            return
        
        embed = discord.Embed(title="🎵 播放隊列", color=discord.Color.blue())
        
        # 当前播放
        if player.current:
            current = player.current
            embed.add_field(
                name="▶️ 正在播放",
                value=f"[{current.title}]({current.uri})\n`{self._format_duration(player.position)}/{self._format_duration(current.length)}`",
                inline=False
            )
        
        # 队列中的歌曲
        if not player.queue.is_empty:
            queue_list = []
            for i, track in enumerate(list(player.queue)[:10], 1):
                queue_list.append(f"`{i}.` [{track.title}]({track.uri}) - `{self._format_duration(track.length)}`")
            
            embed.add_field(
                name=f"📋 接下來 ({player.queue.count} 首)",
                value="\n".join(queue_list),
                inline=False
            )
            
            if player.queue.count > 10:
                embed.set_footer(text=f"還有 {player.queue.count - 10} 首歌曲...")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="當前", description="顯示當前播放的歌曲")
    async def now_playing(self, interaction: discord.Interaction):
        """显示当前播放的歌曲"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or not player.current:
            await interaction.response.send_message("❌ 目前沒有正在播放的音樂", ephemeral=True)
            return
        
        track = player.current
        
        embed = discord.Embed(
            title="🎵 正在播放",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.green()
        )
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        
        embed.add_field(name="作者", value=track.author, inline=True)
        embed.add_field(name="時長", value=self._format_duration(track.length), inline=True)
        embed.add_field(name="進度", value=f"{self._format_duration(player.position)}/{self._format_duration(track.length)}", inline=True)
        
        # 进度条
        progress = int((player.position / track.length) * 20)
        progress_bar = "▓" * progress + "░" * (20 - progress)
        embed.add_field(name="⏱️", value=f"`{progress_bar}`", inline=False)
        
        if player.paused:
            embed.add_field(name="狀態", value="⏸️ 已暫停", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="音量", description="調整播放音量")
    @app_commands.describe(音量="音量大小 (0-100)")
    async def volume(self, interaction: discord.Interaction, 音量: int):
        """调整音量"""
        if not 0 <= 音量 <= 100:
            await interaction.response.send_message("❌ 音量必須在 0-100 之間", ephemeral=True)
            return
        
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
            return
        
        await player.set_volume(音量)
        await interaction.response.send_message(f"🔊 音量已設定為 {音量}%")
    
    @app_commands.command(name="清空隊列", description="清空播放隊列")
    async def clear(self, interaction: discord.Interaction):
        """清空队列"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
            return
        
        player.queue.clear()
        await interaction.response.send_message("🗑️ 已清空播放隊列")
    
    @app_commands.command(name="洗牌", description="隨機打亂隊列順序")
    async def shuffle(self, interaction: discord.Interaction):
        """随机打乱队列"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or player.queue.is_empty:
            await interaction.response.send_message("❌ 播放隊列為空", ephemeral=True)
            return
        
        player.queue.shuffle()
        await interaction.response.send_message("🔀 已隨機打亂隊列順序")
    
    @app_commands.command(name="循環", description="設定循環模式")
    @app_commands.describe(模式="循環模式 (關閉/單曲/隊列)")
    @app_commands.choices(模式=[
        app_commands.Choice(name="關閉", value="off"),
        app_commands.Choice(name="單曲循環", value="track"),
        app_commands.Choice(name="隊列循環", value="queue")
    ])
    async def loop(self, interaction: discord.Interaction, 模式: str):
        """设置循环模式"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
            return
        
        if 模式 == "off":
            player.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("🔁 已關閉循環")
        elif 模式 == "track":
            player.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("🔂 已開啟單曲循環")
        elif 模式 == "queue":
            player.queue.mode = wavelink.QueueMode.loop_all
            await interaction.response.send_message("🔁 已開啟隊列循環")


async def setup(bot):
    await bot.add_cog(Music(bot))
