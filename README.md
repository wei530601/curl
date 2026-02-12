# curl 源代碼

这是一個使用Python编写的Discord機器人，支援Slash Commands和Cogs模組化結構。

## 功能特點

- ✅ 使用Discord.py 2.0+ 
- ✅ 支援Slash Commands (斜杠指令)
- ✅ 模組化Cogs結構
- ✅ 自動載入所有cogs
- ✅ 環境變數配置
- ✅ 自動日誌記錄系統
- ✅ 伺服器資訊統計
- ✅ 實用工具集合
- ✅ 等級經驗系統
- ✅ 網頁後台控制台（包含警告和成就管理）
- ✅ 自定義命令系統
- ✅ 臨時語音頻道系統
- ✅ 個人資料卡片系統
- ✅ 成就系統（40+ 成就）
- ✅ 警告系統（自動處罰）

## 已包含的Cogs

### 1. General (一般指令) - `/一般`
- `/一般 延遲檢查` - 檢查機器人延遲
- `/一般 打招呼` - 打招呼
- `/一般 查看用戶資訊` - 查看用戶資訊

### 2. Moderation (管理指令) - `/管理`
**基礎管理：**
- `/管理 踢出用戶` - 踢出用戶
- `/管理 封鎖用戶` - 封鎖用戶
- `/管理 清除訊息` - 清除訊息

**⚠️ 警告系統：**
- `/管理 警告 [用戶] [理由]` - 警告用戶
- `/管理 取消警告 [用戶]` - 取消最近一次警告
- `/管理 警告記錄 [用戶]` - 查看警告歷史
- `/管理 清除警告 [用戶]` - 清除所有警告（需要管理員權限）

**自動處罰規則：**
- 3次警告 → 自動踢出伺服器
- 5次警告 → 自動封禁

### 3. Fun (娛樂指令) - `/娛樂`
- `/娛樂 投擲骰子` - 投擲骰子
- `/娛樂 擲硬幣` - 擲硬幣
- `/娛樂 魔法8球` - 魔法8球
- `/娛樂 幫你選擇` - 帮你做選擇

### 4. Server Info (伺服器資訊) - `/伺服器`
- `/伺服器 資訊` - 查看伺服器詳細資訊
- `/伺服器 圖標` - 查看伺服器圖標
- `/伺服器 成員統計` - 查看成員詳細統計和在线状态分布
- `/伺服器 角色列表` - 查看所有角色

### 5. Utilities (實用工具集合) - `/工具集合`
- `/工具集合 頭像` - 查看用戶頭像
- `/工具集合 計算器` - 计算数学表达式
- `/工具集合 倒數計時` - 創建倒數計時
- `/工具集合 投票` - 創建投票（支援最多5個選項）
- `/工具集合 提醒我` - 設定定时提醒
- `/工具集合 縮短文字` - 缩短长文本
- `/工具集合 隨機數` - 生成指定範圍的隨機數

### 6. Leveling (等級系統) - `/等級`
- `/等級 查看` - 查看自己或他人的等級
- `/等級 排行榜` - 查看伺服器等級排行榜（前10名）
- `/等級 重置` - 重置用戶等級（需要管理员權限）
- **自動功能**: 發送訊息獲得經驗值，升級时自動通知

### 7. Logging System (日誌系統)
- 自動記錄所有指令使用
- 彩色Embed格式，根據指令類型顯示不同顏色
- 需要在 `.env` 中配置日誌頻道ID

### 8. Custom Commands (自定義命令系統) - `/自定義`
- `/自定義 添加` - 添加自定義文字回覆命令
- `/自定義 刪除` - 刪除自定義命令
- `/自定義 編輯` - 編輯自定義命令內容
- `/自定義 列表` - 查看所有自定義命令
- **使用方式**: 用 `!命令名稱` 觸發自定義命令
- **網頁管理**: 可在網頁控制台直接創建和管理命令

### 9. Temp Voice (臨時語音頻道系統) - `/臨時語音`
- `/臨時語音 設定` - 設定觸發頻道和分類
- `/臨時語音 停用` - 停用系統
- `/臨時語音 狀態` - 查看系統狀態
- `/臨時語音 限制人數` - 設定頻道人數限制
- `/臨時語音 重命名` - 重命名你的臨時頻道
- **自動功能**: 用戶加入觸發頻道自動創建私人語音室，離開後自動刪除
- **網頁管理**: 可在網頁控制台配置觸發頻道和命名格式

### 10. Profile (個人資料卡片系統) - `/個人資料`
- `/個人資料 查看` - 查看自己或他人的個人資料卡片
- `/個人資料 設定簡介` - 設定個人簡介（最多100字）
- `/個人資料 設定標題` - 設定個人標題（最多30字）
- `/個人資料 設定顏色` - 自定義資料卡顏色（十六進位）
- `/個人資料 清除` - 清除所有自定義設定
- **顯示內容**: 等級、經驗、排名、遊戲統計、成就數量、活躍度等
- **自定義**: 可設定個人簡介、標題和卡片顏色

### 11. Achievements (成就系統) - `/成就`
- `/成就 列表` - 查看所有可用成就及解鎖狀態
- `/成就 我的成就` - 查看已解鎖的成就列表
- `/成就 進度` - 查看各類成就的進度統計
- **成就類型**: 訊息、等級、遊戲、簽到、特殊成就
- **稀有度**: 普通、稀有、史詩、傳奇
- **自動解鎖**: 達成條件後自動解鎖成就

## 安裝步骤

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 配置環境變數
複製 `.env.example` 为 `.env`：和日誌頻道ID：
```
DISCORD_TOKEN=你的機器人token
LOG_CHANNEL_ID=日誌頻道的ID（可选）
```

**獲取頻道ID：**
1. 在Discord中啟用開發者模式（設定 > 高级 > 開發者模式）
2. 右键点击要用作日誌的頻道
3. 点击"複製頻道ID"
4. 粘贴到 `.env` 檔案中

然后编辑 `.env` 檔案，填入你的Discord Bot Token：
```
DISCORD_TOKEN=你的機器人token
```

### 3. 獲取Discord Bot Token

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 創建新應用或選擇現有應用
3. 在左側選單選擇 "Bot"
4. 点击 "Add Bot" (如果还没有)
5. 複製Token
6. 在 "Privileged Gateway Intents" 中啟用：
   - **MESSAGE CONTENT INTENT** - 讀取訊息內容
   - **SERVER MEMBERS INTENT** - 獲取成員列表
   - **PRESENCE INTENT** - 獲取成員在線狀態（顯示正確的在線/離線統計）

### 4. 邀請機器人到伺服器

1. 在Developer Portal中選擇 "OAuth2" > "URL Generator"
2. 選擇scope:
   - `bot`
   - `applications.commands`
3. 選擇Bot Permissions (根據需要):
   - Send Messages
   - Manage Messages
   - Kick Members
   - Ban Members
   - Embed Links
   等等
4. 複製生成的URL并在浏览器中打开，選擇伺服器邀請機器人

### 5. 運行機器人
```bash
python bot.py
```

機器人啟動後會自動：
- 載入所有Cogs模組
- 同步Slash指令
- 啟動網頁後台控制台（預設端口：8080）

**訪問網頁控制台**：
- 本地訪問：http://localhost:8080
- 網路訪問：http://你的IP:8080

**網頁管理功能**：
- 📊 實時統計數據：成員數、頻道數、角色數等
- ⭐ 等級系統：查看排行榜和用戶等級
- 📅 簽到系統：簽到統計和排行
- 👋 歡迎系統：配置歡迎/離開訊息
- 🎂 生日系統：查看生日列表
- 🎮 遊戲系統：遊戲統計和排行
- 📈 活躍度分析：服務器活躍度數據
- 📝 自定義命令：創建和管理自定義命令
- 🎤 臨時語音：配置臨時語音頻道
- ⚠️ 警告系統：查看和管理用戶警告記錄
- 🏆 成就系統：查看用戶成就解鎖情況

**終端命令控制**：
機器人運行時，可直接在終端輸入以下命令進行控制：
- `restart` 或 `重啟` - 重新啟動機器人
- `stop` 或 `關閉` - 安全關閉機器人
- `status` 或 `狀態` - 顯示機器人當前狀態
- `help` 或 `幫助` - 顯示終端命令幫助

**自訂網頁端口**（可選）：
在 `.env` 檔案中添加：
```
WEB_PORT=8080
```

## 添加新的Cog

在 `cogs/` 資料夾中創建新的Python檔案，例如 `cogs/mycog.py`:

```python
import discord
from discord import app_commands
from discord.ext import commands

class MyCog(commands.Cog):
    """我的自訂Cog"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="mycommand", description="我的指令描述")
    async def mycommand(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'📦 {self.__class__.__name__} cog已載入')

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

機器人会自動載入所有在 `cogs/` 資料夾中的Python檔案。

## 專案結構

```
.
├── bot.py              # 主程式檔案
├── .env                # 環境變數 (需要創建)
├── .env.example        # 環境變數示例
├── requirements.txt    # Python依賴
├── README.md          # 說明文档
├── levels.json        # 等級數據 (自動生成)
├── .gitignore         # Git忽略檔案
├── web/               # 網頁控制台
│   ├── server.py      # Web伺服器
│   └── index.html     # 控制台首頁
└── cogs/              # Cogs資料夾
    ├── general.py        # 一般指令
    ├── moderation.py     # 管理指令
    ├── fun.py            # 娛樂指令
    ├── serverinfo.py     # 伺服器資訊統計
    ├── utilities.py      # 實用工具集合
    ├── leveling.py       # 等級系統
    └── logging_system.py # 日誌系統
```

## 等級系統說明

等級系統会自動追蹤用戶的活躍度：
- 每發送一則訊息獲得 15-25 随机經驗值
- 60秒冷卻時間防止刷經驗
- 升級时自動發送通知
- 數據存儲在 `levels.json` 檔案中
- 每個伺服器的數據獨立

**經驗公式**: 
- 等級1→2: 100 XP
- 等級2→3: 150 XP
- 等級N→N+1: 100 + (N-1) × 50 XP

## 注意事項

- 確保機器人有足夠的權限執行指令
- Slash commands需要一些時間同步（最多1小时）
- 首次運行时会自動同步所有slash commands
- 不要將 `.env` 檔案提交到Git倉庫
- `levels.json` 会自動創建，建議定期備份

## 故障排除

### Slash commands没有顯示
- 確保bot有 `applications.commands` scope
- 等待1小时让Discord同步指令
- 檢查機器人是否在伺服器中

### 權限錯誤
- 確保在Developer Portal中啟用了必要的Intents
- 檢查機器人在伺服器中的角色權限

## 許可證

MIT License
