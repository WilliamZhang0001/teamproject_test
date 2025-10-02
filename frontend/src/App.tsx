import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, AppBar, Toolbar, Typography, Box, Button, Avatar } from '@mui/material';
import { useAuth } from './contexts/AuthContext';

// Import pages
import HomePage from './pages/HomePage';
import ParameterQueryPage from './pages/ParameterQueryPage';
import DataInputPage from './pages/DataInputPage';
import UploadDatasetPage from './pages/UploadDatasetPage';
import FeedbackPage from './pages/FeedbackPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import WelcomePage from './pages/WelcomePage';

// Import components
import ProtectedRoute from './components/ProtectedRoute';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Navigation Bar Component
const NavigationBar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
  };

  const handleLogoClick = () => {
    navigate('/');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ 
            flexGrow: 1,
            cursor: 'pointer',
            '&:hover': {
              opacity: 0.8
            }
          }}
          onClick={handleLogoClick}
        >
          DoE-Assist
        </Typography>
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'secondary.main' }}>
              {user.name.charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="body2">
              {user.name}
            </Typography>
            <Button color="inherit" onClick={handleLogout}>
              Logout
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

const AppContent: React.FC = () => {
  const { user } = useAuth();

  return (
    <Box sx={{ flexGrow: 1 }}>
      <NavigationBar />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Welcome page for unauthenticated users */}
        <Route path="/" element={
          user ? (
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
              <HomePage />
            </Container>
          ) : (
            <WelcomePage />
          )
        } />
        
        {/* Protected routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
              <HomePage />
            </Container>
          </ProtectedRoute>
        } />
        <Route path="/query" element={
          <ProtectedRoute>
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
              <ParameterQueryPage />
            </Container>
          </ProtectedRoute>
        } />
        <Route path="/input" element={
          <ProtectedRoute>
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
              <DataInputPage />
            </Container>
          </ProtectedRoute>
        } />
        <Route path="/upload" element={
          <ProtectedRoute>
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
              <UploadDatasetPage />
            </Container>
          </ProtectedRoute>
        } />
        <Route path="/feedback" element={
          <ProtectedRoute>
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
              <FeedbackPage />
            </Container>
          </ProtectedRoute>
        } />
        
        {/* Redirect unknown routes */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
};

export default App;
