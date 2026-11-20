"""소개글 없는 새 매물을 골라 사진·사진시트·사실정보를 작업 폴더에 준비한다.
사용: python3 intro/prep.py [최대대수=20]   (작업 폴더: 환경변수 W, 기본 /tmp/mt-intro)
출력 마지막 줄: 고른 매물번호 쉼표 목록 (없으면 'NONE')"""
import json, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SITE
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.environ.get("W", "/tmp/mt-intro"); os.makedirs(B, exist_ok=True)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
d = [r for r in json.load(open(f"{S}/data/all_raw.json")) if r["handled"]]
d.sort(key=lambda r: r["id"], reverse=True)
# 1번 대성트럭에 사장님이 상세설명(desc)을 입력한 매물만 쓴다. 비었거나 "@@"뿐이면 아직 미입력 → 고르지 않는다.
def has_desc(r): return any((x or "").strip() not in ("", "@@") for x in (r.get("desc") or []))
no_desc = [r["id"] for r in d if not has_desc(r)]
d = [r for r in d if has_desc(r)]
done = {f[:-5] for f in os.listdir(f"{S}/data/desc") if f.endswith(".json")}
# 상세설명 없이 썼던 소개글("seller_desc_missing": true)은 상세설명이 들어오면 다시 쓴다 → facts 에 "rewrite": true
rewrite = []
for i in list(done):
    try: w = json.load(open(f"{S}/data/desc/{i}.json"))
    except Exception: continue
    if w.get("seller_desc_missing") and any(r["id"] == i for r in d): done.discard(i); rewrite.append(i)
# 보류(desc-hold)는 보류 당시 사진 목록("photos")과 지금 사진이 같을 때만 건너뛴다.
# 사진이 바뀌면(새로 올라오면) 자동으로 다시 고른다 → 소개글을 쓴 뒤 desc-hold 파일을 지울 것.
photos_now = {r["id"]: r["photos"] for r in d}
rehold = []
for f in os.listdir(f"{S}/data/desc-hold"):
    if not f.endswith(".json"): continue
    i = f[:-5]
    try: h = json.load(open(f"{S}/data/desc-hold/{f}"))
    except Exception: h = {}
    if i in photos_now and "photos" in h and h["photos"] != photos_now[i]: rehold.append(i)
    else: done.add(i)
pick = [r for r in d if r["id"] not in done and len(r["photos"]) >= 3][:N]
if rehold: print("사진 바뀐 보류 매물(다시 고름):", ",".join(i for i in rehold if any(r["id"] == i for r in pick)) or "없음(이번 회차 밖)")
if rewrite: print("상세설명 들어와 다시 쓰는 매물:", ",".join(i for i in rewrite if any(r["id"] == i for r in pick)) or "없음(이번 회차 밖)")
try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
except Exception: font = ImageFont.load_default()
jobs = [(r["id"], n, p) for r in pick for n, p in enumerate(r["photos"][:16], 1)]
for r in pick: os.makedirs(f"{B}/{r['id']}", exist_ok=True)
def get(j):
    i, n, p = j; f = f"{B}/{i}/{n:02d}.jpg"
    if os.path.exists(f) and os.path.getsize(f) > 0: return
    for _ in range(3):
        try:
            open(f, "wb").write(urllib.request.urlopen(urllib.request.Request(f"{SITE['img_host']}/x/{p}", headers={"User-Agent": "mt"}), timeout=30).read()); return
        except Exception: pass
with ThreadPoolExecutor(12) as ex: list(ex.map(get, jobs))
for r in pick:
    i = r["id"]; fs = sorted(x for x in os.listdir(f"{B}/{i}") if x.endswith(".jpg"))
    W, H = 480, 360; sh = Image.new("RGB", (W * 4, H * max(1, (len(fs) + 3) // 4)), "white")
    for k, f in enumerate(fs):
        try: im = Image.open(f"{B}/{i}/{f}").convert("RGB")
        except Exception: continue
        im.thumbnail((W, H)); x, y = (k % 4) * W, (k // 4) * H; sh.paste(im, (x, y))
        dr = ImageDraw.Draw(sh); dr.rectangle([x, y, x + 70, y + 50], fill="black"); dr.text((x + 8, y + 3), f[:2], fill="yellow", font=font)
    sh.save(f"{B}/sheet-{i}.jpg", quality=80)
    facts = {k: r.get(k) for k in ("id", "type", "maker", "model", "ton", "year", "firstReg", "km", "price", "tm", "fuel", "color", "plate", "seizure", "mortgage", "title_hint", "desc")}
    facts["n_photos"] = len(fs)
    facts["photos"] = r["photos"]          # 보류할 때 desc-hold 파일에 그대로 넣는다 (사진 변경 감지용)
    facts["held_before"] = os.path.exists(f"{S}/data/desc-hold/{i}.json")
    facts["rewrite"] = i in rewrite             # 상세설명 없이 썼던 소개글 → 새로 써서 덮어쓸 것
    json.dump(facts, open(f"{B}/facts-{i}.json", "w"), ensure_ascii=False, indent=1)
print("고름", len(pick), "대 / 남은 소개글 없는 매물", len([r for r in d if r["id"] not in done]) - len(pick), "대 (사진 2장 이하 포함) / 상세설명 미입력 대기", len(no_desc), "대")
print(",".join(r["id"] for r in pick) or "NONE")
