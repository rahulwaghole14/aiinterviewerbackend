// Test script to check user data
console.log('=== Testing User Data ===');

// Check localStorage
const authToken = localStorage.getItem('authToken');
const userData = localStorage.getItem('userData');

console.log('Auth Token exists:', !!authToken);
console.log('User Data exists:', !!userData);

if (userData) {
  try {
    const user = JSON.parse(userData);
    console.log('User data from localStorage:', user);
    console.log('User role:', user.role);
    console.log('User email:', user.email);
    console.log('User company:', user.company_name);
  } catch (error) {
    console.error('Error parsing user data:', error);
  }
}

// Check if Redux store is available
if (window.__REDUX_DEVTOOLS_EXTENSION__) {
  console.log('Redux DevTools available');
} else {
  console.log('Redux DevTools not available');
}

console.log('=== End Test ===');

