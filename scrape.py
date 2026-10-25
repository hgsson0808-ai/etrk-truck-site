"""카매니저 홈페이지(brand.json의 source_site) 매물 수집기.

카매니저 서버가 중간 인증서를 보내지 않아 일반 TLS 검증이 실패하므로,
Sectigo 중간 인증서(certs/)를 신뢰 묶음에 추가해 정상 검증한다 (검증을 끄지 않음).
"""
import random, os, re, json, time, tempfile
import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.abspath(__file__))
from config import SITE
BASE = SITE["source_site"]  # 매물을 가져올 카매니저 홈페이지 (brand.json)
PHOTO_PREFIX = "https://myshop-img.carmanager.co.kr/temp/photo/"


def _bundle():
    sys_ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    if not os.path.exists(sys_ca):
        import certifi; sys_ca = certifi.where()
    out = os.path.join(tempfile.gettempdir(), "truck-site-ca.pem")
    with open(out, "w") as f:
        f.write(open(sys_ca).read()); f.write("\n"); f.write(open(os.path.join(ROOT, "certs", "sectigo-dv-r36.pem")).read())
    return out


S = requests.Session()
S.verify = _bundle()
S.headers["User-Agent"] = "Mozilla/5.0 (truck-site builder)"


CA = S.verify


def get(url, method="GET", **kw):
    for t in range(4):
        time.sleep(random.uniform(0.8, 1.8))  # 천천히: 사람이 넘겨 보는 속도로
        try:
            r = S.request(method, url, timeout=25, verify=CA, **kw)
            r.raise_for_status(); r.encoding = "utf-8"; return r.text
        except Exception:
            if t == 3: raise
            time.sleep(1.5 * (t + 1))


def list_page(n, maker=""):
    data = {"GotoPage": str(n)}
    if maker: data["Maker"] = maker  # 공개 목록 기본값은 중대형화물(AAG)만 → 소형화물(AAK)·중대형버스(AAF)는 따로
    html = get(BASE + "/model/Newmodel.asp", method="POST", data=data)
    soup = BeautifulSoup(html, "html.parser")
    out, seen = [], set()
    for a in soup.select('a[href*="DetailView.asp"]'):
        m = re.search(r"encOnCarNo=([^&\"']+)", a["href"])
        if not m or m.group(1) in seen: continue
        seen.add(m.group(1))
        el = a
        for _ in range(6):
            el = el.parent
            if len(el.get_text(" ", strip=True)) > 40: break
        card = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        card = re.sub(r"^.*닫기 ", "", card).replace(" 상담문의 " + SITE["phone"], "")
        out.append({"enc": m.group(1), "card": card, "category": card.split(" ")[0]})
    return out


def list_all(max_pages=120):
    """공개 목록 전체(중대형화물+소형화물+버스). 페이지를 8개씩 동시에 받아 빠르게."""
    from concurrent.futures import ThreadPoolExecutor
    allc = []
    for mk in ("", "AAK", "AAF"):
        p, done = 1, False
        while not done and p <= max_pages:
            batch = list(range(p, min(p + 2, max_pages + 1)))
            with ThreadPoolExecutor(2) as ex:
                res = list(ex.map(lambda n: list_page(n, mk), batch))
            for cs in res:
                if not cs: done = True; break
                allc += cs
            p += 2
    # 중복 제거
    seen, uniq = set(), []
    for c in allc:
        if c["enc"] in seen: continue
        seen.add(c["enc"]); uniq.append(c)
    return uniq


def detail(enc):
    from urllib.parse import quote
    html = get(BASE + "/model/DetailView.asp?encOnCarNo=" + quote(enc, safe=""))
    soup = BeautifulSoup(html, "html.parser")
    o = {"enc": enc}
    t = lambda sel: (soup.select_one(sel).get_text(strip=True) if soup.select_one(sel) else "")
    o["vname"], o["plate"], o["price"] = t(".vname"), t(".vnumber"), t(".vcash .red")
    o["fields"] = {dt.get_text(strip=True): re.sub(r"\s+", " ", dt.find_next_sibling("dd").get_text(" ", strip=True))
                   for dt in soup.select(".car-detail dt") if dt.find_next_sibling("dd")}
    v = soup.select_one(".vcontent")
    o["desc"] = normalize_desc([l.strip() for l in (v.get_text("\n") if v else "").split("\n") if l.strip()])
    o["photos"] = list(dict.fromkeys(img["src"].replace(PHOTO_PREFIX, "") for img in soup.select(".bxslider img") if img.get("src")))
    m = re.search(r"CarCheck_Form_my\.asp\?OnCarNo=(\d+)", html)
    o["onCarNo"] = m.group(1) if m else None
    return o


def normalize_desc(lines):
    """카매니저 상세설명을 '항목:값' 줄로 정리한다.
    - '▶ 추가장착 옵션 :: 300마력 8m30 카고' → '옵션:300마력 8m30 카고'
    - '차종:' 다음 줄 '현대 카고' 처럼 항목과 값이 나뉜 경우 합친다.
    - 값이 없는 항목은 버린다."""
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("▶"):
            k, _, v = l.lstrip("▶ ").partition("::")
            k, v = k.strip(), v.strip()
            if v and "옵션" in k: out.append("옵션:" + v)
            elif v: out.append(f"{k}:{v}")
            i += 1; continue
        if l.endswith(":") and ":" not in l[:-1]:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if nxt and not nxt.endswith(":") and not nxt.startswith("▶"):
                out.append(l + nxt); i += 2; continue
            i += 1; continue
        out.append(l); i += 1
    return out


def download(path, dst):
    r = S.get(PHOTO_PREFIX + path, timeout=30, verify=CA)
    r.raise_for_status()
    open(dst, "wb").write(r.content)


if __name__ == "__main__":
    cs = list_all()
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(cs, open(os.path.join(ROOT, "data", "listing_index.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(len(cs), "cards")
