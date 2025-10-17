// Final login test with updated admin user
console.log('🧪 Final Login Test...');

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
  return response.json();
})
.then(data => {
  console.log('Response data:', data);
  if (data.token) {
    console.log('🎉 SUCCESS! Login worked!');
    console.log('Token:', data.token.substring(0, 20) + '...');
    console.log('User:', data.user);
    
    // Test using the token for an authenticated request
    return fetch('http://localhost:8000/api/jobs/', {
      headers: {
        'Authorization': `Token ${data.token}`,
        'Content-Type': 'application/json',
      }
    });
  } else {
    console.log('❌ Login failed:', data);
  }
})
.then(response => {
  if (response) {
    console.log('✅ Authenticated request status:', response.status);
    return response.json();
  }
})
.then(data => {
  if (data) {
    console.log('✅ Jobs data:', data);
  }
})
.catch(error => {
  console.log('❌ Error:', error.message);
});

console.log('💡 If you see "SUCCESS! Login worked!", everything is working!'); 