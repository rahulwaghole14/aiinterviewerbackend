import requests
import json

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@rslsolution.com"
ADMIN_PASSWORD = "admin123"


# Helper to get token
def get_token(email, password):
    resp = requests.post(
        f"{BASE_URL}/auth/login/", json={"email": email, "password": password}
    )
    if resp.status_code == 200:
        return resp.json()["token"]
    print("Login failed:", resp.text)
    return None


def test_bulk_candidate_submit(token):
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    # Use a unique_resume_filename from a previous extract step or mock it
    test_data = {
        "domain": "Data Science",
        "role": "Data Scientist",
        "candidates": [
            {
                "filename": "Anas Khan_Data Scientist_UnionSys.pdf",
                "edited_data": {
                    "name": "Anas Khan",
                    "email": "k.anas4982@outlook.com",
                    "phone": "8329796747",
                    "work_experience": 3,
                    "unique_resume_filename": "Anas_Khan_Data_Scientist_UnionSys_krO3awu.pdf",
                },
            }
        ],
    }
    resp = requests.post(
        f"{BASE_URL}/candidates/bulk-create/?step=submit",
        json=test_data,
        headers=headers,
    )
    print("\nPOST /api/candidates/bulk-create/?step=submit:")
    print(resp.status_code, resp.json())
    return resp


def test_candidates_list(token):
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(f"{BASE_URL}/candidates/", headers=headers)
    print("\nGET /api/candidates/:")
    print(resp.status_code, json.dumps(resp.json(), indent=2))
    return resp


def test_companies():
    resp = requests.get(f"{BASE_URL}/companies/")
    print("\nGET /api/companies/:")
    print(resp.status_code, resp.text)
    return resp


def test_hiring_agency():
    resp = requests.get(f"{BASE_URL}/hiring_agency/")
    print("\nGET /api/hiring_agency/:")
    print(resp.status_code, resp.text)
    return resp


def test_recruiters():
    resp = requests.get(f"{BASE_URL}/companies/recruiters/")
    print("\nGET /api/companies/recruiters/:")
    print(resp.status_code, resp.text)
    return resp


def test_admin_list(token):
    headers = {"Authorization": f"Token {token}"}
    resp = requests.get(f"{BASE_URL}/auth/admins/", headers=headers)
    print("\nGET /api/auth/admins/:")
    print(resp.status_code, json.dumps(resp.json(), indent=2))
    return resp


if __name__ == "__main__":
    token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        exit(1)
    test_bulk_candidate_submit(token)
    test_candidates_list(token)
    test_companies()
    test_hiring_agency()
    test_recruiters()
    test_admin_list(token)
