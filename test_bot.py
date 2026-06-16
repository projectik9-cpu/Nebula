"""
Скрипт для тестирования и отладки бота
"""
from database import Database

def main():
    db = Database()
    
    print("=" * 50)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # Тест 1: Проверка пользователей
    print("\n📊 Статистика:")
    stats = db.get_statistics()
    print(f"  Всего пользователей: {stats['total_users']}")
    print(f"  Общий баланс: {stats['total_balance']} ⭐")
    print(f"  Всего рефералов: {stats['total_referrals']}")
    print(f"  Всего выводов: {stats['total_withdrawals']}")
    print(f"  Сумма выводов: {stats['total_withdrawn']} ⭐")
    
    # Тест 2: Список всех пользователей
    print("\n👥 Пользователи:")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, full_name, balance, referrer_id, referral_count 
        FROM users 
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    
    if users:
        for user in users:
            print(f"\n  ID: {user[0]}")
            print(f"  Username: {user[1]}")
            print(f"  Имя: {user[2]}")
            print(f"  Баланс: {user[3]} ⭐")
            print(f"  Реферер: {user[4] or 'Нет'}")
            print(f"  Рефералов: {user[5]}")
    else:
        print("  Пользователей нет")
    
    # Тест 3: Список промокодов
    print("\n🎁 Промокоды:")
    cursor.execute("SELECT code, amount FROM promocodes")
    promos = cursor.fetchall()
    
    if promos:
        for promo in promos:
            print(f"  {promo[0]}: {promo[1]} ⭐")
    else:
        print("  Промокодов нет")
    
    # Тест 4: Заявки на вывод
    print("\n💰 Заявки на вывод:")
    cursor.execute("""
        SELECT w.id, w.user_id, u.username, w.amount, w.status, w.created_at 
        FROM withdrawals w
        LEFT JOIN users u ON w.user_id = u.user_id
        ORDER BY w.created_at DESC
    """)
    withdrawals = cursor.fetchall()
    
    if withdrawals:
        for w in withdrawals:
            print(f"  #{w[0]} | User: @{w[2]} | Сумма: {w[3]} ⭐ | Статус: {w[4]}")
    else:
        print("  Заявок нет")
    
    conn.close()
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
