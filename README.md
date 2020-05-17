# 104 人力銀行爬蟲專案

輸入關鍵字，根據該關鍵字，爬取 104 人力銀行中符合的職缺資料。

## Project Setup

進入專案資料夾，輸入

```
source venv/bin/activate
```

就會進入虛擬環境，進入後，輸入

```
pip3 install -r requirements.txt
```

就會安裝這個專案所需要的套件

## Run Project

輸入

```
python3 scraping.py
```

啟動後，在 console 會出現： **輸入你想要搜尋的關鍵字來找到相關工作:**

此時必須輸入你想要查詢的工作關鍵字，輸入後即會自動開始抓取資料，並將資料存放至 local 端 MongoDB。

## Notice

`/bin` 底下有兩個檔案分別為 `chromedriver` 和 `chromedriver.exe`，如果為 Windows 系統，請將 `scraping.py` 的第 183 行的 `path.join()` 的第二個參數更改成 `bin/chromedriver.exe`。
