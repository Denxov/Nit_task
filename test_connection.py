import socket
import sys



def test_server(host=host_addr, port=1234):
    print(f"Тестирование подключения к {host}:{port}")

    try:
        # Тест порта
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print("✓ УСПЕХ: Порт открыт и доступен")
            return True
        else:
            print(f"✗ ОШИБКА: Порт недоступен (код {result})")
            return False

    except Exception as e:
        print(f"✗ ОШИБКА: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = '192.168.0.128'

    test_server(host)