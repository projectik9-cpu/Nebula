"""
Работа с PostgreSQL базой данных для Serverless (Vercel)
Singleton pattern с глобальным пулом для переиспользования соединений
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import Optional, Dict
import logging
import re
from config_serverless import DATABASE_URL

logger = logging.getLogger(__name__)


def clean_database_url(url: str) -> str:
    """
    Очистка DATABASE_URL от параметров pgbouncer и настройка порта
    Supabase использует порт 6543 для пулера, psycopg2 не понимает параметры в URL
    """
    # Убираем всё после знака ? (параметры pgbouncer и т.д.)
    if '?' in url:
        clean_url = url.split('?')[0]
        logger.info("Removed query parameters from DATABASE_URL")
    else:
        clean_url = url
    
    # Меняем порт 5432 на 6543 (Supabase pooler) если используется Supabase
    if ':5432/' in clean_url:
        clean_url = re.sub(r':5432/', ':6543/', clean_url)
        logger.info("Changed port from 5432 to 6543 (Supabase pooler)")
    
    logger.info(f"Cleaned database URL: {clean_url[:50]}...")
    return clean_url


class Database:
    """
    Singleton класс для работы с PostgreSQL в Serverless окружении
    Пул хранится на уровне класса, а не инстанса, для переиспользования
    """
    
    # Глобальный пул на уровне класса (синглтон)
    _pool: Optional[SimpleConnectionPool] = None
    _initialized: bool = False
    
    def __init__(self):
        """
        Инициализация. Пул создаётся один раз на уровне класса
        """
        if not Database._pool:
            try:
                # Очищаем URL от параметров pgbouncer
                logger.info(f"Original DATABASE_URL: {DATABASE_URL[:60]}...")
                clean_url = clean_database_url(DATABASE_URL)
                logger.info(f"Clean DATABASE_URL: {clean_url[:60]}...")
                
                # Создаём глобальный пул
                Database._pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=3,  # Меньше соединений для Serverless
                    dsn=clean_url
                )
                logger.info("Global database pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                logger.error(f"DATABASE_URL was: {DATABASE_URL[:60]}...")
                raise
        
        # Инициализируем таблицы только один раз
        if not Database._initialized:
            self.init_db()
            Database._initialized = True
    
    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """
        Context manager для безопасной работы с БД
        Автоматически управляет транзакциями и возвратом соединения в пул
        
        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
        """
        conn = None
        cursor = None
        try:
            conn = Database._pool.getconn()
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                Database._pool.putconn(conn)
    
    def init_db(self):
        """Инициализация таблиц"""
        with self.get_cursor() as cursor:
            # Таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    balance REAL DEFAULT 0,
                    referrer_id BIGINT,
                    referral_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица промокодов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица использованных промокодов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS used_promocodes (
                    user_id BIGINT,
                    code TEXT,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, code)
                )
            """)
            
            # Таблица заявок на вывод
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    amount REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Database tables initialized")
    
    def health_check(self) -> Dict:
        """Проверка подключения к базе данных"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {"status": "connected"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result is not None
    
    def add_user(self, user_id: int, username: str, full_name: str, referrer_id: Optional[int] = None):
        """Добавление нового пользователя"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, username, full_name, referrer_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, username, full_name, referrer_id))
            logger.info(f"User {user_id} added to database")
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение данных пользователя"""
        with self.get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT user_id, username, full_name, balance, referrer_id, referral_count
                FROM users WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def add_balance(self, user_id: int, amount: float):
        """Начисление баланса"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET balance = balance + %s WHERE user_id = %s
            """, (amount, user_id))
            logger.info(f"Added {amount} stars to user {user_id}")
    
    def set_balance(self, user_id: int, balance: float):
        """Установка баланса"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET balance = %s WHERE user_id = %s
            """, (balance, user_id))
            logger.info(f"Set balance of user {user_id} to {balance}")
    
    def subtract_balance(self, user_id: int, amount: float):
        """Списание баланса"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET balance = balance - %s WHERE user_id = %s
            """, (amount, user_id))
            logger.info(f"Subtracted {amount} stars from user {user_id}")
    
    def increment_referral_count(self, user_id: int):
        """Увеличение счётчика рефералов"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE users SET referral_count = referral_count + 1 WHERE user_id = %s
            """, (user_id,))
    
    def create_promocode(self, code: str, amount: float):
        """Создание промокода"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO promocodes (code, amount) VALUES (%s, %s)
                ON CONFLICT (code) DO NOTHING
            """, (code, amount))
            logger.info(f"Promocode {code} created")
    
    def activate_promocode(self, user_id: int, code: str) -> Dict:
        """Активация промокода"""
        with self.get_cursor() as cursor:
            # Проверяем существование промокода
            cursor.execute("SELECT amount FROM promocodes WHERE code = %s", (code,))
            promo = cursor.fetchone()
            
            if not promo:
                logger.warning(f"Promocode {code} not found")
                return {'success': False, 'message': 'Промокод не найден.\nПроверьте правильность ввода.'}
            
            # Проверяем использование
            cursor.execute("""
                SELECT * FROM used_promocodes WHERE user_id = %s AND code = %s
            """, (user_id, code))
            used = cursor.fetchone()
            
            if used:
                logger.warning(f"User {user_id} already used promocode {code}")
                return {'success': False, 'message': 'Вы уже активировали этот промокод ранее.'}
            
            # Начисляем бонус
            amount = promo[0]
            cursor.execute("""
                UPDATE users SET balance = balance + %s WHERE user_id = %s
            """, (amount, user_id))
            
            # Отмечаем как использованный
            cursor.execute("""
                INSERT INTO used_promocodes (user_id, code) VALUES (%s, %s)
            """, (user_id, code))
            
            logger.info(f"User {user_id} activated promocode {code}, added {amount} stars")
            return {'success': True, 'amount': amount}
    
    def create_withdrawal(self, user_id: int, amount: float):
        """Создание заявки на вывод"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO withdrawals (user_id, amount) VALUES (%s, %s)
            """, (user_id, amount))
            logger.info(f"Withdrawal request created: user {user_id}, amount {amount}")
    
    def get_statistics(self) -> Dict:
        """Получение статистики"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(balance), 0) FROM users")
            total_balance = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(referral_count), 0) FROM users")
            total_referrals = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM withdrawals")
            total_withdrawals = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM withdrawals")
            total_withdrawn = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'total_balance': float(total_balance),
                'total_referrals': total_referrals,
                'total_withdrawals': total_withdrawals,
                'total_withdrawn': float(total_withdrawn)
            }
