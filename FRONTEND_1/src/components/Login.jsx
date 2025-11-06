// components/Login.jsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { setUser } from '../redux/slices/userSlice';
import { fetchJobs, fetchDomains } from '../redux/slices/jobsSlice';
import { fetchCandidates } from '../redux/slices/candidatesSlice';
import { baseURL } from '../config/constants';
import { useNotification } from '../hooks/useNotification';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import './Login.css';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const notify = useNotification();
  
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (!email || !password) {
      notify.error('Please enter both email and password.');
      setLoading(false);
      return;
    }

    try {
      // Step 1: Call the login API
      
      const loginResponse = await fetch(`${baseURL}/api/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        localStorage.setItem('authToken', loginData.token);
        localStorage.setItem('userData', JSON.stringify(loginData.user));


        dispatch(setUser(loginData.user));
        dispatch(fetchJobs());
        dispatch(fetchDomains());
        dispatch(fetchCandidates());

        if (onLogin) onLogin(loginData.user);
        notify.success('Successfully logged in! Welcome back.');
        // Don't navigate here - let App.jsx handle navigation
      } else {
        const errorData = await loginResponse.json();
        notify.error(errorData.detail || 'Invalid email or password. Please try again.');
      }
    } catch (err) {
      notify.error('An error occurred. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Login to Talaro</h2>
        <form onSubmit={handleLogin} className="login-form" role="form" aria-label="Login form">
          <div className="login-form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              disabled={loading}
              aria-label="Email address"
              aria-describedby="email-help"
            />
            <div id="email-help" className="sr-only">Enter your registered email address</div>
          </div>
          <div className="login-form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input-container">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={loading}
                className="password-input"
                aria-label="Password"
                aria-describedby="password-help"
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={togglePasswordVisibility}
                disabled={loading}
                tabIndex={-1}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
              >
                {showPassword ? <FiEyeOff size={20} aria-hidden="true" /> : <FiEye size={20} aria-hidden="true" />}
              </button>
            </div>
            <div id="password-help" className="sr-only">Enter your password</div>
          </div>
          <button 
            type="submit" 
            className="login-button" 
            disabled={loading}
            aria-label={loading ? "Logging in, please wait" : "Login to your account"}
          >
            {loading ? (
              <>
                Logging in
                <span className="loading-dots" aria-hidden="true">
                  <span>.</span><span>.</span><span>.</span>
                </span>
              </>
            ) : (
              'Login'
            )}
          </button>
        </form>
        <p className="login-link-text">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
