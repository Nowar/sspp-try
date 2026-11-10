# 投資組合調整比較（台幣）

個人用的投資組合儀表板：用真實歷史價格（Yahoo Finance 還原價）比較「調整前 A／調整後 B」兩組配置，全部換算成台幣，並記錄股利、資產變化、即時報價與負債。

- 網站：`https://nowar.github.io/sspp-try/`
- 即時報價 Worker：`https://quote.whgu.workers.dev/`
- 資料每天由 GitHub Actions 自動更新；個人資料（持股、負債、股利、變化紀錄）只存在自己的瀏覽器，登入雲端同步時加密存放。

## 檔案

| 檔案 | 用途 |
|---|---|
| `template.html` | 網頁本體（版面、計算、圖表、股利、變化、即時報價、負債、PDF、雲端同步）。沒有資料時顯示合成示範資料與黃色警示。 |
| `build_site.py` | 抓歷史價格、清理與補正、轉成月資料後寫進 `dist/index.html`。 |
| `.github/workflows/pages.yml` | 每天自動執行 `build_site.py`、部署到 GitHub Pages，並把價格快取存回 repo。 |
| `cloudflare-worker.js` | 即時報價代理的程式碼（備份；實際在 Cloudflare 執行）。 |
| `data/` | 價格快取（`prices.csv`、`vt_raw.csv`、`meta.json`）與加密的雲端資料 `vault.json`，由程式自動維護。 |
| `CREDITS.md` | 致謝與聲明。 |

## 標的

GLDM、GOVT、VT、0050、009826、00646、VXUS，另有三個虛擬標的：卓越50連結基金（填現值，報酬比照 0050）、台幣現金、美元現金。

- 代號是數字開頭的為台幣計價，其他為美元計價（美元資產與美元現金自動乘匯率）。
- 現金報酬視為 0；美元現金會隨匯率漲跌。
- 009826 上市時間太短，上市前以 VT（換台幣、每年扣 1.1%）代替，網頁底部會註明。
- VT 依每次實際配息扣 30% 股息預扣稅；其他標的未計稅。
- 回測共同期間由最晚上市的 GLDM 決定（約 2018 年中起）。

## 網頁功能

### 頁面上方
- **雲端同步**（可摺疊）：通關密語登入，股利、持股與設定、變化紀錄都會加密同步到各裝置。
- **顯示未持有** 撥鈕：關閉時隱藏沒持有的標的（A 區、B 區、即時報價同步）。
- **輸出 PDF**：第 1 頁現況（持股、資產類別、負債、淨值），第 2 頁起股利；用瀏覽器列印另存 PDF。
- **A 調整前**：填各標的股數（自動千分位）與台幣／美元現金，自動換算台幣市值與比例。
  - **產生文字**：產生可貼給別人的文字，格式如下，D 幾＝今天 − 2026-10-25 + 1（起算日在 `template.html` 的 `TXD0`）：
    ```
    【D4】2026.10.28 匯 32.55
    總 3385 淨 2019
    11.4 : 38.5 : 50.1 (台 12.9%)
    GLDM x 1,500
    …
    ```
- **B 調整後**（可摺疊）：摺疊時仍顯示「現金：黃金：債券：股票」比例、單一市場曝險佔股票比例、每月貸款支出與利息。
  - 輸入方式：「目標比例（%）」或「股數加減」（每檔選買或賣再填股數）。股數加減模式下，模擬比較只取調整後比例、總額沿用 A，實際要投入或取回的現金顯示在 B 下方。
  - 出生年月（年齡以月計）、歷史試算方向（正推／反推）、再平衡方式。
- **配置一覽**（可摺疊）：
  - A／B 各標的金額橫條（現金在左、紫色單一市場在右）。
  - 依 5/25 法則需要買賣的金額（股數加減模式下直接畫輸入的加減）。
  - 資產類別圓環：股票／單一市場股票／債券／黃金／現金。
  - 顏色：股票藍色系（VT 與 009826 同色）、0050 與 卓越50連結基金紫色、債券綠色、黃金黃色、現金灰色。

### 分頁：股利｜變化｜即時｜未來模擬｜歷史回測
- **股利**：日期、標的（預設 GOVT）、金額；列表由新到舊、一頁 10 筆；每年統計依標的分欄；平均每月統計（今年除以已過月數）；CSV 匯出／匯入（`日期,標的,金額`）。
- **變化**：記錄每天的總值、淨值（萬）與匯率。
  - 可手動新增，或按「帶入目前數值」自動填入；同一天只留一筆。
  - 週一到週五台灣時間 14:00 之後，只要網頁有打開就自動記錄一筆（標示「自動」）；當天沒打開就不會記錄。
  - 走勢圖：紀錄 120 筆以內畫每一筆，超過後改為每週取最後一筆。
- **即時**：透過 Cloudflare Worker 抓 Yahoo 報價，每 5 分鐘自動更新。
  - 灰底＝目前盤中；美股盤前／盤後價以小字顯示（不計入市值）；漲跌顏色可切換。
  - 總市值、盤中變動（只加總盤中且有持有的標的）、淨值。
  - **負債**（可摺疊）：信貸、房貸（本息平均攤還、寬限期、提前還本，可選月付降低或期數縮短）、理財型房貸（填目前動用餘額、年利率、額度）。
- **未來模擬**：蒙地卡羅 2000 條路徑（歷史月報酬 bootstrap）。
  - 滑桿：模擬年數 5～50 年（預設 50）、每年提領 0～300 萬、提領年增率 0～20%。
  - 表格：整體虧損機率、資產耗盡機率（非 0 標紅）、最大拉回。
  - 未來資產分布圖：P5／中位數／P95，紅色區塊標示耗盡；以年齡顯示。
- **歷史回測**：區間滑桿（預設全部）；YTD、年化報酬、波動、最大拉回、最差 12 個月、最差單月、期末資產、最大拉回金額；資產總值與距高點虧損圖；資料檢核表。

## GitHub 一次性設定
1. GitHub → New repository → **Public** → Create。
2. Settings → Pages → Source 選 **GitHub Actions**。
3. Add file → Upload files → 上傳 `template.html`、`build_site.py`、`README.md`、`CREDITS.md`、`cloudflare-worker.js` → Commit。
4. Add file → Create new file → 檔名 `.github/workflows/pages.yml` → 貼上內容 → Commit。
5. Actions → build-and-deploy → Run workflow；build、deploy 都綠勾即完成。

## 更新與調整
- **改網頁**：上傳新的 `template.html` 覆蓋，Commit 後自動重新部署。
- **改 workflow**：repo 裡打開 `.github/workflows/pages.yml` → 鉛筆 → 全選貼上 → Commit。
- **換標的**：改 `build_site.py` 的 `TICKERS` 與 `NAMES`（最後一個必須是匯率 `USDTWD`）；第一次會自動整段重抓。輸入欄位以代號記憶，加減標的不會讓其他數字錯位。
- **`build_site.py` 其他設定**：
  - `PROXY`：上市太短的標的用哪一檔代替、每年扣多少。
  - `CHECK_SKIP`：單月漲跌超過 40% 只提示不中止的標的（目前沒有）。
- **`template.html` 裡的設定**：
  - `TWS`：單一市場標的（目前 0050、卓越50連結基金）。
  - `CLS`：黃金、債券的代號清單（其他歸股票）。
  - `ORD`、`CMAP`：配置圖的排列順序與指定顏色。
  - `TXD0`：產生文字的 D1 日期。
  - `QURL`：即時報價 Worker 網址。

## 資料抓取與快取
- 價格存在 `data/prices.csv`、`data/vt_raw.csv`，每次只抓「快取最後一天前 20 天」起的新資料，用重疊日對齊 Yahoo 的還原基準後接回；每 30 天整段重抓一次。手動整段重抓：Actions → Run workflow → 勾「整段重抓」。
- 下載為單執行緒，只重抓失敗的代號（避免 yfinance 的 `database is locked`）。
- 自動處理：分割斷層補正（相鄰交易日差 2～10 倍且持續）、匯率錯誤報價剔除、假日或缺值用前幾天補上。
- Yahoo 暫時抓不到時沿用快取繼續產生網頁。

## 自動排程（`pages.yml`）
- 每天台灣時間約 06:30（美股收盤後）與 14:30（台股收盤後）各跑一次。
- `data/vault.json` 的變動不觸發部署；build 最多 30 分鐘、deploy 最多 15 分鐘，逾時就放棄，下次排程再部署。

## 即時報價（Cloudflare Worker）
瀏覽器不能直接向 Yahoo 要報價（CORS），所以在 Cloudflare 放一個代理。

1. `dash.cloudflare.com` 用 Email 註冊（免費方案）。
2. Workers & Pages → Create → Create Worker → 名稱 `quote` → Deploy（第一次需設定 `workers.dev` 子網域）。
3. Edit code → 全選刪除 → 貼上 `cloudflare-worker.js` → Deploy。
4. 測試：瀏覽器打開 `https://quote.<子網域>.workers.dev/?s=VT,0050.TW,TWD=X`，看到含 `"price"` 的 JSON 即成功。
5. 網址不同時改 `template.html` 的 `QURL`；網站網址改了要改 Worker 的 `ALLOW` 並重新 Deploy。

更新 Worker：Workers & Pages → `quote` → Edit code → 貼上新版 → Deploy。免費額度每天 10 萬次請求。

## 雲端同步（通關密語）
- 加密存在 `data/vault.json`（AES-GCM，金鑰由通關密語經 PBKDF2 60 萬次產生），內容包括：加密的 GitHub token、股利紀錄、持股與所有設定（含負債）、變化紀錄。
- 股利與變化紀錄每次寫入都先抓雲端最新版本再修改，多裝置不互相覆蓋；設定以最後修改的裝置為準。
- repo 是公開的，安全性取決於通關密語強度：請用 16 個字元以上、不常見的詞組合。忘記就救不回，請偶爾匯出股利 CSV 備份。
- token：GitHub → Settings → Developer settings → Fine-grained tokens → Generate；Repository access 只選這個 repo；Permissions → Contents 設 Read and write。過期時登入後在「更換 GitHub token」換掉。

## 疑難排解
- **Actions 紅叉**：多半是 Yahoo 暫時限流，舊網頁仍在線上；進該次執行按 Re-run all jobs。
- **「資料異常」**：某標的單月漲跌超過 40%，日誌會列出月份與價格；確認是真實行情就加進 `CHECK_SKIP`。
- **deploy 一直 `updating_pages`**：通常是 GitHub Pages 本身的問題；看 `githubstatus.com`、取消後重跑，或到 Settings → Pages 把 Source 暫改「Deploy from a branch」再改回「GitHub Actions」。
- **儲存快取時 403**：Settings → Actions → General → Workflow permissions 改 Read and write。
- **資料很多天沒更新**：到 Actions 頁看排程是否被停用，按 Enable。
- **即時分頁抓不到**：確認 Worker 網址能打開、`ALLOW` 與網站網址一致；claude.ai 預覽頁本來就抓不到，請在 GitHub 網址測試。
- **改了設定但數字沒變**：重新整理頁面；GitHub Pages 剛部署完幾分鐘內可能還是舊版。
