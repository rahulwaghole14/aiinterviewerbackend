// Detailed auth test to see exact error
console.log('🧪 Detailed Auth Test...');

// Test 1: Check what the actual error is
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
  console.log('Response status:', response.status);
  console.log('Response headers:', response.headers);
  return response.json();
})
.then(data => {
  console.log('Response data:', data);
  if (data.error) {
    console.log('❌ Error:', data.error);
  } else if (data.token) {
    console.log('✅ Success! Token:', data.token);
  }
})
.catch(error => {
  console.log('❌ Network error:', error.message);
});

// Test 2: Check if admin user exists
fetch('http://localhost:8000/api/auth/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'admin@rslsolution.com',
    password: 'admin123',
    full_name: 'Admin User',
    role: 'ADMIN',
    company_name: 'RSL Solutions'
  })
})
.then(response => {
  console.log('Register response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('Register response:', data);
  if (data.error) {
    console.log('User might already exist');
  }
})
.catch(error => {
  console.log('Register error:', error.message);
});

console.log('💡 Check the console for detailed error information'); 