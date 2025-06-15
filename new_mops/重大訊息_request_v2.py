import requests
import time
import pandas as pd
import calendar
from selenium import webdriver
from datetime import datetime
import json
import os
import random

# 動態獲取 Cookie（含快取）
def get_cookies():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get("https://mops.twse.com.tw/mops/#/web/t05st02")
    time.sleep(2)
    cookies = driver.get_cookies()
    requests_cookies = {cookie["name"]: cookie["value"] for cookie in cookies}
    driver.quit()
    return requests_cookies

def get_cookies_cached():
    cache_path = "mops_cookie.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    cookies = get_cookies()
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cookies, f)
    return cookies

# 日期模式處理
def get_date_range(mode, start_year=None):
    today = datetime.today()
    if mode == "today":
        return [(today.year - 1911, today.month, today.day)]
    elif mode == "from_year" and start_year is not None:
        dates = []
        for year in range(start_year, today.year - 1911 + 1):
            for month in range(1, 13):
                if year == today.year - 1911 and month > today.month:
                    break
                days_in_month = calendar.monthrange(year + 1911, month)[1]
                for day in range(1, days_in_month + 1):
                    if year == today.year - 1911 and month == today.month and day > today.day:
                        break
                    dates.append((year, month, day))
        return dates
    else:
        raise ValueError("Invalid mode or missing start_year")

# 爬蟲
def scrape_mops_data(mode="today", start_year=None):
    start_time = time.time()
    all_data = []
    error_log = []
    base_url = "https://mops.twse.com.tw/mops/api/t05st02"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    cookies = get_cookies_cached()
    date_range = get_date_range(mode, start_year)

    for year, month, day in date_range:
        retry = 0
        max_retry = 3
        print(f"\n📅 正在爬取：{year}-{month:02d}-{day:02d}")

        while retry < max_retry:
            stage_times = {}
            daily_data = []

            try:
                # 發送 POST 請求
                stage_start = time.time()
                payload = {
                    "year": str(year),
                    "month": str(month),
                    "day": str(day).zfill(2),
                    "TYPEK": "all",
                    "encodeURIComponent": 1
                }
                response = requests.post(
                    base_url,
                    json=payload,
                    headers=headers,
                    cookies=cookies,
                    timeout=20
                )
                stage_times["API 請求"] = time.time() - stage_start
                
                # 處理響應
                if response.status_code == 200:
                    try:
                        stage_start = time.time()
                        data = response.json()
                        if data.get("code") != 200:
                            raise ValueError(f"API 回傳 code 錯誤：{data.get('code')}")

                        for item in data.get("result", {}).get("data", []):
                            if len(item) >= 5 and "董事會決議發行" in item[4] and "轉換公司債" in item[4]:
                                daily_data.append({
                                    "發言日期": item[0],
                                    "發言時間": item[1],
                                    "公司代號": item[2],
                                    "公司名稱": item[3],
                                    "主旨": item[4]
                                })
                        stage_times["JSON 處理"] = time.time() - stage_start
                        print("✅ 當日爬取筆數：", len(daily_data))
                        all_data.extend(daily_data)

                        if not daily_data:
                            print("❌ 無符合資料")
                        break  # 無論有無資料皆跳出 retry

                    except Exception as e:
                        retry += 1
                        print(f"❌ JSON 解析錯誤，重試中...：{e}")
                        time.sleep(2)
                else:
                    retry += 1
                    print(f"⚠️ HTTP 狀態碼錯誤：{response.status_code}，重試中...")
                    if response.status_code == 502:
                        print("🔁 檢測到 502 Bad Gateway，可能是伺服器暫時不可用")
                    time.sleep(random.uniform(3, 6))

            except requests.exceptions.ReadTimeout:
                print(f"❌ ReadTimeout：{year}-{month:02d}-{day:02d} => 伺服器已連線但讀取超時")
                retry += 1
                time.sleep(random.uniform(3, 6))
                if retry == max_retry:
                    error_log.append({
                        "日期": f"{year}-{month:02d}-{day:02d}",
                        "錯誤訊息": "ReadTimeout"
                    })

            except requests.exceptions.ConnectTimeout:
                print(f"❌ ConnectTimeout：{year}-{month:02d}-{day:02d} => 無法連上伺服器（連線超時）")
                retry += 1
                time.sleep(random.uniform(3, 6))
                if retry == max_retry:
                    error_log.append({
                        "日期": f"{year}-{month:02d}-{day:02d}",
                        "錯誤訊息": "ConnectTimeout"
                    })

            except requests.exceptions.ConnectionError as ce:
                print(f"❌ ConnectionError：{year}-{month:02d}-{day:02d} => {ce}")
                retry += 1
                time.sleep(random.uniform(3, 6))
                if retry == max_retry:
                    error_log.append({
                        "日期": f"{year}-{month:02d}-{day:02d}",
                        "錯誤訊息": f"ConnectionError: {ce}"
                    })

            except Exception as e:
                print(f"❌ 其他錯誤：{year}-{month:02d}-{day:02d} => {e}")
                retry += 1
                time.sleep(random.uniform(3, 6))
                if retry == max_retry:
                    error_log.append({
                        "日期": f"{year}-{month:02d}-{day:02d}",
                        "錯誤訊息": str(e)
                    })

        # 輸出階段時間
        print("各階段耗時：")
        for stage, t in stage_times.items():
            print(f"  {stage}: {t:.2f} 秒")

        time.sleep(0.5) # 反爬蟲

    if error_log:
        print("\n❗ 以下日期發生錯誤：")
        for entry in error_log:
            print(f"  📅 {entry['日期']} => ❌ {entry['錯誤訊息']}")
    else:
        print("\n✅ 所有日期皆成功爬取")

    end_time = time.time()
    print(f"\n✅ 總花費時間：{end_time - start_time:.2f} 秒，總筆數：{len(all_data)}")

    # 發言日期轉為 datetime 物件，並依主旨去除重複，保留最早日期
    df = pd.DataFrame(all_data)
    df["發言日期"] = df["發言日期"].str.replace("/", "-")
    df["發言日期"] = df["發言日期"].apply(lambda x: f"{1911 + int(x.split('-')[0])}-{x.split('-')[1]}-{x.split('-')[2]}")
    df["發言日期"] = pd.to_datetime(df["發言日期"], errors="coerce")
    df = df.sort_values("發言日期").drop_duplicates(subset="主旨", keep="first")
    df.to_csv("重大訊息.csv", index=False, encoding="utf-8-sig")
    print("✅ 資料已儲存為：重大訊息_v3.csv，總筆數：", len(df))

# Case1: 單獨爬取今天資料
# scrape_mops_data(mode="today")

# Case2: 爬取從指定年份到今天
scrape_mops_data(mode="from_year", start_year=108)