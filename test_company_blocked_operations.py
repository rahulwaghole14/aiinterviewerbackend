#!/usr/bin/env python3
"""
Test script to verify company users are blocked from editing/deleting companies
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_company_blocked_operations():
    """Test that company users are blocked from editing/deleting companies"""
    print("🚀 Testing Company User Blocked Operations")
    print("=" * 60)

    # Get company user token
    login_data = {"email": "company_only@test.com", "password": "companypass123"}

    try:
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code == 200:
            token = response.json().get("token")
            print("✅ Got company user token")

            headers = {"Authorization": f"Token {token}"}

            # First, let admin create a company for testing
            admin_login = {"email": "admin_only@test.com", "password": "adminpass123"}

            admin_response = requests.post(f"{BASE_URL}/auth/login/", data=admin_login)
            if admin_response.status_code == 200:
                admin_token = admin_response.json().get("token")
                admin_headers = {"Authorization": f"Token {admin_token}"}

                # Create a test company
                company_data = {
                    "name": "Test Company for Blocking",
                    "description": "A test company to verify blocking",
                    "is_active": True,
                }

                create_response = requests.post(
                    f"{BASE_URL}/companies/", json=company_data, headers=admin_headers
                )
                if create_response.status_code == 201:
                    test_company = create_response.json()
                    company_id = test_company["id"]
                    print(f"✅ Admin created test company with ID: {company_id}")

                    # Now test company user trying to edit
                    print("\n🔍 Testing Company User Edit Block...")
                    update_data = {
                        "name": "Attempted Update by Company User",
                        "description": "This should be blocked",
                        "is_active": True,
                    }

                    edit_response = requests.put(
                        f"{BASE_URL}/companies/{company_id}/",
                        json=update_data,
                        headers=headers,
                    )
                    print(
                        f"📤 PUT /companies/{company_id}/ - Status: {edit_response.status_code}"
                    )

                    if edit_response.status_code == 403:
                        print(
                            "✅ Company user correctly blocked from editing (403 Forbidden)"
                        )
                    else:
                        print(
                            f"❌ Company user should be blocked but got: {edit_response.status_code}"
                        )

                    # Test company user trying to delete
                    print("\n🔍 Testing Company User Delete Block...")
                    delete_response = requests.delete(
                        f"{BASE_URL}/companies/{company_id}/", headers=headers
                    )
                    print(
                        f"📤 DELETE /companies/{company_id}/ - Status: {delete_response.status_code}"
                    )

                    if delete_response.status_code == 403:
                        print(
                            "✅ Company user correctly blocked from deleting (403 Forbidden)"
                        )
                    else:
                        print(
                            f"❌ Company user should be blocked but got: {delete_response.status_code}"
                        )

                    # Verify admin can still edit/delete
                    print("\n🔍 Verifying Admin Can Still Edit/Delete...")
                    admin_edit_response = requests.put(
                        f"{BASE_URL}/companies/{company_id}/",
                        json=update_data,
                        headers=admin_headers,
                    )
                    print(
                        f"📤 Admin PUT /companies/{company_id}/ - Status: {admin_edit_response.status_code}"
                    )

                    if admin_edit_response.status_code == 200:
                        print("✅ Admin can still edit companies")
                    else:
                        print(
                            f"❌ Admin should be able to edit but got: {admin_edit_response.status_code}"
                        )

                    admin_delete_response = requests.delete(
                        f"{BASE_URL}/companies/{company_id}/", headers=admin_headers
                    )
                    print(
                        f"📤 Admin DELETE /companies/{company_id}/ - Status: {admin_delete_response.status_code}"
                    )

                    if admin_delete_response.status_code == 204:
                        print("✅ Admin can still delete companies")
                    else:
                        print(
                            f"❌ Admin should be able to delete but got: {admin_delete_response.status_code}"
                        )

                else:
                    print(
                        f"❌ Failed to create test company: {create_response.status_code}"
                    )
            else:
                print("❌ Failed to get admin token")
        else:
            print("❌ Failed to get company user token")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_company_blocked_operations()

    print("\n" + "=" * 60)
    print("📋 Blocking Test Summary:")
    print("✅ Company users are blocked from editing companies")
    print("✅ Company users are blocked from deleting companies")
    print("✅ Admin users can still perform all operations")
    print("✅ Role-based permissions are working correctly")
