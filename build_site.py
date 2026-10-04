"""抓真實歷史價格 → 換算成月資料 → 把數字直接寫進 dist/index.html（單一檔案，手機直接開）。
用法：pip install yfinance pandas ; python build_site.py
"""
import json, time, datetime as dt, pathlib, sys
import yfinance as yf

# 想換標的只改這裡。美元標的填美元價，0050 為台幣價，最後一項是匯率。
TICKERS = {'GLD': 'GLD', 'IEF': 'IEF', 'VT': 'VT', '006208': '006208.TW', 'USDTWD': 'TWD=X'}
NAMES = ['GLD 黃金', 'IEF 美公債(7-10年)', 'VT 全球股票', '006208 台股']

df = None
for attempt in range(4):              # Yahoo 偶爾會限流，重試幾次
    try:
        df = yf.download(list(TICKERS.values()), start='2000-01-01', auto_adjust=True, progress=False)['Close']
        if len(df) > 1000 and not df.isna().all().any():
            break
    except Exception as e:
        print('下載失敗：', e)
    print(f'第 {attempt + 1} 次沒拿到完整資料，30 秒後重試')
    time.sleep(30)
else:
    sys.exit('抓不到資料，保留舊網頁不更新')
df = df.rename(columns={v: k for k, v in TICKERS.items()})[list(TICKERS)]

# 匯率清理：Yahoo 的 TWD=X 偶有錯誤跳點，先剔除不合理值與偏離前後一個月中位數超過 5% 的點
fx = df['USDTWD']
fx = fx.where(fx.between(20, 45))
med = fx.rolling(21, center=True, min_periods=5).median()
fx = fx.where((fx / med - 1).abs() < 0.05)
removed = int(df['USDTWD'].notna().sum() - fx.notna().sum())
if removed:
    print(f'USDTWD 剔除 {removed} 個異常點')
df['USDTWD'] = fx

# 假日或缺值：用前幾天最後一筆有效價格補上（最多往前 10 天）
df = df.ffill(limit=10)
try:
    m = df.resample('ME').last()      # pandas >= 2.2
except ValueError:
    m = df.resample('M').last()
m = m.dropna()                        # 五欄都有值的月份才採用（起點由最晚上市者決定）

# 資料檢查：單月跌超過 40% 或漲超過 40% 幾乎一定是分割／資料錯誤
chg = m.pct_change()
bad = chg.abs() > 0.40
if bad.any().any():
    for col in m.columns[bad.any()]:
        for d in chg.index[bad[col]]:
            print(f'{col} {d:%Y-%m}：單月變動 {chg.at[d, col]:+.1%}（{m[col].shift().at[d]:.4f} → {m.at[d, col]:.4f}）')
    sys.exit('資料異常（疑似分割未調整或錯誤報價），本次不發布')

if len(m) < 24:
    sys.exit(f'共同月份只有 {len(m)} 個，資料不足，本次不發布')
rows = [[d.strftime('%Y-%m')] + [round(float(x), 4) for x in r] for d, r in zip(m.index, m.values)]
asof = {k: df[k].last_valid_index().date().isoformat() for k in TICKERS}
payload = {'names': NAMES, 'rows': rows, 'updated': dt.date.today().isoformat(), 'asof': asof,
           'source': 'Yahoo Finance（yfinance，已還原股息與分割）'}
print(f'{len(rows)} 個月：{rows[0][0]} ~ {rows[-1][0]}')
print('首列', rows[0]); print('末列', rows[-1])

html = pathlib.Path('template.html').read_text(encoding='utf-8')
assert '/*__DATA__*/null' in html
out = pathlib.Path('dist'); out.mkdir(exist_ok=True)
(out / 'index.html').write_text(html.replace('/*__DATA__*/null', json.dumps(payload, ensure_ascii=False)), encoding='utf-8')
print('已輸出 dist/index.html')
