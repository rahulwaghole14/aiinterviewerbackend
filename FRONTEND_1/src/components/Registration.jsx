// components/Register.jsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { baseURL } from '../data'; // Import baseURL
import { useNotification } from '../hooks/useNotification';
import './Registration.css'; // Import the new CSS file for Registration

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [role, setRole] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();
  const notify = useNotification();

  const handleRegister = async (e) => {
    e.preventDefault();

    // Basic validation
    if (!username || !email || !fullName || !companyName || !role || !password || !confirmPassword) {
      notify.error('Please fill in all fields.');
      return;
    }

    if (password !== confirmPassword) {
      notify.error('Passwords do not match.');
      return;
    }

    try {
      const response = await fetch(`${baseURL}/api/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          full_name: fullName,
          company_name: companyName,
          role,
          password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        notify.success('Registration successful! You can now log in.', 'Welcome to Talaro', 3000);
        setUsername('');
        setEmail('');
        setFullName('');
        setCompanyName('');
        setRole('');
        setPassword('');
        setConfirmPassword('');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        const errorData = await response.json();
        notify.error(errorData.detail || 'Registration failed. Please try again.');
      }
    } catch (err) {
      notify.error('An error occurred during registration. Please try again later.');
    }
  };

  return (
    <div className="registration-container">
      <div className="registration-card">
        <h2 className="registration-title">Register for Talaro</h2>
        <form onSubmit={handleRegister} className="registration-form">
          <div className="registration-form-grid"> {/* Container for two-column layout */}
            <div className="registration-form-group">
              <label htmlFor="reg-username">Username</label>
              <input
                type="text"
                id="reg-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
              />
            </div>
            <div className="registration-form-group">
              <label htmlFor="reg-email">Email</label>
              <input
                type="email"
                id="reg-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>
            <div className="registration-form-group">
              <label htmlFor="reg-full-name">Full Name</label>
              <input
                type="text"
                id="reg-full-name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
                required
              />
            </div>
            <div className="registration-form-group">
              <label htmlFor="reg-company-name">Company Name</label>
              <input
                type="text"
                id="reg-company-name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Enter your company name"
                required
              />
            </div>
            <div className="registration-form-group">
              <label htmlFor="reg-role">Role</label>
              <input
                type="text"
                id="reg-role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Enter your role (e.g., Admin, Recruiter)"
                required
              />
            </div>
            <div className="registration-form-group">
              <label htmlFor="reg-password">Password</label>
              <input
                type="password"
                id="reg-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a password"
                required
              />
            </div>
            <div className="registration-form-group">
              <label htmlFor="confirm-password">Confirm Password</label>
              <input
                type="password"
                id="confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                required
              />
            </div>
          </div>
          <button type="submit" className="registration-button">
            Register
          </button>
        </form>
        <p className="registration-link-text">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
