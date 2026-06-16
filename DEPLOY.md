# 🚀 Деплой на Vercel за 10 минут

## Шаг 1: Supabase (2 мин)

1. https://supabase.com
2. New Project
3. Name: `bot-db`
4. Password: придумайте
5. Region: ближайший
6. Create Project (ждите 1-2 мин)
7. Settings → Database → Connection String (URI)
8. **Скопируйте без `?pgbouncer=true`**

Формат:
```
postgresql://postgres:PASSWORD@db.xxx.supabase.co:6543/postgres
```

## Шаг 2: GitHub (3 мин)

### Через веб:
1. https://github.com → New repository
2. Name: `telegram-bot`
3. Private: ✅
4. Create
5. "uploading an existing file"
6. Загрузите ВСЕ файлы кроме `.env`, `bot.db`

**Обязательные файлы:**
- `api/index.py`
- `handlers.py`
- `database_serverless.py`
- `config_serverless.py`
- `vercel.json`
- `requirements.txt`

## Шаг 3: Vercel (5 мин)

1. https://vercel.com
2. Sign Up → GitHub
3. New Project
4. Import репозиторий

**Environment Variables:**

| Name | Value |
|------|-------|
| `BOT_TOKEN` | Ваш токен |
| `ADMIN_CHAT_ID` | Ваш ID |
| `WEBHOOK_URL` | `https://temp.vercel.app` |
| `DATABASE_URL` | Из Supabase (**БЕЗ ?pgbouncer**) |
| `REFERRAL_REWARD` | `5.0` |

5. Deploy!
6. Скопируйте URL проекта

## Шаг 4: Обновите WEBHOOK_URL

1. Settings → Environment Variables
2. Edit `WEBHOOK_URL` →  вставьте реальный URL
3. Save
4. Redeploy

## Шаг 5: Установите webhook

```
https://ваш-проект.vercel.app/set_webhook
```

Должно вернуть:
```json
{"status": "success"}
```

## ✅ Проверка

```
https://ваш-проект.vercel.app/health
```

Telegram → бот → `/start`

## 🆘 Проблемы?

### Runtime 500 / pgbouncer error
→ Уберите `?pgbouncer=true` из `DATABASE_URL`

### Бот не отвечает
→ Проверьте `/webhook_info`
→ Установите `/set_webhook`

### Database connection failed
→ Формат: `postgresql://postgres:pass@host:6543/postgres`
→ Порт должен быть `6543` (не 5432)

## 📝 Ваш DATABASE_URL

Из Supabase:
```
postgresql://postgres:[ВАШ_ПАРОЛЬ]@db.nndebjrieyxqjnwkslhn.supabase.co:5432/postgres?pgbouncer=true
```

Для Vercel (уберите `?pgbouncer=true` и замените 5432 на 6543):
```
postgresql://postgres:[ВАШ_ПАРОЛЬ]@db.nndebjrieyxqjnwkslhn.supabase.co:6543/postgres
```

## 🎉 Готово!

Бот работает 24/7 на Vercel!
