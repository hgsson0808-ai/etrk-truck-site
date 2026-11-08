// img.내도메인/{키워드-이름}/[{yyyy}/]{yyyymmdd}/{해시}.jpg  (연도 폴더는 있는 사진도, 없는 사진도 있음)
// 앞의 키워드 이름은 검색용(무시), 뒤의 경로로 카매니저 원본 사진을 가져온다.
const ORIGIN = "https://myshop-img.carmanager.co.kr/temp/photo/";

// 사진이 끝까지 다 받아졌는지 확인 (중간에 끊긴 사진은 아래쪽이 회색으로 깨져 보임)
function complete(buf, type, len) {
  const b = new Uint8Array(buf);
  if (b.length < 200) return false;
  if (len && +len > 0 && b.length !== +len) return false;           // 받은 크기가 원본 크기와 다름
  if (b[0] === 0xff && b[1] === 0xd8) {                               // JPEG: 끝 표시(FF D9)가 있어야 완전
    for (let i = b.length - 1; i >= Math.max(1, b.length - 64); i--) if (b[i - 1] === 0xff && b[i] === 0xd9) return true;
    return false;
  }
  if (b[0] === 0x89 && b[1] === 0x50) {                               // PNG: 마지막 IEND
    const t = String.fromCharCode(...b.slice(-12, -4)); return t.indexOf("IEND") >= 0;
  }
  if (b[0] === 0x52 && b[1] === 0x49 && b[8] === 0x57) {               // WEBP: RIFF 크기 확인
    const n = b[4] | (b[5] << 8) | (b[6] << 16) | (b[7] << 24); return n + 8 <= b.length;
  }
  return true;
}

// 원본을 받아 완전한 사진이면 오래 저장, 깨진 사진이면 저장하지 않고 다시 받기 (최대 3번)
async function getPhoto(path, cache, url, waitUntil) {
  const key = new Request(url.origin + "/c2/" + path);                // 예전에 깨진 채 저장된 것과 섞이지 않게 새 이름
  let res = await cache.match(key);
  if (res) return res;
  let buf = null, type = "image/jpeg", ok = false;
  for (let k = 0; k < 3 && !ok; k++) {
    try {
      const o = await fetch(ORIGIN + path + (k ? "?r=" + k + Date.now() : ""), k ? { cf: { cacheTtl: 0 } } : { cf: { cacheTtl: 2592000, cacheEverything: true } });
      if (o.status === 404) return new Response("Not found", { status: 404 });
      if (!o.ok) continue;
      type = o.headers.get("content-type") || type;
      buf = await o.arrayBuffer();
      ok = complete(buf, type, o.headers.get("content-length"));
    } catch (e) { /* 다시 시도 */ }
  }
  if (!buf) return new Response("Not found", { status: 404 });
  res = new Response(buf, { headers: {
    "content-type": type,
    // 완전한 사진만 오래 저장. 깨진 사진은 잠깐만 보여 주고 다음에 다시 받는다.
    "cache-control": ok ? "public, max-age=31536000, immutable" : "no-store",
    "access-control-allow-origin": "*",
  } });
  if (ok) waitUntil(cache.put(key, res.clone()));
  return res;
}
const PATH = /^\/[^/]{1,160}\/((?:\d{4}\/)?\d{8}\/[0-9A-Fa-f]{20,80}\.(?:jpe?g|png|webp))$/;

export default {
  async fetch(req, env, ctx) {
    if (req.method !== "GET" && req.method !== "HEAD") return new Response("", { status: 405 });
    const url = new URL(req.url);
    const m = decodeURIComponent(url.pathname).match(PATH);
    if (!m) return new Response("Not found", { status: 404 });
    return getPhoto(m[1], caches.default, url, (p) => ctx.waitUntil(p));
  },
};
