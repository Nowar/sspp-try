// 即時報價代理（Cloudflare Worker）
// 用法：https://<你的 worker 網址>/?s=VT,0050.TW,TWD=X
// 回傳：{ at: 伺服器時間(毫秒), q: [{ s, price, prev, time, cur, tz } 或 { s, error }] }
//   price = 最新成交價、prev = 前一交易日收盤、time = 報價時間（秒）、cur = 幣別、tz = 交易所時區
//   rs/re = 正規交易時段起訖（秒），用來判斷現在是否盤中

// 只允許你的網站從瀏覽器呼叫；網址不同請改這裡
const ALLOW = ['https://nowar.github.io'];
const OK = /^[A-Z0-9.=^-]{1,15}$/;   // 只接受正常的代號格式
const MAX = 20;                       // 一次最多幾檔

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
        return {
          s,
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
