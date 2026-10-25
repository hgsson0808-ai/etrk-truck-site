"""사이트를 올린 뒤 실행: 이번 빌드에서 바뀐 주소를 네이버·빙(IndexNow)에 바로 알린다.
사용: python3 indexnow.py   (dist/changed-urls.txt 를 읽음)"""
import os, json, requests
from urllib.parse import urlparse
from config import SITE
ROOT = os.path.dirname(os.path.abspath(__file__))
key = open(os.path.join(ROOT, "data", "indexnow_key.txt")).read().strip()
urls = [u for u in open(os.path.join(ROOT, "dist", "changed-urls.txt"), encoding="utf-8").read().split() if u]
if not urls: raise SystemExit("바뀐 주소 없음")
body = {"host": urlparse(SITE["domain"]).netloc, "key": key, "keyLocation": f"{SITE['domain']}/{key}.txt", "urlList": urls[:10000]}
for ep in ("https://searchadvisor.naver.com/indexnow", "https://api.indexnow.org/indexnow"):
    try:
        r = requests.post(ep, data=json.dumps(body), headers={"Content-Type": "application/json; charset=utf-8"}, timeout=20)
        print(ep, r.status_code, len(urls), "개 주소")
    except Exception as e:
        print(ep, "실패:", e)
