# Lavalink 音樂系統設置指南

## 簡介
Lavalink 是一個獨立的音樂播放伺服器，用於為 Discord 機器人提供高質量的音樂播放功能。

## 快速開始

### 方法 1：使用公共 Lavalink 伺服器（推薦新手）
使用現成的公共 Lavalink 服務器，無需自己架設。

在 `.env` 文件中添加：
```env
LAVALINK_HOST=lava.link
LAVALINK_PORT=80
LAVALINK_PASSWORD=youshallnotpass
```

### 方法 2：本地運行 Lavalink

#### 前置要求
- Java 17 或更高版本

#### 步驟

1. **下載 Lavalink**
   訪問 https://github.com/lavalink-devs/Lavalink/releases
   下載最新的 `Lavalink.jar`

2. **創建配置文件**
   在同一目錄創建 `application.yml`：
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
       filters:
         volume: true
         equalizer: true
         karaoke: true
         timescale: true
         tremolo: true
         vibrato: true
         distortion: true
         rotation: true
         channelMix: true
         lowPass: true
       bufferDurationMs: 400
       frameBufferDurationMs: 5000
       opusEncodingQuality: 10
       resamplingQuality: LOW
       trackStuckThresholdMs: 10000
       useSeekGhosting: true
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

3. **啟動 Lavalink**
   ```bash
   java -jar Lavalink.jar
   ```

4. **配置 .env**
   ```env
   LAVALINK_HOST=localhost
   LAVALINK_PORT=2333
   LAVALINK_PASSWORD=youshallnotpass
   ```

### 方法 3：使用 Docker（推薦）

1. **創建 docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     lavalink:
       image: fredboat/lavalink:latest
       container_name: lavalink
       restart: unless-stopped
       environment:
         - _JAVA_OPTIONS=-Xmx2G
         - SERVER_PORT=2333
         - LAVALINK_SERVER_PASSWORD=youshallnotpass
       volumes:
         - ./application.yml:/opt/Lavalink/application.yml
       ports:
         - "2333:2333"
       networks:
         - lavalink

   networks:
     lavalink:
       name: lavalink
   ```

2. **啟動容器**
   ```bash
   docker-compose up -d
   ```

3. **配置 .env**
   ```env
   LAVALINK_HOST=localhost
   LAVALINK_PORT=2333
   LAVALINK_PASSWORD=youshallnotpass
   ```

## 可用的音樂命令

啟動機器人後，可以使用以下命令：

- `/加入` - 讓機器人加入你的語音頻道
- `/離開` - 讓機器人離開語音頻道
- `/播放 <歌曲名稱或連結>` - 播放音樂
- `/暫停` - 暫停播放
- `/繼續` - 繼續播放
- `/停止` - 停止播放並清空隊列
- `/跳過` - 跳過當前歌曲
- `/音量 <0-100>` - 調整音量
- `/隊列` - 顯示播放隊列
- `/正在播放` - 顯示當前播放的歌曲
- `/循環 <模式>` - 設定循環模式（關閉/單曲/隊列）

## 支持的音樂來源

- YouTube
- YouTube Music
- SoundCloud
- Bandcamp
- Twitch
- Vimeo
- HTTP 音頻流

## 常見問題

### Q: Lavalink 連接失敗怎麼辦？
A: 
1. 確認 Lavalink 服務器正在運行
2. 檢查 .env 中的配置是否正確
3. 確認防火牆沒有阻擋端口
4. 查看 Lavalink 的日誌輸出

### Q: 播放 YouTube 視頻時出錯？
A: YouTube 可能會限制某些請求。建議：
1. 使用最新版本的 Lavalink
2. 考慮使用公共 Lavalink 服務器
3. 配置 YouTube API（可選）

### Q: 機器人沒有聲音？
A: 
1. 確認機器人有連接到語音頻道的權限
2. 檢查音量設置（使用 `/音量` 命令）
3. 確認機器人在你的伺服器有 "連接" 和 "說話" 權限

## 公共 Lavalink 服務器列表

以下是一些可用的公共 Lavalink 服務器（免費）：

```
Host: lava.link
Port: 80
Password: youshallnotpass

Host: lavalink.oops.wtf
Port: 443
Password: www.freelavalink.ga

Host: lavalink.devamop.in
Port: 443
Password: DevamOP
```

⚠️ 注意：公共服務器可能不穩定或有使用限制，生產環境建議自己架設。

## 進階配置

### YouTube Cookie（解決地區限制）
可以在 `application.yml` 中配置 YouTube cookies 來解決某些地區限制問題。

### 自定義過濾器
Lavalink 支持多種音頻過濾器，如均衡器、顫音、失真等。

### 性能調優
- 調整 `bufferDurationMs` 來優化延遲
- 調整 `opusEncodingQuality` 來平衡質量和性能
- 為高流量分配更多內存（`-Xmx` 參數）

## 支持與幫助

- Lavalink GitHub: https://github.com/lavalink-devs/Lavalink
- Discord.py 文檔: https://discordpy.readthedocs.io/
- Wavelink 文檔: https://wavelink.readthedocs.io/

## 許可證

本音樂系統使用 Lavalink 和 Wavelink，均為開源項目。
