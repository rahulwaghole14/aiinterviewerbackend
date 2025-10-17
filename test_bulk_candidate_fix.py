import requests
import json


# Test the fixed bulk candidate creation endpoint
def test_bulk_candidate_creation():
    base_url = "http://localhost:8000"

    # First, login to get token
    login_data = {"email": "company_test@example.com", "password": "password123"}

    login_response = requests.post(f"{base_url}/api/auth/login/", json=login_data)
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return

    token = login_response.json().get("token")
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    # Test bulk candidate creation with step=submit
    test_data = {
        "domain": "Data Science",
        "role": "Data Scientist",
        "candidates": [
            {
                "filename": "resume1.pdf",
                "edited_data": {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "work_experience": 5,
                },
            }
        ],
    }

    print("Testing bulk candidate creation with fixed field names...")
    response = requests.post(
        f"{base_url}/api/candidates/bulk-create/?step=submit",
        json=test_data,
        headers=headers,
    )

    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 200:
        print("\n✅ SUCCESS: Bulk candidate creation is now working!")
    else:
        print("\n❌ FAILED: Still having issues with bulk candidate creation")


if __name__ == "__main__":
    test_bulk_candidate_creation()
