#!/bin/bash
# Включает HTTPS для bunker17.ru. Запускать один раз от root:
#   bash /opt/bunker17/deploy/https.sh
# Повторный запуск безопасен: живой сертификат не перевыпускается.
set -e
D=bunker17.ru
cd /opt/bunker17
git fetch -q origin main && git reset -q --hard origin/main

echo "1. certbot"
apt-get install -y -qq certbot >/dev/null
mkdir -p /var/www/letsencrypt
cp deploy/nginx.conf /etc/nginx/sites-available/bunker17
nginx -t -q && systemctl reload nginx

# порт 443 в локальном файрволе, если он включен
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; echo "   ufw: 80 и 443 открыты"; fi

echo "2. сертификат"
a=$(getent ahostsv4 $D | awk 'NR==1{print $1}')
w=$(getent ahostsv4 www.$D | awk 'NR==1{print $1}')
[ -n "$a" ] || { echo "   $D не резолвится с сервера, DNS еще не обновился"; exit 1; }
DOMS="-d $D"
if [ -n "$w" ] && [ "$w" = "$a" ]; then DOMS="$DOMS -d www.$D"; echo "   $D и www.$D -> $a"; else echo "   $D -> $a (www без записи, сертификат только на $D)"; fi
certbot certonly --webroot -w /var/www/letsencrypt $DOMS --cert-name $D \
  --agree-tos --register-unsafely-without-email --non-interactive --keep-until-expiring \
  --deploy-hook "systemctl reload nginx"

echo "3. nginx на 443"
ln -sf /opt/bunker17/deploy/nginx-ssl.conf /etc/nginx/sites-enabled/bunker17-ssl
if ! nginx -t -q; then rm -f /etc/nginx/sites-enabled/bunker17-ssl; echo "   конфиг не прошел проверку, HTTPS не включен"; exit 1; fi
systemctl reload nginx

echo
echo "Готово. Проверка:"
curl -s -o /dev/null -w "  https://$D/            HTTP %{http_code}\n" https://$D/
curl -s -o /dev/null -w "  https://$D/api/scores  HTTP %{http_code}\n" https://$D/api/scores
curl -s -o /dev/null -w "  http://$D/ -> %{redirect_url}\n" http://$D/
systemctl list-timers --all | grep -q certbot && echo "  автопродление: таймер certbot включен"
certbot renew --dry-run -q && echo "  пробное продление: ок"
