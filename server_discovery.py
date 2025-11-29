import socket
import threading
import time
import json


class ServerDiscovery:
    def __init__(self, server_port=12345, discovery_port=12346):
        self.server_port = server_port
        self.discovery_port = discovery_port
        self.running = False
        self.udp_socket = None

    def start_server_discovery(self, server_name="ProductionServer"):
        """Запуск сервера для ответа на UDP запросы"""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind(('', self.discovery_port))
            self.running = True

            print(f"UDP discovery сервер запущен на порту {self.discovery_port}")

            discovery_thread = threading.Thread(target=self._discovery_listener)
            discovery_thread.daemon = True
            discovery_thread.start()

            return True

        except Exception as e:
            print(f"Ошибка запуска UDP discovery: {e}")
            return False

    def _discovery_listener(self):
        """Прослушивание UDP запросов"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode('utf-8').strip()

                if message == "DISCOVER_SERVER_REQUEST":
                    # Отправляем ответ с информацией о сервере
                    response = {
                        'server_name': 'ProductionServer',
                        'host': addr[0],  # IP клиента для обратного подключения
                        'port': self.server_port,
                        'timestamp': time.time()
                    }

                    response_str = json.dumps(response)
                    self.udp_socket.sendto(response_str.encode('utf-8'), addr)
                    print(f"Отправлен discovery ответ клиенту {addr[0]}:{addr[1]}")

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Ошибка в discovery listener: {e}")

    def stop_discovery(self):
        """Остановка discovery сервера"""
        self.running = False
        if self.udp_socket:
            self.udp_socket.close()


class ClientDiscovery:
    def __init__(self, discovery_port=12346, timeout=5):
        self.discovery_port = discovery_port
        self.timeout = timeout
        self.udp_socket = None

    def discover_server(self, broadcast_address='255.255.255.255'):
        """Поиск сервера в сети через UDP broadcast"""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp_socket.settimeout(self.timeout)

            # Отправляем broadcast запрос
            message = "DISCOVER_SERVER_REQUEST"
            self.udp_socket.sendto(message.encode('utf-8'), (broadcast_address, self.discovery_port))
            print(f"Отправлен discovery запрос на {broadcast_address}:{self.discovery_port}")

            # Ждем ответы
            start_time = time.time()
            servers = []

            while time.time() - start_time < self.timeout:
                try:
                    data, addr = self.udp_socket.recvfrom(1024)
                    response_str = data.decode('utf-8').strip()

                    try:
                        server_info = json.loads(response_str)
                        server_info['response_addr'] = addr[0]
                        servers.append(server_info)
                        print(f"Найден сервер: {server_info}")
                    except json.JSONDecodeError:
                        continue

                except socket.timeout:
                    continue

            self.udp_socket.close()
            return servers

        except Exception as e:
            print(f"Ошибка при поиске сервера: {e}")
            if self.udp_socket:
                self.udp_socket.close()
            return []

    def discover_first_server(self):
        """Поиск первого доступного сервера"""
        servers = self.discover_server()
        if servers:
            return servers[0]  # Возвращаем первый найденный сервер
        return None