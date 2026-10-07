# 致謝與聲明（Credits & Notice）

## 誰做了什麼
本專案「投資組合調整比較（台幣）」由 **WH（GitHub：nowar）** 提出需求、逐步測試回饋，並負責部署與維運。

專案中的程式碼與文件，是由 **Anthropic 的 AI 助手 Claude**（Claude Opus 5.5）在 2026 年 10 月透過對話協作產生，包括：

- `template.html`：網頁、計算、圖表、股利紀錄與加密同步、即時報價
- `build_site.py`：抓取歷史價格、資料清理與分割補正、產生網頁
- `.github/workflows/pages.yml`：每日自動建置與部署
- `cloudflare-worker.js`：即時報價代理
- `README.md`、`CREDITS.md`：說明文件

## 權利歸屬
- 依 Anthropic 的服務條款，Claude 產生的內容權利歸使用者所有；Anthropic 與 Claude 不對本專案主張著作權。
- AI 產生的內容在各國著作權法下是否受保護、保護到什麼程度，目前仍有爭議。本檔案用來說明專案的產生方式，不構成法律意見。

## 使用的第三方元件與服務
- [Chart.js](https://www.chartjs.org/)：圖表（MIT License）
- [yfinance](https://github.com/ranaroussi/yfinance)：下載 Yahoo Finance 資料（Apache License 2.0）
- [pandas](https://pandas.pydata.org/)：資料處理（BSD 3-Clause License）
- Yahoo Finance：歷史與即時價格資料，依其使用條款僅供個人參考
- GitHub Pages、GitHub Actions：網站託管與自動建置
- Cloudflare Workers：即時報價代理

## 免責聲明
- 本工具僅供個人研究與參考，不構成任何投資建議。
- 價格資料來自第三方，可能延遲、缺漏或有誤；歷史回測與蒙地卡羅模擬的結果不代表未來表現。
- 稅負、交易成本、匯差等僅部分估算，實際情況請自行確認。

---

**English summary**
Built and maintained by WH (nowar). Code and documentation were generated in collaboration with Claude (Claude Opus 5.5), an AI assistant made by Anthropic, in October 2026. Under Anthropic's terms, rights in Claude's outputs belong to the user; Anthropic and Claude claim no copyright in this project. Uses Chart.js (MIT), yfinance (Apache-2.0), pandas (BSD-3-Clause), Yahoo Finance data, GitHub Pages/Actions, and Cloudflare Workers. For personal reference only; not investment advice.
