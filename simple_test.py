import requests

BASE_URL = "http://localhost:8000"


def test_server():
    try:
        response = requests.get(f"{BASE_URL}/api/")
        print(f"Server response: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    test_server()
