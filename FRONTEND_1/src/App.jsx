// App.jsx
import { useState, useEffect, useRef, Suspense, lazy } from 'react';
import { useLocation, Route, Routes, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { setSearchTerm } from './redux/actions/searchActions';
import { setUser, clearUser } from './redux/slices/userSlice'; // Import setUser and clearUser

// Lazy load components for better performance
const SideBar = lazy(() => import('./components/SideBar'));
const Header = lazy(() => import('./components/Header'));
const Dashboard = lazy(() => import('./components/Dashboard'));
const AddCandidates = lazy(() => import('./components/AddCandidates'));
const Candidates = lazy(() => import('./components/Candidates'));
// Import CandidateDetails directly to avoid Vite HMR issues with recharts
import CandidateDetails from './components/CandidateDetails';
const Jobs = lazy(() => import('./components/Jobs'));
const Settings = lazy(() => import('./components/Settings'));
const Login = lazy(() => import('./components/Login'));
const Register = lazy(() => import('./components/Registration'));
const Profile = lazy(() => import('./components/Profile'));
const HiringAgencies = lazy(() => import('./components/HiringAgency'));
const AiInterviewScheduler = lazy(() => import('./components/AiInterviewScheduler'));
const InterviewPortal = lazy(() => import('./components/InterviewPortal'));
const InterviewResults = lazy(() => import('./components/InterviewResults'));
const InterviewResultsList = lazy(() => import('./components/InterviewResultsList'));

// Keep these as regular imports since they're used frequently
import NotificationToast from './components/common/NotificationToast';
import ErrorBoundary from './components/common/ErrorBoundary';
import SectionErrorBoundary from './components/common/SectionErrorBoundary';
import LoadingSpinner from './components/common/LoadingSpinner';
import { ThemeProvider } from './contexts/ThemeContext';
import "./App.css";

const getInitialHeaderTitle = () => {
  const path = window.location.pathname.split('/')[1];
  const subPath = window.location.pathname.split('/')[2];
  let title = 'Dashboard';

  switch (path) {
    case 'dashboard':
      title = 'Dashboard';
      break;
    case 'add-candidates':
      title = 'Add Candidates';
      break;
    case 'candidates':
      title = subPath ? 'Candidate Details' : 'Candidates';
      break;
    case 'jobs':
      title = 'Jobs';
      break;
    case 'settings':
      title = 'Settings';
      break;
    case 'profile':
      title = 'User Profile';
      break;
    case 'hiring-agencies':
      title = 'Hiring Agencies';
      break;
          case 'ai-interview-scheduler':
        title = 'Talaro Interview Manager';
        break;
      case 'interview-results':
        title = 'Interview Results';
        break;
    case 'login':
      title = 'Login';
      break;
    case 'register':
      title = 'Register';
      break;
    default:
      title = localStorage.getItem('authToken') ? 'Dashboard' : 'Login';
      break;
  }
  return title;
};


function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  // Add the user selector
  const user = useSelector((state) => state.user.user);
  const searchTerm = useSelector((state) => state.search.searchTerm);

  const [isLoggedIn, setIsLoggedIn] = useState(null); // Start with null to show loading state
  const [isInitialized, setIsInitialized] = useState(false);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);
  const [sidebarMobileOpen, setSidebarMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [headerTitle, setHeaderTitle] = useState(getInitialHeaderTitle());

  // Effect to initialize authentication state on app load
  useEffect(() => {
    const initializeAuth = () => {
      const authToken = localStorage.getItem('authToken');
      const storedUserData = localStorage.getItem('userData');
      
      if (authToken && storedUserData) {
        try {
          const user = JSON.parse(storedUserData);
          dispatch(setUser(user));
          setIsLoggedIn(true);
        } catch (error) {
          console.error("Failed to parse user data from localStorage:", error);
          // Clear invalid data and log out if parsing fails
          localStorage.removeItem('userData');
          localStorage.removeItem('authToken');
          dispatch(clearUser());
          setIsLoggedIn(false);
        }
      } else {
        // No valid authentication data
        dispatch(clearUser());
        setIsLoggedIn(false);
      }
      
      setIsInitialized(true);
    };
    
    // Listen for authentication errors from API calls
    const handleAuthError = () => {
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      dispatch(clearUser());
      setIsLoggedIn(false);
      navigate('/login', { replace: true });
    };
    
    window.addEventListener('authError', handleAuthError);
    initializeAuth();
    
    return () => {
      window.removeEventListener('authError', handleAuthError);
    };
  }, [dispatch, navigate]); // Add navigate to dependencies

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (document.body.getAttribute('data-theme') !== savedTheme) {
      document.body.setAttribute('data-theme', savedTheme);
    }
  }, []);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Handle routing after authentication is initialized
  useEffect(() => {
    if (!isInitialized || isLoggedIn === null) {
      return; // Don't handle routing until auth is initialized
    }

    const currentPath = location.pathname;

    if (isLoggedIn) {
      // Only redirect to dashboard if user is on login/register pages or root
      if (currentPath === '/' || currentPath === '/login' || currentPath === '/register') {
        navigate('/dashboard', { replace: true });
      }
      // For all other authenticated routes, stay on current page
    } else {
      // If not logged in, redirect to login unless already on login/register or public candidate pages
      if (currentPath !== '/login' && currentPath !== '/register' && !currentPath.startsWith('/candidates/')) {
        navigate('/login', { replace: true });
      }
    }
  }, [location.pathname, navigate, isLoggedIn, isInitialized]);

  useEffect(() => {
    const pathParts = location.pathname.split('/');
    const path = pathParts[1];
    const subPath = pathParts[2];
    let title = 'Dashboard';

    switch (path) {
      case 'dashboard':
        title = 'Dashboard';
        break;
      case 'add-candidates':
        title = 'Add Candidates';
        break;
      case 'candidates':
        title = subPath ? 'Candidate Details' : 'Candidates';
        break;
      case 'jobs':
        title = 'Jobs';
        break;
      case 'settings':
        title = 'Settings';
        break;
      case 'profile':
        title = 'User Profile';
        break;
      case 'hiring-agencies':
        title = 'All Users';
        break;
      case 'login':
        title = 'Login';
        break;
      case 'register':
        title = 'Register';
        break;
      default:
        title = isLoggedIn ? 'Dashboard' : 'Login';
        break;
    }
    setHeaderTitle(title);
  }, [location.pathname, isLoggedIn]);

  const updateHeaderTitle = (newTitle) => {
    setHeaderTitle(newTitle);
  };

  const handleToggleSidebar = () => {
    setIsSidebarExpanded((prev) => !prev);
  };

  const handleMobileSidebarToggle = () => {
    setSidebarMobileOpen((prev) => !prev);
  };

  const handleSidebarMenuItemClick = () => {
    if (isMobile) {
      setSidebarMobileOpen(false);
    }
  };

  const handleLoginSuccess = (userData) => {
    
    // Update Redux state with user data
    if (userData) {
      dispatch(setUser(userData));
    }
    
    // Update local state
    setIsLoggedIn(true);
    
    // Navigate to dashboard (the routing effect will handle this)
    navigate('/dashboard', { replace: true });
  };

  const handleLogout = () => {
    
    // Clear local storage
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    
    // Clear Redux state
    dispatch(clearUser());
    
    // Update local state
    setIsLoggedIn(false);
    
    // Navigate to login
    navigate('/login', { replace: true });
  };

  const handleProfileMenuItemClick = (item) => {
    if (item === 'logout') {
      handleLogout();
    } else {
      navigate(`/${item}`);
    }
  };

  // Show loading state while initializing authentication
  if (!isInitialized) {
    return (
      <div className="loading-container" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <ThemeProvider>
      {isLoggedIn ? (
      <div className={`app-container ${isSidebarExpanded ? 'expanded' : ''} ${sidebarMobileOpen ? 'sidebar-mobile-open' : ''}`}>
        {isMobile && sidebarMobileOpen && <div className="sidebar-mobile-overlay" onClick={handleMobileSidebarToggle}></div>}
        <SideBar
          isExpanded={isSidebarExpanded}
          onToggleSidebar={handleToggleSidebar}
          isMobile={isMobile}
          onMenuItemClick={handleSidebarMenuItemClick}
        />
        <div className="main-content">
          <Header
            headerTitle={headerTitle}
            searchTerm={searchTerm}
            onSearchChange={(term) => dispatch(setSearchTerm(term))}
            onToggleSidebar={handleToggleSidebar}
            isMobile={isMobile}
            onMobileSidebarToggle={handleMobileSidebarToggle}
            onLogout={handleLogout}
            onProfileMenuItemClick={handleProfileMenuItemClick}
          />
          <div className="content-area">
            <ErrorBoundary
              title="Application Error"
              message="Something went wrong while loading the application. Please try refreshing the page."
              showDetails={process.env.NODE_ENV === 'development'}
            >
              <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
                <Routes key={isLoggedIn ? "logged-in" : "logged-out"}>
                <Route path="/" element={
                  <SectionErrorBoundary sectionName="Dashboard">
                    <Dashboard />
                  </SectionErrorBoundary>
                } />
                <Route path="/dashboard" element={
                  <SectionErrorBoundary sectionName="Dashboard">
                    <Dashboard />
                  </SectionErrorBoundary>
                } />
                <Route path="/add-candidates" element={
                  <SectionErrorBoundary sectionName="Add Candidates">
                    <AddCandidates />
                  </SectionErrorBoundary>
                } />
                <Route path="/candidates" element={
                  <SectionErrorBoundary sectionName="Candidates">
                    <Candidates />
                  </SectionErrorBoundary>
                } />
                <Route path="/candidates/:id" element={
                  <SectionErrorBoundary sectionName="Candidate Details">
                    <CandidateDetails onTitleChange={updateHeaderTitle} />
                  </SectionErrorBoundary>
                } />
                <Route path="/jobs" element={
                  <SectionErrorBoundary sectionName="Jobs">
                    <Jobs />
                  </SectionErrorBoundary>
                } />
                <Route path="/settings" element={
                  <SectionErrorBoundary sectionName="Settings">
                    <Settings onTitleChange={updateHeaderTitle} />
                  </SectionErrorBoundary>
                } />
                <Route path="/profile" element={
                  <SectionErrorBoundary sectionName="Profile">
                    <Profile onTitleChange={updateHeaderTitle} />
                  </SectionErrorBoundary>
                } />
                <Route path="/hiring-agencies" element={
                  <SectionErrorBoundary sectionName="Hiring Agencies">
                    <HiringAgencies />
                  </SectionErrorBoundary>
                } />
                <Route 
                  path="/ai-interview-scheduler" 
                  element={
                    <SectionErrorBoundary sectionName="AI Interview Scheduler">
                      <AiInterviewScheduler onTitleChange={updateHeaderTitle} />
                    </SectionErrorBoundary>
                  } 
                />
                <Route 
                  path="/interview/:sessionKey" 
                  element={
                    <SectionErrorBoundary sectionName="Interview Portal">
                      <InterviewPortal />
                    </SectionErrorBoundary>
                  } 
                />
                <Route 
                  path="/interview-results" 
                  element={
                    <SectionErrorBoundary sectionName="Interview Results">
                      <InterviewResultsList />
                    </SectionErrorBoundary>
                  } 
                />
                <Route 
                  path="/interview-results/:sessionId" 
                  element={
                    <SectionErrorBoundary sectionName="Interview Results">
                      <InterviewResults />
                    </SectionErrorBoundary>
                  } 
                />
              </Routes>
              </Suspense>
            </ErrorBoundary>
          </div>
        </div>
        {/* Global Notification Toast */}
        <NotificationToast />
      </div>
    ) : (
      <div>
        <ErrorBoundary
          title="Authentication Error"
          message="Something went wrong while loading the authentication page. Please try refreshing the page."
          showDetails={process.env.NODE_ENV === 'development'}
        >
          <Suspense fallback={<LoadingSpinner message="Loading page..." />}>
            <Routes key={isLoggedIn ? "logged-in" : "logged-out"}>
            <Route path="/" element={
              <SectionErrorBoundary sectionName="Login">
                <Login onLogin={handleLoginSuccess} autoFocusEmail={true} />
              </SectionErrorBoundary>
            } />
            <Route path="/login" element={
              <SectionErrorBoundary sectionName="Login">
                <Login onLogin={handleLoginSuccess} autoFocusEmail={true} />
              </SectionErrorBoundary>
            } />
            <Route path="/register" element={
              <SectionErrorBoundary sectionName="Registration">
                <Register autoFocusUsername={true} />
              </SectionErrorBoundary>
            } />
            <Route path="*" element={
              <SectionErrorBoundary sectionName="Login">
                <Login onLogin={handleLoginSuccess} autoFocusEmail={true} />
              </SectionErrorBoundary>
            } />
          </Routes>
          </Suspense>
        </ErrorBoundary>
        {/* Global Notification Toast for unauthenticated users */}
        <NotificationToast />
      </div>
      )}
    </ThemeProvider>
  );
}

export default App;
