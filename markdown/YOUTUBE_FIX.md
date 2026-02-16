# Lavalink YouTube 問題修復指南

## 常見錯誤

### ❌ "Something went wrong while looking up the track"

這是最常見的 YouTube 播放錯誤，通常由以下原因造成：

1. **YouTube 封鎖了 Lavalink 的請求**
2. **Lavalink 版本過舊**
3. **沒有配置 YouTube Rotation**

---

## 解決方案

### 方案 1：更新 Lavalink（推薦）

下載最新版本的 Lavalink，支持更好的 YouTube 處理：

**下載地址：**
https://github.com/lavalink-devs/Lavalink/releases/latest

下載 `Lavalink.jar` 並替換舊版本。

---

### 方案 2：配置 YouTube Plugin（最有效）

使用 YouTube Source Plugin 來改善 YouTube 支持。

#### 步驟 1：修改 `application.yml`

```yaml
lavalink:
  plugins:
    - dependency: "dev.lavalink.youtube:youtube-plugin:1.5.2"
      repository: "https://maven.lavalink.dev/releases"
  
  server:
    password: "youshallnotpass"
    sources:
      youtube: false  # 關閉原生 YouTube，使用 plugin
    
    # 其他配置...

plugins:
  youtube:
    enabled: true
    allowSearch: true
    allowDirectVideoIds: true
    allowDirectPlaylistIds: true
    # 使用 OAuth 來避免封鎖（可選）
    clients:
      - MUSIC
      - ANDROID_TESTSUITE
      - WEB
      - TVHTML5EMBEDDED
```

#### 步驟 2：重啟 Lavalink

```bash
java -jar Lavalink.jar
```

Lavalink 會自動下載並安裝 YouTube plugin。

---

### 方案 3：使用替代音樂源

如果 YouTube 持續無法使用，可以改用其他音樂源：

#### SoundCloud
```
/播放 https://soundcloud.com/artist/track
```

#### Bandcamp
```
/播放 https://artist.bandcamp.com/track/song
```

#### 直接音頻連結
```
/播放 https://example.com/audio.mp3
```

---

### 方案 4：配置 YouTube OAuth（進階）

為 Lavalink 配置 YouTube OAuth 可以避免大部分封鎖問題。

#### 步驟 1：獲取 OAuth Refresh Token

1. 訪問：https://developers.google.com/oauthplayground
2. 在左側選擇 "YouTube Data API v3"
3. 選擇 `https://www.googleapis.com/auth/youtube`
4. 點擊 "Authorize APIs"
5. 登入你的 Google 帳號
6. 點擊 "Exchange authorization code for tokens"
7. 複製 "Refresh token"

#### 步驟 2：修改 `application.yml`

```yaml
plugins:
  youtube:
    enabled: true
    oauth:
      enabled: true
      refreshToken: "YOUR_REFRESH_TOKEN_HERE"
      clientId: "YOUR_CLIENT_ID"
      clientSecret: "YOUR_CLIENT_SECRET"
```

---

### 方案 5：使用 IPv6（如果可用）

YouTube 對 IPv6 的封鎖較少。

在 `application.yml` 中添加：

```yaml
server:
  address: "::"  # 使用 IPv6
```

---

### 方案 6：使用代理

如果你的 IP 被封鎖，可以配置代理。

在 `application.yml` 中添加：

```yaml
lavalink:
  server:
    httpConfig:
      proxyHost: "proxy.example.com"
      proxyPort: 8080
      proxyUser: "username"  # 可選
      proxyPassword: "password"  # 可選
```

---

## 完整的推薦配置

以下是一個完整的 `application.yml` 配置範例：

```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  plugins:
    - dependency: "dev.lavalink.youtube:youtube-plugin:1.5.2"
      repository: "https://maven.lavalink.dev/releases"
  
  server:
    password: "youshallnotpass"
    sources:
      youtube: false  # 使用 plugin 代替
      bandcamp: true
      soundcloud: true
      twitch: true
      vimeo: true
      http: true
      local: false
    
    bufferDurationMs: 400
    frameBufferDurationMs: 5000
    youtubePlaylistLoadLimit: 10
    playerUpdateInterval: 5
    youtubeSearchEnabled: true
    soundcloudSearchEnabled: true
    gc-warnings: true

plugins:
  youtube:
    enabled: true
    allowSearch: true
    allowDirectVideoIds: true
    allowDirectPlaylistIds: true
    clients:
      - MUSIC
      - ANDROID_TESTSUITE
      - WEB
      - TVHTML5EMBEDDED

metrics:
  prometheus:
    enabled: false

sentry:
  dsn: ""

logging:
  file:
    path: ./logs/
  level:
    root: INFO
    lavalink: INFO
```

---

## 測試是否修復

1. **重啟 Lavalink**
   ```bash
   java -jar Lavalink.jar
   ```

2. **重啟機器人**
   ```bash
   python bot.py
   ```

3. **測試播放**
   ```
   /播放 test
   ```

---

## 如果仍然失敗

### 檢查 Lavalink 日誌

查看 Lavalink 的控制台輸出或 `./logs/` 目錄中的日誌文件，找出具體錯誤。

### 使用公共 Lavalink 服務器

如果自建服務器持續有問題，可以臨時使用公共服務器：

在 `.env` 中修改：
```env
LAVALINK_HOST=lavalink.devamop.in
LAVALINK_PORT=443
LAVALINK_PASSWORD=DevamOP
```

### 加入 Discord 支持服務器

- **Lavalink Discord**: https://discord.gg/lavalink
- **Wavelink Discord**: Search for wavelink support

---

## 其他常見問題

### Q: 播放卡頓或延遲？
A: 增加 `bufferDurationMs` 的值（建議 400-1000）

### Q: 機器人沒有聲音？
A: 
1. 檢查機器人權限（連接+說話）
2. 使用 `/音量 100` 確認音量
3. 確認你在同一個語音頻道

### Q: 無法播放某些歌曲？
A: 可能是版權限制，嘗試使用其他音樂源（SoundCloud）

---

## 推薦設置總結

| 設置 | 推薦值 | 說明 |
|------|--------|------|
| Lavalink 版本 | 最新版 | 支持更好的 YouTube 處理 |
| YouTube Plugin | 啟用 | 必須，原生 YouTube 已不穩定 |
| 替代音樂源 | SoundCloud | 作為備用 |
| Buffer | 400ms | 平衡延遲和穩定性 |

---

## 更新記錄

- 2026-02-17: 添加多源搜尋支持
- 2026-02-17: 改進錯誤處理和用戶提示
- 2026-02-16: 初始版本

需要更多幫助？請查看：
- Lavalink 文檔: https://lavalink.dev
- YouTube Plugin: https://github.com/lavalink-devs/youtube-source
