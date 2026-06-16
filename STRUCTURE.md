# 📁 Структура проекта для Vercel

## 🌟 Новая структура (Serverless):

```
telegram-referral-bot/
│
├── 📂 api/                    ← Vercel Serverless Functions
│   └── index.py               ← Главная точка входа (вебхуки)
│
├── 📄 handlers.py             ← Обработчики команд и сообщений
├── 📄 database_serverless.py  ← PostgreSQL база данных
├── 📄 config_serverless.py    ← Конфигурация из env
│
├── 📄 vercel.json             ← Конфигурация Vercel
├── 📄 requirements.txt        ← Зависимости Python
├── 📄 .gitignore              ← Игнорируемые файлы
│
├── 📄 migrate_to_postgres.py  ← Миграция SQLite → PostgreSQL
│
├── 📚 Документация:
│   ├── README_SERVERLESS.md   ← Главный README для Serverless
│   ├── VERCEL_DEPLOY.md       ← Полная инструкция по деплою
│   ├── QUICK_DEPLOY.md        ← Быстрый деплой за 10 минут
│   └── STRUCTURE.md           ← Этот файл
│
└── 📄 .env.vercel.example     ← Пример переменных окружения
```

---

## 🗂️ Старая структура (Локальная, больше не используется):

```
Эти файлы НЕ нужны для Vercel:
❌ bot.py                  → заменён на api/index.py + handlers.py
❌ database.py             → заменён на database_serverless.py
❌ config.py               → заменён на config_serverless.py
❌ bot.db                  → заменён на PostgreSQL
❌ test_bot.py             → не работает с PostgreSQL
❌ fix_balance.py          → используйте админ команды
```

---

## 🔄 Сравнение архитектур:

### Локальная версия:
```
bot.py (long polling)
  ↓
database.py (SQLite)
  ↓
bot.db (файл)
```

### Serverless версия:
```
Telegram → Webhook
  ↓
api/index.py (FastAPI)
  ↓
handlers.py
  ↓
database_serverless.py (PostgreSQL)
  ↓
Supabase/Neon (облако)
```

---

## 📦 Зависимости:

### requirements.txt:
```
aiogram==3.4.1           # Telegram Bot framework
fastapi==0.109.0         # Web framework для webhooks
uvicorn==0.27.0          # ASGI server
psycopg2-binary==2.9.9   # PostgreSQL драйвер
python-dotenv==1.0.0     # Env переменные
```

---

## 🔧 Конфигурация Vercel:

### vercel.json:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

**Что это делает:**
- `builds` - компилирует Python в serverless функцию
- `routes` - все запросы идут в api/index.py
- Vercel автоматически установит зависимости из requirements.txt

---

## 🌐 API Endpoints:

| URL | Метод | Описание |
|-----|-------|----------|
| `/` | GET | Статус бота |
| `/webhook/{BOT_TOKEN}` | POST | Telegram вебхуки |
| `/set_webhook` | GET | Установка вебхука |
| `/webhook_info` | GET | Инфо о вебхуке |
| `/health` | GET | Health check |

---

## 🗄️ База данных:

### Таблицы PostgreSQL:

**users**
```sql
user_id BIGINT PRIMARY KEY
username TEXT
full_name TEXT
balance REAL DEFAULT 0
referrer_id BIGINT
referral_count INTEGER DEFAULT 0
created_at TIMESTAMP
```

**promocodes**
```sql
code TEXT PRIMARY KEY
amount REAL
created_at TIMESTAMP
```

**used_promocodes**
```sql
user_id BIGINT
code TEXT
used_at TIMESTAMP
PRIMARY KEY (user_id, code)
```

**withdrawals**
```sql
id SERIAL PRIMARY KEY
user_id BIGINT
amount REAL
status TEXT DEFAULT 'pending'
created_at TIMESTAMP
```

---

## 🔐 Environment Variables:

Эти переменные добавляются в Vercel:

| Переменная | Пример | Где взять |
|------------|--------|-----------|
| `BOT_TOKEN` | `123:ABC...` | @BotFather |
| `ADMIN_CHAT_ID` | `123456789` | @userinfobot |
| `WEBHOOK_URL` | `https://bot.vercel.app` | Vercel (после деплоя) |
| `DATABASE_URL` | `postgresql://...` | Supabase/Neon |
| `REFERRAL_REWARD` | `5.0` | По желанию |

---

## 📊 Workflow деплоя:

```
1. Локальная разработка
   ├── Изменения в коде
   └── Тестирование

2. Git commit & push
   ├── git add .
   ├── git commit -m "..."
   └── git push

3. Vercel автодеплой
   ├── Сборка проекта
   ├── Установка зависимостей
   └── Деплой функций

4. Автоматически online!
   └── https://your-bot.vercel.app
```

---

## 🔄 Миграция данных:

Если есть данные в `bot.db`:

```bash
# 1. Установите psycopg2
pip install psycopg2-binary

# 2. Добавьте DATABASE_URL в .env

# 3. Запустите миграцию
python migrate_to_postgres.py

# 4. Проверьте данные в Supabase/Neon

# 5. Деплойте на Vercel!
```

---

## 📝 Чеклист перед деплоем:

- [ ] `api/index.py` создан
- [ ] `handlers.py` создан
- [ ] `database_serverless.py` создан
- [ ] `config_serverless.py` создан
- [ ] `vercel.json` создан
- [ ] `requirements.txt` обновлён
- [ ] `.gitignore` обновлён
- [ ] PostgreSQL база создана
- [ ] Environment Variables готовы
- [ ] Код загружен на GitHub

---

## 🎯 После деплоя:

1. ✅ Скопируйте Vercel URL
2. ✅ Обновите `WEBHOOK_URL` в Environment Variables
3. ✅ Redeploy проекта
4. ✅ Установите вебхук: `/set_webhook`
5. ✅ Проверьте: `/health`
6. ✅ Тестируйте в Telegram!

---

## 📚 Документы по порядку:

1. **README_SERVERLESS.md** - Начните здесь
2. **QUICK_DEPLOY.md** - Быстрый старт
3. **VERCEL_DEPLOY.md** - Подробная инструкция
4. **STRUCTURE.md** - Структура проекта (вы здесь)

---

Готово к деплою! 🚀
