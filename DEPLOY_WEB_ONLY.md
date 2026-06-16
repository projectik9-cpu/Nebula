# 🌐 Деплой только через браузер (БЕЗ программ!)

Самый простой способ - всё через веб-интерфейс.

---

## 📤 Шаг 1: Загрузка на GitHub (5 минут)

### 1. Создайте репозиторий:
1. Зайдите: https://github.com
2. Sign In (или Sign Up если нет аккаунта)
3. Нажмите `+` (справа вверху) → New repository
4. Repository name: `telegram-referral-bot`
5. Private: ✅ (рекомендуется)
6. **НЕ** ставьте галочки на README, .gitignore, license
7. Create repository

### 2. Загрузите файлы:
1. На странице репозитория нажмите: "uploading an existing file"
2. Перетащите ВСЕ файлы из папки `c:\Users\lifes\Downloads\гейбот`
3. **Важно загрузить:**
   - Папку `api` с файлом `index.py`
   - `handlers.py`
   - `database_serverless.py`
   - `config_serverless.py`
   - `vercel.json`
   - `requirements.txt`
   - `.gitignore`
   - Все `.md` файлы (документация)

4. Внизу Commit message: `Initial commit`
5. Commit changes

**Примечание:** GitHub не загружает пустые папки, поэтому загружайте файлы по одному или архивом.

### 3. Проверьте структуру:
В репозитории должно быть:
```
telegram-referral-bot/
├── api/
│   └── index.py
├── handlers.py
├── database_serverless.py
├── config_serverless.py
├── vercel.json
├── requirements.txt
└── (другие файлы)
```

✅ **Готово!** Код на GitHub!

---

## 🌐 Шаг 2: Деплой на Vercel (5 минут)

### 1. Подключите GitHub:
1. Зайдите: https://vercel.com
2. Sign Up → Continue with GitHub
3. Authorize Vercel

### 2. Импортируйте проект:
1. Dashboard → Add New... → Project
2. Import Git Repository
3. Найдите `telegram-referral-bot`
4. Import

### 3. Настройте:
- Framework Preset: `Other`
- Root Directory: `./`
- Build Command: (оставить пустым)
- Output Directory: (оставить пустым)

### 4. Environment Variables:

Добавьте эти переменные (кнопка Add):

| Name | Value |
|------|-------|
| `BOT_TOKEN` | Ваш токен от @BotFather |
| `ADMIN_CHAT_ID` | Ваш Telegram ID |
| `WEBHOOK_URL` | `https://temp.vercel.app` |
| `DATABASE_URL` | `postgresql://postgres:[3159202177Ss]@db.nndebjrieyxqjnwkslhn.supabase.co:5432/postgres` |
| `REFERRAL_REWARD` | `5.0` |

**ВАЖНО для DATABASE_URL:**
- Ваш пароль в квадратных скобках: `[3159202177Ss]`
- Нужно убрать скобки: `3159202177Ss`
- Итоговая строка:
```
postgresql://postgres:3159202177Ss@db.nndebjrieyxqjnwkslhn.supabase.co:5432/postgres
```

### 5. Deploy:
- Нажмите "Deploy"
- Ждите 2-3 минуты
- Скопируйте URL проекта

---

## 🔧 Шаг 3: Обновление WEBHOOK_URL

1. Settings → Environment Variables
2. Edit у `WEBHOOK_URL`
3. Вставьте реальный URL (например: `https://telegram-bot-abc.vercel.app`)
4. Save
5. Deployments → три точки → Redeploy

---

## 🎯 Шаг 4: Установка вебхука

Откройте в браузере:
```
https://ваш-проект.vercel.app/set_webhook
```

Должно вернуть:
```json
{
  "status": "success"
}
```

---

## ✅ Шаг 5: Проверка

### Health Check:
```
https://ваш-проект.vercel.app/health
```

### Telegram:
Откройте бота → `/start`

✅ Если отвечает - **готово!** 🎉

---

## 🔄 Обновление кода

Если нужно обновить код:

1. GitHub → Ваш репозиторий
2. Найдите файл (например, `handlers.py`)
3. Нажмите карандаш (Edit)
4. Внесите изменения
5. Commit changes
6. Vercel автоматически задеплоит!

---

## 💾 Миграция данных

Если нужно перенести данные из bot.db:

### Через Python локально:
```bash
pip install psycopg2-binary
```

Создайте `.env`:
```
DATABASE_URL=postgresql://postgres:3159202177Ss@db.nndebjrieyxqjnwkslhn.supabase.co:5432/postgres
```

Запустите:
```bash
python migrate_to_postgres.py
```

---

## 🆘 Частые проблемы

### 1. "BOT_TOKEN not set"
→ Добавьте в Vercel Environment Variables

### 2. Бот не отвечает
→ Проверьте `/webhook_info` - вебхук должен быть установлен

### 3. Database error
→ Проверьте `DATABASE_URL` - уберите скобки из пароля!

### 4. Папка api не загрузилась
→ Загрузите `api/index.py` вручную:
1. В репозитории: Add file → Create new file
2. Имя файла: `api/index.py`
3. Скопируйте содержимое из локального файла
4. Commit

---

## 📝 Ваши данные для копирования:

### DATABASE_URL (БЕЗ скобок!):
```
postgresql://postgres:3159202177Ss@db.nndebjrieyxqjnwkslhn.supabase.co:5432/postgres
```

### Структура должна быть:
```
telegram-referral-bot/
├── api/index.py          ← ОБЯЗАТЕЛЬНО!
├── handlers.py           ← ОБЯЗАТЕЛЬНО!
├── database_serverless.py
├── config_serverless.py
├── vercel.json           ← ОБЯЗАТЕЛЬНО!
├── requirements.txt      ← ОБЯЗАТЕЛЬНО!
└── .gitignore
```

---

## 🎉 Готово!

Ваш бот работает на Vercel без установки Git!

**Полезные ссылки:**
- Ваш GitHub: https://github.com/ваш-username/telegram-referral-bot
- Vercel: https://vercel.com/dashboard
- Supabase: https://app.supabase.com

Удачи! 🚀
