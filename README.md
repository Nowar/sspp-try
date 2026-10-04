# 投資組合調整比較（台幣）

用真實歷史價格（Yahoo Finance 還原價）比較「調整前 A／調整後 B」兩組配置，全部換算成台幣計算。
GitHub Actions 每天自動抓資料、產生網頁並發布到 GitHub Pages。

## 檔案
- `template.html`：網頁本體（版面、計算、圖表）。沒有資料時會顯示合成示範資料並出現黃色警示。
- `build_site.py`：抓 GLD、IEF、VT、0050.TW、TWD=X 的還原價，轉成月資料後寫進 `dist/index.html`。
- `.github/workflows/pages.yml`：每天台灣時間約 06:30、14:30 自動執行並部署。

## 一次性設定
1. GitHub → New repository → 名稱 `portfolio-compare` → Public → 勾 Add a README → Create。
2. Settings → Pages → Source 選 **GitHub Actions**。
3. Add file → Upload files → 上傳 `template.html`、`build_site.py` → Commit changes。
4. Add file → Create new file → 檔名輸入 `.github/workflows/pages.yml` → 貼上內容 → Commit changes。
   （用電腦可以直接把解壓後的所有檔案與 `.github` 資料夾拖進 Upload files。）
5. Actions → build-and-deploy → Run workflow。build、deploy 都綠勾就完成。
6. 網址：`https://你的帳號.github.io/portfolio-compare/`

## 日常
- 打開網址即可，資料每天自動更新；頁面底部有各標的最新價日期。
- 你的輸入只存在你自己的瀏覽器（localStorage），不會進 repo，別人打開看到的是預設值。

## 更新網頁
- 只改版面或計算：上傳新的 `template.html` 覆蓋舊檔，push 後會自動重新部署。
- 換標的：改 `build_site.py` 最上面的 `TICKERS` 與 `NAMES`（前三個為美元資產，第四個為台幣資產，最後是匯率）。

## 分割補正
- `build_site.py` 裡的 `SPLITS` 記錄已知分割（目前是 0050 於 2025-06-18 一拆四）。程式會判斷 Yahoo 是否已調整，未調整才自動校正，結果會印在 Actions 日誌。

## 疑難排解
- Actions 出現紅色叉叉：多半是 Yahoo 暫時限流，舊網頁仍在線上。進該次執行按 Re-run all jobs。
- 日誌出現「資料異常」：某標的單月漲跌超過 40%，通常是錯誤報價或分割沒調整，日誌會列出是哪個月份，暫不發布以免錯誤數字上線。
- 資料很多天沒更新：到 Actions 頁看排程是否被停用，若有提示按 Enable。
