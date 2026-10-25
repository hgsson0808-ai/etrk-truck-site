"""AI 설명이 아직 없는 매물용 자동 설명.

수집한 사실(연식·주행거리·차량번호·압류/저당·판매자 글)만 문장으로 정리한다.
사진 내용이나 차 상태를 추측해서 쓰지 않는다.
"""
from config import SITE

HIDE_KEYS = {"차종", "톤수", "연식", "변속기", "주행거리", "주행"}  # 위쪽 표에 이미 나오는 항목


def name_of(c):
    return " ".join(x for x in (c.get("maker"), c.get("model"), f"{c['ton']}톤", c["type"]) if x)


def seller_lines(c):
    out = []
    for l in c.get("desc", []):
        if ":" in l:
            k, v = (s.strip() for s in l.split(":", 1))
            if k in HIDE_KEYS or not v: continue
            out.append((k, v))
        elif l.strip():
            out.append(("", l.strip()))
    return out


def make(c):
    nm = name_of(c)
    km = f"{c['km']:,}km"
    man_km = f"{round(c['km'] / 10000)}만km" if c["km"] >= 10000 else km
    hint = (c.get("title_hint") or "").strip(" /,")
    title = f"{nm} {c['year']}년식 {man_km} 중고화물차"
    headline = f"{nm} {c['year']}년식" + (f" · {hint}" if hint else "")
    pz = "압류 " + (c.get("seizure") or "-") + " · 저당 " + (c.get("mortgage") or "-")
    meta = (f"{c['year']}년식 {nm} 매물, 주행거리 {km}, {c.get('tm') or ''} 변속기. "
            + (f"{hint}. " if hint else "")
            + f"차량번호 {c.get('plate')}, {pz}, 성능점검기록부 공개. {SITE['name']} {SITE['phone']}").replace("  ", " ")
    intro = (f"{c['year']}년식 {nm} 매물입니다. 주행거리는 {km}, 변속기는 {c.get('tm') or '-'}, 연료는 {c.get('fuel') or '-'}입니다. "
             f"차량번호 {c.get('plate')}로 등록원부상 {pz}입니다.")
    outro = ("판매자가 올린 정보를 그대로 정리했습니다. 적재함 치수, 장비 작동, 하체 상태처럼 사진만으로 알기 어려운 부분은 "
             f"전화 주시면 실물 기준으로 확인해 드립니다. {SITE['phone']}")
    faq = [
        {"q": "압류나 저당이 있나요?", "a": f"등록 정보 기준 {pz}입니다. 계약 전 등록원부로 다시 확인해 드립니다."},
        {"q": "성능점검기록부를 볼 수 있나요?", "a": f"네. 성능번호 {c.get('perfNo') or '-'} 기록부를 이 페이지의 '성능·상태점검기록부 보기'에서 바로 보실 수 있습니다."},
        {"q": "명의이전 서류는 어떻게 하나요?", "a": "사고팔 때 필요한 명의이전 서류는 " + SITE["name"] + "이(가) 챙겨 드립니다."},
        {"q": "차를 직접 보러 갈 수 있나요?", "a": f"네. 방문 전에 {SITE['phone']}로 연락 주시면 차량 위치와 시간을 맞춰 안내해 드립니다."},
    ]
    return dict(seo_title=title, headline=headline, meta=meta, cover=1, intro=intro, sections=[], outro=outro, faq=faq, notes=[])
