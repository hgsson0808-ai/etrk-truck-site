"""광고용 사이트 설정 — 업체 정보, 취급 기준 필터."""

import json as _json, os as _os
_B = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "brand.json"), encoding="utf-8"))
SITE = {k: v for k, v in _B.items() if not k.startswith("_")}
SITE["phone_tel"] = SITE["phone"].replace("-", "")
SITE["promises"] = [tuple(x) for x in SITE.get("promises", [])]
SITE["source_site"] = SITE["source_site"].rstrip("/")
SITE["img_host"] = SITE["img_host"].rstrip("/")

PERF_URL = "http://autocafe.co.kr/ASSO/CarCheck_Form_my.asp?OnCarNo={id}"
PHOTO_BASE = "https://myshop-img.carmanager.co.kr/temp/photo/"

IMPORT_BRANDS = ("이베코", "스카니아", "볼보", "MAN", "벤츠", "이스즈", "다프", "DAF", "TGS", "TGX", "후소")


def ton_value(ton: str) -> float:
    try:
        return float(ton)
    except (TypeError, ValueError):
        return 0.0


# 톤수 구간 (바디 기준): 1톤 / 2.5톤 / 3.5톤 / 4.5~5톤 / 5톤 이상
#   1톤 = 2톤 미만 · 2.5톤 = 2~2.5톤 · 3.5톤 = 3~4.2톤 · 4.5~5톤 = 4.5~5.5톤 · 5톤 이상 = 5.5톤 초과
TON_BUCKETS = [("1", "1톤", "1톤"), ("2.5", "2.5톤", "2.5톤"), ("3.5", "3.5톤", "3.5톤"), ("5", "4.5~5톤", "4.5-5톤"), ("L", "5톤 이상", "5톤이상")]


# 톤수 분류는 등록 톤수가 아니라 "바디(캡)" 기준 — 증톤·가변축으로 등록 톤수가 올라가도 바디가 같으면 같은 분류
HEAVY_MODELS = ("엑시언트", "트라고", "뉴파워트럭", "파워트럭", "슈퍼트럭", "맥쎈", "차세대")   # 대형 바디 → 5톤 이상
MEDIUM_MODELS = ("메가트럭", "파비스", "노부스", "구쎈")                                    # 중형(5톤) 바디 → 4.5~5톤
LIGHT_MODELS = ("마이티", "더쎈", "덱센", "쎈", "이마이티", "e마이티", "올뉴마이티", "더뉴마이티")  # 2.5·3.5톤 바디


def ton_bucket(ton, model="", body="") -> tuple[str, str, str]:
    """(키, 화면 표시, 주소용) 반환. model이 있으면 바디 기준으로 분류한다. body("5"/"L")는 사진으로 확인한 값."""
    v, m = ton_value(ton), (model or "")
    if body in ("5", "L"):
        return TON_BUCKETS[3 if body == "5" else 4]
    by_ton = 0 if v < 2 else 1 if v <= 2.5 else 2 if v <= 4.2 else 3 if v <= 5.5 else 4
    if any(k in m for k in HEAVY_MODELS):
        i = 4
    elif "프리마" in m:                       # 프리마: 9.5톤 이하는 중형 바디, 그 이상은 대형 (사장님 기준)
        i = 3 if v <= 9.5 else 4
    elif any(k in m for k in MEDIUM_MODELS):
        i = 3 if v < 14 else 4                # 14톤 이상은 입력 오류 가능 → 대형으로
    elif any(k in m for k in LIGHT_MODELS):
        i = 1 if v <= 2.5 else 2
    elif v > 5.5:                             # 모델 모름: 11톤 미만은 중형 증톤으로, 11톤 이상은 대형으로 본다
        i = 3 if v < 11 else 4
    else:
        i = by_ton
    return TON_BUCKETS[i]


def is_handled(car: dict) -> tuple[bool, str]:
    """취급 기준(지금은 전부 취급). (취급여부, 사유) 반환.
    2026-10-22 사장님: 수입차·대형 암롤·기타 특장차 등 전부 취급 → 제외 규칙 해제."""
    return True, ""
    t, ton = car.get("type", ""), ton_value(car.get("ton"))
    body = ton_bucket(car.get("ton"), car.get("model", ""), car.get("body", ""))[0]  # 바디 기준 분류
    text = " ".join([car.get("maker", ""), car.get("model", ""), car.get("title_hint", "")] + car.get("desc", []))
    domestic = car.get("maker") in ("현대", "기아", "타타대우", "대우")  # 국산 차는 엔진명(이베코 등)이 있어도 국산
    if not domestic and any(b in text for b in IMPORT_BRANDS):
        return False, "수입 트럭"
    if ton and ton < 2:
        if t not in ("집게차", "카고크레인", "바가지차", "고소작업차") and "홈로리" not in text:
            return False, "1톤은 바가지차·고소작업차(스카이)·카고크레인·집게차·홈로리만"
    if t == "덤프" and body == "L":
        return False, "덤프는 5톤급까지"
    if t in ("탱크로리", "암롤", "셀프로더", "압착진개차", "음식물수거차", "활어차", "카고크레인") and body == "L":
        return False, f"{t}는 5톤까지"
    if t == "살수차" and ton > 16:
        return False, "살수차는 16톤까지"
    return True, ""
