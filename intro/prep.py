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
done = {f[:-5] for f in os.listdir(f"{S}/data/desc") + os.listdir(f"{S}/data/desc-hold")}
pick = [r for r in d if r["id"] not in done and len(r["photos"]) >= 3][:N]
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
    json.dump(facts, open(f"{B}/facts-{i}.json", "w"), ensure_ascii=False, indent=1)
print("고름", len(pick), "대 / 남은 소개글 없는 매물", len([r for r in d if r["id"] not in done]) - len(pick), "대 (사진 2장 이하 포함)")
print(",".join(r["id"] for r in pick) or "NONE")
