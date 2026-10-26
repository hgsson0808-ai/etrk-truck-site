"""카매니저 홈페이지 전체 매물 수집 → data/all_raw.json

사용: python3 sync.py            (목록 + 상세 전부)
      python3 sync.py --limit 30 (시험용)
- 카매니저 분류명을 18개 차종으로 바꾸고, 취급 기준(config.is_handled)을 적용한다.
- 상세 페이지는 동시에 4개까지만 요청한다 (원본 서버 부담 줄이기).
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import scrape
from config import is_handled

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "all_raw.json")

# 카매니저 분류 → 18개 차종 (None = 취급 안 함)
def to_type(category, text):
    c, t = category, text
    # 버큠·살수 글자는 '분류가 정해지지 않은 액체운반류'에서만 본다 (설명글 전체를 훑으면 윙바디·냉동탑까지 버큠로리로 잘못 들어감)
    BODY = ("윙", "냉동", "냉장", "카고", "덤프", "집게", "셀프", "암롤", "익스", "내장탑", "고소작업", "크레인", "바가지", "진개", "음식물", "활어")
    if not any(b in c for b in BODY):
        if "버큠" in t: return "버큠로리"
        if "살수" in t: return "살수차"
    if "음식물" in c: return "음식물수거차"
    if "진개" in c: return "압착진개차"
    if "활어" in c: return "활어차"
    if "홈로리" in c or "탱크로리" in c: return "탱크로리"
    if "기타액체" in c: return "탱크로리"
    if "고소작업" in c: return "바가지차" if "바가지" in t else "고소작업차"
    if "카고크레인" in c: return "카고크레인"
    if "집게" in c: return "집게차"
    if "셀프" in c: return "셀프로더"
    if "암롤" in c: return "암롤"
    if "덤프" in c: return "덤프"
    if "냉동" in c or "냉장" in c: return "냉동탑"
    if "익스" in c or "하이내장" in c: return "익스탑"
    if "내장탑" in c: return "내장탑"
    if "윙" in c: return "윙바디"
    if c.startswith("카고"): return "카고"
    # 소형화물(1톤급) 분류: [바가지차] [홈로리] [이동주유] [유조차] [크레인] [덤프] …
    if "바가지" in c: return "바가지차"
    if "이동주유" in c or "유조" in c: return "탱크로리"
    if "크레인" in c: return "카고크레인"
    return None


MAKERS = ["현대", "기아", "타타대우", "대우", "쌍용", "한국상용트럭", "볼보", "스카니아", "만(MAN)", "MAN", "벤츠", "이베코", "다프", "DAF", "이스즈", "후소"]


def find_maker(*texts):
    """제조사: 상세 '차종' 값 → 매물명 순서로, 단어 단위로 찾는다 ('4,500만원'의 '만' 오인 방지)."""
    for t in texts:
        for w in re.split(r"[\s/,·()]+", t or ""):
            for mk in MAKERS:
                if w == mk or (mk in ("만(MAN)", "MAN") and w in ("만", "MAN")):
                    return "만(MAN)" if mk in ("만(MAN)", "MAN") else mk
        if t and "만(MAN)" in t: return "만(MAN)"
    return ""
MODELS = ["올뉴마이티", "더뉴마이티", "이마이티", "마이티", "메가트럭", "파비스", "엑시언트", "트라고", "뉴파워트럭", "파워트럭", "슈퍼트럭",
          "프리마", "노부스", "맥쎈", "구쎈", "더쎈", "봉고", "포터", "카운티", "에어로", "차세대", "e마이티"]


def parse(card, d):
    f, kv = d["fields"], {}
    for l in d["desc"]:
        if ":" in l:
            k, v = l.split(":", 1); kv[k.strip()] = v.strip()
    text = " ".join([card, d.get("vname", ""), " ".join(d["desc"])])
    cat = card.split(" ")[0]
    typ = to_type(cat, text)
    m = re.search(r"(\d{4})\s*년형\s*\|\s*(\d{8})", f.get("년형 | 등록", ""))
    year = int(m.group(1)) if m else (int(re.search(r"(\d{4})년", card).group(1)) if re.search(r"(\d{4})년", card) else None)
    first = f"{m.group(2)[:4]}-{m.group(2)[4:6]}-{m.group(2)[6:]}" if m else ""
    ton = (re.search(r"([\d.]+)\s*톤", kv.get("톤수", "")) or re.search(r"([\d.]+)톤\s*$", card) or re.search(r"([\d.]+)\s*톤", card))
    ton = ton.group(1) if ton else ""
    maker = find_maker(kv.get("차종", ""), d.get("vname", ""), card.split(" 판매중")[0])
    model = next((x for x in MODELS if x in (kv.get("차종", "") + " " + card).replace(" ", "")), "")
    if not maker and model:  # 모델명으로 제조사가 확정되는 경우만 채움
        maker = {"봉고": "기아"}.get(model) or ("타타대우" if model in ("프리마", "노부스", "맥쎈", "구쎈", "더쎈", "차세대") else
                 "현대" if model in ("올뉴마이티", "더뉴마이티", "이마이티", "마이티", "e마이티", "메가트럭", "파비스", "엑시언트", "트라고", "뉴파워트럭", "파워트럭", "슈퍼트럭", "포터", "카운티", "에어로") else "")
    sm = re.search(r"\|\s*(\S+)", f.get("압류 | 저당", "")); sz = re.search(r"^\s*(\S+)", f.get("압류 | 저당", ""))
    shop = re.search(r"판매상사\s*:\s*(.*?)\s*광고동의", f.get("판매방식", ""))
    mid = re.sub(r"^\S+\s+", "", card.split(" 판매중")[0])  # 분류명 뒤 ~ '판매중' 앞
    mid = re.sub(r"^(\d+(\.\d+)?톤(이상|이하)?|크레인|압착식|5톤이하|3톤이상|2\.5톤이하|5\.5톤이상|5톤이상|4\.5톤이하)\s+", "", mid)
    for w in ([maker] if maker else []) + MODELS:
        mid = re.sub(r"(?<![가-힣])" + re.escape(w) + r"(?![가-힣])", " ", mid) if len(w) < 3 else mid.replace(w, " ")
    title = re.sub(r"\s+", " ", re.sub(r"[\d.]+\s*톤", " ", mid)).strip(" ,/·")[:40]
    return {
        "id": d.get("onCarNo"), "enc": d["enc"], "category": cat, "type": typ, "maker": maker, "model": model, "ton": ton,
        "title_hint": title or (kv.get("옵션", "")[:40]), "plate": d.get("plate", ""),
        "price": int(re.sub(r"\D", "", d.get("price", "") or "0") or 0),
        "year": year, "firstReg": first, "fuel": f.get("연료", ""), "tm": f.get("변속기", ""), "color": f.get("색상", ""),
        "km": int(re.sub(r"\D", "", f.get("주행거리", "") or "0") or 0),
        "seizure": sz.group(1) if sz else "", "mortgage": sm.group(1) if sm else "",
        "tax": f.get("세금미납", ""), "presentNo": f.get("제시번호", ""),
        "perfNo": (f.get("성능번호", "").split(" ")[0] if f.get("성능번호") else ""),
        "saleShop": shop.group(1).strip() if shop else "",
        "desc": [l for l in d["desc"] if not l.startswith("☎")], "photos": d["photos"], "card": card, "vname": d.get("vname", ""),
    }


_FP = os.path.join(ROOT, "data", "maker_fill.json")
FILL = json.load(open(_FP, encoding="utf-8")) if os.path.exists(_FP) else {}


def recheck(out):
    """취급 기준 다시 적용 (차종·사진·가격·config.is_handled)."""
    for r in out:
        # 차종은 매번 분류명·매물 제목으로 다시 정한다 (예전 잘못된 분류가 남지 않게)
        r["type"] = to_type(r.get("category", ""), (r.get("card", "") + " " + r.get("vname", "")))
        if r["type"] is None:  # 18개 차종 밖(사료운반차·카캐리어 등)도 취급 → 카매니저 분류명을 차종으로
            r["type"] = (r.get("category") or "기타특장차").strip()
        # 사장님이 목록으로 확인해 준 제조사·모델만 채운다 (data/maker_fill.json) — 다른 매물의 제조사는 건드리지 않는다
        f = FILL.get(r.get("id"))
        if f and not r.get("maker"):
            r["maker"] = f["maker"]
            if f.get("model") and not r.get("model"): r["model"] = f["model"]
        if not r["photos"] or not r["price"]:
            r["handled"], r["why"] = False, "사진 또는 가격 없음"
        else:
            ok, why = is_handled(r); r["handled"], r["why"] = ok, why


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    t0 = time.time()
    cards = scrape.list_all()
    print(f"목록 {len(cards)}대 ({time.time()-t0:.0f}초)", flush=True)
    if limit: cards = cards[:limit]
    out, fails = [], []
    prev_all = {r["enc"]: r for r in json.load(open(OUT, encoding="utf-8"))} if os.path.exists(OUT) else {}
    if "--quick" in sys.argv and os.path.exists(OUT):  # 빠른 확인: 목록 카드 글(가격·주행거리 등)이 그대로인 매물은 상세를 다시 받지 않음
        prev = {r["enc"]: r for r in json.load(open(OUT, encoding="utf-8"))}
        keep = [c for c in cards if c["enc"] in prev and prev[c["enc"]].get("card") == c["card"]]
        out = [prev[c["enc"]] for c in keep]
        kept = {c["enc"] for c in keep}
        cards = [c for c in cards if c["enc"] not in kept]
        print(f"그대로 {len(out)}대, 새로 받을 {len(cards)}대", flush=True)
    with ThreadPoolExecutor(2) as ex:
        futs = {ex.submit(scrape.detail, c["enc"]): c for c in cards}
        for i, fu in enumerate(as_completed(futs), 1):
            c = futs[fu]
            try:
                out.append(parse(c["card"], fu.result()))
            except Exception as e:
                try:  # 한 번 더 받아 본다
                    time.sleep(3); out.append(parse(c["card"], scrape.detail(c["enc"])))
                except Exception as e2:
                    fails.append((c["enc"], str(e2)[:80]))
                    # 상세를 못 받았다고 매물 페이지가 사라지지 않게, 지난번에 받아 둔 정보를 그대로 둔다 (다음 갱신 때 다시 받음)
                    if c["enc"] in prev_all: out.append(prev_all[c["enc"]])
            if i % 100 == 0: print(f"  상세 {i}/{len(cards)} ({time.time()-t0:.0f}초)", flush=True)
    recheck(out)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    ok = [r for r in out if r["handled"]]
    print(f"완료: 상세 {len(out)}대, 실패 {len(fails)}대, 취급 기준 통과 {len(ok)}대 ({time.time()-t0:.0f}초)")


if __name__ == "__main__":
    main()
