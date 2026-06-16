# 🚀 Деплой на Vercel - Пошаговая инструкция

## 📋 Что нужно перед началом:

1. ✅ Аккаунт на [Vercel](https://vercel.com)
2. ✅ Аккаунт на [GitHub](https://github.com) (для загрузки кода)
3. ✅ PostgreSQL база данных (выберите один вариант):
   - [Supabase](https://supabase.com) (Рекомендуется, бесплатный план)
   - [Neon](https://neon.tech) (Serverless PostgreSQL)
   - [Railway](https://railway.app)
   - [Vercel Postgres](https://vercel.com/storage/postgres)

---

## 🗄️ Шаг 1: Создание базы данных

### Вариант A: Supabase (Рекомендуется)

1. Зайдите на https://supabase.com
2. Нажмите "Start your project"
3. Создайте новый проект:
   - Name: `referral-bot-db`
   - Database Password: придумайте надёжный пароль
   - Region: выберите ближайший к вам
4. Дождитесь создания проекта (1-2 минуты)
5. Перейдите в Settings → Database
6. Скопируйте **Connection String** (URI формат)
   - Формат: `postgresql://postgres:password@...`
7. Сохраните эту строку - она понадобится!

### Вариант B: Neon

1. Зайдите на https://neon.tech
2. Sign Up → Create Project
3. Скопируйте Connection String
4. Сохраните

---

## 📤 Шаг 2: Загрузка кода на GitHub

### Способ 1: Через GitHub Desktop (Проще)

1. Скачайте [GitHub Desktop](https://desktop.github.com/)
2. Войдите в свой аккаунт
3. File → New Repository:
   - Name: `telegram-referral-bot`
   - Local Path: выберите папку с ботом
4. Publish repository
5. Готово!

### Способ 2: Через командную строку

```bash
cd c:\Users\lifes\Downloads\гейбот

# Инициализация git (если ещё не сделано)
git init

# Добавляем все файлы
git add .

# Коммит
git commit -m "Initial commit for Vercel deploy"

# Создайте репозиторий на GitHub.com
# Затем:
git remote add origin https://github.com/YOUR_USERNAME/telegram-referral-bot.git
git branch -M main
git push -u origin main
```

---

## 🌐 Шаг 3: Деплой на Vercel

1. Зайдите на https://vercel.com
2. Нажмите "Add New..." → "Project"
3. Import Git Repository:
   - Выберите ваш репозиторий `telegram-referral-bot`
   - Нажмите "Import"

4. Configure Project:
   - Framework Preset: `Other`
   - Root Directory: `./` (оставьте как есть)
   - Build Command: оставьте пустым
   - Output Directory: оставьте пустым

5. **Environment Variables** (ВАЖНО!):
   
   Добавьте эти переменные:
   
   ```
   BOT_TOKEN=ваш_токен_от_BotFather
   ADMIN_CHAT_ID=ваш_telegram_id
   WEBHOOK_URL=https://your-project-name.vercel.app
   DATABASE_URL=postgresql://user:password@host/db
   REFERRAL_REWARD=5.0
   ```
   
   **Важно для WEBHOOK_URL:**
   - Пока не знаете URL? Напишите временный: `https://temp.vercel.app`
   - После деплоя вернётесь и исправите!

6. Нажмите **"Deploy"**

7. Дождитесь окончания деплоя (2-3 минуты)

8. Скопируйте URL вашего проекта (например: `https://telegram-bot-abc123.vercel.app`)

---

## 🔧 Шаг 4: Обновление WEBHOOK_URL

1. В Vercel зайдите в Settings → Environment Variables
2. Найдите `WEBHOOK_URL`
3. Измените на реальный URL (который скопировали выше)
4. Сохраните
5. Redeploy проект (нажмите на три точки у последнего деплоя → Redeploy)

---

## 🎯 Шаг 5: Установка вебхука

После успешного деплоя:

1. Откройте в браузере:
   ```
   https://ваш-проект.vercel.app/set_webhook
   ```

2. Вы должны увидеть JSON ответ:
   ```json
   {
     "status": "success",
     "webhook_url": "https://ваш-проект.vercel.app/webhook/ваш_токен"
   }
   ```

3. Если видите `"status": "success"` - отлично! Вебхук установлен.

---

## ✅ Шаг 6: Проверка работы

### Проверка 1: Health Check
```
https://ваш-проект.vercel.app/health
```

Должно вернуть:
```json
{
  "status": "healthy",
  "bot": { ... },
  "database": { "status": "connected" }
}
```

### Проверка 2: Webhook Info
```
https://ваш-проект.vercel.app/webhook_info
```

Должно показать ваш webhook URL.

### Проверка 3: Telegram
Откройте бота в Telegram и напишите `/start`

Если бот отвечает - всё работает! 🎉

---

## 🔍 Отладка проблем

### Проблема: "BOT_TOKEN environment variable is not set"

**Решение:**
1. Vercel → Settings → Environment Variables
2. Добавьте переменную `BOT_TOKEN`
3. Redeploy проект

### Проблема: "DATABASE_URL environment variable is not set"

**Решение:**
1. Создайте базу данных (Supabase/Neon)
2. Добавьте `DATABASE_URL` в Environment Variables
3. Redeploy

### Проблема: Бот не отвечает в Telegram

**Чеклист:**
1. Вебхук установлен? Проверьте `/webhook_info`
2. Health check проходит? Проверьте `/health`
3. Логи в Vercel: Deployments → View Function Logs

### Проблема: "Connection to database failed"

**Решение:**
1. Проверьте правильность `DATABASE_URL`
2. Формат должен быть: `postgresql://user:pass@host:5432/db`
3. Проверьте что база данных доступна извне
4. В Supabase: Settings → Database → Connection String (URI)

---

## 📊 Мониторинг

### Логи в Vercel:
1. Зайдите в проект на Vercel
2. Deployments → Latest Deployment
3. View Function Logs

### Логи в реальном времени:
```bash
vercel logs --follow
```

---

## 🔄 Обновление бота

После изменений в коде:

```bash
# Commit изменения
git add .
git commit -m "Update bot"
git push

# Vercel автоматически задеплоит изменения!
```

Или через GitHub Desktop:
1. Commit changes
2. Push origin
3. Vercel задеплоит автоматически

---

## 💾 Миграция данных из SQLite

Если у вас уже есть данные в `bot.db`:

### Шаг 1: Установите psycopg2 локально
```bash
pip install psycopg2-binary
```

### Шаг 2: Создайте скрипт миграции
```python
# migrate_to_postgres.py
import sqlite3
import psycopg2
from config_serverless import DATABASE_URL

# SQLite
sqlite_conn = sqlite3.connect('bot.db')
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL
pg_conn = psycopg2.connect(DATABASE_URL)
pg_cursor = pg_conn.cursor()

# Миграция пользователей
sqlite_cursor.execute("SELECT * FROM users")
users = sqlite_cursor.fetchall()
for user in users:
    pg_cursor.execute("""
        INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
    """, user)

pg_conn.commit()
print("Migration complete!")
```

### Шаг 3: Запустите миграцию
```bash
python migrate_to_postgres.py
```

---

## 🎉 Готово!

Теперь ваш бот работает на Vercel 24/7!

### Преимущества:
- ✅ Бесплатный хостинг
- ✅ Автоматические обновления из GitHub
- ✅ Высокая доступность
- ✅ HTTPS из коробки
- ✅ Логи и мониторинг

### Важные ссылки:
- Ваш бот: `https://ваш-проект.vercel.app`
- Health check: `https://ваш-проект.vercel.app/health`
- Webhook info: `https://ваш-проект.vercel.app/webhook_info`
- Vercel панель: https://vercel.com/dashboard

---

## 📞 Поддержка

Если что-то не работает:
1. Проверьте `/health` endpoint
2. Посмотрите логи в Vercel
3. Проверьте Environment Variables
4. Убедитесь что вебхук установлен (`/set_webhook`)

Удачи! 🚀
