import datetime
import sqlite3
import time


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        """Добавляем пользователя в бд"""
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO users (user_id) VALUES (:user_id)",
                {'user_id': user_id}
            )

    def user_exists(self, user_id):
        """Проверяем существует ли пользователь в бд"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchall()
            return bool(len(result))

    def set_nickname(self, user_id, nickname):
        """Добовляет никнейм пользователю"""
        with self.connection:
            return self.cursor.execute(
                "UPDATE users SET nickname = ? WHERE user_id = ?",
                (nickname, user_id,)
            )

    def get_signup(self, user_id):
        """Выводит статус регистрации"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT signup FROM users WHERE user_id = ?", (user_id,)
            )
            signup = str(result.fetchone()[0])
            return signup

    def set_signup(self, user_id, signup):
        """Обновляет статус регистрации"""
        with self.connection:
            return self.cursor.execute(
                "UPDATE users SET signup = ? WHERE user_id = ?",
                (signup, user_id,)
            )

    def get_nickname(self, user_id):
        """Выводит никнейм пользователя"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT nickname FROM users WHERE user_id = ?",
                (user_id,)
            )
            nickname = str(result.fetchone()[0])
            return nickname

    def set_time_sub(self, user_id, time_sub):
        """Обновляет время подписки"""
        with self.connection:
            return self.cursor.execute(
                "UPDATE users SET time_sub = ? WHERE user_id = ?",
                (time_sub, user_id,)
            )

    def get_time_sub(self, user_id):
        """Выводит время подписки"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT time_sub FROM users WHERE user_id = ?",
                (user_id,)
            )
            time_sub = int(result.fetchone()[0])
            return time_sub

    def get_sub_status(self, user_id):
        """Проверяет есть подписка или нет"""
        with self.connection:
            result = self.cursor.execute(
                "SELECT time_sub FROM users WHERE user_id = ?",
                (user_id,)
            )
            time_sub = int(result.fetchone()[0])

            return time_sub > int(time.time())

    def get_all_users(self):
        """Выводит всех пользователей"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM users')
            users = result.fetchall()
            return users

    def add_payment(self, user_id, tg_payment_id, provider_payment_id):
        """Добавляет данные об оплате"""
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connection:
            return self.cursor.execute(
                "INSERT INTO payments (user_id, tg_payment_id, "
                "provider_payment_id, date) VALUES (?, ?, ?, ?)",
                (user_id, tg_payment_id, provider_payment_id, date)
            )
