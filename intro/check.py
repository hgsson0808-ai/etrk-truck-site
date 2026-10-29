"""소개글 검사: python3 intro/check.py 매물번호,매물번호,...  → remote 표시, 길이·전화번호·과장표현·FAQ·제목 쉼표 확인"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SITE
PH = SITE["phone"]
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ids = [i for i in sys.argv[1].split(",") if i and os.path.exists(f"{S}/data/desc/{i}.json")]
short, bad = [], []
for i in ids:
    p = f"{S}/data/desc/{i}.json"; d = json.load(open(p)); d["remote"] = True
    d["title"] = d["title"].replace(",", "")
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
    body = d["intro"] + "".join(s["text"] for s in d["sections"]) + d["outro"] + "".join(q["a"] for q in d["faq"])
    if len(body) < 1000: short.append((i, len(body)))
    vis = json.dumps({k: d[k] for k in ("title", "meta_description", "intro", "sections", "outro", "faq")}, ensure_ascii=False)
    if PH not in d["outro"]: bad.append((i, "phone"))
    for ph in re.findall(r"0\d{1,2}-\d{3,4}-\d{4}", vis):
        if ph != PH: bad.append((i, ph))
    for w in ["최상", "완벽", "강추", "대박", "무조건", "A급", "신차급", "거의 새"]:
        if w in vis: bad.append((i, w))
    if len(d["faq"]) != 4: bad.append((i, "faq", len(d["faq"])))
    if re.search(r"[A-HJ-NPR-Z0-9]{17}", vis): bad.append((i, "VIN?"))
print("검사", len(ids), "대 / 짧음", short, "/ 문제", bad)
