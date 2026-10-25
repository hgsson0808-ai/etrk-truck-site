"""중고화물차 광고용 사이트 생성기 (업체 정보는 brand.json).

사용:  python3 build.py site     → dist/site/    (실제 배포용, 한글 URL)
       python3 build.py preview  → dist/preview/ (Claude 미리보기용, 영문 파일명)
입력:  data/cars_raw.json (수집 매물), data/desc/{id}.json (AI 상세설명), data/photos/{id}/NN.jpg
"""
import json, os, re, shutil, sys, html, datetime
from collections import OrderedDict
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from config import SITE, PERF_URL, is_handled, ton_value, ton_bucket, TON_BUCKETS
import truck_art
import spec_extract
import autodesc

ROOT = os.path.dirname(os.path.abspath(__file__))
MODE = sys.argv[1] if len(sys.argv) > 1 else "site"
OUT = os.path.join(ROOT, "dist", MODE)
TODAY = datetime.date.today().isoformat()

TYPE_ASCII = {"내장탑": "box", "고소작업차": "sky", "활어차": "fish", "윙바디": "wing", "카고": "cargo", "덤프": "dump", "냉동탑": "freezer", "암롤": "armroll",
              "압착진개차": "garbage", "익스탑": "extop", "카고크레인": "crane", "집게차": "grab", "바가지차": "bucket",
              "셀프로더": "selfloader", "탱크로리": "tanker", "살수차": "sprayer", "버큠로리": "vacuum",
              "음식물수거차": "foodwaste", "자동사다리차": "ladder"}
# 차종 분류 체계 (그대로 유지)
# 카매니저 홈페이지 첫 화면과 같은 18개 차종 (순서·이름·사진 동일). (내부 키, 화면 이름, 사진 번호)
MT_CATS = [
    ("카고", "카고트럭", 1), ("윙바디", "윙바디", 2), ("내장탑", "내장탑차", 3), ("익스탑", "익스탑차", 4),
    ("냉동탑", "냉동탑차", 5), ("바가지차", "바가지차", 6), ("고소작업차", "고소작업차", 7), ("카고크레인", "카고크레인", 8),
    ("집게차", "집게차", 9), ("덤프", "덤프트럭", 10), ("탱크로리", "홈로리/탱크로리", 11), ("살수차", "살수차", 12),
    ("버큠로리", "버큠로리", 13), ("셀프로더", "셀프로더", 14), ("암롤", "암롤트럭", 15), ("활어차", "활어차", 16),
    ("압착진개차", "진개 압축/압착", 17), ("음식물수거차", "음식물차", 18),
]
TYPE_LABEL = {k: l for k, l, _ in MT_CATS}
TYPE_IMG = {k: f"img/types/cat{n:02d}.webp" for k, _, n in MT_CATS}
TYPE_GROUPS = [("차종", [k for k, _, _ in MT_CATS])]
TYPE_BLURB = {
    "카고": "가장 활용 폭이 넓은 화물차입니다. 적재함 길이와 고상·저상 여부가 운송 품목을 좌우합니다.",
    "윙바디": "측면이 열려 지게차 상하차가 빠른 차종입니다. 파렛트 장수와 적재함 폭(일반폭·광폭)을 먼저 확인하세요.",
    "냉동탑": "온도 관리가 필요한 화물을 싣는 차종입니다. 냉동기 가동 상태와 탑 단열 상태가 핵심입니다.",
    "카고크레인": "적재함과 크레인을 함께 갖춘 차종입니다. 크레인 제조사·단수와 아웃트리거 작동을 확인하세요.",
    "바가지차": "전기·통신 공사에 쓰는 작업대 차량입니다. 붐 길이와 작업대 높이, 절연 여부가 중요합니다.",
    "집게차": "고철·폐기물 상차용 집게 크레인 차량입니다. 집게 회전과 유압 누유를 꼭 확인하세요.",
    "내장탑": "화물을 비·먼지로부터 지키는 박스형 탑차입니다. 적재함 길이·높이와 리프트 유무를 확인하세요.",
    "고소작업차": "높은 곳 작업용 스카이 차량입니다. 작업 높이와 장비 모델, 안전검사 여부를 확인하세요.",
    "활어차": "수산물을 산 채로 운반하는 수조 차량입니다. 수조 용량과 산소·냉각 장치 작동을 확인하세요.",
    "익스탑": "높이를 키운 탑차로 부피 큰 화물에 유리합니다. 실내 높이와 옆문 구성을 확인하세요.",
    "음식물수거차": "음식물 폐기물 수거용 특장차입니다. 탱크 부식과 배출 장치 작동 상태를 봐야 합니다.",
    "압착진개차": "생활폐기물 수거용 압착 특장차입니다. 압착판·유압 계통 작동과 호퍼 상태를 함께 봐야 합니다.",
    "덤프": "토사·골재 운반용 차종입니다. 적재함 보강 상태와 유압 작동, 4륜 여부를 함께 보셔야 합니다.",
    "암롤": "적재함(박스)을 내리고 올리는 차종입니다. 보유하신 박스 규격과 호환되는지 꼭 확인하세요.",
    "셀프로더": "적재함을 기울여 장비를 직접 싣는 차종입니다. 윈치·사다리 작동과 적재함 길이를 확인하세요.",
    "자동사다리차": "이삿짐·자재를 고층으로 올리는 사다리 특장차입니다. 사다리 단수와 작업 높이를 확인하세요.",
    "탱크로리": "유류·액체 운송용 탱크 차량입니다. 탱크 용량과 검사 유효기간을 확인하세요.",
    "살수차": "도로·현장 살수용 차량입니다. 탱크 용량과 펌프·노즐 작동을 확인하세요.",
    "버큠로리": "흡입식 오수·슬러지 수거 차량입니다. 진공 펌프 상태와 탱크 용량을 확인하세요.",
}
TYPE_BLURB.update(SITE.get('seo', {}).get('type_blurb', {}))  # 업체마다 다른 차종 설명(중복 문서 방지)
ALL_TYPES = [t for _, ts in TYPE_GROUPS for t in ts]
# 적재함 치수가 구매 판단에 중요한 차종
BOX_TYPES = {"카고", "윙바디", "냉동탑", "익스탑", "카고크레인", "셀프로더", "덤프", "집게차"}

if MODE == "site":
    def car_file(c): return re.sub(r"\s+", "-", f"{c['seo_title']}-{c['id']}") + ".html"
    def type_file(t, key=None): return (f"차종-{next(x[2] for x in TON_BUCKETS if x[0] == key)}-{t}" if key else f"차종-{t}") + ".html"
    LIST_FILE, SELL_FILE, INDEX_FILE = "전체매물.html", "내차팔기.html", "index.html"
    GUIDE_FILE = "가이드.html"
else:
    GUIDE_FILE = "guide.html"
    def car_file(c): return f"car-{c['id']}.html"
    def type_file(t, key=None):
        a = TYPE_ASCII.get(t, "etc")
        return (f"type-{a}-{key.replace('.', '_')}t" if key else f"type-{a}") + ".html"
    LIST_FILE, SELL_FILE, INDEX_FILE = "list.html", "sell.html", "index.html"


IMPORT_MK = ("볼보", "스카니아", "만(MAN)", "MAN", "만", "벤츠", "이베코", "다프", "DAF", "이스즈", "후소", "테낙스(TENAX)")


def maker_group(c):
    """필터용 제조사 묶음: 현대 / 타타대우 / 기아 / 수입 / 기타. 제조사가 비어 있으면 모델명으로 추정."""
    mk, md = c.get("maker") or "", c.get("model") or ""
    if mk in IMPORT_MK or any(k in mk for k in ("TENAX",)): return "수입"
    if mk in ("타타대우", "대우"): return "타타대우"
    if mk in ("현대", "기아"): return mk
    if any(k in md for k in ("프리마", "노부스", "구쎈", "더쎈", "맥쎈", "차세대")): return "타타대우"
    if "봉고" in md: return "기아"
    if any(k in md for k in ("마이티", "메가", "파비스", "엑시언트", "트라고", "파워트럭", "포터", "슈퍼트럭")): return "현대"
    return "기타"


def text_logo():
    """data/brand/logo.png 가 없을 때: brand.json 업체명으로 글자 로고(투명 배경)를 만든다. 진짜 로고가 있으면 그 파일로 바꾸면 됨."""
    from PIL import ImageDraw, ImageFont
    font = None
    for f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf", "C:/Windows/Fonts/malgunbd.ttf"):
        if os.path.exists(f): font = ImageFont.truetype(f, 150, index=1 if f.endswith(".ttc") else 0); break
    font = font or ImageFont.load_default()
    col = SITE.get("colors", {}).get("dark") or "#18445d"
    im = Image.new("RGBA", (1200, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((20, 60), SITE["name"], font=font, fill=col)
    im = im.crop(im.getbbox()); pad = 20
    out = Image.new("RGBA", (im.width + pad * 2, int((im.width + pad * 2) * .78)), (0, 0, 0, 0))
    out.alpha_composite(im, (pad, (out.height - im.height) // 2))
    os.makedirs(os.path.join(ROOT, "data", "brand"), exist_ok=True); out.save(os.path.join(ROOT, "data", "brand", "logo.png"))


def brandify(text):
    """템플릿 속 업체 토큰을 brand.json 값으로 바꾼다."""
    return text.replace("__BRAND__", SITE["name"]).replace("__IMGHOST__", SITE["img_host"])


def _mix(hex1, hex2, t):
    a = [int(hex1[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(hex2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def color_css():
    """brand.json colors(main, dark)로 사이트 색 변수를 덮어쓴다. 다른 변수도 이름 그대로 넣으면 적용."""
    col = {k: v for k, v in SITE.get("colors", {}).items() if not k.startswith("_") and v}
    m, d = col.pop("main", None), col.pop("dark", None)
    v = {}
    if m: v.update({"teal": m, "teal-btn": _mix(m, "#000000", .12), "teal-dark": _mix(m, "#000000", .25), "teal-pale": _mix(m, "#ffffff", .88), "soft": _mix(m, "#ffffff", .93)})
    if d: v.update({"navy": d, "navy-2": d})
    v.update(col)
    css = ("\n:root {" + " ".join(f"--{k}: {x};" for k, x in v.items()) + "}\n") if v else ""
    if d:  # 첫 화면 큰 사진 위 어두운 바탕·배너를 업체 색(dark)으로 맞춘다 (스타일 파일에는 파란 바탕이 고정돼 있음)
        h1, h2, h3 = _mix(d, "#000000", .62), _mix(d, "#000000", .45), _mix(d, "#000000", .2)
        rg = lambda c, a: "rgba(%d,%d,%d,%s)" % (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), a)
        css += (f".hero2 {{ background: linear-gradient(115deg, {h1} 0%, {h2} 55%, {h3} 100%) !important; }}\n"
                f".hero2::before, .h2-slide::before {{ background: linear-gradient(90deg, {rg(h1,.96)} 0%, {rg(h2,.88)} 38%, {rg(h2,.4)} 62%, {rg(h2,0)} 82%) !important; }}\n"
                f"@media (max-width: 760px) {{ .hero2::before, .h2-slide::before {{ background: linear-gradient(180deg, {rg(h1,0)} 0, {rg(h1,0)} 170px, {h2} 300px, {h2} 100%) !important; }} .hero2-bar {{ background: {h1} !important; }} }}\n"
                f".hero2-cred .ic, .hero2-bar .ic, .bn-kicker::before {{ color: #ffc48a; background-color: transparent; }} .bn-kicker::before {{ background: #ffc48a; }} .foot-phone {{ color: #ffc48a !important; }}\n"
                f".bn-1::before {{ background: linear-gradient(115deg, {h2} 0%, {d} 55%, {m or d} 100%) !important; }}\n"
                f".bn-2::before {{ background: linear-gradient(115deg, {m or d} 0%, {d} 60%, {h2} 100%) !important; }}\n"
                f".bn-3::before {{ background: linear-gradient(115deg, {d} 0%, {m or d} 100%) !important; }}\n")
    return css


def man(n):  # 만원 → '2,900만원'
    return f"{n:,}만원"


IMG_HOST = SITE["img_host"]  # 카매니저 원본 사진 중계 (img-worker)
MAX_PHOTOS = 16


def _ai_desc(c):
    """AI 상세설명이 있고, 사진 순서가 원본과 같은 경우에만 사용."""
    dp = os.path.join(ROOT, "data", "desc", f"{c['id']}.json")
    pd = os.path.join(ROOT, "data", "photos", c["id"])
    if not os.path.exists(dp):
        return None
    # 예전 시험 매물은 로컬 사진 순서 기준 → 원본과 장수가 같을 때만 사용. 새 설명은 원본 사진 순서 기준.
    d = json.load(open(dp, encoding="utf-8"))
    if not d.get("remote") and os.path.isdir(pd) and len(os.listdir(pd)) != len(c["photos"]):
        return None  # 원본 사진 기준으로 다시 쓴 글("remote": true)은 그대로 사용
    for k in ("maker", "model", "type", "km", "body"):  # 사진으로 확인한 제조사·모델·차종·주행거리 보정
        if d.get(k): c[k] = d[k]
    secs = [x for x in d["sections"] if x["photo"] <= MAX_PHOTOS]
    return dict(seo_title=d["title"], headline=d["headline"], meta=d["meta_description"], cover=min(d["cover"], MAX_PHOTOS),
                intro=d["intro"], sections=secs, outro=d["outro"], faq=d["faq"], notes=d.get("notes", []))


_bp = os.path.join(ROOT, "data", "body.json")
BODY = json.load(open(_bp, encoding="utf-8")) if os.path.exists(_bp) else {}  # {매물번호: "5" 또는 "L"} 사진으로 확인한 바디(프리마 등)
_vp = os.path.join(ROOT, "data", "videos.json")
VIDEOS = json.load(open(_vp, encoding="utf-8")) if os.path.exists(_vp) else {}  # {매물번호: 유튜브 영상 ID}


def load():
    raw = json.load(open(os.path.join(ROOT, "data", "all_raw.json"), encoding="utf-8"))
    raw.sort(key=lambda c: c["id"], reverse=True)  # 매물번호가 클수록 최근 등록
    cars, skipped = [], []
    from urllib.parse import quote
    for c in raw:
        if not c.get("handled"):
            skipped.append((c["id"], c.get("why", ""))); continue
        d = _ai_desc(c)
        c["body"] = BODY.get(c["id"], c.get("body", ""))
        ok, why = is_handled(c)  # 사진으로 보정한 모델·차종·바디로 취급 기준 다시 확인
        if not ok:
            skipped.append((c["id"], why + " (사진 확인 후)")); continue
        c["ai"] = bool(d)
        c.update(d or autodesc.make(c))
        c["seller"] = autodesc.seller_lines(c)
        c["photos"] = c["photos"][:MAX_PHOTOS]
        c["n_photos"] = len(c["photos"])
        c["file"] = car_file(c)
        c["type_file"] = type_file(c["type"])
        c["body"] = BODY.get(c["id"], c.get("body", ""))
        c["ton_bucket"], c["ton_label"], _ = ton_bucket(c["ton"], c.get("model", ""), c.get("body", ""))  # 바디 기준
        c["ton_file"] = type_file(c["type"], c["ton_bucket"])
        c["price_txt"] = man(c["price"])
        c["km_txt"] = f"{c['km']:,}km"
        c["mkg"] = maker_group(c)  # 첫 화면·차종 페이지 제조사 필터용
        c["perf_url"] = PERF_URL.format(id=c["id"])
        c["specs"] = [l.split(":", 1) for l in c["desc"] if ":" in l]
        rows = spec_extract.extract(c)
        asks = [k for k, v in rows if v == spec_extract.ASK]
        rows = [(k, v) for k, v in rows if v != spec_extract.ASK]
        if asks:  # '전화 문의' 항목은 한 줄로 합침 (예: 적재함 길이·높이)
            lab = ("적재함 " + "·".join(a.replace("적재함 ", "") for a in asks)) if all(a.startswith("적재함 ") for a in asks) else "·".join(asks)
            rows.insert(1, (lab, spec_extract.ASK))
        c["spec_main"] = rows  # 차종별 주요 제원 (글에 적힌 값만, 없으면 전화 문의)
        base_name = re.sub(r"[^0-9A-Za-z가-힣.]+", "-", c["seo_title"].replace("중고화물차", "중고")).strip("-")[:60]
        c["img_base"] = base_name
        heads = {sec["photo"]: sec["heading"] for sec in c["sections"]}
        label = autodesc.name_of(c)
        c["imgs"] = [f"{IMG_HOST}/{quote(base_name + '-' + format(i, '02d'))}/{p}" for i, p in enumerate(c["photos"], 1)]
        c["thumbs"] = c["imgs"]  # 상세 사진 아래 작은 사진 (원본 사용, 늦게 불러오기)
        c["card_thumb"] = f"img/t/{c['id']}.webp"  # 목록 카드용 작은 사진 (빌드 때 만듦)
        c["alts"] = [f"{label} {c['year']}년식 {heads.get(i, '사진 ' + str(i))}" for i in range(1, c["n_photos"] + 1)]
        c["youtube"] = VIDEOS.get(c["id"], "")  # 유튜브 영상 ID (data/videos.json, 올리면 사진 자동 영상 대신 표시)
        c["idx"] = len(cars)  # 최근 등록순 정렬 기준
        cars.append(c)
    return cars, skipped


STATE_PATH = os.path.join(ROOT, "data", "state.json")
SOLD_KEEP_DAYS = 90  # 판매완료 페이지를 남겨 두는 기간 (이후 삭제 → 404)


def _fingerprint(c):
    import hashlib
    keys = ("price", "km", "year", "plate", "photos", "desc", "seo_title", "headline", "intro", "sections", "outro", "faq")
    return hashlib.sha1(json.dumps({k: c.get(k) for k in keys}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def track(cars):
    """매물별 최초등록일·최종수정일·판매완료일을 data/state.json에 누적한다."""
    st = json.load(open(STATE_PATH, encoding="utf-8")) if os.path.exists(STATE_PATH) else {}
    if MODE != "site":  # 미리보기 빌드는 상태를 바꾸지 않음
        for c in cars:
            c["lastmod"] = st.get(c["id"], {}).get("lastmod", TODAY); c["first_seen"] = st.get(c["id"], {}).get("first", TODAY)
        return [], []
    changed, live = [], {c["id"] for c in cars}
    for c in cars:
        fp, e = _fingerprint(c), st.get(c["id"])
        if e and e.get("car", {}).get("file"): c["file"] = e["car"]["file"]  # 한 번 정해진 매물 주소는 글·제목이 바뀌어도 바꾸지 않는다(검색에 잡힌 주소 보존)
        if not e or e.get("fp") != fp or e.get("sold"):
            changed.append(c["file"])
            e = {"first": (e or {}).get("first", TODAY), "fp": fp, "lastmod": TODAY}
        c["lastmod"], c["first_seen"] = e["lastmod"], e["first"]
        e["car"] = c; st[c["id"]] = e
    sold = []
    for cid, e in list(st.items()):
        if cid in live: continue
        if not e.get("sold"):
            e["sold"] = TODAY; e["lastmod"] = TODAY; changed.append(e["car"]["file"])
        if (datetime.date.fromisoformat(TODAY) - datetime.date.fromisoformat(e["sold"])).days > SOLD_KEEP_DAYS:
            changed.append(e["car"]["file"]); del st[cid]; continue
        sc = dict(e["car"]); sc["sold_on"] = e["sold"]; sc["lastmod"] = e["lastmod"]; sold.append(sc)
    json.dump(st, open(STATE_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    return sold, changed


def photos(cars):
    """목록 카드용 작은 사진: 대표 사진을 받아 480px로 줄여 data/thumbs에 보관 (한 번 받은 건 다시 안 받음)."""
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor
    cache = os.path.join(ROOT, "data", "thumbs"); os.makedirs(cache, exist_ok=True)
    dst = os.path.join(OUT, "img", "t"); os.makedirs(dst, exist_ok=True)
    def one(c):
        p = os.path.join(cache, f"{c['id']}-{c['cover']}.jpg")
        if not os.path.exists(p):
            for k in range(3):  # 원본 서버가 잠깐 실패할 수 있어 3번까지 시도
                try:
                    req = urllib.request.Request(c["imgs"][c["cover"] - 1], headers={"User-Agent": "truck-site-build"})
                    im = Image.open(__import__("io").BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
                    im.thumbnail((480, 480)); im.save(p, quality=72, optimize=True, progressive=True); break
                except Exception as e:
                    err = str(e)[:60]; __import__("time").sleep(1 + k)
            else:
                return c["id"], err
        Image.open(p).save(os.path.join(dst, f"{c['id']}.webp"), quality=70, method=4)  # 가벼운 WebP로
        return c["id"], None
    with ThreadPoolExecutor(8) as ex:
        bad = [r for r in ex.map(one, cars) if r[1]]
    if bad: print("작은 사진 실패:", len(bad), bad[:3])
    return {b[0] for b in bad}


def jsonld(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    cars, skipped = load()
    sold, changed = track(cars)
    for c in sold: c.setdefault("card_thumb", c["imgs"][c["cover"] - 1])
    bad = photos(cars + sold)
    for c in cars + sold:
        if c["id"] in bad: c["card_thumb"] = c["imgs"][c["cover"] - 1]
    truck_art.write_all(os.path.join(OUT, 'img', 'types'))
    if not os.path.exists(os.path.join(ROOT, 'data', 'brand', 'logo.png')): text_logo()  # 로고 파일이 없으면 업체명 글자 로고를 만든다
    shutil.copy(os.path.join(ROOT, 'data', 'brand', 'logo.png'), os.path.join(OUT, 'img', 'logo.png'))
    _lw = Image.open(os.path.join(ROOT, 'data', 'brand', 'logo.png')).convert('RGBA'); _lw.thumbnail((476, 374)); _lw.save(os.path.join(OUT, 'img', 'logo.webp'), quality=88, method=6)
    lg = Image.open(os.path.join(ROOT, 'data', 'brand', 'logo.png')).convert('RGBA')
    _ip = os.path.join(ROOT, 'data', 'brand', 'icon.png')  # 가로형 로고는 아이콘 그림만 파비콘으로 쓴다
    fv = Image.new('RGBA', (192, 192), (255, 255, 255, 255)); t = Image.open(_ip).convert('RGBA') if os.path.exists(_ip) else lg.crop((0, 0, lg.width, int(lg.height * .62))); t.thumbnail((176, 176))
    fv.alpha_composite(t, ((192 - t.width) // 2, (192 - t.height) // 2)); fv.convert('RGB').save(os.path.join(OUT, 'img', 'favicon.png'))
    og = Image.new('RGB', (1200, 630), (230, 244, 248)); tr = Image.open(os.path.join(ROOT, 'data', 'type-photo', 'wing.webp')).convert('RGBA'); tr.thumbnail((700, 420))
    og.paste(tr, (470, 170), tr); l2 = lg.copy(); l2.thumbnail((360, 290)); og.paste(l2, (70, 170), l2); og.save(os.path.join(OUT, 'img', 'og.jpg'), quality=85)
    tp = os.path.join(ROOT, 'data', 'type-photo')
    for f in os.listdir(tp) if os.path.isdir(tp) else []:
        if f.endswith('.webp'): shutil.copy(os.path.join(tp, f), os.path.join(OUT, 'img', 'types', f))
    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "templates")), autoescape=True,
                      trim_blocks=True, lstrip_blocks=True)
    by_type = OrderedDict()
    for c in sorted(cars, key=lambda c: c["type"]):
        by_type.setdefault(c["type"], []).append(c)
    combos = OrderedDict()
    for c in cars:
        combos.setdefault((c["type"], c["ton_bucket"]), []).append(c)

    dealer_ld = {"@context": "https://schema.org", "@type": "AutoDealer", "@id": SITE["domain"] + "#dealer",
                 "name": SITE["name"], "url": SITE["domain"], "telephone": SITE["phone"],
                 "address": {"@type": "PostalAddress", "addressCountry": "KR", "streetAddress": SITE["dealer"].get("address", "")},
                 "areaServed": "KR"}
    types_present = [t for t in by_type]
    groups = [(g, [(t, len(by_type.get(t, [])), type_file(t)) for t in ts]) for g, ts in TYPE_GROUPS]
    # 첫 화면 큰 사진 5장: data/hero/1~5.jpg → 없으면 brand.json hero_ids(매물번호) → 없으면 최근 매물 대표 사진
    import io, urllib.request
    byid = {c["id"]: c for c in cars}
    hero_ids = SITE.get("hero_ids", [])
    for i in range(1, 6):
        fp = os.path.join(ROOT, "data", "hero", f"{i}.jpg")
        if os.path.exists(fp): hp = Image.open(fp).convert("RGB")
        else:
            hid = hero_ids[i - 1] if i - 1 < len(hero_ids) else None
            c = byid.get(hid) or cars[(i - 1) % len(cars)]
            hp = Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(c["imgs"][c["cover"] - 1], headers={"User-Agent": "truck-site-build"}), timeout=30).read())).convert("RGB")
            if c["id"] == hid:  # 고른 사진은 data/hero 에 저장해 두어 차가 팔려도 첫 화면 사진이 바뀌지 않게 한다
                os.makedirs(os.path.dirname(fp), exist_ok=True); hp.save(fp, quality=92)
        hp.save(os.path.join(OUT, "img", f"hero-{i}.webp"), quality=78, method=6)
        hm = hp.copy(); hm.thumbnail((828, 828)); hm.save(os.path.join(OUT, "img", f"hero-{i}-m.webp"), quality=72, method=6)
    for k, _, n in MT_CATS:  # 카매니저 차종 사진
        Image.open(os.path.join(ROOT, "data", "mt-cat", f"img_carlistnew{n:02d}_m.jpg")).convert("RGB").save(os.path.join(OUT, "img", "types", f"cat{n:02d}.webp"), quality=75, method=6)
    import hashlib
    asset_v = hashlib.md5((open(os.path.join(ROOT, "templates", "style.css"), "rb").read() + open(os.path.join(ROOT, "templates", "app.js"), "rb").read())).hexdigest()[:8]  # 바뀌면 브라우저가 새로 받음
    hero_v = hashlib.md5(b''.join(open(os.path.join(OUT, 'img', f'hero-{i}.webp'), 'rb').read() for i in range(1, 6))).hexdigest()[:8]  # 첫 화면 사진이 바뀌면 브라우저가 새로 받음
    base = dict(asset_v=asset_v, hero_v=hero_v, type_file_of={t: type_file(t) for t in ALL_TYPES}, type_label=TYPE_LABEL, type_img=TYPE_IMG, art=truck_art.ASCII, art_photo={f[:-5] for f in os.listdir(os.path.join(ROOT, 'data', 'type-photo')) if f.endswith('.webp')}, n_types=len(ALL_TYPES), thumb="-s" if MODE == "site" else "", site=SITE, mode=MODE, groups=groups, list_file=LIST_FILE, sell_file=SELL_FILE, guide_file=GUIDE_FILE,
                index_file=INDEX_FILE, today=TODAY, jsonld=jsonld, dealer_ld=dealer_ld)
    pages, noindex_pages, lastmods = [], set(), {}
    newest = max([c["lastmod"] for c in cars] or [TODAY])
    HOME_N, LIST_N = 24, 8  # 첫 화면 최근 매물 수, 전체매물 페이지의 차종별 미리보기 수

    SMS_DEFAULT = f"[{SITE['name']} 홈페이지 문의]\n중고화물차 문의드립니다.\n찾는 차종·톤수: "
    def sms_car(c, sold=False):
        url = f"{SITE['domain']}/{c['file'][:-5]}"
        return (f"[{SITE['name']} 매물 문의]\n{c['seo_title']}\n차량번호 {c['plate']} / {c['price_txt']}\n{url}\n"
                + ("이 차와 비슷한 매물 문의드립니다." if sold else "이 차량 문의드립니다."))

    def write(name, tpl, noindex=False, lastmod=None, **kw):
        kw.setdefault("sms_body", sms_car(kw["c"], kw.get("sold")) if "c" in kw else SMS_DEFAULT)
        out = brandify(env.get_template(tpl).render(**{**base, "page_file": name, "noindex": noindex, **kw}))
        if noindex: noindex_pages.add(name)
        lastmods[name] = lastmod or newest
        if MODE == "site":
            out = re.sub(r'(?<=["/])([^"/\s<>]+?)\.html(?=["#])', lambda m: m.group(1), out)
            out = out.replace('href="index"', 'href="./"').replace('href="index#', 'href="./#').replace(SITE["domain"] + '/index"', SITE["domain"] + '/"')
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(out)
        pages.append(name)

    hero = cars[0]
    write(INDEX_FILE, "home.html", cars=cars[:HOME_N], by_type=by_type, total=len(cars), hero=hero, type_blurb=TYPE_BLURB)
    write(LIST_FILE, "list.html", by_type=OrderedDict((t, by_type[t]) for t in ALL_TYPES + [x for x in by_type if x not in ALL_TYPES] if t in by_type), total=len(cars), type_blurb=TYPE_BLURB, per_type=LIST_N)
    # 첫 화면 검색·톤수·정렬용 전체 매물 목록 (필요할 때만 불러옴)
    def link(f): return f[:-5] if MODE == "site" else f
    idx = [{"f": link(c["file"]), "t": c["card_thumb"], "ty": c["type"], "tb": c["ton_bucket"],
            "p": c["price"], "k": c["km"], "y": c["year"], "i": c["idx"], "n": c["n_photos"], "tm": c["tm"], "kt": c["km_txt"],
            "h": f"{c['maker']}{' ' + c['model'] if c['model'] else ''} {c['ton']}톤 {c['title_hint']}".strip(),
            "q": re.sub(r"\s+", "", f"{c['maker']}{c['model']}{c['ton']}톤{c['type']}{c['title_hint']}{c['plate']}{c['year']}{c['ton_label']}").lower()} for c in cars]
    json.dump(idx, open(os.path.join(OUT, "cars.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    write(SELL_FILE, "sell.html")
    # 질문·답 형식 가이드 글 (구글 AI 개요·네이버 AI 브리핑 인용용, 업체마다 내용이 다름)
    _gp = os.path.join(ROOT, "data", "guides.json")
    _gl = json.load(open(_gp, encoding="utf-8")) if os.path.exists(_gp) else []
    for _g in _gl: _g["file"] = (f"가이드-{_g['slug']}.html" if MODE == "site" else f"guide-{_gl.index(_g) + 1}.html")
    if _gl:
        write(GUIDE_FILE, "guide.html", g=None, guides=[{**x, "file": x["file"][:-5] if MODE == "site" else x["file"]} for x in _gl])
        for _g in _gl:
            write(_g["file"], "guide.html", g=_g, others=[{**x, "file": x["file"][:-5] if MODE == "site" else x["file"]} for x in _gl if x is not _g])
    write("404.html", "404.html")
    order = [k for k, _, _ in TON_BUCKETS]
    def ton_page(t, key, cs, **kw):
        label = next(l for k, l, _ in TON_BUCKETS if k == key)
        exact = "·".join(f"{x}톤" for x in sorted({c["ton"] for c in cs}, key=ton_value))
        kw.pop("rep", None)
        write(type_file(t, key), "type.html", t=t, ton=label, ton_note=exact, cars=cs,
              blurb=TYPE_BLURB.get(t, ""), ton_links=[], type_link=type_file(t), **kw)
    for t in ALL_TYPES + [x for x in by_type if x not in ALL_TYPES]:
        cs = by_type.get(t, [])
        keys = sorted({c["ton_bucket"] for c in cs}, key=order.index)
        links = [(next(c["ton_label"] for c in cs if c["ton_bucket"] == k), type_file(t, k)) for k in keys]
        lm = max([c["lastmod"] for c in cs] or [newest])
        write(type_file(t), "type.html", t=t, ton=None, cars=cs, blurb=TYPE_BLURB.get(t, ""),
              ton_links=links, type_link=type_file(t), noindex=not cs, lastmod=lm)  # 매물 0대 → 검색 제외
    for (t, key), cs in combos.items():
        ton_page(t, key, cs, lastmod=max(c["lastmod"] for c in cs))
    for c in sold:  # 판매로 0대가 된 톤수 페이지는 404 대신 검색 제외로 유지
        if (c["type"], c.get("ton_bucket")) not in combos:
            combos[(c["type"], c["ton_bucket"])] = []
            ton_page(c["type"], c["ton_bucket"], [], rep=c["ton"], noindex=True)
    def similar_to(c):
        sim = [x for x in cars if x["id"] != c["id"] and x["type"] == c["type"]]
        return (sim + [x for x in cars if x["id"] != c["id"] and x not in sim])[:4]
    for c in cars:
        write(c["file"], "car.html", c=c, similar=similar_to(c), lastmod=c["lastmod"])
    for c in sold:  # 판매완료: 페이지는 남기고(유입 유지) 검색에서는 제외
        write(c["file"], "car.html", c=c, sold=True, similar=similar_to(c), noindex=True, lastmod=c["lastmod"])

    open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(brandify(open(os.path.join(ROOT, "templates", "style.css"), encoding="utf-8").read()) + color_css())
    # 브라우저 캐시: 버전 붙은 css/js는 1년, 사진은 1주일 (다시 방문할 때 바로 뜨게)
    open(os.path.join(OUT, "_headers"), "w").write(
        "/style.css\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/app.js\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/img/*\n  Cache-Control: public, max-age=604800\n"
        "/cars.json\n  Cache-Control: public, max-age=3600\n")
    open(os.path.join(OUT, "app.js"), "w", encoding="utf-8").write(brandify(open(os.path.join(ROOT, "templates", "app.js"), encoding="utf-8").read()))
    if MODE == "site":
        from urllib.parse import quote
        from email.utils import formatdate
        from xml.sax.saxutils import escape as xe
        bycar = {c["file"]: c for c in cars}
        parts = []
        for p in pages:
            if p == "404.html" or p in noindex_pages: continue
            loc = f"{SITE['domain']}/{quote(p[:-5]) if p != 'index.html' else ''}"
            imgs = ""
            if p in bycar:
                imgs = "".join(f"<image:image><image:loc>{xe(u)}</image:loc></image:image>" for u in bycar[p]["imgs"])
            parts.append(f"<url><loc>{xe(loc)}</loc><lastmod>{lastmods.get(p, TODAY)}</lastmod>{imgs}</url>\n")
        open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + "".join(parts) + "</urlset>\n")
        def rfc(d): return formatdate(datetime.datetime.fromisoformat(d + "T09:00:00+09:00").timestamp(), localtime=True)
        items = "".join(
            f"<item><title>{xe(c['seo_title'] + ' ' + c['price_txt'])}</title><link>{xe(SITE['domain'] + '/' + quote(c['file'][:-5]))}</link>"
            f"<guid>{xe(SITE['domain'] + '/' + quote(c['file'][:-5]))}</guid><description>{xe(c['meta'])}</description>"
            f"<enclosure url=\"{xe(c['imgs'][c['cover'] - 1])}\" type=\"image/jpeg\" length=\"0\"/><pubDate>{rfc(c['first_seen'])}</pubDate></item>\n"
            for c in sorted(cars, key=lambda c: c["first_seen"], reverse=True))
        open(os.path.join(OUT, "rss.xml"), "w", encoding="utf-8").write(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE['name']} 중고화물차 매물</title>'
            f'<link>{SITE["domain"]}/</link><description>{SITE['name']} 신규 중고화물차·특장차 매물</description><language>ko</language>\n{items}</channel></rss>\n')
        _rp = os.path.join(ROOT, "data", "redirects.json")  # 예전 주소 → 지금 주소 (301)
        if os.path.exists(_rp):
            _cur = {c["file"] for c in cars + sold}
            _rl = [f"/{quote(o[:-5])} /{quote(n[:-5])} 301" for o, n in json.load(open(_rp, encoding="utf-8")).items() if n in _cur]
            open(os.path.join(OUT, "_redirects"), "w", encoding="utf-8").write("\n".join(_rl) + "\n")
        open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE['domain']}/sitemap.xml\n")
        # IndexNow: 키 파일 + 이번 빌드에서 바뀐 주소 목록 (업로드 후 indexnow.py로 전송)
        kp = os.path.join(ROOT, "data", "indexnow_key.txt")
        if not os.path.exists(kp):
            import secrets; open(kp, "w").write(secrets.token_hex(16))
        key = open(kp).read().strip()
        open(os.path.join(OUT, f"{key}.txt"), "w").write(key)
        urls = [f"{SITE['domain']}/{quote(f[:-5])}" for f in dict.fromkeys(changed)]
        if changed:
            urls += [f"{SITE['domain']}/", f"{SITE['domain']}/{quote(LIST_FILE[:-5])}"]
            urls += sorted({f"{SITE['domain']}/{quote(c['type_file'][:-5])}" for c in cars + sold if c["file"] in changed})
        open(os.path.join(ROOT, "dist", "changed-urls.txt"), "w", encoding="utf-8").write("\n".join(urls) + ("\n" if urls else ""))
    json.dump({"built": TODAY, "cars": len(cars), "sold": [c["id"] for c in sold], "changed": changed, "skipped": skipped, "pages": pages,
               "notes": {c["id"]: c["notes"] for c in cars}},
              open(os.path.join(ROOT, "dist", f"report-{MODE}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{MODE}: {len(cars)} cars, {len(pages)} pages, skipped {len(skipped)}")


if __name__ == "__main__":
    main()
