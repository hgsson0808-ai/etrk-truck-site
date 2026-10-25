"""차종별 주요 제원 뽑기.

매물 설명·옵션·제목에 적힌 글자에서만 값을 찾는다 (추측해서 채우지 않음).
값이 없으면 '전화 문의'로 표시해 손님이 바로 물어볼 수 있게 한다.
"""
import re

ASK = "전화 문의"

# 차종별로 보여줄 제원 항목 (순서대로)
SCHEMA = {
    "카고":       ["적재함 길이", "적재함 폭", "축", "마력"],
    "윙바디":     ["적재함 길이", "적재함 폭", "적재함 높이", "파렛트", "축", "마력"],
    "냉동탑":     ["적재함 길이", "적재함 높이", "냉동기", "파렛트", "축", "마력"],
    "익스탑":     ["적재함 길이", "적재함 높이", "옆문", "마력"],
    "내장탑":     ["적재함 길이", "적재함 높이", "파렛트", "옆문", "마력"],
    "활어차":     ["탱크 용량", "탱크 재질", "장비", "마력"],
    "카고크레인": ["적재함 길이", "크레인", "축", "마력"],
    "집게차":     ["적재함 길이", "크레인", "마력"],
    "바가지차":   ["작업 높이", "장비", "마력"],
    "고소작업차": ["작업 높이", "장비", "마력"],
    "셀프로더":   ["적재함 길이", "윈치", "마력"],
    "덤프":       ["적재함 길이", "구동", "덮개", "마력"],
    "암롤":       ["박스 규격", "축", "마력"],
    "압착진개차": ["적재 용량", "장비", "마력"],
    "음식물수거차": ["탱크 용량", "탱크 재질", "장비", "마력"],
    "자동사다리차": ["작업 높이", "장비", "마력"],
    "탱크로리":   ["탱크 용량", "탱크 재질", "용도", "릴·펌프", "마력"],
    "살수차":     ["탱크 용량", "탱크 재질", "펌프·노즐", "마력"],
    "버큠로리":   ["탱크 용량", "탱크 재질", "진공펌프", "마력"],
}
# 이 항목들은 값이 없으면 '전화 문의'로 표시 (구매 판단에 꼭 필요한 것)
MUST = {"적재함 길이", "적재함 높이", "탱크 용량", "탱크 재질", "작업 높이", "크레인", "박스 규격", "적재 용량"}

NUM = r"(\d{1,2}[,.]?\d{3}|\d{1,2}(?:\.\d{1,2})?)"


def _mm(s):
    """'8,300' / '8300' / '8.3' / '8m30' → '8,300mm' 형식."""
    s = s.replace(",", "")
    v = float(s)
    if v < 30:          # 미터 단위
        v *= 1000
    return f"{int(round(v)):,}mm"


def _find(pats, text):
    for p in pats:
        m = re.search(p, text)
        if m:
            return m
    return None


def extract(c):
    """c: 매물 dict (type, ton, title_hint, model, desc[...]) → [(항목, 값)]"""
    t = c.get("type", "")
    kv = {}
    for l in c.get("desc", []):
        if ":" in l:
            k, v = l.split(":", 1)
            if v.strip():
                kv[k.strip()] = v.strip()
    text = " ".join([c.get("title_hint", ""), c.get("model", ""), kv.get("옵션", ""), kv.get("적재함", ""),
                     kv.get("특이사항", ""), kv.get("차종", ""), kv.get("탱크", ""), kv.get("크레인", "")]
                    + [f"{k} {v}" for k, v in kv.items()])
    box = kv.get("적재함", "")
    out = {}

    # --- 적재함 치수: '10,200 × 2,400' 또는 '6,700 × 2,300 × 2,300' (길이 × 폭 × 높이)
    m = re.search(r"(\d{1,2},?\d{3})\s*(?:mm)?\s*[×xX\*]\s*(\d,?\d{3})(?:\s*(?:mm)?\s*[×xX\*]\s*(\d,?\d{3}))?", text)
    if m:
        out["적재함 길이"], out["적재함 폭"] = _mm(m.group(1)), _mm(m.group(2))
        if m.group(3): out["적재함 높이"] = _mm(m.group(3))
    m = re.search(r"길이\s*" + NUM, box + " " + text)
    if "적재함 길이" in out: pass
    elif m: out["적재함 길이"] = _mm(m.group(1))
    else:
        m = re.search(r"(\d{1,2})\s*m\s*(\d{1,2})(?!\d)", text)          # 8m30, 6m2
        if m: out["적재함 길이"] = _mm(f"{m.group(1)}.{m.group(2).ljust(2, '0')}")
        else:
            m = re.search(r"(\d{1,2}(?:\.\d{1,2})?)\s*(?:m|미터)\s*(?:적재함|카고|윙|탑|짜리)", text) or re.search(r"적재함\s*(\d{1,2}(?:\.\d{1,2})?)\s*m(?!m)", text)
            if m: out["적재함 길이"] = _mm(m.group(1))
    m = re.search(r"폭\s*" + NUM, box + " " + text)
    if "적재함 폭" in out: pass
    elif m: out["적재함 폭"] = _mm(m.group(1))
    elif "광폭" in text and "광폭 아님" not in text: out["적재함 폭"] = "광폭"
    elif "일반폭" in text: out["적재함 폭"] = "일반폭"
    m = re.search(r"높이\s*" + NUM, box + " " + text)
    if "적재함 높이" in out: pass
    elif m: out["적재함 높이"] = _mm(m.group(1))
    elif re.search(r"하이\s*(탑|내장|윙)|익스", text): out["적재함 높이"] = "하이탑"

    # --- 공통
    m = re.search(r"(\d{3})\s*마력", text)
    if m: out["마력"] = f"{m.group(1)}마력"
    m = _find([r"(가변축|후축|앞축|전축|3축|4축|5축|탠덤|초장축|장축|단축)"], text)
    if m: out["축"] = m.group(1)
    m = re.search(r"(\d{1,2})\s*(?:파렛트|빠레트|파레트|팔레트|PL)", text) or re.search(r"(?:파렛트|빠레트|파레트|팔레트)\s*(\d{1,2})\s*장", text)
    if m: out["파렛트"] = f"{m.group(1)}파렛트"

    # --- 냉동탑
    m = _find([r"(투냉|단냉)", r"(영하\s*\d+\s*도|-\s*\d+\s*℃)"], text)
    if m: out["냉동기"] = m.group(1)
    if re.search(r"옆문\s*(\d)", text): out["옆문"] = re.search(r"옆문\s*(\d)", text).group(1) + "개"

    # --- 크레인·장비
    m = _find([r"((?:동양|수산|광림|인성|히아브|HIAB|해태|DY|팔핑거|PALFINGER)[\w\s\-]{0,12}?\d{2,5}[A-Z]{0,3})",
               r"((?:동양|수산|광림|인성|히아브|HIAB|해태|팔핑거))"], text)
    if m: out["크레인"] = m.group(1).strip()
    m = _find([r"((?:호룡|노바스|동해|한성|DHT|HS)\s*[\w\-]*\d{2,4}[A-Z\-]*)"], text)
    if m: out["장비"] = m.group(1).strip()
    if "장비" not in out:
        m = re.search(r"(동양특장|동양|현대특장|대흥특장|에이엠|한국쓰리축|원쓰리|토미|신세계|오텍|엠뱅크|광림|수산|호룡|노바스|한성특장|진우)", text)
        if m: out["장비"] = m.group(1)
    m = re.search(r"작업\s*높이\s*(\d{1,2}(?:\.\d)?)\s*m", text) or re.search(r"(\d{2}(?:\.\d)?)\s*m\s*(?:스카이|고소|사다리)", text)
    if m: out["작업 높이"] = f"{m.group(1)}m"
    if "윈치" in text: out["윈치"] = "있음"
    if re.search(r"4륜|4WD|사륜", text): out["구동"] = "4륜"
    m = _find([r"(자동\s*덮개|전동\s*덮개|수동\s*덮개)"], text)
    if m: out["덮개"] = m.group(1).replace(" ", "")

    # --- 탱크
    m = re.search(r"(\d{1,2}(?:\.\d)?)\s*KL", text)
    if m: out["탱크 용량"] = f"{int(float(m.group(1)) * 1000):,}L"
    m = None if "탱크 용량" in out else re.search(r"(\d{1,2}[,.]?\d{3}|\d{1,2}(?:\.\d)?)\s*(리터|ℓ|L(?![a-z])|톤\s*탱크|㎥|루베|헤베)", text)
    if m:
        n, u = m.group(1), m.group(2)
        if u in ("리터", "ℓ", "L"): out["탱크 용량"] = f"{int(float(n.replace(',', ''))):,}L"
        elif "탱크" in u: out["탱크 용량"] = f"{n}톤"
        else: out["적재 용량" if t == "압착진개차" else "탱크 용량"] = f"{n}㎥"
    m = _find([r"(스테인리스|스텐|SUS\s*\d*|서스)", r"(알루미늄|알미늄)", r"(FRP|에프알피)", r"(철\s*탱크|스틸)"], text)
    if m:
        w = m.group(1)
        out["탱크 재질"] = {"스텐": "스테인리스", "서스": "스테인리스", "알미늄": "알루미늄", "에프알피": "FRP"}.get(w, w)
    m = _find([r"(경질유|중질유|등유|경유|휘발유|LPG|식용유|화학|물탱크)"], kv.get("특이사항", "") + " " + c.get("title_hint", ""))
    if m and t == "탱크로리": out["용도"] = m.group(1)
    m = _find([r"(전동\s*릴|자동\s*릴|수동\s*릴|유량계|펌프)"], text)
    if m: out["릴·펌프" if t == "탱크로리" else "펌프·노즐"] = m.group(1).replace(" ", "")
    m = re.search(r"(진공\s*펌프[\w\s]{0,10})", text)
    if m: out["진공펌프"] = m.group(1).strip()
    m = re.search(r"(\d{1,2})\s*(?:㎥|루베)\s*박스|박스\s*(\d{1,2})\s*(?:㎥|루베)", text)
    if m: out["박스 규격"] = (m.group(1) or m.group(2)) + "㎥"

    rows = [("톤수", f"{c.get('ton')}톤")]
    for k in SCHEMA.get(t, ["적재함 길이", "마력"]):
        if k in out: rows.append((k, out[k]))
        elif k in MUST: rows.append((k, ASK))
    for k in ("사고유무", "특이사항"):
        if kv.get(k): rows.append((k, kv[k]))
    if kv.get("옵션"): rows.append(("옵션", kv["옵션"]))
    return rows
