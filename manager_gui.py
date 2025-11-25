import tkinter as tk
from tkinter import ttk, messagebox
from server_manager import ServerManager


class LoginWindow:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success = on_success_callback
        self.setup_login_window()

    def setup_login_window(self):
        """Окно авторизации для менеджера"""
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Авторизация менеджера")
        self.login_window.geometry("350x250")
        self.login_window.resizable(False, False)
        self.login_window.transient(self.root)
        self.login_window.grab_set()

        # Центрируем окно
        self.login_window.update_idletasks()
        x = (self.login_window.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.login_window.winfo_screenheight() // 2) - (250 // 2)
        self.login_window.geometry(f"350x250+{x}+{y}")

        # Основной фрейм
        main_frame = ttk.Frame(self.login_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="Вход для менеджера",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=10)

        # Поля ввода
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=20)

        ttk.Label(input_frame, text="Логин:", font=('Arial', 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(input_frame, width=20, font=('Arial', 10))
        self.username_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=10)

        ttk.Label(input_frame, text="Пароль:", font=('Arial', 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(input_frame, width=20, show="*", font=('Arial', 10))
        self.password_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=10)

        input_frame.columnconfigure(1, weight=1)

        # Статус
        self.status_label = ttk.Label(
            main_frame,
            text="Введите учетные данные",
            foreground="blue"
        )
        self.status_label.pack(pady=5)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        login_btn = ttk.Button(
            button_frame,
            text="Войти",
            command=self.do_login,
            width=15
        )
        login_btn.pack(side=tk.LEFT, padx=5)

        exit_btn = ttk.Button(
            button_frame,
            text="Выход",
            command=self.exit_app,
            width=15
        )
        exit_btn.pack(side=tk.LEFT, padx=5)

        # Тестовая информация
        test_frame = ttk.Frame(main_frame)
        test_frame.pack(fill=tk.X, pady=10)

        test_label = ttk.Label(
            test_frame,
            text="Тестовые данные: manager / manager",
            font=('Arial', 9),
            foreground="gray"
        )
        test_label.pack()

        # Автозаполнение для тестирования
        self.username_entry.insert(0, "manager")
        self.password_entry.insert(0, "manager")

        # Привязка Enter
        self.login_window.bind('<Return>', lambda e: self.do_login())
        self.username_entry.focus()

    def do_login(self):
        """Проверка учетных данных"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_label.config(text="Введите логин и пароль", foreground="red")
            return

        # Проверяем учетные данные
        if username == "manager" and password == "manager":
            self.status_label.config(text="Успешный вход!", foreground="green")
            self.login_window.after(1000, self.login_success)
        else:
            self.status_label.config(text="Неверные учетные данные", foreground="red")

    def login_success(self):
        """Успешный вход"""
        self.login_window.destroy()
        self.on_success()

    def exit_app(self):
        """Выход из приложения"""
        self.root.destroy()


class ManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Manager Panel - Production Control System")
        self.root.geometry("1200x700")

        # Сначала показываем окно авторизации
        self.show_authorization()

    def show_authorization(self):
        """Показ окна авторизации"""
        self.login = LoginWindow(self.root, self.on_auth_success)

    def on_auth_success(self):
        """Успешная авторизация - запускаем основное приложение"""
        self.setup_main_application()

    def setup_main_application(self):
        """Настройка основного приложения после авторизации"""
        # Запускаем сервер
        self.server = ServerManager()
        self.server.start_server()

        self.current_operator = None
        self.current_conveyor = 0

        self.setup_gui()
        self.start_periodic_updates()

    def setup_gui(self):
        """Настройка основного GUI"""
        # Верхняя панель с операторами
        operator_frame = ttk.Frame(self.root)
        operator_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(operator_frame, text="Операторы:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)

        # Фрейм для кнопок операторов с прокруткой
        self.operator_canvas = tk.Canvas(operator_frame, height=60)
        self.operator_scrollbar = ttk.Scrollbar(operator_frame, orient=tk.HORIZONTAL,
                                                command=self.operator_canvas.xview)
        self.operator_inner_frame = ttk.Frame(self.operator_canvas)

        self.operator_canvas.configure(xscrollcommand=self.operator_scrollbar.set)
        self.operator_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.operator_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.operator_canvas.create_window((0, 0), window=self.operator_inner_frame, anchor="nw")
        self.operator_inner_frame.bind("<Configure>", self.on_operator_frame_configure)

        # Основная область с задачами
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Заголовок выбранного оператора
        self.operator_label = ttk.Label(main_frame, text="Выберите оператора", font=('Arial', 14, 'bold'))
        self.operator_label.pack(pady=10)

        # Фрейм для двух конвейеров
        conveyor_frame = ttk.Frame(main_frame)
        conveyor_frame.pack(fill=tk.BOTH, expand=True)

        # Конвейер 1
        conveyor1_frame = ttk.LabelFrame(conveyor_frame, text="Конвейер 1", padding=10)
        conveyor1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.conveyor1_canvas = tk.Canvas(conveyor1_frame)
        conveyor1_scrollbar = ttk.Scrollbar(conveyor1_frame, orient=tk.VERTICAL, command=self.conveyor1_canvas.yview)
        self.conveyor1_inner_frame = ttk.Frame(self.conveyor1_canvas)

        self.conveyor1_canvas.configure(yscrollcommand=conveyor1_scrollbar.set)
        self.conveyor1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conveyor1_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conveyor1_canvas.create_window((0, 0), window=self.conveyor1_inner_frame, anchor="nw")

        # Конвейер 2
        conveyor2_frame = ttk.LabelFrame(conveyor_frame, text="Конвейер 2", padding=10)
        conveyor2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.conveyor2_canvas = tk.Canvas(conveyor2_frame)
        conveyor2_scrollbar = ttk.Scrollbar(conveyor2_frame, orient=tk.VERTICAL, command=self.conveyor2_canvas.yview)
        self.conveyor2_inner_frame = ttk.Frame(self.conveyor2_canvas)

        self.conveyor2_canvas.configure(yscrollcommand=conveyor2_scrollbar.set)
        self.conveyor2_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conveyor2_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conveyor2_canvas.create_window((0, 0), window=self.conveyor2_inner_frame, anchor="nw")

        # Привязка событий прокрутки
        self.conveyor1_inner_frame.bind("<Configure>", lambda e: self.conveyor1_canvas.configure(
            scrollregion=self.conveyor1_canvas.bbox("all")))
        self.conveyor2_inner_frame.bind("<Configure>", lambda e: self.conveyor2_canvas.configure(
            scrollregion=self.conveyor2_canvas.bbox("all")))

        # Панель управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(control_frame, text="Обновить", command=self.refresh_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)

        # Статус сервера
        self.server_status = ttk.Label(control_frame, text="Сервер запущен", foreground="green")
        self.server_status.pack(side=tk.RIGHT, padx=20)

        self.refresh_operators()

    def on_operator_frame_configure(self, event):
        self.operator_canvas.configure(scrollregion=self.operator_canvas.bbox("all"))

    def start_periodic_updates(self):
        """Запуск периодического обновления данных"""

        def update():
            self.refresh_operators()
            if self.current_operator:
                self.refresh_tasks()
            self.root.after(5000, update)

        self.root.after(5000, update)

    def refresh_all(self):
        """Обновление всех данных"""
        self.refresh_operators()
        if self.current_operator:
            self.refresh_tasks()

    def refresh_operators(self):
        """Обновление списка операторов"""
        # Очистка текущих кнопок операторов
        for widget in self.operator_inner_frame.winfo_children():
            widget.destroy()

        operators_data = self.server.handle_get_operators()['operators']

        # Кнопки операторов
        for username, data in operators_data.items():
            color = 'lightblue' if data['active'] else 'lightgray'
            btn = tk.Button(
                self.operator_inner_frame,
                text=username,
                width=15,
                height=2,
                bg=color,
                font=('Arial', 10),
                command=lambda u=username: self.select_operator(u)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)

            # Выделение выбранного оператора
            if username == self.current_operator:
                btn.config(bg='lightgreen', relief=tk.SUNKEN)

        # Кнопка добавления оператора
        add_btn = tk.Button(
            self.operator_inner_frame,
            text="+",
            width=5,
            height=2,
            bg='lightgreen',
            font=('Arial', 14, 'bold'),
            command=self.add_operator
        )
        add_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def select_operator(self, username):
        """Выбор оператора для просмотра задач"""
        self.current_operator = username
        self.operator_label.config(text=f"Оператор: {username}")
        self.refresh_operators()
        self.refresh_tasks()

    def refresh_tasks(self):
        """Обновление отображения задач для выбранного оператора"""
        if not self.current_operator:
            return

        # Очистка текущих задач
        for widget in self.conveyor1_inner_frame.winfo_children():
            widget.destroy()
        for widget in self.conveyor2_inner_frame.winfo_children():
            widget.destroy()

        operators_data = self.server.handle_get_operators()['operators']
        if self.current_operator not in operators_data:
            return

        tasks = operators_data[self.current_operator]['tasks']

        # Отображение задач для конвейера 1
        self.display_tasks_for_conveyor(tasks[0], self.conveyor1_inner_frame, 0)

        # Отображение задач для конвейера 2
        self.display_tasks_for_conveyor(tasks[1], self.conveyor2_inner_frame, 1)

    def display_tasks_for_conveyor(self, tasks, frame, conveyor):
        """Отображение задач для конкретного конвейера"""
        # Кнопка добавления задачи
        add_task_btn = tk.Button(
            frame,
            text="+",
            height=3,
            bg='lightgreen',
            font=('Arial', 20, 'bold'),
            command=lambda: self.add_task(conveyor)
        )
        add_task_btn.pack(fill=tk.X, padx=5, pady=2)

        # Существующие задачи
        for task in tasks:
            color = 'lightyellow' if task.get('status') == 'completed' else 'white'
            task_frame = tk.Frame(frame, bg=color, relief=tk.RAISED, bd=1)
            task_frame.pack(fill=tk.X, padx=5, pady=2)

            info_text = f"Сырье: {task['material']}\nЦвет: {task['color']}\nСкорость: {task['speed']}\nТемпература: {task['temperature']}"
            if task.get('status') == 'completed':
                info_text += f"\nВыполнено: {task.get('completed', '')}"
            else:
                info_text += f"\nСоздано: {task.get('created', '')}"

            tk.Label(
                task_frame,
                text=info_text,
                bg=color,
                font=('Arial', 9),
                justify=tk.LEFT
            ).pack(padx=5, pady=5)

    def add_task(self, conveyor):
        """Добавление новой задачи"""
        if not self.current_operator:
            messagebox.showwarning("Предупреждение", "Сначала выберите оператора")
            return

        self.show_task_dialog(conveyor)

    def show_task_dialog(self, conveyor):
        """Диалоговое окно для создания новой задачи"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая задача")
        dialog.geometry("300x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрирование диалога
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

        ttk.Label(dialog, text="Сырье:").pack(pady=5)
        material_entry = ttk.Entry(dialog, width=30)
        material_entry.pack(pady=5)
        material_entry.focus()

        ttk.Label(dialog, text="Цвет:").pack(pady=5)
        color_entry = ttk.Entry(dialog, width=30)
        color_entry.pack(pady=5)

        ttk.Label(dialog, text="Скорость подачи:").pack(pady=5)
        speed_entry = ttk.Entry(dialog, width=30)
        speed_entry.pack(pady=5)

        ttk.Label(dialog, text="Температура:").pack(pady=5)
        temp_entry = ttk.Entry(dialog, width=30)
        temp_entry.pack(pady=5)

        def save_task():
            # Проверка заполнения полей
            if not all([material_entry.get(), color_entry.get(), speed_entry.get(), temp_entry.get()]):
                messagebox.showwarning("Предупреждение", "Заполните все поля")
                return

            task_data = {
                'material': material_entry.get(),
                'color': color_entry.get(),
                'speed': speed_entry.get(),
                'temperature': temp_entry.get()
            }

            result = self.server.handle_add_task({
                'operator': self.current_operator,
                'conveyor': conveyor,
                'task': task_data
            })

            if result['status'] == 'success':
                print(f"Задача успешно добавлена: {result['task_id']}")
                self.refresh_tasks()
                dialog.destroy()
                messagebox.showinfo("Успех", "Задача успешно добавлена")
            else:
                messagebox.showerror("Ошибка", result.get('message', 'Не удалось добавить задачу'))

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Сохранить", command=save_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Привязка Enter к сохранению
        dialog.bind('<Return>', lambda e: save_task())

    def add_operator(self):
        """Добавление нового оператора"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить оператора")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрирование диалога
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

        ttk.Label(dialog, text="Логин:").pack(pady=5)
        login_entry = ttk.Entry(dialog, width=30)
        login_entry.pack(pady=5)
        login_entry.focus()

        ttk.Label(dialog, text="Пароль:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)

        def save_operator():
            if not login_entry.get() or not password_entry.get():
                messagebox.showwarning("Предупреждение", "Заполните все поля")
                return

            result = self.server.handle_add_operator({
                'username': login_entry.get(),
                'password': password_entry.get()
            })

            if result['status'] == 'success':
                self.refresh_operators()
                dialog.destroy()
                messagebox.showinfo("Успех", "Оператор успешно добавлен")
            else:
                messagebox.showerror("Ошибка", result['message'])

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Сохранить", command=save_operator).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Привязка Enter к сохранению
        dialog.bind('<Return>', lambda e: save_operator())

    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Выйти из системы менеджера?"):
            if hasattr(self, 'server'):
                self.server.running = False
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ManagerGUI(root)
    root.mainloop()