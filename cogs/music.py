"""
音樂播放系統 - 使用 Lavalink
支持播放、暫停、跳過、隊列管理等功能
"""

import discord
from discord.ext import commands
from discord import app_commands
import wavelink
from wavelink.ext import spotify
import asyncio
from typing import cast
import os
from datetime import timedelta

class Music(commands.Cog):
    """音樂播放系統"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """當 Cog 載入時執行"""
        print("🎵 音樂系統已載入")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """當 Lavalink 節點就緒時"""
        print(f"✅ Lavalink 節點已就緒: {payload.node.identifier}")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """當歌曲開始播放時"""
        player: wavelink.Player = payload.player
        track: wavelink.Playable = payload.track

        if player.guild:
            embed = discord.Embed(
                title="🎵 正在播放",
                description=f"**{track.title}**",
                color=discord.Color.green()
            )
            
            if track.author:
                embed.add_field(name="作者", value=track.author, inline=True)
            if track.length:
                duration = str(timedelta(milliseconds=track.length))
                embed.add_field(name="時長", value=duration, inline=True)
            if track.uri:
                embed.add_field(name="連結", value=f"[點擊這裡]({track.uri})", inline=False)
            
            if track.artwork:
                embed.set_thumbnail(url=track.artwork)
            
            # 獲取原始頻道發送訊息
            if hasattr(player, 'text_channel') and player.text_channel:
                await player.text_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """當歌曲結束時"""
        player: wavelink.Player = payload.player
        
        # 如果隊列中還有歌曲，自動播放下一首
        if not player.queue.is_empty:
            next_track = player.queue.get()
            await player.play(next_track)

    @app_commands.command(name="加入", description="讓機器人加入你的語音頻道")
    async def join(self, interaction: discord.Interaction):
        """加入語音頻道"""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ 你需要先加入一個語音頻道！", ephemeral=True)
            return

        channel = interaction.user.voice.channel

        try:
            player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
            
            if player:
                if player.channel == channel:
                    await interaction.response.send_message("✅ 我已經在你的語音頻道了！", ephemeral=True)
                    return
                await player.move_to(channel)
                await interaction.response.send_message(f"🔄 已移動到 {channel.mention}")
            else:
                player = await channel.connect(cls=wavelink.Player)
                player.text_channel = interaction.channel
                await interaction.response.send_message(f"✅ 已加入 {channel.mention}")
                
        except Exception as e:
            await interaction.response.send_message(f"❌ 加入頻道時發生錯誤: {str(e)}", ephemeral=True)

    @app_commands.command(name="離開", description="讓機器人離開語音頻道")
    async def leave(self, interaction: discord.Interaction):
        """離開語音頻道"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 我還沒有加入任何語音頻道！", ephemeral=True)
            return

        await player.disconnect()
        await interaction.response.send_message("👋 已離開語音頻道")

    @app_commands.command(name="播放", description="播放音樂")
    @app_commands.describe(搜尋="歌曲名稱或 YouTube/SoundCloud 連結")
    async def play(self, interaction: discord.Interaction, 搜尋: str):
        """播放音樂"""
        await interaction.response.defer()

        # 檢查用戶是否在語音頻道
        if not interaction.user.voice:
            await interaction.followup.send("❌ 你需要先加入一個語音頻道！")
            return

        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        # 如果機器人還沒加入頻道，先加入
        if not player:
            channel = interaction.user.voice.channel
            player = await channel.connect(cls=wavelink.Player)
            player.text_channel = interaction.channel

        # 搜尋歌曲 - 嘗試多個來源
        try:
            tracks = None
            error_messages = []
            
            # 嘗試不同的搜尋源
            search_sources = [
                ("YouTube Music", f"ytmsearch:{搜尋}"),
                ("YouTube", f"ytsearch:{搜尋}"),
                ("SoundCloud", f"scsearch:{搜尋}"),
            ]
            
            # 如果是直接連結，直接搜尋
            if 搜尋.startswith(('http://', 'https://')):
                try:
                    tracks = await wavelink.Playable.search(搜尋)
                except Exception as e:
                    error_messages.append(f"連結載入失敗: {str(e)[:50]}")
            
            # 如果直接連結失敗或不是連結，嘗試搜尋
            if not tracks:
                for source_name, search_query in search_sources:
                    try:
                        tracks = await wavelink.Playable.search(search_query)
                        if tracks:
                            break
                    except Exception as e:
                        error_messages.append(f"{source_name}: {str(e)[:50]}")
                        continue
            
            if not tracks:
                error_msg = "❌ 找不到該歌曲！\n\n**可能的原因：**\n"
                error_msg += "• YouTube 可能暫時無法使用\n"
                error_msg += "• 請嘗試使用 SoundCloud 連結\n"
                error_msg += "• 檢查 Lavalink 是否正常運行\n"
                if error_messages:
                    error_msg += f"\n**錯誤詳情：**\n" + "\n".join(f"• {msg}" for msg in error_messages[:3])
                await interaction.followup.send(error_msg)
                return

            # 如果是播放列表
            if isinstance(tracks, wavelink.Playlist):
                added: int = await player.queue.put_wait(tracks)
                embed = discord.Embed(
                    title="✅ 已添加播放列表",
                    description=f"**{tracks.name}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="歌曲數量", value=f"{added} 首", inline=True)
                await interaction.followup.send(embed=embed)
            else:
                track: wavelink.Playable = tracks[0]
                await player.queue.put_wait(track)
                
                if player.playing:
                    embed = discord.Embed(
                        title="✅ 已添加到隊列",
                        description=f"**{track.title}**",
                        color=discord.Color.blue()
                    )
                    if track.author:
                        embed.add_field(name="作者", value=track.author, inline=True)
                    if track.length:
                        duration = str(timedelta(milliseconds=track.length))
                        embed.add_field(name="時長", value=duration, inline=True)
                    position = len(player.queue)
                    embed.add_field(name="隊列位置", value=f"第 {position} 首", inline=True)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"🔍 正在載入 **{track.title}**...")

            # 如果沒有正在播放的歌曲，開始播放
            if not player.playing:
                next_track = player.queue.get()
                await player.play(next_track)

        except wavelink.LavalinkLoadException as e:
            await interaction.followup.send(
                f"❌ Lavalink 載入失敗！\n\n"
                f"**錯誤：** {str(e)[:100]}\n\n"
                f"**建議：**\n"
                f"• 更新 Lavalink 到最新版本\n"
                f"• 檢查 Lavalink 配置文件\n"
                f"• 嘗試使用 SoundCloud 連結"
            )
        except Exception as e:
            error_str = str(e)
            if "Something went wrong" in error_str or "Failed to Load Tracks" in error_str:
                await interaction.followup.send(
                    f"❌ 音樂源暫時無法使用！\n\n"
                    f"**可能原因：**\n"
                    f"• YouTube 封鎖了請求\n"
                    f"• Lavalink 需要更新\n"
                    f"• 網路連線問題\n\n"
                    f"**解決方案：**\n"
                    f"1. 嘗試使用 SoundCloud 連結\n"
                    f"2. 更新 Lavalink 到最新版本\n"
                    f"3. 檢查 application.yml 配置\n"
                    f"4. 稍後再試"
                )
            else:
                await interaction.followup.send(f"❌ 播放時發生錯誤:\n```{error_str[:200]}```")

    @app_commands.command(name="暫停", description="暫停播放")
    async def pause(self, interaction: discord.Interaction):
        """暫停播放"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or not player.playing:
            await interaction.response.send_message("❌ 目前沒有正在播放的歌曲！", ephemeral=True)
            return

        await player.pause(True)
        await interaction.response.send_message("⏸️ 已暫停播放")

    @app_commands.command(name="繼續", description="繼續播放")
    async def resume(self, interaction: discord.Interaction):
        """繼續播放"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 目前沒有正在播放的歌曲！", ephemeral=True)
            return

        await player.pause(False)
        await interaction.response.send_message("▶️ 已繼續播放")

    @app_commands.command(name="停止", description="停止播放並清空隊列")
    async def stop(self, interaction: discord.Interaction):
        """停止播放"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 目前沒有正在播放的歌曲！", ephemeral=True)
            return

        player.queue.clear()
        await player.stop()
        await interaction.response.send_message("⏹️ 已停止播放並清空隊列")

    @app_commands.command(name="跳過", description="跳過目前播放的歌曲")
    async def skip(self, interaction: discord.Interaction):
        """跳過歌曲"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or not player.playing:
            await interaction.response.send_message("❌ 目前沒有正在播放的歌曲！", ephemeral=True)
            return

        await player.skip()
        await interaction.response.send_message("⏭️ 已跳過目前的歌曲")

    @app_commands.command(name="音量", description="調整播放音量")
    @app_commands.describe(音量="音量大小 (0-100)")
    async def volume(self, interaction: discord.Interaction, 音量: int):
        """調整音量"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 我還沒有加入任何語音頻道！", ephemeral=True)
            return

        if 音量 < 0 or 音量 > 100:
            await interaction.response.send_message("❌ 音量必須在 0-100 之間！", ephemeral=True)
            return

        await player.set_volume(音量)
        await interaction.response.send_message(f"🔊 音量已調整為 {音量}%")

    @app_commands.command(name="隊列", description="顯示播放隊列")
    async def queue(self, interaction: discord.Interaction):
        """顯示隊列"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 我還沒有加入任何語音頻道！", ephemeral=True)
            return

        if player.queue.is_empty:
            await interaction.response.send_message("📝 隊列是空的！")
            return

        embed = discord.Embed(
            title="📝 播放隊列",
            description=f"隊列中有 {player.queue.count} 首歌曲",
            color=discord.Color.blue()
        )

        # 顯示前 10 首歌曲
        queue_list = []
        for i, track in enumerate(list(player.queue)[:10], 1):
            duration = str(timedelta(milliseconds=track.length)) if track.length else "未知"
            queue_list.append(f"`{i}.` **{track.title}** ({duration})")

        embed.description = "\n".join(queue_list)
        
        if player.queue.count > 10:
            embed.set_footer(text=f"還有 {player.queue.count - 10} 首歌曲...")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="正在播放", description="顯示目前播放的歌曲")
    async def nowplaying(self, interaction: discord.Interaction):
        """顯示正在播放的歌曲"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player or not player.playing:
            await interaction.response.send_message("❌ 目前沒有正在播放的歌曲！", ephemeral=True)
            return

        track = player.current
        
        embed = discord.Embed(
            title="🎵 正在播放",
            description=f"**{track.title}**",
            color=discord.Color.green()
        )
        
        if track.author:
            embed.add_field(name="作者", value=track.author, inline=True)
        if track.length:
            duration = str(timedelta(milliseconds=track.length))
            position = str(timedelta(milliseconds=player.position))
            embed.add_field(name="進度", value=f"{position} / {duration}", inline=True)
        
        embed.add_field(name="音量", value=f"{player.volume}%", inline=True)
        
        if track.uri:
            embed.add_field(name="連結", value=f"[點擊這裡]({track.uri})", inline=False)
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="循環", description="設定循環模式")
    @app_commands.describe(模式="循環模式 (關閉/單曲/隊列)")
    @app_commands.choices(模式=[
        app_commands.Choice(name="關閉", value=0),
        app_commands.Choice(name="單曲循環", value=1),
        app_commands.Choice(name="隊列循環", value=2)
    ])
    async def loop(self, interaction: discord.Interaction, 模式: int):
        """設定循環模式"""
        player: wavelink.Player = cast(wavelink.Player, interaction.guild.voice_client)
        
        if not player:
            await interaction.response.send_message("❌ 我還沒有加入任何語音頻道！", ephemeral=True)
            return

        if 模式 == 0:
            player.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("🔁 已關閉循環")
        elif 模式 == 1:
            player.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("🔂 已開啟單曲循環")
        elif 模式 == 2:
            player.queue.mode = wavelink.QueueMode.loop_all
            await interaction.response.send_message("🔁 已開啟隊列循環")

async def setup(bot):
    await bot.add_cog(Music(bot))
