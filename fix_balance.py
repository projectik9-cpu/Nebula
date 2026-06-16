"""
Скрипт для исправления баланса пользователя
Используйте если баланс сбросился после перезапуска
"""
from database import Database

def main():
    db = Database()
    
    print("=" * 50)
    print("ИСПРАВЛЕНИЕ БАЛАНСА")
    print("=" * 50)
    
    # Ваш ID
    user_id = 7328504615
    
    # Получаем текущие данные
    user_data = db.get_user(user_id)
    
    if not user_data:
        print(f"❌ Пользователь {user_id} не найден!")
        return
    
    print(f"\n👤 Пользователь: {user_data['full_name']}")
    print(f"🆔 ID: {user_id}")
    print(f"💰 Текущий баланс: {user_data['balance']} ⭐")
    print(f"👥 Количество рефералов: {user_data['referral_count']}")
    
    # Рассчитываем должный баланс
    # 4 реферала по 5 звёзд = 20 звёзд заработано
    # Вы вывели 30 звёзд (15 + 15)
    # Но это было когда награда была 15 звёзд
    
    # Текущая ситуация:
    # - У вас 4 реферала
    # - По новой системе это 4 × 5 = 20 звёзд
    # - Вы вывели 30 звёзд
    # - Баланс должен быть 0 (вы вывели больше чем заработали по новой системе)
    
    # НО по старой системе у вас было:
    # - 1 реферал вчера = 5 звёзд (когда награда уже была 5)
    # - 3 реферала сегодня = 3 × 5 = 15 звёзд
    # - Итого заработано: 20 звёзд
    # - Вывели: 30 звёзд
    # - Должно остаться: 0 звёзд (вы ушли в минус на 10 звёзд)
    
    print("\n" + "=" * 50)
    print("АНАЛИЗ:")
    print("=" * 50)
    
    # Получаем данные о выводах
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(amount) FROM withdrawals WHERE user_id = ?
    """, (user_id,))
    total_withdrawn = cursor.fetchone()[0] or 0
    
    print(f"💸 Всего выведено: {total_withdrawn} ⭐")
    print(f"📊 Заработано (4 реферала × 5): {user_data['referral_count'] * 5} ⭐")
    print(f"💰 Должно быть на балансе: {user_data['referral_count'] * 5 - total_withdrawn} ⭐")
    
    # Исправляем баланс
    correct_balance = max(0, user_data['referral_count'] * 5 - total_withdrawn)
    
    if user_data['balance'] != correct_balance:
        print(f"\n⚠️ Баланс неверный!")
        print(f"Исправляю: {user_data['balance']} → {correct_balance}")
        
        response = input("\nПрименить исправление? (y/n): ")
        if response.lower() == 'y':
            db.set_balance(user_id, correct_balance)
            print("✅ Баланс исправлен!")
        else:
            print("❌ Отменено")
    else:
        print(f"\n✅ Баланс корректный!")
    
    conn.close()
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
