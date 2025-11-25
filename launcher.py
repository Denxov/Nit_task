import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

def start_manager():
    try:
        if os.path.exists('manager_gui.py'):
            subprocess.Popen([sys.executable, 'manager_gui.py'])
            messagebox.showinfo("Успех", "Менеджер запущен")
        else:
            messagebox.showerror("Ошибка", "_old.py не найден")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить: {e}")

def start_operator():
    try:
        if os.path.exists('operator_gui.py'):
            subprocess.Popen([sys.executable, 'operator_gui.py'])
            messagebox.showinfo("Успех", "Оператор запущен")
        else:
            messagebox.showerror("Ошибка", "operator_gui.py не найден")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить: {e}")

# Простой интерфейс
root = tk.Tk()
root.title("Запуск системы")
root.geometry("300x200")

tk.Label(root, text="Выберите приложение для запуска:",
         font=('Arial', 12)).pack(pady=20)

tk.Button(root, text="Менеджер", command=start_manager,
          width=20, height=2).pack(pady=10)

tk.Button(root, text="Оператор", command=start_operator,
          width=20, height=2).pack(pady=10)

root.mainloop()