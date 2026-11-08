"""차량 상세 설명(소개글·판매자 설명·자주 묻는 질문)에서 가격을 뺀다.

가격은 매물 화면 위쪽 가격 칸에만 보이게 한다 (사장님 요청 2026-11-08).
가격이 바뀌거나 '가격 상담'으로 바뀌어도 설명 글과 어긋나지 않게 하려는 것.
  - 가격만 말하는 문장은 통째로 뺀다.
  - "…이고 판매 가격은 3,500만원입니다"처럼 문장 끝에 가격이 붙은 경우는 가격 부분만 떼고 문장을 살린다.
  - 그래도 가격이 남는 문장은 뺀다. (주행거리 '15만km' 같은 숫자는 건드리지 않음)
"""
import re

# 3,500만원 · 3500 만원 · 1억 2,000만원 · 1억원 · 3,500만 원(부가세 별도)
PRICE = r"(?:\d+\s*억\s*(?:\d[\d,]*\s*만\s*)?원|\d[\d,]*\s*만\s*원)(?:\s*\([^)]*\))?"
HAS_PRICE = re.compile(r"\d+\s*억\s*(?:\d[\d,]*\s*만\s*)?원|\d[\d,]*\s*만\s*원|(?:가격|판매가|금액)\s*[:：]\s*\d|(?:^|\s)\d{3,5}\s*만(?!\s*(?:km|키로|킬로|㎞))")
VAT = r"(?:\s*(?:이고|이며|,)\s*부가세(?:는)?\s*(?:별도|따로)(?:입니다|이에요)?)?"
# 문장 앞: "가격은 5,350만원, 판매 정보 주행거리는 …" → "판매 정보 주행거리는 …"
LEAD = re.compile(r"^(?:(?:판매\s*|희망\s*)?(?:가격|값|판매가)(?:은|는)?\s*" + PRICE + VAT + r"\s*(?:,|이고|이며|이고요)\s*|" + PRICE + r"\s*(?:에 나온|인|짜리)\s+)")
# 문장 끝: "… 30일이고 판매 가격은 7,900만원입니다" → "… 30일입니다"
TAIL = re.compile(r"\s*(?P<sep>이고|이며|,|고)?\s*,?\s*(?:판매\s*|희망\s*)?(?:가격|값|판매가)(?:은|는)\s*" + PRICE + VAT + r"\s*(?:입니다|이에요|예요)?(?=[.\s]*$)")
# 끝이 이 글자로 끝날 때만 "입니다"를 붙여도 문장이 자연스럽다
OK_END = re.compile(r"(?:\d|km|kg|리터|톤|mm|cm|m|[A-Za-z)]|일|년|월|식|대|번|색|차|장|형|급|축|마력|cc)$")


def _sentences(t):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]


def _fix(s):
    if not HAS_PRICE.search(s):
        return s
    r = _cut(s)
    if r and "부가세" in r and len(r) < 30:  # 가격을 빼고 나니 "부가세 별도"만 남은 문장 → 뺀다
        return None
    return r


def _cut(s):
    x = LEAD.sub("", s).strip()
    if x != s.strip() and not HAS_PRICE.search(x) and len(x) > 8:
        return x[0].upper() + x[1:] if x[0].isascii() else x
    m = TAIL.search(s)
    if m:
        head, sep = s[:m.start()].rstrip(" ,"), m.group("sep")
        if len(head) > 8 and not HAS_PRICE.search(head):
            if sep in ("이고", "이며"):  # 앞말이 이름씨(…차량이며) → "…차량입니다"
                return head + "입니다."
            if sep == "고" and re.search(r"(?:었|았|였|렸|했|됐|있|없)$", head):  # 달렸고 → 달렸습니다
                return head + "습니다."
            if OK_END.search(head):
                return head + "입니다."
    return None  # 가격만 말하거나 자연스럽게 떼기 어려운 문장 → 뺀다


def text(t):
    if not t or not HAS_PRICE.search(t):
        return t
    out = [x for x in (_fix(s.strip()) for s in _sentences(t)) if x]
    return " ".join(out)


def parts(h):
    """"2020년식 · 367,168km · 6,950만원(부가세 별도)" 같은 나열형 제목에서 가격 조각만 뺀다."""
    if not h or not HAS_PRICE.search(h):
        return h
    tok = re.split(r"(\s+·\s+|,\s+)", h)  # 숫자 속 쉼표(3,950)는 나누지 않음
    items, seps = tok[0::2], tok[1::2]
    out = ""
    for i, it in enumerate(items):
        if HAS_PRICE.search(it):
            continue
        out += (seps[i - 1] if out and i > 0 else "") + it
    return out.strip(" ·,") or h


def apply(c):
    """매물 정보 c 의 설명 글에서 가격을 뺀다 (화면 위 가격 칸은 그대로)."""
    c["headline"] = parts(c.get("headline", ""))
    c["intro"] = text(c.get("intro", ""))
    c["outro"] = text(c.get("outro", ""))
    secs = []
    for s in c.get("sections") or []:
        s = dict(s); s["text"] = text(s.get("text", ""))
        if s["text"].strip(): secs.append(s)
    c["sections"] = secs
    faq = []
    for q in c.get("faq") or []:
        if HAS_PRICE.search(q.get("q", "")): continue  # 가격을 묻는 질문은 뺀다
        a = text(q.get("a", ""))
        if a.strip(): faq.append({**q, "a": a})
    c["faq"] = faq
    if c.get("seller"):
        c["seller"] = [(k, v) for k, v in c["seller"] if not HAS_PRICE.search(f"{k} {v}") and k not in ("가격", "판매가", "금액")]
    return c
