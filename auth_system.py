import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os


class AuthSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Production System - Авторизация")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Центрируем окно
        self.center_window()

        # Создаем основной фрейм
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_ui()

    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Заголовок
        title_label = ttk.Label(
            self.main_frame,
            text="Система управления производством",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=20)

        subtitle_label = ttk.Label(
            self.main_frame,
            text="Выберите тип пользователя",
            font=('Arial', 12)
        )
        subtitle_label.pack(pady=10)

        # Фрейм для кнопок выбора
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(pady=30)

        # Кнопка менеджера
        manager_btn = ttk.Button(
            buttons_frame,
            text="Менеджер",
            command=self.start_manager,
            width=20,
            style='Accent.TButton'
        )
        manager_btn.grid(row=0, column=0, padx=20, pady=10, ipady=10)

        # Кнопка оператора
        operator_btn = ttk.Button(
            buttons_frame,
            text="Оператор",
            command=self.start_operator,
            width=20,
            style='Accent.TButton'
        )
        operator_btn.grid(row=0, column=1, padx=20, pady=10, ipady=10)

        # Разделительная линия
        separator = ttk.Separator(self.main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=20)

        # Тестовый доступ
        test_frame = ttk.LabelFrame(self.main_frame, text="Быстрый доступ для тестирования", padding=10)
        test_frame.pack(fill=tk.X, pady=10)

        test_label = ttk.Label(
            test_frame,
            text="Для тестирования системы:",
            font=('Arial', 10)
        )
        test_label.pack(anchor=tk.W)

        # Кнопки быстрого доступа
        quick_access_frame = ttk.Frame(test_frame)
        quick_access_frame.pack(fill=tk.X, pady=10)

        quick_manager_btn = ttk.Button(
            quick_access_frame,
            text="Запуск менеджера",
            command=self.start_manager_direct,
            width=15
        )
        quick_manager_btn.pack(side=tk.LEFT, padx=5)

        quick_operator_btn = ttk.Button(
            quick_access_frame,
            text="Запуск оператора",
            command=self.start_operator_direct,
            width=15
        )
        quick_operator_btn.pack(side=tk.LEFT, padx=5)

        # Информация о тестовых учетных данных
        creds_frame = ttk.Frame(test_frame)
        creds_frame.pack(fill=tk.X, pady=5)

        creds_label = ttk.Label(
            creds_frame,
            text="Тестовые учетные данные:\n"
                 "Менеджер: manager / manager\n"
                 "Операторы: operator1 / pass1, operator2 / pass2, operator3 / pass3",
            font=('Arial', 9),
            foreground="gray",
            justify=tk.LEFT
        )
        creds_label.pack(anchor=tk.W)

        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        # Настраиваем стиль для акцентных кнопок
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))

    def start_manager(self):
        """Запуск менеджера с подтверждением"""
        result = messagebox.askyesno(
            "Подтверждение",
            "Запустить панель менеджера?\n\n"
            "Для входа используйте:\n"
            "Логин: manager\n"
            "Пароль: manager"
        )
        if result:
            self.start_manager_direct()

    def start_operator(self):
        """Запуск оператора с подтверждением"""
        result = messagebox.askyesno(
            "Подтверждение",
            "Запустить панель оператора?\n\n"
            "Для входа используйте:\n"
            "operator1 / pass1\n"
            "operator2 / pass2\n"
            "operator3 / pass3"
        )
        if result:
            self.start_operator_direct()

    def start_manager_direct(self):
        """Прямой запуск менеджера"""
        self.status_var.set("Запуск панели менеджера...")
        self.root.update()

        try:
            # Проверяем существование файла
            if not os.path.exists('manager_gui.py'):
                messagebox.showerror(
                    "Ошибка",
                    "Файл manager_gui.py не найден!\n\n"
                    "Убедитесь, что все файлы находятся в одной папке:\n"
                    "- auth_system.py\n"
                    "- manager_gui.py\n"
                    "- operator_gui.py\n"
                    "- server_manager.py"
                )
                self.status_var.set("Ошибка: файл manager_gui.py не найден")
                return

            # Запускаем в отдельном процессе
            if sys.platform == "win32":
                # На Windows используем CREATE_NEW_CONSOLE чтобы видеть ошибки
                subprocess.Popen(
                    [sys.executable, 'manager_gui.py'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # На других ОС
                subprocess.Popen([sys.executable, 'manager_gui.py'])

            self.status_var.set("Панель менеджера запущена")

            # Спрашиваем, закрыть ли окно авторизации
            if messagebox.askyesno("Авторизация", "Закрыть окно авторизации?"):
                self.root.destroy()
            else:
                self.status_var.set("Готов к работе")

        except Exception as e:
            error_msg = f"Ошибка запуска менеджера: {str(e)}"
            messagebox.showerror("Ошибка", error_msg)
            self.status_var.set("Ошибка запуска")
            print(f"Debug: {e}")

    def start_operator_direct(self):
        """Прямой запуск оператора"""
        self.status_var.set("Запуск панели оператора...")
        self.root.update()

        try:
            # Проверяем существование файла
            if not os.path.exists('operator_gui.py'):
                messagebox.showerror(
                    "Ошибка",
                    "Файл operator_gui.py не найден!\n\n"
                    "Убедитесь, что все файлы находятся в одной папке:\n"
                    "- auth_system.py\n"
                    "- manager_gui.py\n"
                    "- operator_gui.py\n"
                    "- server_manager.py"
                )
                self.status_var.set("Ошибка: файл operator_gui.py не найден")
                return

            # Запускаем в отдельном процессе
            if sys.platform == "win32":
                subprocess.Popen(
                    [sys.executable, 'operator_gui.py'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([sys.executable, 'operator_gui.py'])

            self.status_var.set("Панель оператора запущена")

            # Спрашиваем, закрыть ли окно авторизации
            if messagebox.askyesno("Авторизация", "Закрыть окно авторизации?"):
                self.root.destroy()
            else:
                self.status_var.set("Готов к работе")

        except Exception as e:
            error_msg = f"Ошибка запуска оператора: {str(e)}"
            messagebox.showerror("Ошибка", error_msg)
            self.status_var.set("Ошибка запуска")
            print(f"Debug: {e}")

    def safe_destroy(self):
        """Безопасное закрытие приложения"""
        try:
            self.root.destroy()
        except:
            pass


def main():
    """Главная функция с обработкой исключений"""
    try:
        # Создаем главное окно
        root = tk.Tk()

        # Устанавливаем иконку если есть
        try:
            root.iconbitmap("icon.ico")  # Если есть иконка
        except:
            pass

        # Создаем приложение
        app = AuthSystem(root)

        # Обработка закрытия окна
        def on_closing():
            if messagebox.askokcancel("Выход", "Закрыть систему авторизации?"):
                app.safe_destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Запускаем главный цикл
        root.mainloop()

    except Exception as e:
        # Критическая ошибка - показываем в messagebox
        error_msg = f"Критическая ошибка при запуске:\n{str(e)}"
        print(error_msg)
        try:
            tk.Tk().withdraw()  # Скрытое окно для messagebox
            messagebox.showerror("Ошибка запуска", error_msg)
        except:
            print("Не удалось показать сообщение об ошибке")


if __name__ == "__main__":
    main()