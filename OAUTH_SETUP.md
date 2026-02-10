# Discord OAuth2 設定指南

## 如何獲取 Discord Client Secret

1. **前往 Discord Developer Portal**
   - 訪問：https://discord.com/developers/applications
   - 使用您的 Discord 帳號登入

2. **選擇您的應用程式**
   - 點擊您的機器人應用程式

3. **進入 OAuth2 設定**
   - 在左側選單點擊「OAuth2」→「General」

4. **獲取 Client Secret**
   - 找到「CLIENT SECRET」欄位
   - 點擊「Copy」複製您的 Client Secret
   - **重要：請妥善保管，不要公開分享**

5. **設定重定向 URI**
   - 在「Redirects」區域
   - 添加：`http://localhost:8080/callback`
   - 如果部署到伺服器，也添加：`https://your-domain.com/callback`
   - 點擊「Save Changes」

6. **更新 .env 文件**
   - 打開專案根目錄的 `.env` 文件
   - 將複製的 Client Secret 貼到對應位置：
   ```
   DISCORD_CLIENT_SECRET=這裡貼上你的_client_secret
   ```

7. **（可選）OAuth2 URL Generator**
   - 在「URL Generator」中可以看到授權範圍
   - 確保勾選：`identify` 和 `guilds`

## 完整的 .env 配置範例

```env
DISCORD_TOKEN=你的機器人token
LOG_CHANNEL_ID=日誌頻道ID
WEB_PORT=8080

# Discord OAuth2 設定
DISCORD_CLIENT_ID=1470688452784820327
DISCORD_CLIENT_SECRET=你的_client_secret
DISCORD_REDIRECT_URI=http://localhost:8080/callback
```

## 測試登入功能

1. 啟動機器人：`python bot.py`
2. 打開瀏覽器訪問：`http://localhost:8080`
3. 點擊「使用 Discord 登入」
4. 授權後將自動跳轉到控制台

## 常見問題

**Q: 為什麼登入後顯示錯誤？**
A: 請檢查：
- Client Secret 是否正確
- 重定向 URI 是否完全匹配（包括 http/https 和 port）
- 機器人是否正在運行

**Q: 如何部署到公網？**
A: 修改 `.env` 中的 `DISCORD_REDIRECT_URI` 為您的域名：
```
DISCORD_REDIRECT_URI=https://your-domain.com/callback
```

**Q: 安全性問題？**
A: 
- 永遠不要公開 Client Secret
- 使用 HTTPS（生產環境）
- 定期更換 Client Secret（如果洩露）

## 需要幫助？

如有問題請查看 Discord 官方文檔：
https://discord.com/developers/docs/topics/oauth2
