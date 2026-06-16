# 🌟 Telegram Referral Bot - Serverless

Реферальный Telegram бот для Vercel с PostgreSQL.

## 🚀 Быстрый деплой

### 1. База данных (2 минуты)
1. https://supabase.com → New Project
2. Скопируйте Connection String (URI)

### 2. GitHub (3 минуты)
1. Создайте репозиторий на GitHub
2. Загрузите все файлы

### 3. Vercel (5 минут)
1. https://vercel.com → New Project
2. Import вашего репозитория
3. Добавьте Environment Variables:
   - `BOT_TOKEN` - от @BotFather
   - `ADMIN_CHAT_ID` - ваш Telegram ID
   - `WEBHOOK_URL` - `https://temp.vercel.app` (временно)
   - `DATABASE_URL` - от Supabase (БЕЗ параметров `?pgbouncer=true`)
   - `REFERRAL_REWARD` - `5.0`
4. Deploy

### 4. Обновите WEBHOOK_URL
1. Скопируйте URL проекта после деплоя
2. Settings → Environment Variables
3. Измените `WEBHOOK_URL` на реальный
4. Redeploy

### 5. Установите webhook
```
https://ваш-проект.vercel.app/set_webhook
```

## ✅ Проверка

```
https://ваш-проект.vercel.app/health
```

Откройте бота → `/start`

## 📁 Структура

```
├── api/index.py            # Serverless функция
├── handlers.py             # Обработчики
├── database_serverless.py  # PostgreSQL (синглтон + пул)
├── config_serverless.py    # Конфиг
├── vercel.json             # Настройки Vercel
└── requirements.txt        # Зависимости
```

## 🔧 Особенности database_serverless.py

- **Singleton pattern** - глобальный пул на уровне класса
- **Context manager** - автоматический commit/rollback
- **Очистка URL** - убирает параметры `?pgbouncer=true`
- **Порт 6543** - автоматически для Supabase pooler
- **Минимум соединений** - maxconn=3 для Serverless

## 💡 Админ команды

```
/create_promo CODE 100     # Создать промокод
/check_user 123456789      # Проверить пользователя
/stats                     # Статистика
/set_balance 123 50        # Установить баланс
/add_balance 123 5         # Добавить к балансу
```

## 🔐 Важно для DATABASE_URL

Supabase даёт URL вида:
```
postgresql://...?pgbouncer=true&...
```

Используйте БЕЗ параметров:
```
postgresql://postgres:password@host:6543/postgres
```

Бот автоматически:
- Уберёт всё после `?`
- Изменит порт с 5432 на 6543

## 📝 Лицензия

MIT
