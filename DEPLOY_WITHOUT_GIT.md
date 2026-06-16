# 🚀 Деплой без Git командной строки

У вас нет Git? Без проблем! Используем GitHub Desktop.

## 📥 Шаг 1: Установка GitHub Desktop (2 минуты)

1. Скачайте: https://desktop.github.com/
2. Установите (просто запустите .exe)
3. Войдите в GitHub аккаунт (создайте если нет)

---

## 📂 Шаг 2: Загрузка проекта (3 минуты)

1. **Откройте GitHub Desktop**

2. **File → Add Local Repository**
   - Выберите папку: `c:\Users\lifes\Downloads\гейбот`
   - Нажмите "Add Repository"

3. **Если появится ошибка "not a git repository":**
   - Нажмите "create a repository"
   - Name: `telegram-referral-bot`
   - Initialize with README: НЕ ставьте галочку!
   - Create Repository

4. **Commit изменений:**
   - В левой панели увидите все файлы
   - Внизу Summary: `Initial commit for Vercel`
   - Нажмите "Commit to main"

5. **Publish на GitHub:**
   - Вверху: "Publish repository"
   - Name: `telegram-referral-bot`
   - Keep this code private: ✅ (для безопасности)
   - Publish Repository

✅ **Готово!** Код на GitHub!

---

## 🌐 Шаг 3: Vercel Deploy (5 минут)

1. **Зайдите на Vercel:**
   - https://vercel.com
   - Sign Up → Continue with GitHub

2. **New Project:**
   - Add New... → Project
   - Import Git Repository
   - Найдите `telegram-referral-bot`
   - Import

3. **Configure Project:**
   - Framework Preset: `Other`
   - Root Directory: `./` (оставить как есть)
   - Build Command: оставить пустым
   - Output Directory: оставить пустым

4. **Environment Variables** (ВАЖНО!):

Нажмите "Add" и добавьте по одной:

```
BOT_TOKEN
Значение: (ваш токен от @BotFather)
```

```
ADMIN_CHAT_ID
Значение: (ваш Telegram ID)
```

```
WEBHOOK_URL
Значение: https://temp.vercel.app
```

```
DATABASE_URL
Значение: postgresql://postgres:[3159202177Ss]@db.nndebjrieyxqjnwkslhn.supabase.co:5432/postgres
```

```
REFERRAL_REWARD
Значение: 5.0
```

5. **Deploy!**
   - Нажмите кнопку "Deploy"
   - Ждите 2-3 минуты

---

## 🔧 Шаг 4: Обновление WEBHOOK_URL (2 минуты)

После деплоя:

1. **Скопируйте URL проекта**
   - Вверху будет что-то вроде: `https://telegram-referral-bot-abc123.vercel.app`
   - Нажмите Copy

2. **Обновите переменную:**
   - Settings → Environment Variables
   - Найдите `WEBHOOK_URL`
   - Edit → вставьте реальный URL
   - **БЕЗ слеша в конце!**
   - Save

3. **Redeploy:**
   - Deployments (вверху)
   - Три точки у последнего деплоя
   - Redeploy
   - Ждите минуту

---

## 🎯 Шаг 5: Установка Webhook (1 минута)

1. Откройте в браузере:
```
https://ваш-проект.vercel.app/set_webhook
```

2. Должно вернуть:
```json
{
  "status": "success",
  "webhook_url": "..."
}
```

✅ Если видите `"status": "success"` - готово!

---

## ✅ Шаг 6: Проверка

### 1. Health Check:
```
https://ваш-проект.vercel.app/health
```
Должно: `{"status": "healthy"}`

### 2. Telegram:
- Откройте бота
- Напишите `/start`
- Должен ответить!

---

## 🎉 ГОТОВО!

Ваш бот работает на Vercel 24/7!

### Что делать дальше:

#### Обновление кода:
1. Измените файлы в папке
2. GitHub Desktop покажет изменения
3. Commit → Push
4. Vercel автоматически задеплоит!

#### Миграция старых данных:
Если нужно перенести данные из bot.db:
```bash
pip install psycopg2-binary
python migrate_to_postgres.py
```

---

## 🆘 Проблемы?

### Бот не отвечает:
1. Проверьте `/webhook_info`
2. Если webhook пустой → откройте `/set_webhook`

### Database error:
1. Проверьте что `DATABASE_URL` правильный
2. Формат: `postgresql://postgres:password@host:5432/postgres`

### Import error:
1. Проверьте что все файлы загружены на GitHub
2. Должны быть: `api/index.py`, `handlers.py`, `vercel.json`

---

## 📝 Важные ссылки:

- GitHub Desktop: https://desktop.github.com/
- Ваш GitHub: https://github.com/ваш-username/telegram-referral-bot
- Vercel Dashboard: https://vercel.com/dashboard
- Supabase: https://app.supabase.com

---

Удачи! 🚀
