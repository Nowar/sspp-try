// 即時報價代理（Cloudflare Worker）
// 用法：https://<你的 worker 網址>/?s=VT,0050.TW,TWD=X
// 回傳：{ at: 伺服器時間(毫秒), q: [{ s, price, prev, time, cur, tz } 或 { s, error }] }
//   price = 最新成交價、prev = 前一交易日收盤、time = 報價時間（秒）、cur = 幣別、tz = 交易所時區
//   rs/re = 正規交易時段起訖（秒），用來判斷現在是否盤中
//   ext = 美股盤前／盤後最新成交 { price, time, session: 'pre'|'post' }，正規時段內或沒有成交時不回傳

// 只允許你的網站從瀏覽器呼叫；網址不同請改這裡
const ALLOW = ['https://nowar.github.io'];
const OK = /^[A-Z0-9.=^-]{1,15}$/;   // 只接受正常的代號格式
const MAX = 20;                       // 一次最多幾檔

// 美股盤前盤後：另外抓一次含延長時段的分鐘線，取最後一筆成交；台股、匯率、指數沒有延長時段
async function extHours(s) {
  if (/\.TW$|=X$|^\^/.test(s)) return null;
  try {
    const r = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(s)}?interval=1m&range=1d&includePrePost=true`,
      { headers: { 'User-Agent': 'Mozilla/5.0' }, cf: { cacheTtl: 15 } },
    );
    if (!r.ok) return null;
    const res = (await r.json()).chart.result[0];
    const ts = res.timestamp || [], cl = (res.indicators.quote[0] || {}).close || [];
    const tp = res.meta.currentTradingPeriod || {}, R = tp.regular || {}, P = tp.pre || {};
    for (let i = ts.length - 1; i >= 0; i--) {
      if (cl[i] == null) continue;
      const t = ts[i];
      if (t >= R.start && t < R.end) return null;                 // 最後一筆在正規時段內：不需要延長時段價格
      const session = t >= R.end ? 'post' : (P.start && t >= P.start ? 'pre' : 'post');
      return { price: cl[i], time: t, session };
    }
  } catch (e) { /* 抓不到就不回傳 */ }
  return null;
}

export default {
  async fetch(req) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ALLOW.includes(origin) ? origin : ALLOW[0],
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Vary': 'Origin',
    };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });

    const json = (obj, status = 200) => new Response(JSON.stringify(obj), {
      status,
      headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'max-age=15' },
    });

    const syms = (new URL(req.url).searchParams.get('s') || '')
      .split(',').map(s => s.trim().toUpperCase()).filter(s => OK.test(s)).slice(0, MAX);
    if (!syms.length) return json({ error: '用法：?s=VT,0050.TW,TWD=X' }, 400);

    const q = await Promise.all(syms.map(async s => {
      try {
        const r = await fetch(
          `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(s)}?interval=1m&range=1d`,
          { headers: { 'User-Agent': 'Mozilla/5.0' }, cf: { cacheTtl: 15 } },
        );
        if (!r.ok) return { s, error: 'Yahoo 回應 ' + r.status };
        const m = (await r.json()).chart.result[0].meta;
        const ext = await extHours(s);
        return {
          s,
          ext,
          price: m.regularMarketPrice,
          prev: m.chartPreviousClose ?? m.previousClose,
          time: m.regularMarketTime,
          cur: m.currency,
          tz: m.exchangeTimezoneName,
          rs: m.currentTradingPeriod?.regular?.start,   // 本次（或最近一次）正規交易時段開始（秒）
          re: m.currentTradingPeriod?.regular?.end,     // 結束（秒）
        };
      } catch (e) {
        return { s, error: String(e) };
      }
    }));
    return json({ at: Date.now(), q });
  },
};
