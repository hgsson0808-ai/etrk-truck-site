#!/usr/bin/env bash
# 매물 갱신: 카매니저 홈페이지(brand.json source_site) 공개 매물 가져오기 → 사이트 만들기 → main에 올리기(Cloudflare가 자동 배포)
# 사용: bash daily.sh             매시간용(바뀐 매물만 상세를 다시 받음)
#       FULL=1 bash daily.sh      전체 다시 받기(하루 한 번)
#       NO_PUSH=1 bash daily.sh   시험(올리지 않음)
set -euo pipefail
cd "$(dirname "$0")"
python3 -c "import requests, bs4, jinja2, PIL" 2>/dev/null || pip install -q -r requirements.txt --break-system-packages
git pull -q --rebase origin main || true
if [ -n "${FULL:-}" ]; then python3 sync.py; else python3 sync.py --quick; fi
python3 build.py site | tail -3
rm -rf site && cp -r dist/site site
git add -A site data/state.json data/all_raw.json data/hero
if git diff --cached --quiet; then echo "바뀐 매물 없음"; exit 0; fi
n=$(python3 -c "import json;print(len(json.load(open('site/cars.json'))))")
git -c user.name="${GIT_NAME:-truck-site-bot}" -c user.email="${GIT_EMAIL:-bot@users.noreply.github.com}" commit -qm "매물 갱신 $(TZ=Asia/Seoul date '+%F %H:%M') — ${n}대"
if [ -z "${NO_PUSH:-}" ]; then
  for t in 1 2 3; do git push -q origin HEAD:main && break || { git pull -q --rebase origin main; }; done
  echo "올림: ${n}대"
else echo "시험이라 올리지 않음: ${n}대"; fi
