#!/bin/bash
# Первичная установка на сервере. Запускать от root из /opt/bunker17:
#   bash /opt/bunker17/deploy/install.sh
set -e
cd /opt/bunker17
apt-get update -qq
apt-get install -y -qq nginx git python3 >/dev/null
mkdir -p /var/lib/bunker17
chown www-data:www-data /var/lib/bunker17
cp deploy/nginx.conf /etc/nginx/sites-available/bunker17
ln -sf /etc/nginx/sites-available/bunker17 /etc/nginx/sites-enabled/bunker17
rm -f /etc/nginx/sites-enabled/default
cp deploy/*.service deploy/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now bunker17-api
systemctl restart bunker17-api
systemctl enable --now bunker17-update.timer
nginx -t
systemctl reload nginx
echo
echo "Готово. Проверка:"
curl -s -o /dev/null -w "  игра:    HTTP %{http_code}\n" http://127.0.0.1/
curl -s -o /dev/null -w "  рекорды: HTTP %{http_code}\n" http://127.0.0.1/api/scores
systemctl is-active --quiet bunker17-update.timer && echo "  автообновление: включено, раз в минуту"
