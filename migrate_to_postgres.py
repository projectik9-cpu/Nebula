"""
Миграция данных из SQLite в PostgreSQL
Используйте этот скрипт если у вас уже есть данные в bot.db
"""
import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Ошибка: DATABASE_URL не установлен!")
    print("Добавьте DATABASE_URL в .env файл")
    exit(1)

def migrate():
    print("=" * 50)
    print("МИГРАЦИЯ ДАННЫХ SQLite → PostgreSQL")
    print("=" * 50)
    
    # Проверяем наличие SQLite базы
    if not os.path.exists('bot.db'):
        print("\n❌ Файл bot.db не найден!")
        print("Нечего мигрировать.")
        return
    
    try:
        # Подключение к SQLite
        print("\n📂 Подключение к SQLite...")
        sqlite_conn = sqlite3.connect('bot.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Подключение к PostgreSQL
        print("🐘 Подключение к PostgreSQL...")
        pg_conn = psycopg2.connect(DATABASE_URL)
        pg_cursor = pg_conn.cursor()
        
        # Миграция пользователей
        print("\n👥 Миграция пользователей...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        migrated_users = 0
        for user in users:
            try:
                pg_cursor.execute("""
                    INSERT INTO users (user_id, username, full_name, balance, referrer_id, referral_count, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                """, user)
                migrated_users += 1
            except Exception as e:
                print(f"  ⚠️ Ошибка при миграции пользователя {user[0]}: {e}")
        
        print(f"  ✅ Мигрировано пользователей: {migrated_users}/{len(users)}")
        
        # Миграция промокодов
        print("\n🎁 Миграция промокодов...")
        sqlite_cursor.execute("SELECT * FROM promocodes")
        promocodes = sqlite_cursor.fetchall()
        
        migrated_promos = 0
        for promo in promocodes:
            try:
                pg_cursor.execute("""
                    INSERT INTO promocodes (code, amount, created_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (code) DO NOTHING
                """, promo)
                migrated_promos += 1
            except Exception as e:
                print(f"  ⚠️ Ошибка при миграции промокода {promo[0]}: {e}")
        
        print(f"  ✅ Мигрировано промокодов: {migrated_promos}/{len(promocodes)}")
        
        # Миграция использованных промокодов
        print("\n🔖 Миграция использованных промокодов...")
        sqlite_cursor.execute("SELECT * FROM used_promocodes")
        used_promos = sqlite_cursor.fetchall()
        
        migrated_used = 0
        for used in used_promos:
            try:
                pg_cursor.execute("""
                    INSERT INTO used_promocodes (user_id, code, used_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, code) DO NOTHING
                """, used)
                migrated_used += 1
            except Exception as e:
                print(f"  ⚠️ Ошибка: {e}")
        
        print(f"  ✅ Мигрировано записей: {migrated_used}/{len(used_promos)}")
        
        # Миграция заявок на вывод
        print("\n💰 Миграция заявок на вывод...")
        sqlite_cursor.execute("SELECT * FROM withdrawals")
        withdrawals = sqlite_cursor.fetchall()
        
        migrated_withdrawals = 0
        for withdrawal in withdrawals:
            try:
                # В PostgreSQL id автогенерируется, поэтому пропускаем его
                pg_cursor.execute("""
                    INSERT INTO withdrawals (user_id, amount, status, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (withdrawal[1], withdrawal[2], withdrawal[3], withdrawal[4]))
                migrated_withdrawals += 1
            except Exception as e:
                print(f"  ⚠️ Ошибка: {e}")
        
        print(f"  ✅ Мигрировано заявок: {migrated_withdrawals}/{len(withdrawals)}")
        
        # Коммит изменений
        pg_conn.commit()
        
        # Закрываем подключения
        sqlite_cursor.close()
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()
        
        print("\n" + "=" * 50)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 50)
        print(f"\n📊 Итого:")
        print(f"  Пользователей: {migrated_users}")
        print(f"  Промокодов: {migrated_promos}")
        print(f"  Использований: {migrated_used}")
        print(f"  Заявок на вывод: {migrated_withdrawals}")
        print("\n💡 Теперь можете деплоить на Vercel!")
        
    except Exception as e:
        print(f"\n❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  ВНИМАНИЕ!")
    print("Этот скрипт перенесёт данные из bot.db в PostgreSQL")
    print(f"Database URL: {DATABASE_URL[:30]}...")
    
    response = input("\nПродолжить? (y/n): ")
    if response.lower() == 'y':
        migrate()
    else:
        print("❌ Отменено")
