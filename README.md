# 投資組合調整比較（台幣）

用真實歷史價格（Yahoo Finance 還原價）比較「調整前 A／調整後 B」兩組配置，全部換算成台幣計算。
GitHub Actions 每天自動抓資料、產生網頁並發布到 GitHub Pages；即時報價透過 Cloudflare Worker 代理。

網站：`https://nowar.github.io/sspp-try/`
即時報價 Worker：`https://quote.whgu.workers.dev/`

## 檔案
- `template.html`：網頁本體（版面、計算、圖表、股利、即時報價）。沒有資料時會顯示合成示範資料並出現黃色警示。
- `build_site.py`：抓各標的的還原價與匯率，轉成月資料後寫進 `dist/index.html`。
- `.github/workflows/pages.yml`：每天台灣時間約 06:30、14:30 自動執行、部署，並把價格快取存回 repo。
- `cloudflare-worker.js`：即時報價代理的程式碼（備份用；實際執行在 Cloudflare 上，GitHub 不會執行它）。

## 網頁功能
- 上方：今年年紀、A 調整前（填股數，自動用最新收盤價與匯率換成台幣）、B 調整後（目標比例，顯示要買賣的金額與股數）、歷史試算方向、再平衡方式、提領年增率。
- 配置一覽：A/B 各標的比例、依 5/25 法則需要買賣的金額、資產類別圓環（股票／單一市場股票／債券／黃金）。
- 分頁：股利｜即時｜未來模擬｜歷史回測。
- 所有輸入只存在自己手機的瀏覽器（localStorage），不會進 repo，別人打開看到的是預設值。

## GitHub 一次性設定
1. GitHub → New repository → Public → 勾 Add a README → Create。
2. Settings → Pages → Source 選 **GitHub Actions**。
3. Add file → Upload files → 上傳 `template.html`、`build_site.py`、`README.md`、`cloudflare-worker.js` → Commit changes。
4. Add file → Create new file → 檔名輸入 `.github/workflows/pages.yml` → 貼上內容 → Commit changes。
   （用電腦可以直接把解壓後的所有檔案與 `.github` 資料夾拖進 Upload files。）
5. Actions → build-and-deploy → Run workflow。build、deploy 都綠勾就完成。

## 更新網頁
- 只改版面或計算：上傳新的 `template.html` 覆蓋舊檔，Commit 後會自動重新部署。
- 換標的：改 `build_site.py` 最上面的 `TICKERS` 與 `NAMES`（代號 .TW 結尾為台幣資產，其他為美元資產，最後一個必須是匯率）。第一次會自動整段重抓。
- 改 workflow：repo 裡打開 `.github/workflows/pages.yml` → 鉛筆圖示 → 全選貼上新內容 → Commit。

## 即時報價（Cloudflare Worker）
瀏覽器不能直接向 Yahoo 要報價（CORS 限制），所以在 Cloudflare 放一個小程式當中間人：網頁問 Worker，Worker 去 Yahoo 抓，再回傳。

### 第一次設定
1. 打開 `dash.cloudflare.com`，用 Email 註冊（免費方案，不需信用卡、不需網域），完成信箱驗證。
2. 左側選單「Workers & Pages」（可能在「Compute (Workers)」底下）→「Create」→「Create Worker」或「Start with Hello World!」。
3. 名稱填 `quote` → 「Deploy」。第一次會要求設定 `workers.dev` 子網域，之後網址就是 `https://quote.<子網域>.workers.dev`。
4. 按「Edit code」→ 編輯器全選刪除 → 貼上 `cloudflare-worker.js` 全部內容 →「Deploy」。
5. 測試：瀏覽器打開 `https://quote.<子網域>.workers.dev/?s=VT,0050.TW,TWD=X`，看到含 `"price"` 的 JSON 就成功。
6. 如果網址跟 `https://quote.whgu.workers.dev/` 不同，要改 `template.html` 裡的 `QURL` 那一行。

### 更新 Worker 程式
Cloudflare 登入 → Workers & Pages → 點 `quote` →「Edit code」→ 全選刪除 → 貼上新的 `cloudflare-worker.js` →「Deploy」。

### 注意
- `cloudflare-worker.js` 最上面的 `ALLOW` 只放行 `https://nowar.github.io`；網站網址改了要一起改並重新 Deploy，否則即時分頁會抓不到。
- 免費方案每天 10 萬次請求；即時分頁停留時每 5 分鐘自動更新一次，切到別的分頁就停止。
- 美股報價接近即時，台股可能延遲數分鐘到 20 分鐘；灰底列表示目前正在盤中（依 Yahoo 回傳的正規交易時段判斷）。
- 偶爾 Yahoo 會限制 Cloudflare 的請求（某檔顯示「Yahoo 回應 429」），稍後按「更新」通常就好。
- Cloudflare 介面偶爾改版，按鈕名稱可能略有不同，找意思相近的即可。

## 本地資料快取
- 每日價格存在 `data/prices.csv`、`data/vt_raw.csv`，每次執行後自動 commit 回 repo。
- 平常只抓「快取最後一天前 20 天」起的新資料，用重疊的日子對齊 Yahoo 的還原基準，再接回舊資料。
- 每 30 天自動整段重抓一次；想立刻重抓：Actions → build-and-deploy → Run workflow → 勾「整段重抓」。
- Yahoo 暫時抓不到時會沿用快取繼續產生網頁，頁面底部的最新價日期會停在快取的最後一天。

## 資料檢查與補正
- 分割補正：自動找出相鄰交易日價格差 2～10 倍、且之後一直維持的斷點，把斷點之前的價格校正到同一基準。
- 單月漲跌超過 40% 會中止發布；`CHECK_SKIP` 裡的標的（目前 2454）只提示不中止。
- `PROXY`：上市太短的標的上市前用替代標的（009826 上市前用 VT 換台幣、每年扣 1.1%），網頁底部會註明。
- VT 依每次實際配息扣 30% 股息預扣稅；其他標的未計稅。

## 股利雲端同步（通關密語）
- 股利紀錄加密後存在 repo 的 `data/vault.json`（AES-GCM，金鑰由通關密語經 PBKDF2 60 萬次產生），裡面也包含加密過的 GitHub token，任何裝置只要輸入通關密語就能讀寫。
- repo 是公開的，安全性完全取決於通關密語強度：請用 16 個字元以上、不常見的詞組合。忘記通關密語就救不回資料，請偶爾匯出 CSV 備份。
- token 建立：GitHub 頭像 → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token；Repository access 只選這個 repo；Permissions → Contents 設為 Read and write。
- token 過期時：登入後在「更換 GitHub token」貼上新的即可。
- 修改 `data/vault.json` 不會觸發重新部署。

## 疑難排解
- Actions 紅色叉叉：多半是 Yahoo 暫時限流，舊網頁仍在線上。進該次執行按 Re-run all jobs。
- 日誌出現「資料異常」：某標的單月漲跌超過 40%，日誌會列出月份與價格；確認是真實行情的話把代號加進 `CHECK_SKIP`。
- 日誌出現 `database is locked`：yfinance 多執行緒衝突，程式已改成單執行緒並只重抓失敗的代號。
- deploy 一直顯示 `updating_pages`：通常是 GitHub Pages 本身的問題。先看 `githubstatus.com`；取消後重跑；還不行就到 Settings → Pages 把 Source 暫時改成「Deploy from a branch」再改回「GitHub Actions」。workflow 已設定 15 分鐘逾時，不會無限轉下去。
- 資料很多天沒更新：到 Actions 頁看排程是否被停用，若有提示按 Enable。
- 即時分頁抓不到：確認 Worker 網址能在瀏覽器打開、`ALLOW` 與網站網址一致；claude.ai 預覽頁本來就抓不到，請在 GitHub 網址測試。
