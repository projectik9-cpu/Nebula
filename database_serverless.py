"""
Работа с PostgreSQL базой данных для Serverless
Вместо SQLite используем PostgreSQL (Supabase/Neon/Railway)
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Dict
import logging
from config_serverless import DATABASE_URL

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        """Инициализация пула подключений"""
        try:
            # Создаём пул подключений для эффективной работы
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL
            )
            logger.info("Database connection pool created")
            self.init_db()
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    def get_connection(self):
        """Получить подключение из пула"""
        return self.pool.getconn()
    
    def release_connection(self, conn):
        """Вернуть подключение в пул"""
        self.pool.putconn(conn)
    
    def init_db(self):
        """Инициализация таблиц"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
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
            
            conn.commit()
            logger.info("Database tables initialized")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def health_check(self) -> Dict:
        """Проверка подключения к базе данных"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return {"status": "connected"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self.release_connection(conn)
    
    def user_exists(self, user_id: int) -> bool:
        """Проверка существования пользователя"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        finally:
            self.release_connection(conn)
    
    def add_user(self, user_id: int, username: str, full_name: str, referrer_id: Optional[int] = None):
        """Добавление нового пользователя"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, full_name, referrer_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, username, full_name, referrer_id))
            conn.commit()
            cursor.close()
            logger.info(f"User {user_id} added to database")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding user {user_id}: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение данных пользователя"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT user_id, username, full_name, balance, referrer_id, referral_count
                FROM users WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        finally:
            self.release_connection(conn)
    
    def add_balance(self, user_id: int, amount: float):
        """Начисление баланса"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET balance = balance + %s WHERE user_id = %s
            """, (amount, user_id))
            conn.commit()
            cursor.close()
            logger.info(f"Added {amount} stars to user {user_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding balance to user {user_id}: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def set_balance(self, user_id: int, balance: float):
        """Установка баланса"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET balance = %s WHERE user_id = %s
            """, (balance, user_id))
            conn.commit()
            cursor.close()
            logger.info(f"Set balance of user {user_id} to {balance}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error setting balance for user {user_id}: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def subtract_balance(self, user_id: int, amount: float):
        """Списание баланса"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET balance = balance - %s WHERE user_id = %s
            """, (amount, user_id))
            conn.commit()
            cursor.close()
            logger.info(f"Subtracted {amount} stars from user {user_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error subtracting balance from user {user_id}: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def increment_referral_count(self, user_id: int):
        """Увеличение счётчика рефералов"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET referral_count = referral_count + 1 WHERE user_id = %s
            """, (user_id,))
            conn.commit()
            cursor.close()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error incrementing referral count for user {user_id}: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def create_promocode(self, code: str, amount: float):
        """Создание промокода"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO promocodes (code, amount) VALUES (%s, %s)
                ON CONFLICT (code) DO NOTHING
            """, (code, amount))
            conn.commit()
            cursor.close()
            logger.info(f"Promocode {code} created")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating promocode {code}: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def activate_promocode(self, user_id: int, code: str) -> Dict:
        """Активация промокода"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Проверяем существование промокода
            cursor.execute("SELECT amount FROM promocodes WHERE code = %s", (code,))
            promo = cursor.fetchone()
            
            if not promo:
                cursor.close()
                logger.warning(f"Promocode {code} not found")
                return {'success': False, 'message': 'Промокод не найден.\nПроверьте правильность ввода.'}
            
            # Проверяем использование
            cursor.execute("""
                SELECT * FROM used_promocodes WHERE user_id = %s AND code = %s
            """, (user_id, code))
            used = cursor.fetchone()
            
            if used:
                cursor.close()
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
            
            conn.commit()
            cursor.close()
            
            logger.info(f"User {user_id} activated promocode {code}, added {amount} stars")
            return {'success': True, 'amount': amount}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error activating promocode: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def create_withdrawal(self, user_id: int, amount: float):
        """Создание заявки на вывод"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO withdrawals (user_id, amount) VALUES (%s, %s)
            """, (user_id, amount))
            conn.commit()
            cursor.close()
            logger.info(f"Withdrawal request created: user {user_id}, amount {amount}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating withdrawal: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def get_statistics(self) -> Dict:
        """Получение статистики"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
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
            
            cursor.close()
            
            return {
                'total_users': total_users,
                'total_balance': float(total_balance),
                'total_referrals': total_referrals,
                'total_withdrawals': total_withdrawals,
                'total_withdrawn': float(total_withdrawn)
            }
        finally:
            self.release_connection(conn)
