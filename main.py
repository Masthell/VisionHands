"""
Gesture Controller
==================
Точка входа приложения.

Функционал:
  - Управление компьютером жестами (курсор, клик, скролл)

Управление:
  G — вкл/выкл управление жестами
  Q / ESC — выход
"""

from app import App


if __name__ == "__main__":
    application = App()
    application.run()
