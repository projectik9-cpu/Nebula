# 🌐 Telegram Referral Bot - Serverless Version

Реферальный Telegram бот, переработанный для деплоя на **Vercel** с использованием **webhooks** и **PostgreSQL**.

## 🎯 Ключевые изменения от локальной версии:

### ✅ Архитектура:
- **Было:** Long polling (bot.infinity_polling())
- **Стало:** Webhooks через FastAPI
- **Результат:** Работает на Vercel Serverless Functions

### ✅ База данных:
- **Было:** SQLite (bot.db) - локальный файл
- **Стало:** PostgreSQL (Supabase/Neon)
- **Результат:** Данные сохраняются между перезапусками

### ✅ Структура проекта:
```
telegram-referral-bot/
│
├── api/
│   └── index.py          ← Serverless функция (точка входа)
│
├── handlers.py           ← Обработчики команд
├── database_serverless.py ← PostgreSQL вместо SQLite
├── config_serverless.py  ← Конфиг из env переменных
│
├── vercel.json           ← Конфигурация Vercel
├── requirements.txt      ← Зависимости
│
└── VERCEL_DEPLOY.md      ← Инструкция по деплою
```

---

## 🚀 Быстрый старт:

### 1. Создайте PostgreSQL базу:
- [Supabase](https://supabase.com) (рекомендуется)
- [Neon](https://neon.tech)
- [Railway](https://railway.app)

### 2. Загрузите код на GitHub

### 3. Деплой на Vercel:
1. Import Git Repository
2. Добавьте Environment Variables:
   - `BOT_TOKEN`
   - `ADMIN_CHAT_ID`
   - `WEBHOOK_URL`
   - `DATABASE_URL`
3. Deploy!

### 4. Установите webhook:
```
https://ваш-проект.vercel.app/set_webhook
```

### 5. Готово! 🎉

Подробная инструкция: [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md)

---

## 🔧 API Endpoints:

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/` | GET | Статус бота |
| `/webhook/{token}` | POST | Обработка апдейтов от Telegram |
| `/set_webhook` | GET | Установка webhook |
| `/webhook_info` | GET | Информация о webhook |
| `/health` | GET | Проверка здоровья бота и БД |

---

## 📊 Environment Variables:

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | ✅ | Токен от @BotFather |
| `ADMIN_CHAT_ID` | ✅ | Ваш Telegram ID |
| `WEBHOOK_URL` | ✅ | URL вашего Vercel проекта |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REFERRAL_REWARD` | ❌ | Награда за реферала (по умолчанию 5.0) |
| `DEBUG` | ❌ | Режим отладки (по умолчанию False) |

---

## 🔍 Отладка:

### Health Check:
```bash
curl https://ваш-проект.vercel.app/health
```

### Webhook Info:
```bash
curl https://ваш-проект.vercel.app/webhook_info
```

### Логи:
```bash
vercel logs --follow
```

---

## 💡 Преимущества Serverless:

✅ **Бесплатный хостинг** - Vercel Free Tier  
✅ **Автомасштабирование** - выдерживает любую нагрузку  
✅ **Zero downtime** - всегда онлайн  
✅ **HTTPS из коробки** - безопасность  
✅ **Автообновления** - push в GitHub = автодеплой  
✅ **Мониторинг** - встроенные логи и метрики

---

## 🔄 Миграция с локальной версии:

Если у вас уже есть SQLite база с данными:

1. Установите зависимости: `pip install psycopg2-binary`
2. Используйте скрипт миграции (см. VERCEL_DEPLOY.md)
3. Данные будут перенесены в PostgreSQL

---

## 📝 Команды бота:

### Для пользователей:
- `/start` - Запуск (с реферальной ссылкой или без)
- Кнопки в меню

### Для администратора:
- `/create_promo <код> <сумма>` - Создать промокод
- `/check_user <id>` - Проверить пользователя
- `/stats` - Статистика бота
- `/set_balance <id> <сумма>` - Установить баланс
- `/add_balance <id> <сумма>` - Добавить к балансу

---

## 🛠️ Локальная разработка:

```bash
# Установка зависимостей
pip install -r requirements.txt

# Создайте .env файл
cp .env.vercel.example .env

# Заполните переменные в .env

# Запуск локально
cd api
uvicorn index:app --reload

# Установка локального вебхука (используйте ngrok)
curl http://localhost:8000/set_webhook
```

---

## 📞 Поддержка:

- **Документация:** [VERCEL_DEPLOY.md](VERCEL_DEPLOY.md)
- **GitHub Issues:** Создайте issue в репозитории
- **Vercel Docs:** https://vercel.com/docs

---

## 📄 Лицензия:

MIT License

---

**Версия:** 3.0 Serverless  
**Платформа:** Vercel  
**База данных:** PostgreSQL  
**Framework:** FastAPI + Aiogram

Готово к продакшену! 🚀
