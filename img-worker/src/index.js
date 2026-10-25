// img.내도메인/{키워드-이름}/[{yyyy}/]{yyyymmdd}/{해시}.jpg  (연도 폴더는 있는 사진도, 없는 사진도 있음)
// 앞의 키워드 이름은 검색용(무시), 뒤의 경로로 카매니저 원본 사진을 가져온다.
const ORIGIN = "https://myshop-img.carmanager.co.kr/temp/photo/";
const PATH = /^\/[^/]{1,160}\/((?:\d{4}\/)?\d{8}\/[0-9A-Fa-f]{20,80}\.(?:jpe?g|png|webp))$/;

export default {
  async fetch(req, env, ctx) {
    if (req.method !== "GET" && req.method !== "HEAD") return new Response("", { status: 405 });
    const url = new URL(req.url);
    const m = decodeURIComponent(url.pathname).match(PATH);
    if (!m) return new Response("Not found", { status: 404 });
    const cache = caches.default;
    const key = new Request(url.origin + "/c/" + m[1]);
    let res = await cache.match(key);
    if (!res) {
      const o = await fetch(ORIGIN + m[1], { cf: { cacheTtl: 2592000, cacheEverything: true } });
      if (!o.ok) return new Response("Not found", { status: 404 });
      res = new Response(o.body, { headers: {
        "content-type": o.headers.get("content-type") || "image/jpeg",
        "cache-control": "public, max-age=31536000, immutable",
        "access-control-allow-origin": "*",
      } });
      ctx.waitUntil(cache.put(key, res.clone()));
    }
    return res;
  },
};
