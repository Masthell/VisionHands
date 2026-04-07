"""
Менеджер настроек пользователя (SQLite).
Хранит персональные профили на флешке рядом с .exe.
"""

import sqlite3
import os
import sys


def get_app_dir():
    """Определить папку, где лежит программа (работает и для .exe, и для .py)."""
    if getattr(sys, 'frozen', False):
        # Скомпилированный .exe — папка, где лежит сам .exe (на флешке)
        return os.path.dirname(sys.executable)
    else:
        # Обычный запуск из IDE / терминала
        return os.path.dirname(os.path.abspath(__file__))


def get_resource_dir():
    """Определить папку с ресурсами (модели и т.д.).
    
    При PyInstaller --onefile ресурсы распаковываются во временную папку.
    При обычном запуске — папка со скриптом.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))


class SettingsManager:
    """Класс для хранения настроек пользователя в SQLite."""

    DEFAULT_SETTINGS = {
        'active_hand': 'right',
        'smoothing': 5,
        'click_cooldown': 0.4,
        'right_click_cooldown': 0.8,
        'scroll_speed': 5,
        'detection_confidence': 0.5,
    }

    def __init__(self, profile_name='default'):
        """
        Инициализация менеджера настроек.

        Args:
            profile_name: Имя профиля пользователя
        """
        app_dir = get_app_dir()
        self.db_path = os.path.join(app_dir, 'user_settings.db')
        self.profile_name = profile_name
        self._init_db()
        self._ensure_profile()

    def _init_db(self):
        """Создать таблицы при первом запуске."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    name TEXT PRIMARY KEY,
                    active_hand TEXT DEFAULT 'right',
                    smoothing INTEGER DEFAULT 5,
                    click_cooldown REAL DEFAULT 0.4,
                    right_click_cooldown REAL DEFAULT 0.8,
                    scroll_speed INTEGER DEFAULT 5,
                    detection_confidence REAL DEFAULT 0.5
                )
            ''')
            conn.commit()

    def _ensure_profile(self):
        """Создать профиль, если его ещё нет."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                'SELECT name FROM profiles WHERE name = ?',
                (self.profile_name,)
            ).fetchone()

            if row is None:
                conn.execute(
                    'INSERT INTO profiles (name) VALUES (?)',
                    (self.profile_name,)
                )
                conn.commit()

    def get_all(self):
        """Получить все настройки профиля как словарь."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT * FROM profiles WHERE name = ?',
                (self.profile_name,)
            ).fetchone()

            if row is None:
                return dict(self.DEFAULT_SETTINGS)

            return {
                'active_hand': row['active_hand'],
                'smoothing': row['smoothing'],
                'click_cooldown': row['click_cooldown'],
                'right_click_cooldown': row['right_click_cooldown'],
                'scroll_speed': row['scroll_speed'],
                'detection_confidence': row['detection_confidence'],
            }

    def get(self, key):
        """Получить одну настройку по ключу."""
        settings = self.get_all()
        return settings.get(key, self.DEFAULT_SETTINGS.get(key))

    def update(self, key, value):
        """Обновить одну настройку."""
        allowed = list(self.DEFAULT_SETTINGS.keys())
        if key not in allowed:
            raise ValueError(f"Неизвестная настройка: {key}")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'UPDATE profiles SET {key} = ? WHERE name = ?',
                (value, self.profile_name)
            )
            conn.commit()

    def list_profiles(self):
        """Получить список всех профилей."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('SELECT name FROM profiles').fetchall()
            return [r[0] for r in rows]

    def __repr__(self):
        return f"SettingsManager(profile='{self.profile_name}', db='{self.db_path}')"
