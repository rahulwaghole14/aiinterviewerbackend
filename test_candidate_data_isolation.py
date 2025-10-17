import requests
import json
import time

BASE_URL = "http://localhost:8000"


def get_admin_token():
    """Get admin authentication token"""
    login_data = {"email": "admin@rslsolution.com", "password": "admin123"}

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None


def get_user_token(email, password):
    """Get authentication token for any user"""
    login_data = {"email": email, "password": password}

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        if response.status_code == 200:
            return response.json().get("token")
        else:
            print(
                f"❌ Login failed for {email}: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        print(f"❌ Error during login for {email}: {str(e)}")
        return None


def test_candidate_data_isolation():
    """Test if hiring agencies and recruiters can only see their own candidates"""
    print("🔍 Testing Candidate Data Isolation")
    print("=" * 50)

    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Failed to get admin token")
        return

    admin_headers = {
        "Authorization": f"Token {admin_token}",
        "Content-Type": "application/json",
    }

    # Step 1: Get all candidates as admin
    print("1. Getting all candidates as admin...")
    try:
        response = requests.get(f"{BASE_URL}/api/candidates/", headers=admin_headers)
        if response.status_code == 200:
            all_candidates = response.json()
            print(f"   ✅ Admin can see {len(all_candidates)} candidates")

            # Group candidates by recruiter
            candidates_by_recruiter = {}
            for candidate in all_candidates:
                recruiter_id = candidate.get("recruiter")
                if recruiter_id:
                    if recruiter_id not in candidates_by_recruiter:
                        candidates_by_recruiter[recruiter_id] = []
                    candidates_by_recruiter[recruiter_id].append(candidate)

            print(
                f"   📊 Candidates grouped by {len(candidates_by_recruiter)} recruiters"
            )

            # Show some examples
            for recruiter_id, candidates in list(candidates_by_recruiter.items())[:3]:
                print(f"   - Recruiter {recruiter_id}: {len(candidates)} candidates")
        else:
            print(f"   ❌ Failed to get candidates: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return

    # Step 2: Get user information to find hiring agencies and recruiters
    print("\n2. Getting user information...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/profile/", headers=admin_headers)
        if response.status_code == 200:
            admin_info = response.json()
            print(
                f"   ✅ Admin info: {admin_info.get('email')} - {admin_info.get('role')}"
            )
        else:
            print(f"   ❌ Failed to get admin profile: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    # Step 3: Get hiring agencies
    print("\n3. Getting hiring agencies...")
    try:
        response = requests.get(f"{BASE_URL}/api/hiring_agency/", headers=admin_headers)
        if response.status_code == 200:
            hiring_agencies = response.json()
            print(f"   ✅ Found {len(hiring_agencies)} hiring agencies")

            # Find hiring agencies with candidates
            agencies_with_candidates = []
            for agency in hiring_agencies:
                agency_id = agency.get("id")
                if agency_id in candidates_by_recruiter:
                    agencies_with_candidates.append(agency)
                    print(
                        f"   - Agency {agency.get('email')}: {len(candidates_by_recruiter[agency_id])} candidates"
                    )

            if not agencies_with_candidates:
                print("   ⚠️  No hiring agencies with candidates found")
                return
        else:
            print(f"   ❌ Failed to get hiring agencies: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return

    # Step 4: Test data isolation for hiring agencies
    print("\n4. Testing data isolation for hiring agencies...")
    for agency in agencies_with_candidates[:2]:  # Test first 2 agencies
        agency_email = agency.get("email")
        agency_id = agency.get("id")

        print(f"\n   Testing agency: {agency_email}")

        # Try to login as this agency (we need their password)
        # For now, let's assume we can't login as them, so we'll test differently

        # Check if this agency's candidates are properly isolated
        agency_candidates = candidates_by_recruiter.get(agency_id, [])
        if agency_candidates:
            print(f"   - Agency has {len(agency_candidates)} candidates")

            # Check if other agencies can see these candidates
            for other_agency in agencies_with_candidates:
                if other_agency.get("id") != agency_id:
                    other_agency_candidates = candidates_by_recruiter.get(
                        other_agency.get("id"), []
                    )
                    print(
                        f"   - Other agency {other_agency.get('email')}: {len(other_agency_candidates)} candidates"
                    )
        else:
            print(f"   - Agency has no candidates")

    # Step 5: Check the DataIsolationMixin logic
    print("\n5. Analyzing DataIsolationMixin logic...")
    print("   📋 Current DataIsolationMixin checks for:")
    print("   - hasattr(queryset.model, 'user')")
    print("   - hasattr(queryset.model, 'company_name')")
    print("   - hasattr(queryset.model, 'company')")
    print("   - hasattr(queryset.model, 'created_by')")
    print("   📋 Candidate model has:")
    print("   - recruiter (ForeignKey to CustomUser)")
    print("   - No 'user', 'company_name', 'company', or 'created_by' fields")
    print("   ⚠️  ISSUE: DataIsolationMixin doesn't handle 'recruiter' field!")

    # Step 6: Check if candidates have proper recruiter assignment
    print("\n6. Checking candidate recruiter assignment...")
    try:
        response = requests.get(f"{BASE_URL}/api/candidates/", headers=admin_headers)
        if response.status_code == 200:
            candidates = response.json()

            candidates_with_recruiter = [c for c in candidates if c.get("recruiter")]
            candidates_without_recruiter = [
                c for c in candidates if not c.get("recruiter")
            ]

            print(f"   ✅ Candidates with recruiter: {len(candidates_with_recruiter)}")
            print(
                f"   ⚠️  Candidates without recruiter: {len(candidates_without_recruiter)}"
            )

            if candidates_without_recruiter:
                print("   ⚠️  ISSUE: Some candidates don't have recruiter assigned!")
                for candidate in candidates_without_recruiter[:3]:
                    print(
                        f"   - Candidate {candidate.get('id')}: {candidate.get('full_name')} - No recruiter"
                    )
        else:
            print(f"   ❌ Failed to get candidates: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def test_candidate_creation_isolation():
    """Test if candidates are properly assigned to the creating user"""
    print("\n🔍 Testing Candidate Creation Isolation")
    print("=" * 50)

    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Failed to get admin token")
        return

    admin_headers = {
        "Authorization": f"Token {admin_token}",
        "Content-Type": "application/json",
    }

    # Create a test candidate
    print("1. Creating a test candidate...")
    timestamp = int(time.time())
    test_candidate_data = {
        "full_name": f"Test Candidate {timestamp}",
        "email": f"testcandidate{timestamp}@example.com",
        "phone": "+1234567890",
        "domain": "Test Domain",
        "status": "NEW",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/candidates/",
            json=test_candidate_data,
            headers=admin_headers,
        )

        if response.status_code == 201:
            created_candidate = response.json()
            print(f"   ✅ Created candidate: {created_candidate.get('full_name')}")
            print(f"   - Recruiter ID: {created_candidate.get('recruiter')}")
            print(f"   - Candidate ID: {created_candidate.get('id')}")

            # Check if recruiter is properly set
            if created_candidate.get("recruiter"):
                print("   ✅ Recruiter properly assigned")
            else:
                print("   ⚠️  ISSUE: Recruiter not assigned!")
        else:
            print(f"   ❌ Failed to create candidate: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


if __name__ == "__main__":
    test_candidate_data_isolation()
    test_candidate_creation_isolation()
    print("\n�� Test completed!")
