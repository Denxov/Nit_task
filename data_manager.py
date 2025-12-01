import json
import os
from datetime import datetime


# В data_manager.py добавим методы для работы с операторами как со справочником

class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """Создает директорию для данных если ее нет"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    # === ОПЕРАТОРЫ (теперь как справочник) ===
    def load_operators(self):
        """Загрузка списка операторов из файла"""
        try:
            filepath = os.path.join(self.data_dir, "operators.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    operators_data = json.load(f)

                # Конвертируем старый формат в новый если нужно
                if isinstance(operators_data, dict):
                    # Старый формат: {'operator1': {'password': 'pass1', ...}}
                    operators_list = []
                    for username, data in operators_data.items():
                        operators_list.append({
                            'username': username,
                            'password': data.get('password', ''),
                            'active': data.get('active', False),
                            'tasks': data.get('tasks', [[], []])
                        })
                    # Сохраняем в новом формате
                    self.save_operators(operators_list)
                    return operators_list
                else:
                    # Новый формат: список словарей
                    return operators_data
            else:
                # Создаем стандартных операторов при первом запуске
                default_operators = [
                    {
                        'username': 'operator1',
                        'password': 'pass1',
                        'active': False,
                        'tasks': [[], []]
                    },
                    {
                        'username': 'operator2',
                        'password': 'pass2',
                        'active': False,
                        'tasks': [[], []]
                    },
                    {
                        'username': 'operator3',
                        'password': 'pass3',
                        'active': False,
                        'tasks': [[], []]
                    }
                ]
                self.save_operators(default_operators)
                return default_operators
        except Exception as e:
            print(f"Ошибка загрузки операторов: {e}")
            return []

    def save_operators(self, operators):
        """Сохранение списка операторов в файл"""
        try:
            filepath = os.path.join(self.data_dir, "operators.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(operators, f, ensure_ascii=False, indent=2)
            print("Операторы сохранены")
        except Exception as e:
            print(f"Ошибка сохранения операторов: {e}")

    def add_operator(self, username, password):
        """Добавление нового оператора"""
        try:
            operators = self.load_operators()

            # Проверяем, нет ли уже оператора с таким именем
            if any(op['username'] == username for op in operators):
                return False, "Оператор с таким именем уже существует"

            new_operator = {
                'username': username,
                'password': password,
                'active': False,
                'tasks': [[], []]
            }

            operators.append(new_operator)
            self.save_operators(operators)
            return True, "Оператор успешно добавлен"

        except Exception as e:
            return False, f"Ошибка добавления оператора: {e}"

    def remove_operator(self, username):
        """Удаление оператора"""
        try:
            operators = self.load_operators()
            operators = [op for op in operators if op['username'] != username]
            self.save_operators(operators)
            return True, "Оператор успешно удален"
        except Exception as e:
            return False, f"Ошибка удаления оператора: {e}"

    def update_operator_password(self, username, new_password):
        """Обновление пароля оператора"""
        try:
            operators = self.load_operators()
            for operator in operators:
                if operator['username'] == username:
                    operator['password'] = new_password
                    self.save_operators(operators)
                    return True, "Пароль успешно обновлен"
            return False, "Оператор не найден"
        except Exception as e:
            return False, f"Ошибка обновления пароля: {e}"

    def get_operator_by_username(self, username):
        """Получение оператора по имени пользователя"""
        operators = self.load_operators()
        for operator in operators:
            if operator['username'] == username:
                return operator
        return None

    def update_operator_status(self, username, active):
        """Обновление статуса активности оператора"""
        try:
            operators = self.load_operators()
            for operator in operators:
                if operator['username'] == username:
                    operator['active'] = active
                    self.save_operators(operators)
                    return True
            return False
        except Exception as e:
            print(f"Ошибка обновления статуса оператора: {e}")
            return False

    def update_operator_tasks(self, username, tasks):
        """Обновление задач оператора"""
        try:
            operators = self.load_operators()
            for operator in operators:
                if operator['username'] == username:
                    operator['tasks'] = tasks
                    self.save_operators(operators)
                    return True
            return False
        except Exception as e:
            print(f"Ошибка обновления задач оператора: {e}")
            return False

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

    # ... остальные методы для справочников без изменений ...


# Глобальный экземпляр менеджера данных
data_manager = DataManager()