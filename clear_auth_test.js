// Simple script to test authentication flow
// Run this in the browser console to clear auth data and test the flow

console.log('🔧 Authentication Test Script');
console.log('==============================');

// Check current authentication state
const currentToken = localStorage.getItem('authToken');
const currentUser = localStorage.getItem('userData');

console.log('Current auth state:');
console.log('- Token exists:', !!currentToken);
console.log('- User data exists:', !!currentUser);

if (currentToken) {
  console.log('- Token preview:', currentToken.substring(0, 20) + '...');
}

if (currentUser) {
  try {
    const user = JSON.parse(currentUser);
    console.log('- User email:', user.email);
    console.log('- User role:', user.role);
  } catch (e) {
    console.log('- User data: Invalid JSON');
  }
}

// Function to clear auth data
window.clearAuthForTesting = function() {
  console.log('\n🧹 Clearing authentication data...');
  localStorage.removeItem('authToken');
  localStorage.removeItem('userData');
  console.log('✅ Auth data cleared!');
  console.log('💡 Refresh the page to see login screen');
  
  // Optional: Reload the page automatically
  setTimeout(() => {
    console.log('🔄 Reloading page...');
    window.location.reload();
  }, 1000);
};

// Function to check auth state
window.checkAuthState = function() {
  const token = localStorage.getItem('authToken');
  const userData = localStorage.getItem('userData');
  
  console.log('\n📊 Current Authentication State:');
  console.log('- Token:', token ? '✅ Present' : '❌ Missing');
  console.log('- User Data:', userData ? '✅ Present' : '❌ Missing');
  
  if (token && userData) {
    console.log('🟢 User should see: Dashboard');
  } else {
    console.log('🔴 User should see: Login Screen');
  }
};

console.log('\n🎯 Available test functions:');
console.log('- clearAuthForTesting() - Clear auth data and reload');
console.log('- checkAuthState() - Check current auth state');

console.log('\n📋 Test Steps:');
console.log('1. Run clearAuthForTesting() to clear auth data');
console.log('2. Page should reload and show login screen');
console.log('3. Login with: admin@example.com / admin123');
console.log('4. Should redirect to dashboard without 401 errors');

// Auto-run auth state check
checkAuthState();
