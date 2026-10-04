#!/bin/bash
# Забирает изменения из GitHub. Запускается таймером раз в минуту от root.
# База рекордов лежит в /var/lib/bunker17 и этим скриптом не затрагивается.
set -e
cd /opt/bunker17
before=$(git rev-parse HEAD)
git fetch -q origin main
git reset -q --hard origin/main
after=$(git rev-parse HEAD)
[ "$before" = "$after" ] && exit 0
changed=$(git diff --name-only "$before" "$after")
echo "bunker17: $before -> $after"
if echo "$changed" | grep -q '^deploy/nginx.conf$'; then
  cp deploy/nginx.conf /etc/nginx/sites-available/bunker17
  nginx -t && systemctl reload nginx
fi
if echo "$changed" | grep -Eq '^deploy/.*\.(service|timer)$'; then
  cp deploy/*.service deploy/*.timer /etc/systemd/system/
  systemctl daemon-reload
fi
if echo "$changed" | grep -Eq '^api/|^deploy/bunker17-api.service$'; then
  systemctl restart bunker17-api
fi
