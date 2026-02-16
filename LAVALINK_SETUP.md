# Lavalink 設定指南

## 什麼是 Lavalink？

Lavalink 是一個獨立的音頻播放伺服器，它可以為 Discord 機器人提供高品質的音樂播放功能。

## 快速設置

### 方法 1：使用 Docker（推薦）

1. **安裝 Docker**
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/

2. **建立 `application.yml` 配置文件**

創建一個名為 `application.yml` 的文件：

```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    bufferDurationMs: 400
    frameBufferDurationMs: 5000
    youtubePlaylistLoadLimit: 6
    playerUpdateInterval: 5
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    gc-warnings: true

metrics:
  prometheus:
    enabled: false
    endpoint: /metrics

sentry:
  dsn: ""
  environment: ""

logging:
  file:
    path: ./logs/

  level:
    root: INFO
    lavalink: INFO

  logback:
    rollingpolicy:
      max-file-size: 1GB
      max-history: 30
```

3. **運行 Docker 容器**

```bash
docker run -d \
  --name lavalink \
  -p 2333:2333 \
  -v $(pwd)/application.yml:/opt/Lavalink/application.yml \
  --restart unless-stopped \
  fredboat/lavalink:latest
```

**Windows PowerShell:**
```powershell
docker run -d `
  --name lavalink `
  -p 2333:2333 `
  -v ${PWD}/application.yml:/opt/Lavalink/application.yml `
  --restart unless-stopped `
  fredboat/lavalink:latest
```

### 方法 2：手動安裝

1. **下載 Lavalink**
   - 前往 [Lavalink Releases](https://github.com/lavalink-devs/Lavalink/releases)
   - 下載最新版本的 `Lavalink.jar`

2. **安裝 Java**
   - 需要 Java 17 或更高版本
   - 下載：https://adoptium.net/

3. **建立配置文件**
   - 使用上面的 `application.yml` 範例

4. **啟動 Lavalink**

```bash
java -jar Lavalink.jar
```

## 配置機器人

1. **安裝依賴**

```bash
pip install -r requirements.txt
```

2. **設定環境變數**

在 `.env` 文件中添加：

```env
LAVALINK_URI=http://localhost:2333
LAVALINK_PASSWORD=youshallnotpass
```

如果使用遠程 Lavalink 伺服器，請修改：

```env
LAVALINK_URI=http://your-server-ip:2333
LAVALINK_PASSWORD=your-password
```

## 使用免費的公共 Lavalink 節點

如果你不想自己架設 Lavalink，可以使用公共節點（不推薦用於生產環境）：

```env
# 範例（請自行尋找可用的公共節點）
LAVALINK_URI=http://lavalink.example.com:2333
LAVALINK_PASSWORD=公共密碼
```

⚠️ **注意**：公共節點可能不穩定，建議自行架設。

## 音樂功能指令

啟動機器人後，你可以使用以下命令：

| 指令 | 描述 |
|------|------|
| `/播放 <歌曲名稱或URL>` | 播放音樂 |
| `/暫停` | 暫停/繼續播放 |
| `/停止` | 停止播放並離開頻道 |
| `/跳過` | 跳過當前歌曲 |
| `/隊列` | 顯示播放隊列 |
| `/當前` | 顯示當前播放的歌曲 |
| `/音量 <0-100>` | 調整音量 |
| `/清空隊列` | 清空播放隊列 |
| `/洗牌` | 隨機打亂隊列 |
| `/循環 <模式>` | 設定循環模式 |

## 支援的音源

- ✅ YouTube
- ✅ YouTube Music  
- ✅ SoundCloud
- ✅ Bandcamp
- ✅ Twitch
- ✅ Vimeo
- ✅ 直接 HTTP/HTTPS URL

## 故障排除

### Lavalink 無法連接

1. 確認 Lavalink 伺服器正在運行
2. 檢查防火牆設置（2333 端口）
3. 驗證密碼是否正確
4. 查看機器人日誌中的錯誤訊息

### 音樂無法播放

1. 確認機器人在語音頻道中
2. 檢查機器人權限（需要「連接」和「說話」權限）
3. 確認 YouTube 搜尋未被封鎖
4. 查看 Lavalink 日誌

### 查看 Lavalink 日誌

**Docker:**
```bash
docker logs lavalink
```

**手動運行:**
查看 `logs/` 目錄中的日誌文件

## 進階配置

### 啟用 Spotify 支援

需要在 `application.yml` 中添加：

```yaml
plugins:
  lavasrc:
    providers:
      - "ytsearch:\"%ISRC%\""
      - "ytsearch:%QUERY%"
    sources:
      spotify: true
    spotify:
      clientId: "your_spotify_client_id"
      clientSecret: "your_spotify_client_secret"
      countryCode: "TW"
```

## 資源

- [Lavalink GitHub](https://github.com/lavalink-devs/Lavalink)
- [Wavelink 文檔](https://wavelink.dev/)
- [Discord.py 文檔](https://discordpy.readthedocs.io/)

## 支援

如果遇到問題，請查看：
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [GitHub Issues](https://github.com/your-repo/issues)
