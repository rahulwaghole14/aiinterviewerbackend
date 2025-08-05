// Quick CORS test
console.log('🧪 Testing CORS Configuration...');

// Test 1: Check if backend is accessible
fetch('http://localhost:8000/api/')
  .then(response => {
    console.log('✅ Backend is accessible');
    console.log('Status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('✅ CORS is working - received data:', data);
  })
  .catch(error => {
    console.log('❌ CORS still not working:', error.message);
  });

// Test 2: Test login endpoint specifically
fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'test123'
  })
})
.then(response => {
  console.log('✅ Login endpoint CORS is working');
  console.log('Status:', response.status);
  return response.json();
})
.catch(error => {
  console.log('❌ Login endpoint CORS error:', error.message);
});

console.log('💡 If you see "CORS is working" messages, the fix was successful!'); 