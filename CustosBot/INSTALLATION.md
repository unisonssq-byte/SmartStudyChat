# Установка Custos Telegram Bot на Linux сервер

## Системные требования

- Linux сервер (Ubuntu/CentOS/Debian)
- Python 3.8 или выше
- Доступ к панели управления (ispmanager)
- Файловый менеджер

## Подготовка файлов

### 1. Структура проекта для загрузки

Убедитесь, что у вас есть следующая структура файлов для загрузки:

```
CustosBot/
├── main.py                 # Главный файл запуска
├── config.py               # Конфигурация бота
├── handlers/               # Обработчики команд
│   ├── __init__.py
│   ├── main_handlers.py
│   ├── moderation_handlers.py
│   └── user_handlers.py
├── keyboards/              # Клавиатуры
│   └── main_keyboards.py
├── data/                   # База данных
│   └── database.py
├── utils/                  # Утилиты
│   ├── __init__.py
│   └── image_generator.py
├── images/                 # Изображения бота
│   ├── main_menu.png
│   ├── commands.png
│   ├── my_chats.png
│   ├── user_profile.png
│   └── bot_avatar.png
└── requirements.txt        # Зависимости
```

### 2. Создание файла requirements.txt

Создайте файл `requirements.txt` в папке CustosBot со следующим содержимым:

```
aiogram==3.22.0
aiosqlite==0.21.0
Pillow==11.3.0
matplotlib==3.10.6
requests==2.32.5
aiofiles==24.1.0
openai==1.54.4
```

## Установка через ispmanager

### Шаг 1: Загрузка файлов

1. Войдите в ispmanager
2. Перейдите в раздел "Файловый менеджер"
3. Создайте папку для бота, например: `/home/username/custos_bot/`
4. Загрузите всю папку `CustosBot` в созданную директорию

### Шаг 2: Настройка окружения через SSH

Подключитесь к серверу через SSH и выполните следующие команды:

```bash
# Перейдите в директорию с ботом
cd /home/username/custos_bot/CustosBot

# Обновите систему
sudo apt update
sudo apt upgrade -y

# Установите Python и pip (если не установлены)
sudo apt install python3 python3-pip python3-venv -y

# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Создайте папку для базы данных
mkdir -p data
```

### Шаг 3: Настройка API ключей

Если вы планируете использовать генерацию изображений через OpenAI:

```bash
# Экспортируйте API ключи (замените на ваши ключи)
export OPENAI_API_KEY="your-openai-api-key-here"

# Для постоянного сохранения добавьте в .bashrc
echo 'export OPENAI_API_KEY="your-openai-api-key-here"' >> ~/.bashrc
```

### Шаг 4: Проверка конфигурации

Убедитесь, что в файле `config.py` используются переменные окружения для безопасности:

```python
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH")
```

Установите переменные окружения с вашими реальными значениями:

```bash
export BOT_TOKEN="your-bot-token-here"
export API_ID="your-api-id-here"
export API_HASH="your-api-hash-here"
```

### Шаг 5: Тестовый запуск

```bash
# Активируйте виртуальное окружение (если не активировано)
source venv/bin/activate

# Запустите бота для тестирования
python main.py
```

Если бот запустился без ошибок, вы увидите сообщение:
```
INFO:__main__:Custos Bot is starting...
INFO:aiogram.dispatcher:Start polling
INFO:aiogram.dispatcher:Run polling for bot @custoschatbot id=8356598661 - 'Custos | Чат-менеджер'
```

## Автозапуск бота

### Создание systemd сервиса

1. Создайте файл сервиса:

```bash
sudo nano /etc/systemd/system/custos-bot.service
```

2. Добавьте следующий содержимое:

```ini
[Unit]
Description=Custos Telegram Bot
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/custos_bot/CustosBot
Environment=PATH=/home/username/custos_bot/CustosBot/venv/bin
Environment=BOT_TOKEN=your-bot-token-here
Environment=API_ID=your-api-id-here
Environment=API_HASH=your-api-hash-here
Environment=OPENAI_API_KEY=your-openai-api-key-here
ExecStart=/home/username/custos_bot/CustosBot/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

3. Замените `username` на ваше имя пользователя и `your-openai-api-key-here` на ваш API ключ.

4. Активируйте сервис:

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable custos-bot.service

# Запустите сервис
sudo systemctl start custos-bot.service

# Проверьте статус
sudo systemctl status custos-bot.service
```

## Управление ботом

### Основные команды

```bash
# Запуск бота
sudo systemctl start custos-bot.service

# Остановка бота
sudo systemctl stop custos-bot.service

# Перезапуск бота
sudo systemctl restart custos-bot.service

# Просмотр логов
sudo journalctl -u custos-bot.service -f

# Проверка статуса
sudo systemctl status custos-bot.service
```

### Обновление бота

1. Остановите сервис:
```bash
sudo systemctl stop custos-bot.service
```

2. Загрузите новые файлы через ispmanager файловый менеджер

3. Перезапустите сервис:
```bash
sudo systemctl start custos-bot.service
```

## Мониторинг и логи

### Просмотр логов бота
```bash
# Текущие логи
sudo journalctl -u custos-bot.service

# Логи в реальном времени
sudo journalctl -u custos-bot.service -f

# Последние 100 строк логов
sudo journalctl -u custos-bot.service -n 100
```

### Резервное копирование базы данных
```bash
# Создание резервной копии
cp /home/username/custos_bot/CustosBot/data/custos.db /home/username/backup/custos_$(date +%Y%m%d_%H%M%S).db
```

## Устранение проблем

### Частые ошибки

1. **Бот не отвечает**
   - Проверьте токен бота в config.py
   - Убедитесь, что бот запущен: `sudo systemctl status custos-bot.service`

2. **Ошибки модулей Python**
   - Переустановите зависимости: `pip install -r requirements.txt`

3. **Ошибки базы данных**
   - Проверьте права доступа к папке data
   - Убедитесь, что база данных создалась: `ls -la data/`

4. **Ошибки изображений**
   - Проверьте наличие изображений в папке images/
   - Убедитесь в правильности OPENAI_API_KEY (если используется)

### Перезапуск бота при ошибках
```bash
# Полная перезагрузка
sudo systemctl stop custos-bot.service
sleep 5
sudo systemctl start custos-bot.service
```

## Контакты и поддержка

Если у вас возникли проблемы с установкой или настройкой бота, проверьте:

1. Логи сервиса: `sudo journalctl -u custos-bot.service -f`
2. Права доступа к файлам
3. Корректность токенов в config.py
4. Доступность интернет-соединения

Бот готов к работе! Добавьте его в ваши чаты и начните использовать команды управления.