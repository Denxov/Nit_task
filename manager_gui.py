
import tkinter as tk
from tkinter import ttk, messagebox
from server_manager import ServerManager
from data_manager import data_manager
from dictionary_manager import DictionaryManager


class LoginWindow:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success = on_success_callback
        self.setup_login_window()

    def setup_login_window(self):
        """Окно авторизации для менеджера"""
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Авторизация менеджера")
        self.login_window.geometry("350x280")
        self.login_window.resizable(False, False)
        self.login_window.transient(self.root)
        self.login_window.grab_set()

        # Центрируем окно
        self.login_window.update_idletasks()
        x = (self.login_window.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.login_window.winfo_screenheight() // 2) - (280 // 2)
        self.login_window.geometry(f"350x280+{x}+{y}")

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

        # Инициализируем менеджер справочников
        self.dict_manager = DictionaryManager(root)

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

    def setup_conveyor_scroll(self, conveyor_frame, canvas, inner_frame, scrollbar):
        """Настройка прокрутки для конвейера"""

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Создаем тег для всех элементов в canvas
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw", tags=("scrollable",))

        # Привязываем события к тегу
        canvas.tag_bind("scrollable", "<MouseWheel>", on_mousewheel)
        canvas.tag_bind("scrollable", "<Button-4>", on_mousewheel)
        canvas.tag_bind("scrollable", "<Button-5>", on_mousewheel)

        # Также привязываем к самому canvas
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)

        # Привязываем события конфигурации
        canvas.bind("<Configure>", on_frame_configure)
        inner_frame.bind("<Configure>", on_frame_configure)

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
        self.operator_inner_frame.bind("<Configure>", lambda e: self.operator_canvas.configure(
            scrollregion=self.operator_canvas.bbox("all")))

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

        self.conveyor1_canvas = tk.Canvas(conveyor1_frame, highlightthickness=0)
        conveyor1_scrollbar = ttk.Scrollbar(conveyor1_frame, orient=tk.VERTICAL, command=self.conveyor1_canvas.yview)
        self.conveyor1_inner_frame = ttk.Frame(self.conveyor1_canvas)

        self.conveyor1_canvas.configure(yscrollcommand=conveyor1_scrollbar.set)
        self.conveyor1_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conveyor1_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conveyor1_window = self.conveyor1_canvas.create_window((0, 0), window=self.conveyor1_inner_frame,
                                                                    anchor="nw")

        # Конвейер 2
        conveyor2_frame = ttk.LabelFrame(conveyor_frame, text="Конвейер 2", padding=10)
        conveyor2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.conveyor2_canvas = tk.Canvas(conveyor2_frame, highlightthickness=0)
        conveyor2_scrollbar = ttk.Scrollbar(conveyor2_frame, orient=tk.VERTICAL, command=self.conveyor2_canvas.yview)
        self.conveyor2_inner_frame = ttk.Frame(self.conveyor2_canvas)

        self.conveyor2_canvas.configure(yscrollcommand=conveyor2_scrollbar.set)
        self.conveyor2_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conveyor2_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conveyor2_window = self.conveyor2_canvas.create_window((0, 0), window=self.conveyor2_inner_frame,
                                                                    anchor="nw")

        # Настраиваем прокрутку для обоих конвейеров
        self.setup_conveyor_scroll(self.conveyor1_canvas, self.conveyor1_inner_frame, conveyor1_scrollbar, "conv1")
        self.setup_conveyor_scroll(self.conveyor2_canvas, self.conveyor2_inner_frame, conveyor2_scrollbar, "conv2")

        # Панель управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(control_frame, text="Обновить", command=self.refresh_all).pack(side=tk.LEFT, padx=5)

        # Кнопка управления справочниками
        ttk.Button(control_frame, text="Управление справочниками",
                   command=self.dict_manager.show_dictionary_editor).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)

        # Статус сервера
        self.server_status = ttk.Label(control_frame, text="Сервер запущен", foreground="green")
        self.server_status.pack(side=tk.RIGHT, padx=20)

        self.refresh_operators()

    def setup_conveyor_scroll(self, canvas, inner_frame, scrollbar, conveyor_name):
        """Настройка прокрутки для конкретного конвейера"""

        def on_mousewheel(event):
            # Прокручиваем только активный конвейер
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_frame_configure(event):
            # Обновляем scrollregion при изменении размера внутреннего фрейма
            canvas.configure(scrollregion=canvas.bbox("all"))

        # Привязываем события прокрутки к canvas и его содержимому
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)  # Linux scroll up
        canvas.bind("<Button-5>", on_mousewheel)  # Linux scroll down

        # Также привязываем к внутреннему фрейму и всем его потомкам
        def bind_children(parent):
            parent.bind("<MouseWheel>", on_mousewheel)
            parent.bind("<Button-4>", on_mousewheel)
            parent.bind("<Button-5>", on_mousewheel)
            for child in parent.winfo_children():
                bind_children(child)

        bind_children(inner_frame)

        # Привязываем события конфигурации
        inner_frame.bind("<Configure>", on_frame_configure)

    def display_tasks_for_conveyor(self, tasks, frame, conveyor):
        """Отображение задач для конкретного конвейера с кнопкой добавления в конце"""
        # Сначала отображаем существующие задачи
        for task in tasks:
            # Цвет фона в зависимости от статуса и приоритета
            if task.get('status') == 'completed':
                color = 'lightgray'  # Серый для выполненных
            else:
                # Цвет по приоритету для активных задач
                priority = task.get('priority', 'Средний')
                if priority == 'Высокий':
                    color = '#FFCCCC'  # Светло-красный
                elif priority == 'Средний':
                    color = '#FFFFCC'  # Светло-желтый
                else:  # Низкий
                    color = '#CCFFCC'  # Светло-зеленый

            task_frame = tk.Frame(frame, bg=color, relief=tk.RAISED, bd=1)
            task_frame.pack(fill=tk.X, padx=5, pady=2)

            # Информация о количестве
            planned = task.get('planned_quantity', 0)
            completed = task.get('completed_quantity', 0)
            unit = task.get('unit', 'шт')
            progress = f"{completed}/{planned} {unit}"

            # Прогресс выполнения
            if planned > 0:
                progress_percent = (completed / planned) * 100
                progress_text = f" ({progress_percent:.1f}%)"
            else:
                progress_text = ""
            info_text = (f"{task.get('material', 'N/A'):<15} "
                         f"{task.get('color', 'N/A'):<15}"
                         f"{task.get('speed', 'N/A'):<10}"
                         f"{task.get('temperature', 'N/A'):<10}" +
                         progress_text)
            """
            info_text = (f"Приоритет: {task.get('priority', 'Средний')}\n"
                         f"Количество: {progress}{progress_text}\n"
                         f"Сырье: {task['material']}\n"
                         f"Цвет: {task['color']}\n"
                         f"Скорость: {task['speed']}\n"
                         f"Температура: {task['temperature']}")
            """
            if task.get('status') == 'completed':
                info_text += f"\n✅ Выполнено: {task.get('completed', '')}"
            else:
                info_text += f"\nСоздано: {task.get('created', '')}"

            tk.Label(
                task_frame,
                text=info_text,
                bg=color,
                font=('Arial', 9),
                justify=tk.LEFT
            ).pack(padx=5, pady=5)

        # Кнопка добавления задачи В КОНЦЕ списка
        add_task_frame = tk.Frame(frame, bg='lightgreen', relief=tk.RAISED, bd=1)
        add_task_frame.pack(fill=tk.X, padx=5, pady=2)

        add_task_btn = tk.Button(
            add_task_frame,
            text="+",
            height=3,
            bg='lightgreen',
            font=('Arial', 20, 'bold'),
            command=lambda: self.add_task(conveyor)
        )
        add_task_btn.pack(fill=tk.X, padx=5, pady=5)


    def start_periodic_updates(self):
        """Запуск периодического обновления данных"""

        def update():
            self.refresh_operators()
            if self.current_operator:
                self.refresh_tasks()
            self.root.after(5100, update)

        self.root.after(5100, update)

    def refresh_all(self):
        """Обновление всех данных"""
        self.refresh_operators()
        if self.current_operator:
            self.refresh_tasks()

    # В manager_gui.py обновим метод refresh_operators

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

        # Кнопка добавления оператора теперь в редакторе справочников
        # Убираем старую кнопку "+" для операторов

        # Обновляем размер области прокрутки
        self.operator_inner_frame.update_idletasks()
        self.operator_canvas.configure(scrollregion=self.operator_canvas.bbox("all"))

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


    def add_task(self, conveyor):
        """Добавление новой задачи"""
        if not self.current_operator:
            messagebox.showwarning("Предупреждение", "Сначала выберите оператора")
            return

        self.show_task_dialog(conveyor)

    # В методе show_task_dialog класса ManagerGUI
    def show_task_dialog(self, conveyor):
        """Обновленный диалог создания задачи с количеством"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая задача")
        dialog.geometry("350x450")  # Увеличили высоту для количества
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрирование
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

        # Получаем значения из справочников
        materials = self.dict_manager.get_combobox_values("materials")
        colors = self.dict_manager.get_combobox_values("colors")
        speeds = self.dict_manager.get_combobox_values("speeds")
        temperatures = self.dict_manager.get_combobox_values("temperatures")
        priorities = self.dict_manager.get_combobox_values("priorities")
        units = self.dict_manager.get_combobox_values("units")

        ttk.Label(dialog, text="Сырье:").pack(pady=3)
        material_combo = ttk.Combobox(dialog, values=materials, width=28)
        material_combo.pack(pady=3)
        if materials:
            material_combo.set(materials[0])

        ttk.Label(dialog, text="Цвет:").pack(pady=3)
        color_combo = ttk.Combobox(dialog, values=colors, width=28)
        color_combo.pack(pady=3)
        if colors:
            color_combo.set(colors[0])

        ttk.Label(dialog, text="Скорость подачи:").pack(pady=3)
        speed_combo = ttk.Combobox(dialog, values=speeds, width=28)
        speed_combo.pack(pady=3)
        if speeds:
            speed_combo.set(speeds[0])

        ttk.Label(dialog, text="Температура:").pack(pady=3)
        temp_combo = ttk.Combobox(dialog, values=temperatures, width=28)
        temp_combo.pack(pady=3)
        if temperatures:
            temp_combo.set(temperatures[0])

        # Добавляем выбор приоритета
        ttk.Label(dialog, text="Приоритет:").pack(pady=3)
        priority_combo = ttk.Combobox(dialog, values=priorities, width=28)
        priority_combo.pack(pady=3)
        if priorities:
            priority_combo.set(priorities[1])  # Средний по умолчанию

        # Добавляем поля количества
        quantity_frame = ttk.Frame(dialog)
        quantity_frame.pack(fill=tk.X, pady=3)

        ttk.Label(quantity_frame, text="Плановое количество:").pack(side=tk.LEFT)
        quantity_entry = ttk.Entry(quantity_frame, width=8)
        quantity_entry.pack(side=tk.LEFT, padx=5)
        quantity_entry.insert(0, "100")  # Значение по умолчанию

        ttk.Label(quantity_frame, text="Ед.изм:").pack(side=tk.LEFT, padx=(10, 0))
        unit_combo = ttk.Combobox(quantity_frame, values=units, width=5)
        unit_combo.pack(side=tk.LEFT, padx=5)
        if units:
            unit_combo.set(units[0])  # шт по умолчанию

        def save_task():
            # Проверка заполнения полей
            if not all([material_combo.get(), color_combo.get(), speed_combo.get(),
                        temp_combo.get(), priority_combo.get(), quantity_entry.get()]):
                messagebox.showwarning("Предупреждение", "Заполните все поля")
                return

            # Проверка числового значения количества
            try:
                planned_quantity = int(quantity_entry.get())
                if planned_quantity <= 0:
                    raise ValueError("Количество должно быть положительным")
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректное число для количества")
                return

            task_data = {
                'material': material_combo.get(),
                'color': color_combo.get(),
                'speed': speed_combo.get(),
                'temperature': temp_combo.get(),
                'priority': priority_combo.get(),
                'planned_quantity': planned_quantity,
                'unit': unit_combo.get()
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
        material_combo.focus()




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