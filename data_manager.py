import json
import os
from datetime import datetime


class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """Создает директорию для данных если ее нет"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    # === ОПЕРАТОРЫ ===
    def load_operators(self):
        """Загрузка списка операторов из файла"""
        try:
            filepath = os.path.join(self.data_dir, "operators.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Возвращаем стандартных операторов при первом запуске
                default_operators = {
                    'operator1': {'password': 'pass1', 'active': False, 'tasks': [[], []]},
                    'operator2': {'password': 'pass2', 'active': False, 'tasks': [[], []]},
                    'operator3': {'password': 'pass3', 'active': False, 'tasks': [[], []]}
                }
                self.save_operators(default_operators)
                return default_operators
        except Exception as e:
            print(f"Ошибка загрузки операторов: {e}")
            return {}

    def save_operators(self, operators):
        """Сохранение списка операторов в файл"""
        try:
            filepath = os.path.join(self.data_dir, "operators.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(operators, f, ensure_ascii=False, indent=2)
            print("Операторы сохранены")
        except Exception as e:
            print(f"Ошибка сохранения операторов: {e}")

    # === СПРАВОЧНИКИ ===
    def load_dictionary(self, dict_name, default_values=None):
        """Загрузка справочника"""
        try:
            if default_values is None:
                default_values = []

            filepath = os.path.join(self.data_dir, f"{dict_name}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Создаем файл с значениями по умолчанию
                self.save_dictionary(dict_name, default_values)
                return default_values
        except Exception as e:
            print(f"Ошибка загрузки справочника {dict_name}: {e}")
            return default_values

    def save_dictionary(self, dict_name, data):
        """Сохранение справочника"""
        try:
            filepath = os.path.join(self.data_dir, f"{dict_name}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Справочник {dict_name} сохранен")
        except Exception as e:
            print(f"Ошибка сохранения справочника {dict_name}: {e}")

    def add_to_dictionary(self, dict_name, value):
        """Добавление значения в справочник"""
        try:
            current_data = self.load_dictionary(dict_name, [])
            if value not in current_data:
                current_data.append(value)
                self.save_dictionary(dict_name, current_data)
                return True
            return False
        except Exception as e:
            print(f"Ошибка добавления в справочник {dict_name}: {e}")
            return False

    def remove_from_dictionary(self, dict_name, value):
        """Удаление значения из справочника"""
        try:
            current_data = self.load_dictionary(dict_name, [])
            if value in current_data:
                current_data.remove(value)
                self.save_dictionary(dict_name, current_data)
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления из справочника {dict_name}: {e}")
            return False


# Глобальный экземпляр менеджера данных
data_manager = DataManager()