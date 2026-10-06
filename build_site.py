"""抓真實歷史價格 → 換算成月資料 → 把數字直接寫進 dist/index.html（單一檔案，手機直接開）。
用法：pip install yfinance pandas ; python build_site.py
"""
import json, os, time, tempfile, datetime as dt, pathlib, sys
import pandas as pd
import yfinance as yf

# 想換標的只改這裡。美元標的填美元價，0050 為台幣價，最後一項是匯率。
TICKERS = {'GLDM': 'GLDM', 'GOVT': 'GOVT', 'VT': 'VT', '0050': '0050.TW', '009826': '009826.TW', '00646': '00646.TW', 'VXUS': 'VXUS', 'USDTWD': 'TWD=X'}
# 上市太短的標的：上市前用替代標的（換成台幣）接上，並每年扣 extra 代表費用率與稅負差異
# 009826 於 2026 年才上市，追蹤全球股票，上市前以 VT 代替；VT 內扣約 0.06%、009826 約 0.5~0.6%，
# 加上台灣基金投資美股的股息預扣稅（約 0.6%/年），合計每年扣 1.1%
PROXY = {'009826': ('VT', 0.011)}
NAMES = ['GLDM 黃金', 'GOVT 美公債', 'VT 全球股票', '0050 台股', '009826 全球股票(台幣)', '00646 美國S&P500', 'VXUS 美國以外股票']

# ---------- 下載與本地快取 ----------
# 每日收盤價存在 data/*.csv（GitHub Actions 會把它 commit 回 repo）。下次只抓最後一天前 20 天起的新資料，
# 用重疊那段對齊 Yahoo 的還原基準（新除息時 Yahoo 會把整段舊價格等比例縮小），再接回舊資料。
# 每 30 天整段重抓一次，同步 Yahoo 對舊資料的修正；手動執行時勾選「整段重抓」也會重抓。
DATA_DIR = pathlib.Path('data'); DATA_DIR.mkdir(exist_ok=True)
META_PATH = DATA_DIR / 'meta.json'
META = json.loads(META_PATH.read_text(encoding='utf-8')) if META_PATH.exists() else {}
TODAY = dt.date.today()
OVERLAP_DAYS, FULL_EVERY_DAYS = 20, 30

# yfinance 預設多執行緒下載，並共用一個 SQLite 時區快取；多檔同時寫入時會出現 'database is locked'。
# 這裡改成單執行緒、快取放到獨立暫存資料夾，並且只針對失敗的代號重抓。
if hasattr(yf, 'set_tz_cache_location'):
    yf.set_tz_cache_location(tempfile.mkdtemp())

def fetch(symbols, start, adjusted):
    got = {}
    for attempt in range(4):
        need = [s for s in symbols if s not in got]
        try:
            d = yf.download(need, start=start, auto_adjust=adjusted, progress=False, threads=False)['Close']
            if isinstance(d, pd.Series):
                d = d.to_frame(need[0])
            if d.index.tz is not None:
                d.index = d.index.tz_localize(None)
            for s in need:
                if s in d.columns and d[s].notna().any():
                    got[s] = d[s]
        except Exception as e:
            print('下載失敗：', e)
        if len(got) == len(symbols):
            return pd.DataFrame(got)[symbols]
        print(f'第 {attempt + 1} 次缺 {", ".join(s for s in symbols if s not in got)}，30 秒後只重抓這些')
        time.sleep(30)
    return None

def cached(name, symbols, adjusted, required=True):
    path = DATA_DIR / f'{name}.csv'
    old = pd.read_csv(path, index_col=0, parse_dates=True) if path.exists() else None
    last_full = dt.date.fromisoformat(META.get(f'{name}_full', '2000-01-01'))
    full = (old is None or list(old.columns) != symbols or os.environ.get('FULL') == '1'
            or (TODAY - last_full).days >= FULL_EVERY_DAYS)
    start = '2000-01-01' if full else (old.index.max() - pd.Timedelta(days=OVERLAP_DAYS)).strftime('%Y-%m-%d')
    new = fetch(symbols, start, adjusted)
    if new is None:
        if old is not None:
            print(f'{name}：這次抓不到新資料，沿用快取（到 {old.index.max():%Y-%m-%d}）')
            return old
        if required:
            sys.exit(f'{name}：抓不到資料也沒有快取，保留舊網頁不更新')
        return None
    if full:
        merged = new
        META[f'{name}_full'] = TODAY.isoformat()
        print(f'{name}：整段重抓 {len(new)} 天（{new.index.min():%Y-%m-%d} ~ {new.index.max():%Y-%m-%d}）')
    else:
        old = old.copy()
        for c in symbols:
            ov = old[c].dropna().index.intersection(new[c].dropna().index)
            if len(ov):
                f = new.at[ov[0], c] / old.at[ov[0], c]
                if abs(f - 1) > 1e-6:
                    old[c] *= f
                    print(f'{name}：{c} 還原基準改變（新除息或分割），舊資料等比例調整 ×{f:.6f}')
        merged = pd.concat([old[old.index < new.index.min()], new]).sort_index()
        print(f'{name}：增量抓取 {new.index.min():%Y-%m-%d} 起 {len(new)} 天，合併後共 {len(merged)} 天（到 {merged.index.max():%Y-%m-%d}）')
    merged.to_csv(path, float_format='%.6f')
    return merged

df = cached('prices', list(TICKERS.values()), adjusted=True)
df = df.rename(columns={v: k for k, v in TICKERS.items()})[list(TICKERS)].copy()

# 分割斷層自動修復：Yahoo 有時只把分割調整套用到某一段歷史（例如 0050 在 2014-01 前後差 4 倍）。
# 對每個價格欄位找「相鄰兩個交易日價格比 ≈ 1/k 或 k（k=2..10）」且前後 5 天中位數也維持這個比例的斷點，
# 把斷點之前的價格乘上該比例，接回同一個基準。實際 ETF 不可能一天漲跌 50% 以上，所以不會誤判正常行情。
def repair_splits(col):
    v = df[col].dropna()
    r = v / v.shift(1)
    fixes = []
    for i in [j for j in range(1, len(v)) if abs(r.iloc[j] - 1) > 0.4]:
        for k in range(2, 11):
            for f in (1 / k, k):
                pre, post = v.iloc[max(0, i - 5):i].median(), v.iloc[i:i + 5].median()
                if abs(r.iloc[i] / f - 1) < 0.08 and abs(post / pre / f - 1) < 0.15:
                    fixes.append((v.index[i], f))
    for day, f in fixes:
        df.loc[df.index < day, col] *= f
        print(f'{col} {day:%Y-%m-%d} 前後差 {1 / f:.0f} 倍' if f < 1 else f'{col} {day:%Y-%m-%d} 前後差 1/{f:.0f}', '→ 已把之前的價格校正到同一基準')
    if not fixes:
        print(f'{col}：未發現分割斷層')

for col in [c for c in TICKERS if c != 'USDTWD']:
    repair_splits(col)

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

proxy_note = []
for col, (src, extra) in PROXY.items():
    real = df[col].dropna()
    if real.empty:
        sys.exit(f'{col} 沒有任何資料')
    t0 = real.index[0]
    tw = df[src] * (df['USDTWD'] if not TICKERS[src].endswith('.TW') else 1)
    yrs = (t0 - df.index).days / 365.25
    synth = real.iloc[0] * tw / tw.loc[t0] * (1 + extra) ** yrs
    df.loc[df.index < t0, col] = synth[df.index < t0]
    proxy_note.append(f'{col} 於 {t0:%Y-%m-%d} 上市，之前以 {src}（換台幣、每年扣 {extra:.1%}）代替')
    print(proxy_note[-1])
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
# VT 每月配息殖利率：還原價報酬 − 未還原價報酬（給網頁扣股息預扣稅用）
div_vt = None
try:
    raw = cached('vt_raw', ['VT'], adjusted=False, required=False)
    if raw is None:
        raise RuntimeError('沒有資料')
    raw = raw['VT']
    rawm = raw.ffill().groupby(raw.index.to_period('M')).last()
    rawm.index = rawm.index.to_timestamp('M')
    adj = m['VT']
    rawm = rawm.reindex(adj.index, method='nearest')
    dy = ((adj / adj.shift()) - (rawm / rawm.shift())).fillna(0).clip(0, 0.05)
    dy[dy < 0.0005] = 0
    div_vt = [round(float(x), 5) for x in dy]
    print(f'VT 配息月份 {int((dy > 0).sum())} 個，平均年殖利率約 {dy.mean() * 12:.2%}')
except Exception as e:
    print('VT 配息資料抓取失敗，網頁改用 2% 年殖利率估算：', e)

rows = [[d.strftime('%Y-%m')] + [round(float(x), 4) for x in r] for d, r in zip(m.index, m.values)]
asof = {k: df[k].last_valid_index().date().isoformat() for k in TICKERS}
payload = {'names': NAMES, 'rows': rows, 'updated': dt.date.today().isoformat(), 'asof': asof,
           'source': 'Yahoo Finance（yfinance，已還原股息與分割）', 'divVT': div_vt, 'proxyNote': '；'.join(proxy_note),
           'ccy': ['TWD' if v.endswith('.TW') else 'USD' for k, v in TICKERS.items() if k != 'USDTWD']}
print(f'{len(rows)} 個月：{rows[0][0]} ~ {rows[-1][0]}')
print('首列', rows[0]); print('末列', rows[-1])

META['last_update'] = TODAY.isoformat()
META_PATH.write_text(json.dumps(META, ensure_ascii=False, indent=1), encoding='utf-8')

html = pathlib.Path('template.html').read_text(encoding='utf-8')
assert '/*__DATA__*/null' in html
out = pathlib.Path('dist'); out.mkdir(exist_ok=True)
(out / 'index.html').write_text(html.replace('/*__DATA__*/null', json.dumps(payload, ensure_ascii=False)), encoding='utf-8')
print('已輸出 dist/index.html')
