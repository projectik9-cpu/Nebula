# ⚡ Быстрый деплой на Vercel за 10 минут

## 1️⃣ База данных (2 минуты)

### Supabase (Рекомендуется):
1. https://supabase.com → Sign Up
2. New Project:
   - Name: `bot-db`
   - Password: придумайте
   - Region: ближайший
3. Дождитесь создания (1-2 мин)
4. Settings → Database → Connection String (URI)
5. **Скопируйте** строку подключения

Выглядит так:
```
postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

---

## 2️⃣ GitHub (3 минуты)

### Вариант A: GitHub Desktop (Проще)
1. Скачайте: https://desktop.github.com/
2. File → New Repository
3. Local Path: папка с ботом
4. Publish repository

### Вариант B: Командная строка
```bash
cd c:\Users\lifes\Downloads\гейбот
git init
git add .
git commit -m "Deploy to Vercel"
```

Создайте репозиторий на GitHub.com, затем:
```bash
git remote add origin https://github.com/ВАШ_USERNAME/telegram-bot.git
git push -u origin main
```

---

## 3️⃣ Vercel (5 минут)

1. https://vercel.com → Sign Up (через GitHub)

2. New Project → Import репозиторий

3. **Environment Variables** (ВАЖНО!):
   ```
   BOT_TOKEN = ваш_токен_от_BotFather
   ADMIN_CHAT_ID = ваш_telegram_id
   WEBHOOK_URL = https://temp.vercel.app
   DATABASE_URL = postgresql://... (из Supabase)
   REFERRAL_REWARD = 5.0
   ```

4. **Deploy!**

5. После деплоя:
   - Скопируйте URL проекта (например: `https://bot-abc123.vercel.app`)
   - Settings → Environment Variables
   - Измените `WEBHOOK_URL` на реальный URL
   - Redeploy

---

## 4️⃣ Установка Webhook (1 минута)

Откройте в браузере:
```
https://ваш-проект.vercel.app/set_webhook
```

Должно вернуть:
```json
{
  "status": "success",
  "webhook_url": "..."
}
```

---

## ✅ Проверка

### 1. Health Check:
```
https://ваш-проект.vercel.app/health
```

Должно показать: `"status": "healthy"`

### 2. Telegram:
Откройте бота → `/start`

Если отвечает - **готово!** 🎉

---

## 🆘 Не работает?

### Проблема 1: "BOT_TOKEN not set"
→ Добавьте в Vercel Environment Variables

### Проблема 2: Бот не отвечает
→ Проверьте `/webhook_info` - должен быть установлен

### Проблема 3: Database error
→ Проверьте правильность `DATABASE_URL`

### Проблема 4: Webhook не устанавливается
→ Проверьте что `WEBHOOK_URL` указан без слеша в конце

---

## 📚 Полная документация:

- [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md) - Подробная инструкция
- [README_SERVERLESS.md](README_SERVERLESS.md) - Документация по боту

---

## 🎯 Чеклист:

- [ ] База данных создана (Supabase/Neon)
- [ ] Код загружен на GitHub
- [ ] Проект задеплоен на Vercel
- [ ] Environment Variables добавлены
- [ ] WEBHOOK_URL обновлён на реальный
- [ ] Webhook установлен (`/set_webhook`)
- [ ] Health check проходит
- [ ] Бот отвечает в Telegram

---

Готово! Бот работает 24/7 на Vercel! 🚀
