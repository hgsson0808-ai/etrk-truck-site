"""차종별 실사풍 측면 트럭 일러스트(SVG) 생성기 — 그라데이션·광택·그림자로 입체감."""
import os

W, H = 240, 120
GROUND = 101

DEFS = """<defs>
<linearGradient id="cab" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#eef1f4"/><stop offset="1" stop-color="#c6cdd5"/></linearGradient>
<linearGradient id="cabSide" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d5dbe2"/><stop offset=".25" stop-color="#ffffff"/><stop offset="1" stop-color="#e6eaee"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5c7a96"/><stop offset=".45" stop-color="#22374d"/><stop offset="1" stop-color="#101c29"/></linearGradient>
<linearGradient id="alu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fbfcfd"/><stop offset=".5" stop-color="#e3e7ec"/><stop offset="1" stop-color="#b9c1ca"/></linearGradient>
<linearGradient id="alu2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#d9dee4"/><stop offset=".5" stop-color="#f6f7f9"/><stop offset="1" stop-color="#cfd5dc"/></linearGradient>
<linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9edf1"/><stop offset=".18" stop-color="#ffffff"/><stop offset=".45" stop-color="#a7b0ba"/><stop offset=".7" stop-color="#d8dde3"/><stop offset="1" stop-color="#7d8792"/></linearGradient>
<linearGradient id="steel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6d7783"/><stop offset=".5" stop-color="#4a535e"/><stop offset="1" stop-color="#2c333b"/></linearGradient>
<linearGradient id="frame" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a3f46"/><stop offset="1" stop-color="#15181c"/></linearGradient>
<linearGradient id="orange" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc24d"/><stop offset=".5" stop-color="#f39a12"/><stop offset="1" stop-color="#c46d00"/></linearGradient>
<linearGradient id="red" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f2655c"/><stop offset=".5" stop-color="#d4291f"/><stop offset="1" stop-color="#9c1810"/></linearGradient>
<linearGradient id="green" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7fae8c"/><stop offset=".5" stop-color="#4d7f5d"/><stop offset="1" stop-color="#2f5a3d"/></linearGradient>
<linearGradient id="teal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9cc9be"/><stop offset=".5" stop-color="#6aa596"/><stop offset="1" stop-color="#457d70"/></linearGradient>
<linearGradient id="yellow" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe27a"/><stop offset=".5" stop-color="#f5c21b"/><stop offset="1" stop-color="#c79500"/></linearGradient>
<linearGradient id="navy" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3f6690"/><stop offset="1" stop-color="#1a3556"/></linearGradient>
<radialGradient id="tire" cx=".5" cy=".5" r=".5"><stop offset=".62" stop-color="#2a2d31"/><stop offset=".85" stop-color="#16181b"/><stop offset="1" stop-color="#050607"/></radialGradient>
<radialGradient id="rim" cx=".42" cy=".38" r=".7"><stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#d3d9df"/><stop offset="1" stop-color="#7b8590"/></radialGradient>
<radialGradient id="shadow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".38"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
</defs>"""


def wheel(x, dual=False):
    r = 13
    s = f'<circle cx="{x}" cy="{GROUND-r}" r="{r}" fill="url(#tire)"/>'
    s += f'<circle cx="{x}" cy="{GROUND-r}" r="7.2" fill="url(#rim)" stroke="#6a737d" stroke-width=".6"/>'
    s += f'<circle cx="{x}" cy="{GROUND-r}" r="3" fill="#8e98a2" stroke="#5a636c" stroke-width=".5"/>'
    for dx, dy in ((0, -5), (4.3, -2.5), (4.3, 2.5), (0, 5), (-4.3, 2.5), (-4.3, -2.5)):
        s += f'<circle cx="{x+dx:.1f}" cy="{GROUND-r+dy:.1f}" r=".8" fill="#5a636c"/>'
    if dual:
        s += f'<circle cx="{x}" cy="{GROUND-r}" r="9.6" fill="none" stroke="#3a3e43" stroke-width=".8" opacity=".6"/>'
    return s


def fender(x, w=34):
    return (f'<path d="M{x-w/2} {GROUND-12} Q{x-w/2} {GROUND-30} {x} {GROUND-30} Q{x+w/2} {GROUND-30} {x+w/2} {GROUND-12}" '
            f'fill="none" stroke="#1d2126" stroke-width="3.2" stroke-linecap="round"/>')


def cab(tall=False):
    top = 22 if tall else 28
    # 캡 본체 (앞이 왼쪽)
    s = (f'<path d="M24 86 L21 52 Q20 {top+4} 30 {top} L68 {top} Q77 {top} 79 {top+9} L81 86 Z" fill="url(#cab)" stroke="#8d97a2" stroke-width=".8"/>')
    # 앞유리 (측면에서 보이는 경사면)
    s += f'<path d="M24 {top+8} Q25 {top+3} 31 {top+2} L37 {top+2} L33 {top+25} L22.5 {top+26} Z" fill="url(#glass)"/>'
    # 옆창
    s += f'<path d="M39 {top+3} L70 {top+3} Q74 {top+3} 74 {top+8} L74 {top+22} L37 {top+24} Z" fill="url(#glass)"/>'
    s += f'<path d="M42 {top+5} L58 {top+5} L44 {top+19} Z" fill="#fff" opacity=".18"/>'
    # 문선·손잡이·스텝
    s += f'<path d="M36 {top+2} L34 84" stroke="#9aa4ae" stroke-width=".8" fill="none"/>'
    s += f'<path d="M75 {top+4} L77 84" stroke="#9aa4ae" stroke-width=".8" fill="none"/>'
    s += f'<rect x="64" y="{top+28}" width="7" height="1.6" rx=".8" fill="#7a848e"/>'
    s += '<rect x="44" y="80" width="22" height="3" rx="1" fill="#2a2f35"/>'
    # 장식 스트라이프
    s += f'<path d="M37 {top+33} L76 {top+31} L77 {top+35} L37 {top+38} Z" fill="url(#navy)" opacity=".85"/>'
    # 범퍼·헤드램프·그릴
    s += '<path d="M20 74 L30 74 L31 88 L22 88 Z" fill="url(#steel)"/>'
    s += '<rect x="21" y="66" width="7" height="5" rx="1.5" fill="#fff8d9" stroke="#9aa4ae" stroke-width=".6"/>'
    s += f'<rect x="21.5" y="{top+28}" width="3" height="16" rx="1" fill="#3a434c"/>'
    # 사이드미러
    s += f'<path d="M30 {top+6} L17 {top+8}" stroke="#2a2f35" stroke-width="1.6"/><rect x="13.5" y="{top+5}" width="5" height="12" rx="1.5" fill="#2a2f35"/>'
    # 캡 광택
    s += f'<path d="M30 {top+1} L66 {top+1}" stroke="#fff" stroke-width="1.4" opacity=".9"/>'
    return s


def chassis(x2=226):
    return f'<rect x="72" y="80" width="{x2-72}" height="7" rx="1.5" fill="url(#frame)"/>'


def box(x1, y1, x2, y2, fill="url(#alu)", ribs=6, rib_color="#a9b2bc"):
    s = f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" rx="2" fill="{fill}" stroke="#8e98a3" stroke-width=".8"/>'
    step = (x2 - x1) / ribs
    for i in range(1, ribs):
        x = x1 + step * i
        s += f'<path d="M{x:.1f} {y1+2} V{y2-2}" stroke="{rib_color}" stroke-width=".7"/>'
    s += f'<path d="M{x1+2} {y1+1.5} H{x2-2}" stroke="#fff" stroke-width="1.2" opacity=".9"/>'
    s += f'<rect x="{x1}" y="{y2-4}" width="{x2-x1}" height="4" fill="#8f99a4" opacity=".55"/>'
    return s


def tank(x1, y1, x2, y2, fill="url(#chrome)", bands=3):
    h = y2 - y1
    s = f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{h}" rx="{h/2}" fill="{fill}" stroke="#7d8792" stroke-width=".8"/>'
    step = (x2 - x1) / (bands + 1)
    for i in range(1, bands + 1):
        x = x1 + step * i
        s += f'<path d="M{x:.1f} {y1+1} V{y2-1}" stroke="#6f7984" stroke-width="1.2" opacity=".55"/>'
    s += f'<path d="M{x1+h/2} {y1+h*.22} H{x2-h/2}" stroke="#fff" stroke-width="2" opacity=".85"/>'
    return s


def deck(x1=84, x2=226, gates=True):
    s = f'<rect x="{x1}" y="70" width="{x2-x1}" height="10" fill="url(#alu2)" stroke="#8e98a3" stroke-width=".8"/>'
    if gates:
        s += f'<rect x="{x1}" y="62" width="{x2-x1}" height="9" fill="url(#alu)" stroke="#8e98a3" stroke-width=".8"/>'
        for i in range(1, 4):
            x = x1 + (x2 - x1) * i / 4
            s += f'<path d="M{x:.1f} 62 V80" stroke="#8e98a3" stroke-width=".8"/>'
        s += f'<rect x="{x1}" y="58" width="5" height="22" fill="url(#steel)"/>'
    return s


def boom(x1, y1, x2, y2, fill="url(#orange)", w=6):
    import math
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy); nx, ny = -dy / L * w / 2, dx / L * w / 2
    return (f'<path d="M{x1+nx:.1f} {y1+ny:.1f} L{x2+nx:.1f} {y2+ny:.1f} L{x2-nx:.1f} {y2-ny:.1f} L{x1-nx:.1f} {y1-ny:.1f} Z" '
            f'fill="{fill}" stroke="#8a4d00" stroke-width=".6"/>'
            f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" stroke="#fff" stroke-width=".8" opacity=".5"/>')


def column(x=84, top=40, fill="url(#orange)"):
    return (f'<rect x="{x}" y="{top}" width="9" height="{80-top}" rx="1.5" fill="{fill}" stroke="#8a4d00" stroke-width=".6"/>'
            f'<rect x="{x-3}" y="74" width="15" height="7" rx="1" fill="url(#steel)"/>')


def body_for(t):
    tandem = False
    if t == "카고":
        b = deck()
    elif t == "윙바디":
        b = box(84, 34, 226, 80, ribs=8)
        b += '<path d="M84 39 H226" stroke="#7d8792" stroke-width="1.2"/><rect x="150" y="31" width="4" height="4" fill="#7d8792"/>'
        b += '<rect x="84" y="72" width="142" height="5" fill="#f5c21b" opacity=".85"/>'
    elif t == "냉동탑":
        b = box(84, 34, 226, 80, ribs=5)
        b += '<rect x="84" y="26" width="26" height="9" rx="2" fill="url(#alu2)" stroke="#8e98a3" stroke-width=".8"/>'
        b += '<g stroke="#6f7984" stroke-width=".7">' + "".join(f'<path d="M{88+i*4} 28 V33"/>' for i in range(5)) + '</g>'
        b += '<rect x="140" y="40" width="22" height="34" rx="1" fill="none" stroke="#8e98a3" stroke-width="1"/><rect x="157" y="55" width="3" height="6" rx="1" fill="#6f7984"/>'
    elif t == "익스탑":
        b = box(84, 22, 226, 80, ribs=6)
        b += '<rect x="150" y="30" width="24" height="44" rx="1" fill="none" stroke="#8e98a3" stroke-width="1"/>'
    elif t == "카고크레인":
        b = deck(98) + column(84, 34) + boom(88, 36, 214, 22) + boom(186, 25, 214, 22, w=4)
        b += '<path d="M213 23 V46" stroke="#333" stroke-width="1"/><path d="M209 46 h8 l-4 6 z" fill="#d4291f"/>'
    elif t == "바가지차":
        b = deck(98, gates=False) + column(84, 40, "url(#yellow)") + boom(88, 42, 200, 14, "url(#yellow)")
        b += '<path d="M196 4 h22 l-3 14 h-16 z" fill="url(#alu)" stroke="#7d8792" stroke-width=".8"/>'
    elif t == "집게차":
        b = deck(98) + column(84, 30) + boom(88, 32, 200, 18) + boom(200, 18, 206, 40, w=4)
        b += '<path d="M206 40 q-10 4 -8 16 M206 40 q10 4 8 16" stroke="#c46d00" stroke-width="3" fill="none" stroke-linecap="round"/>'
        b += '<circle cx="206" cy="40" r="3" fill="url(#steel)"/>'
    elif t == "음식물수거차":
        b = '<rect x="86" y="40" width="112" height="40" rx="14" fill="url(#chrome)" stroke="#7d8792" stroke-width=".8"/>'
        b += '<path d="M198 46 h26 v34 h-26 z" fill="url(#teal)" stroke="#2e5f53" stroke-width=".8"/>'
        b += '<path d="M100 48 H186" stroke="#fff" stroke-width="2" opacity=".8"/><rect x="120" y="34" width="20" height="7" rx="2" fill="url(#steel)"/>'
    elif t == "압착진개차":
        b = '<path d="M84 36 H186 L202 46 V80 H84 Z" fill="url(#green)" stroke="#2f5a3d" stroke-width=".8"/>'
        b += '<path d="M186 36 L226 50 V80 H202 V46 Z" fill="url(#steel)" stroke="#222" stroke-width=".6"/>'
        b += '<g stroke="#2f5a3d" stroke-width=".8">' + "".join(f'<path d="M{100+i*20} 38 V78"/>' for i in range(5)) + '</g>'
        b += '<path d="M88 40 H182" stroke="#fff" stroke-width="1.4" opacity=".5"/>'
    elif t == "덤프":
        tandem = True
        b = '<path d="M84 44 L226 38 L222 80 L88 80 Z" fill="url(#steel)" stroke="#1e242a" stroke-width=".8"/>'
        b += '<g stroke="#2a3138" stroke-width="2.2">' + "".join(f'<path d="M{108+i*24} 43 V79"/>' for i in range(5)) + '</g>'
        b += '<path d="M86 46 L224 40" stroke="#9aa4ae" stroke-width="1.4"/><path d="M84 44 L76 30 L90 30 L96 44" fill="url(#steel)"/>'
    elif t == "암롤":
        tandem = True
        b = box(98, 38, 226, 80, fill="url(#green)", ribs=7, rib_color="#2f5a3d")
        b += '<path d="M86 80 V36 H104 V44" stroke="url(#orange)" stroke-width="7" fill="none" stroke-linejoin="round"/>'
    elif t == "셀프로더":
        b = '<path d="M84 70 L230 86 L230 92 L84 78 Z" fill="url(#alu2)" stroke="#8e98a3" stroke-width=".8"/>'
        b += '<path d="M226 88 L238 99" stroke="#7d8792" stroke-width="3"/>'
        b += '<rect x="84" y="56" width="10" height="16" rx="1" fill="url(#steel)"/>'
    elif t == "자동사다리차":
        b = deck(98, gates=False) + column(86, 50, "url(#steel)")
        b += '<path d="M88 52 L232 22 M88 60 L232 30" stroke="#c9d0d8" stroke-width="3"/>'
        b += '<g stroke="#9aa4ae" stroke-width="1.6">' + "".join(f'<path d="M{100+i*14} {49.5-i*2.92:.1f} L{100+i*14} {57.5-i*2.92:.1f}"/>' for i in range(10)) + '</g>'
        b += '<rect x="196" y="20" width="16" height="10" rx="1" fill="url(#orange)" transform="rotate(-11 204 25)"/>'
    elif t == "탱크로리":
        tandem = True
        b = tank(86, 36, 226, 78) + '<rect x="120" y="30" width="10" height="7" rx="1" fill="url(#steel)"/><rect x="170" y="30" width="10" height="7" rx="1" fill="url(#steel)"/>'
    elif t == "살수차":
        tandem = True
        b = tank(86, 40, 220, 78)
        b += '<path d="M220 74 h10" stroke="#555" stroke-width="3"/><g stroke="#4aa3df" stroke-width="1.2" opacity=".8"><path d="M231 72 l7 -5"/><path d="M231 75 l8 0"/><path d="M231 78 l7 5"/></g>'
    elif t == "버큠로리":
        tandem = True
        b = tank(86, 38, 226, 78, fill="url(#yellow)")
        b += '<path d="M120 38 C120 22 170 22 172 34" stroke="#2a2f35" stroke-width="3.2" fill="none"/><circle cx="196" cy="34" r="6" fill="url(#steel)"/>'
    else:
        b = box(84, 34, 226, 80)
    return b, tandem


def svg(t):
    body, tandem = body_for(t)
    rear = [168, 196] if tandem else [190]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{t}">', DEFS]
    parts.append(f'<ellipse cx="124" cy="{GROUND+1}" rx="112" ry="7" fill="url(#shadow)"/>')
    parts.append(chassis())
    parts.append(body)
    parts.append(fender(48))
    for x in rear:
        parts.append(fender(x))
    parts.append(cab(tall=t in ('익스탑',)))
    parts.append(wheel(48))
    for x in rear:
        parts.append(wheel(x, dual=True))
    parts.append('</svg>')
    return "".join(parts)


TYPES = ["카고", "윙바디", "냉동탑", "카고크레인", "바가지차", "집게차", "익스탑", "음식물수거차", "압착진개차",
         "덤프", "암롤", "셀프로더", "자동사다리차", "탱크로리", "살수차", "버큠로리"]
ASCII = {"카고": "cargo", "윙바디": "wing", "냉동탑": "freezer", "카고크레인": "crane", "바가지차": "bucket", "집게차": "grab",
         "익스탑": "extop", "음식물수거차": "foodwaste", "압착진개차": "garbage", "덤프": "dump", "암롤": "armroll",
         "셀프로더": "selfloader", "자동사다리차": "ladder", "탱크로리": "tanker", "살수차": "sprayer", "버큠로리": "vacuum"}


def write_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for t in TYPES:
        open(os.path.join(out_dir, f"{ASCII[t]}.svg"), "w", encoding="utf-8").write(svg(t))


if __name__ == "__main__":
    write_all("data/type-art")
    print("ok")
