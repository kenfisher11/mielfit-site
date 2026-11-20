#!/bin/sh
# 홈페이지 날짜(asof)를 오늘(KST)로 갱신해 main에 push. 컨테이너 교체 후 build_site 대신 쓰는 간이판(11/20)
set -e
D=$(TZ=Asia/Seoul date +%F)
[ -d /home/claude/mielfit-site/.git ] || git clone -q --depth 2 https://github.com/kenfisher11/mielfit-site.git /home/claude/mielfit-site
cd /home/claude/mielfit-site && git checkout -q main && git pull -q --depth 2 origin main
grep -q "\"asof\":\"$D\"" mielfit-data.js && { echo "already $D"; exit 0; }
sed -i "0,/\"asof\":\"[0-9-]*\"/s//\"asof\":\"$D\"/" mielfit-data.js
git add mielfit-data.js && git -c user.name=mielfit-bot -c user.email=bot@mielfit commit -qm "mielfit site date $D" && git push -q origin main && echo "pushed $D"
