import tkinter as tk
from tkinter import ttk, messagebox
from data_manager import data_manager


# В dictionary_manager.py добавим вкладку для управления операторами

class DictionaryManager:
    def __init__(self, parent):
        self.parent = parent

    def show_dictionary_editor(self):
        """Показ редактора справочников с операторами"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Управление справочниками")
        dialog.geometry("700x500")
        dialog.transient(self.parent)
        dialog.grab_set()

        # Центрирование
        dialog.geometry("+%d+%d" % (self.parent.winfo_rootx() + 50, self.parent.winfo_rooty() + 50))

        # Создаем notebook для разных справочников
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка для каждого справочника
        self.create_dictionary_tab(notebook, "materials", "Сырье")
        self.create_dictionary_tab(notebook, "colors", "Цвета")
        self.create_dictionary_tab(notebook, "speeds", "Скорости")
        self.create_dictionary_tab(notebook, "temperatures", "Температуры")
        self.create_dictionary_tab(notebook, "priorities", "Приоритеты")
        self.create_dictionary_tab(notebook, "units", "Единицы измерения")
        self.create_operators_tab(notebook)  # Новая вкладка для операторов

        # Кнопка закрытия
        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def create_operators_tab(self, notebook):
        """Создание вкладки для управления операторами"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Операторы")

        # Заголовок
        ttk.Label(frame, text="Управление операторами", font=('Arial', 12, 'bold')).pack(pady=10)

        # Список операторов
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Заголовки таблицы
        header_frame = ttk.Frame(listbox_frame)
        header_frame.pack(fill=tk.X)

        ttk.Label(header_frame, text="Логин", width=15, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Статус", width=10, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Задачи", width=10, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=2)

        # Прокрутка для списка
        canvas = tk.Canvas(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)

        # Загружаем операторов
        self.refresh_operators_list(inner_frame)

        # Панель управления операторами
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Label(control_frame, text="Логин:").pack(side=tk.LEFT)
        username_entry = ttk.Entry(control_frame, width=15)
        username_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Пароль:").pack(side=tk.LEFT, padx=(10, 0))
        password_entry = ttk.Entry(control_frame, width=15, show="*")
        password_entry.pack(side=tk.LEFT, padx=5)

        def add_operator():
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not username or not password:
                messagebox.showwarning("Ошибка", "Введите логин и пароль")
                return

            success, message = data_manager.add_operator(username, password)
            if success:
                messagebox.showinfo("Успех", message)
                username_entry.delete(0, tk.END)
                password_entry.delete(0, tk.END)
                self.refresh_operators_list(inner_frame)
            else:
                messagebox.showerror("Ошибка", message)

        def remove_operator():
            # В реальной реализации здесь нужно получить выбранного оператора
            # Для простоты будем удалять по логину из поля ввода
            username = username_entry.get().strip()
            if not username:
                messagebox.showwarning("Ошибка", "Введите логин оператора для удаления")
                return

            if messagebox.askyesno("Подтверждение", f"Удалить оператора '{username}'?"):
                success, message = data_manager.remove_operator(username)
                if success:
                    messagebox.showinfo("Успех", message)
                    username_entry.delete(0, tk.END)
                    password_entry.delete(0, tk.END)
                    self.refresh_operators_list(inner_frame)
                else:
                    messagebox.showerror("Ошибка", message)

        def change_password():
            username = username_entry.get().strip()
            new_password = password_entry.get().strip()

            if not username or not new_password:
                messagebox.showwarning("Ошибка", "Введите логин и новый пароль")
                return

            success, message = data_manager.update_operator_password(username, new_password)
            if success:
                messagebox.showinfo("Успех", message)
                password_entry.delete(0, tk.END)
                self.refresh_operators_list(inner_frame)
            else:
                messagebox.showerror("Ошибка", message)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(button_frame, text="Добавить", command=add_operator).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Удалить", command=remove_operator).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Сменить пароль", command=change_password).pack(side=tk.LEFT, padx=2)

    def refresh_operators_list(self, parent_frame):
        """Обновление списка операторов"""
        # Очищаем старый список
        for widget in parent_frame.winfo_children():
            widget.destroy()

        operators = data_manager.load_operators()

        for i, operator in enumerate(operators):
            row_frame = ttk.Frame(parent_frame)
            row_frame.pack(fill=tk.X, pady=1)

            # Логин
            ttk.Label(row_frame, text=operator['username'], width=15).pack(side=tk.LEFT, padx=2)

            # Статус
            status = "✅ Онлайн" if operator['active'] else "❌ Офлайн"
            ttk.Label(row_frame, text=status, width=10).pack(side=tk.LEFT, padx=2)

            # Количество задач
            total_tasks = len(operator['tasks'][0]) + len(operator['tasks'][1])
            active_tasks = sum(
                1 for task in operator['tasks'][0] + operator['tasks'][1] if task.get('status') == 'active')
            tasks_text = f"{active_tasks}/{total_tasks}"
            ttk.Label(row_frame, text=tasks_text, width=10).pack(side=tk.LEFT, padx=2)

            # Добавляем разделитель
            if i < len(operators) - 1:
                ttk.Separator(parent_frame, orient='horizontal').pack(fill=tk.X, pady=2)

    # ... остальные методы без изменений ...


    def create_dictionary_tab(self, notebook, dict_name, title):
        """Создание вкладки для справочника"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        # Список значений
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        listbox = tk.Listbox(listbox_frame, font=('Arial', 12))
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Загружаем данные
        self.refresh_listbox(listbox, dict_name)

        # Панель управления
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="Новое значение:").pack(side=tk.LEFT)
        entry = ttk.Entry(control_frame, width=20)
        entry.pack(side=tk.LEFT, padx=5)

        def add_value():
            value = entry.get().strip()
            if value:
                if data_manager.add_to_dictionary(dict_name, value):
                    self.refresh_listbox(listbox, dict_name)
                    entry.delete(0, tk.END)
                else:
                    messagebox.showinfo("Информация", "Значение уже существует")
            else:
                messagebox.showwarning("Ошибка", "Введите значение")

        def remove_value():
            selection = listbox.curselection()
            if selection:
                value = listbox.get(selection[0])
                if messagebox.askyesno("Подтверждение", f"Удалить '{value}'?"):
                    if data_manager.remove_from_dictionary(dict_name, value):
                        self.refresh_listbox(listbox, dict_name)
            else:
                messagebox.showwarning("Ошибка", "Выберите значение для удаления")

        ttk.Button(control_frame, text="Добавить", command=add_value).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить", command=remove_value).pack(side=tk.LEFT, padx=2)

        # Привязка Enter к добавлению
        entry.bind('<Return>', lambda e: add_value())

    def refresh_listbox(self, listbox, dict_name):
        """Обновление списка значений"""
        listbox.delete(0, tk.END)
        values = data_manager.load_dictionary(dict_name, [])
        for value in sorted(values):
            listbox.insert(tk.END, value)

    def get_combobox_values(self, dict_name):
        """Получение значений для Combobox"""
        return data_manager.load_dictionary(dict_name, [])