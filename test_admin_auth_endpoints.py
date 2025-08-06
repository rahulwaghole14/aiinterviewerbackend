import requests

BASE_URL = "http://localhost:8000/api"
ADMIN_TOKEN = "ec5a5347c551cdc8bfcbfd1a03cd84721f9b5e1c"
headers = {"Authorization": f"Token {ADMIN_TOKEN}"}

# 1. Test /api/companies/
companies_resp = requests.get(f"{BASE_URL}/companies/", headers=headers)
print("\nGET /api/companies/:")
print(companies_resp.status_code, companies_resp.text)

# 2. Test /api/hiring_agency/
hiring_agency_resp = requests.get(f"{BASE_URL}/hiring_agency/", headers=headers)
print("\nGET /api/hiring_agency/:")
print(hiring_agency_resp.status_code, hiring_agency_resp.text)

# 3. Test /api/companies/recruiters/
recruiters_resp = requests.get(f"{BASE_URL}/companies/recruiters/", headers=headers)
print("\nGET /api/companies/recruiters/:")
print(recruiters_resp.status_code, recruiters_resp.text)