抓取[公開資訊觀測站](https://mops.twse.com.tw/mops/web/t51sb03)之海外存託憑證的資料，市場別為：上市、上櫃、興櫃、公開發行，年度為：113\
點選查詢後，再點選詳細資料，此時跳出新視窗，爬取海外存託憑證之相關資料，最後輸出成excel格式。\
採用Google Chrome瀏覽器遇到無法跳轉頁面的問題，故使用Firefox瀏覽器，但需下載相對應版本的[geckodriver.exe](https://github.com/mozilla/geckodriver/releases)，將下載的執行檔與.py檔放同個資料夾(省去指定執行檔路徑的麻煩)，Firefox瀏覽器預設路徑為C:\Program Files\Mozilla Firefox\firefox.exe(若有指定其他路徑需更改mops_twse.py中的第12行)，最後在編譯器上直接進行即可。\
![image](https://github.com/rebornlife0218/Web_Crawler/assets/162146061/ae8c8d6e-2efd-4ec9-b012-82371da99100)
![image](https://github.com/rebornlife0218/Web_Crawler/assets/162146061/bf524107-10f9-4683-ba36-fcb51939101e)
