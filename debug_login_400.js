// Debug script to identify 400 error cause
console.log('🔍 Debugging 400 Bad Request Error...');

// Test 1: Check if the endpoint exists and what it expects
fetch('http://localhost:8000/api/auth/login/', {
  method: 'OPTIONS',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(response => {
  console.log('OPTIONS response status:', response.status);
  console.log('OPTIONS response headers:', response.headers);
})
.catch(error => {
  console.log('OPTIONS request failed:', error.message);
});

// Test 2: Try with different content types
fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: 'email=admin@rslsolution.com&password=admin123'
})
.then(response => {
  console.log('Form data response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('Form data response:', data);
})
.catch(error => {
  console.log('Form data request failed:', error.message);
});

// Test 3: Try with minimal JSON
fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'admin@rslsolution.com',
    password: 'admin123'
  })
})
.then(response => {
  console.log('JSON response status:', response.status);
  console.log('JSON response headers:', response.headers);
  return response.json();
})
.then(data => {
  console.log('JSON response data:', data);
  if (data.email) {
    console.log('❌ Email field error:', data.email);
  }
  if (data.password) {
    console.log('❌ Password field error:', data.password);
  }
  if (data.non_field_errors) {
    console.log('❌ General error:', data.non_field_errors);
  }
})
.catch(error => {
  console.log('JSON request failed:', error.message);
});

// Test 4: Check if the user exists and is active
console.log('💡 Checking if user exists...');
fetch('http://localhost:8000/api/auth/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'testuser@example.com',
    password: 'test123',
    full_name: 'Test User',
    role: 'ADMIN',
    company_name: 'Test Company'
  })
})
.then(response => {
  console.log('Register test status:', response.status);
  return response.json();
})
.then(data => {
  console.log('Register test response:', data);
})
.catch(error => {
  console.log('Register test failed:', error.message);
});

console.log('🔍 Check the console output above for detailed error information'); 