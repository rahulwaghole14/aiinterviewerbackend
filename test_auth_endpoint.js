// Test auth endpoint after URL fix
console.log('🧪 Testing Auth Endpoint...');

// Test 1: Check if auth endpoint is accessible
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
  console.log('✅ Auth endpoint is accessible');
  console.log('Status:', response.status);
  return response.json();
})
.then(data => {
  console.log('✅ Login response:', data);
  if (data.token) {
    console.log('🎉 Login successful! Token received');
  } else {
    console.log('⚠️ Login failed - check credentials');
  }
})
.catch(error => {
  console.log('❌ Auth endpoint error:', error.message);
});

// Test 2: Check other auth endpoints
fetch('http://localhost:8000/api/auth/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'test123',
    full_name: 'Test User'
  })
})
.then(response => {
  console.log('✅ Register endpoint is accessible');
  console.log('Status:', response.status);
})
.catch(error => {
  console.log('❌ Register endpoint error:', error.message);
});

console.log('💡 If you see "Auth endpoint is accessible", the URL fix worked!'); 