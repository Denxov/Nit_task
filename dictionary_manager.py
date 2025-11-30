import tkinter as tk
from tkinter import ttk, messagebox
from data_manager import data_manager


class DictionaryManager:
    def __init__(self, parent):
        self.parent = parent
        self.setup_dictionaries()

    # В data_manager.py добавим в метод setup_dictionaries класса DictionaryManager
    def setup_dictionaries(self):
        """Инициализация справочников с значениями по умолчанию"""
        # Справочник сырья
        data_manager.load_dictionary("materials", [
            "Пластик ABS", "Поликарбонат", "Нейлон", "PLA", "PETG",
            "АБС-пластик", "Полипропилен", "Полистирол"
        ])

        # Справочник цветов
        data_manager.load_dictionary("colors", [
            "Красный", "Синий", "Зеленый", "Желтый", "Черный", "Белый",
            "Прозрачный", "Оранжевый", "Фиолетовый", "Серый"
        ])

        # Справочник скоростей
        data_manager.load_dictionary("speeds", [
            "50 мм/с", "60 мм/с", "70 мм/с", "80 мм/с", "90 мм/с",
            "100 мм/с", "110 мм/с", "120 мм/с", "130 мм/с", "140 мм/с"
        ])

        # Справочник температур
        data_manager.load_dictionary("temperatures", [
            "180°C", "190°C", "200°C", "210°C", "220°C", "230°C",
            "240°C", "250°C", "260°C", "270°C", "280°C", "290°C"
        ])

        # Справочник приоритетов
        data_manager.load_dictionary("priorities", [
            "Высокий", "Средний", "Низкий"
        ])

    # В методе show_dictionary_editor класса DictionaryManager
    def show_dictionary_editor(self):
        """Показ редактора справочников с приоритетами"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Управление справочниками")
        dialog.geometry("600x500")
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
        self.create_dictionary_tab(notebook, "priorities", "Приоритеты")  # Новая вкладка

        # Кнопка закрытия
        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

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