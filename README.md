## youtube-downloader使用說明
---
### 安裝
需要python3.10以上
相關依賴套件已包含在虛擬環境中
Windows系統請使用./venv/Script/activate.bat
Linux系統請使用./venv/Script/activate
### 設定檔案說明
config.json內可設定以下參數
```
"paths": {								// {channel_name}表示頻道名稱
		"videos": "{channel_name}/videos",	// 影片存放路徑
		"shorts": "{channel_name}/shorts",	// 短影片存放路徑
		"live": "{channel_name}/live",		// 直播存放路徑
		"posts": "{channel_name}/posts"		// 未實作
	  }
	"channels_text": "channels.txt"			// 欲下載的頻道網址 各頻道以換行區分
	"max_entries": 10,						// 每次下載的最新影片數量 輸入-1則不限制下載數量
	"sleep_seconds": 900,					// 新影片檢查間隔(秒)
	"download": {				
		"videos": true,						// 是否下載影片
		"shorts": true,						// 是否下載短影片
		"live": true						// 是否下載直播
	}
}
##
```# 執行
於專案根目錄開啟終端機並輸入指令
(Windows系統)
```bash
venv\Scripts\activate.bat
venv\Scripts\python.exe main.py
```
(Linux系統)
```bash
venv/Scripts/python.exe main.py
```
