# Бункер 17

Веб-игра, защита базы. Вся игра - один HTML-файл, графика вшита внутрь.

## Структура

- `www/index.html` - страница игры, которую отдает сервер
- `api/server.py` - таблица рекордов: Python без зависимостей, SQLite
- `src/bunker17.html` - исходник игры без обертки страницы
- `src/build.py` - собирает `www/index.html` из исходника: `python3 src/build.py` из корня репозитория
- `deploy/` - конфиг nginx, юниты systemd, скрипты установки и обновления

## Сервер

Первичная установка, от root:

```
apt-get install -y git
git clone https://github.com/alexbournemsk/bunker17 /opt/bunker17
bash /opt/bunker17/deploy/install.sh
```

Дальше сервер сам раз в минуту забирает ветку `main`. Если менялся `api/` - перезапускает сервис рекордов, если `deploy/nginx.conf` - перечитывает nginx.

База рекордов: `/var/lib/bunker17/scores.db`. Вне репозитория, обновлениями не затрагивается.

Полезное:

```
journalctl -u bunker17-update -n 20     # журнал обновлений
systemctl status bunker17-api           # сервис рекордов
git -C /opt/bunker17 log --oneline -5   # что сейчас на сервере
```

Откат на предыдущую версию делается в репозитории: `git revert` и пуш - сервер подхватит сам.

## Баланс

Все числа сложности лежат в начале скрипта в `src/bunker17.html`: блок `BAL`, оружие в `UNITS`, враги в `EN`, волны в `WAVES`, зоны прицела в `ZONES`.

Симулятор: `python3 tools/sim.py 300` - гоняет игру без отрисовки, 300 забегов на каждого из трех ботов (novice, mid, pro), печатает долю прошедших каждую волну и остаток двери. Нужны Python, playwright и Chromium. Цель кривой: novice проигрывает около 5-й волны, mid доходит до 8-й, pro проходит 10.
