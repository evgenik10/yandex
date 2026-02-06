# Mini Rover Fleet (Repka Pi)

Проект-заготовка для автономных мини-роверов на базе **Repka Pi** и единой серверной панели управления множеством роверов.

## 1) BOM (компоненты и альтернативы)

| Компонент | Зачем нужен | Альтернативы |
|---|---|---|
| Repka Pi | Бортовой компьютер, запускает Python-логику и связь с сервером | Raspberry Pi 4/5, Orange Pi |
| microSD 16–32GB | ОС, логи, конфигурация | eMMC (если доступна) |
| DC моторы с редуктором (2–4) | Привод платформы на малой скорости с высоким моментом | BLDC + ESC (сложнее), шаговые |
| TB6612 / L298N | Управление направлением/скоростью моторов | BTS7960, DRV8833 |
| GPS NEO-6M / NEO-M8N | Позиционирование для AUTO режима | u-blox M10, RTK-модули |
| HC-SR04 | Ближняя оценка препятствий по расстоянию | ToF VL53L0X, лидар RPLidar |
| 4 USB камеры | Круговой обзор: front/rear/left/right | CSI-камеры + мультиплексор |
| Аккумулятор 18650/power bank | Автономное питание | LiPo 2S/3S + BMS |
| DC-DC step-down | Стабильное питание 5V для Repka Pi и датчиков | UBEC |
| Крепёж и провода | Механика, монтаж, безопасность | Готовые robot chassis kits |

## 2) Схема подключения

### GPIO/UART таблица (пример)

| Модуль | Пины Repka Pi | Примечание |
|---|---|---|
| TB6612 PWMA | GPIO18 (PWM) | Скорость левого канала |
| TB6612 AIN1/AIN2 | GPIO23/GPIO24 | Направление левого мотора |
| TB6612 PWMB | GPIO19 (PWM) | Скорость правого канала |
| TB6612 BIN1/BIN2 | GPIO27/GPIO22 | Направление правого мотора |
| TB6612 STBY | GPIO17 | Подтяжка в HIGH для enable |
| HC-SR04 TRIG | GPIO5 | Через резистор при необходимости |
| HC-SR04 ECHO | GPIO6 | Понижение уровня до 3.3V обязательно |
| GPS TX/RX | UART RX/TX (GPIO15/GPIO14) | 9600 бод (обычно), общий GND |
| 4 USB камеры | USB0..USB3 | Идентифицировать через `/dev/v4l/by-id` |

### Питание
- Repka Pi: стабильные 5V, достаточный ток.
- Драйвер моторов: отдельная силовая линия (например 6–12V), **общий GND** с Repka Pi.
- Датчики/GPS: от 5V/3.3V согласно datasheet.

### Критические предупреждения
1. Не подавать ECHO HC-SR04 напрямую в 3.3V GPIO без делителя.
2. Не питать моторы от 5V пина Repka Pi.
3. Всегда объединять землю (GND) логики и силовой части.
4. Перед первым стартом проверять полярность батарей и ток нагрузки.

## 3) Режимы и безопасность (ПДД-логика)

Приоритеты: **человек > препятствие > маршрут > скорость**.

- **MANUAL**: команды из панели (кнопки/клавиатура WASD + Space).
- **AUTO**: движение по GPS waypoints с контролем отклонения от коридора.
- Если детектирован `person`/`stop_sign` или неуверенность — немедленный `STOP`.
- Если ультразвук фиксирует близкое препятствие — временный `RETURNING`/объезд.

## 4) Структура проекта

```text
rover/
  motors.py
  gps.py
  sensors.py
  vision.py
  camera.py
  navigation.py
  api_client.py
  main.py
server/
  web.py
  api.py
  templates/dashboard.html
  static/js/dashboard.js
  static/css/dashboard.css
requirements.txt
```

## 5) REST API

- `GET /rovers` — список всех роверов
- `POST /rovers` — создать ровер по ID (с опциональным `ip_address`)
- `POST /rovers/connect` — подключить ровер по IP API
- `GET /rovers/{id}/status` — текущий статус
- `POST /rovers/{id}/command` — команда управления
- `POST /rovers/{id}/goal` — маршрут (GPS точки)
- `POST /rovers/{id}/status` — heartbeat/состояние от ровера
- `POST /rovers/{id}/check_connection` — ручная проверка связи с ровером по IP API
- `GET /rovers/{id}/commands` — очередь команд для ровера

## 6) Запуск

### Сервер (панель)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server/web.py
```
Открыть: `http://<server-ip>:8000`

### Ровер
```bash
export ROVER_ID=rover-01
export CONTROL_SERVER_URL=http://<server-ip>:8000
python rover/main.py
```

## 7) Развёртывание шаг за шагом

1. Установить Linux headless на каждый ровер, настроить SSH-ключи.
2. Обновить систему, выставить hostname (`rover-01`, `rover-02`...).
3. Включить GPIO/PWM/UART в конфигурации ядра/boot.
4. Проверить GPS (`cgps`, `gpsmon` или чтение NMEA из UART).
5. Проверить 4 камеры (`v4l2-ctl --list-devices`).
6. Проверить HC-SR04 и драйвер моторов отдельными smoke-тестами.
7. Установить Python 3, venv, зависимости.
8. Настроить `CONTROL_SERVER_URL` и `ROVER_ID`.
9. Развернуть сервер панели на отдельной машине.
10. Добавить автозапуск через systemd.

### Пример systemd (ровер)
`/etc/systemd/system/rover.service`
```ini
[Unit]
Description=Mini Rover Agent
After=network-online.target

[Service]
Type=simple
User=robot
WorkingDirectory=/opt/mini-rover
Environment=ROVER_ID=rover-01
Environment=CONTROL_SERVER_URL=http://192.168.1.50:8000
ExecStart=/opt/mini-rover/.venv/bin/python rover/main.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

### Пример systemd (сервер)
`/etc/systemd/system/rover-dashboard.service`
```ini
[Unit]
Description=Rover Dashboard Flask API
After=network-online.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/rover-dashboard
ExecStart=/opt/rover-dashboard/.venv/bin/python server/web.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

## 8) Типичные ошибки и решения

- **GPS прыгает/дрейфует**: добавить фильтр (EMA/Kalman), увеличить допустимый коридор.
- **Ложные STOP от CV**: поднять confidence threshold, добавить temporal smoothing.
- **Лаг команд**: уменьшить payload статуса, поднять частоту polling/WebSocket в будущем.
- **Сбросы питания**: отдельный BEC/регулятор для логики и моторов.
- **Камеры меняют порядок**: использовать udev-правила и `/dev/v4l/by-id`.

## 9) Логика системы целиком

1. Ровер читает GPS + ультразвук + детекции с 4 камер.
2. Навигация оценивает PDD-состояние (`ON_TRACK`, `OFF_TRACK`, `RETURNING`, `STOP`).
3. Моторный модуль исполняет безопасную команду с лимитом скорости.
4. Статус и видеопотоки публикуются на сервер.
5. Оператор выбирает ровер в панели, задаёт маршрут или ручные команды.
6. Команды складываются в очередь и забираются ровером при polling.

> Текущий код — production-ready каркас: для реального выезда нужно добавить GPIO/UART drivers, полноценный inference pipeline и контур тестов на железе.
