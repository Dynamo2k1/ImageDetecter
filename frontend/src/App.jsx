import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { useThemeStore } from './store/themeStore';

// Layout
import Layout from './components/layout/Layout';

// Auth
import ProtectedRoute from './components/common/ProtectedRoute';

// Pages
import Dashboard from './pages/Dashboard';
import SubmissionPage from './pages/SubmissionPage';
import JobMonitorPage from './pages/JobMonitorPage';
import EvidenceDetailPage from './pages/EvidenceDetailPage';
import SettingsPage from './pages/SettingsPage';
import PlaceholderPage from './pages/PlaceholderPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import AnalyticsPage from './pages/AnalyticsPage';
import HelpPage from './pages/HelpPage';
import DocsPage from './pages/DocsPage';
import ScannerPage from './pages/ScannerPage';
import VulnerabilitiesPage from './pages/VulnerabilitiesPage';
import ReconPage from './pages/ReconPage';

// Styles
import GlobalStyles from './styles/GlobalStyles';
import { cyberTheme, darkTheme, lightTheme } from './styles/theme';

function App() {
  const { theme } = useThemeStore();

  const getTheme = () => {
    switch (theme) {
      case 'cyber': return cyberTheme;
      case 'dark': return darkTheme;
      case 'light': return lightTheme;
      default: return cyberTheme;
    }
  };

  return (
    <ThemeProvider theme={getTheme()}>
      <GlobalStyles />
      <Router>
        <Routes>
          {/* Auth Routes (without Layout) */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Main App Routes (with Layout and Protected) */}
          <Route path="/" element={<ProtectedRoute><Layout><Navigate to="/dashboard" replace /></Layout></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
          <Route path="/submit" element={<ProtectedRoute><Layout><SubmissionPage /></Layout></ProtectedRoute>} />
          
          {/* Monitor and Database point to the same list for now */}
          <Route path="/monitor" element={<ProtectedRoute><Layout><JobMonitorPage /></Layout></ProtectedRoute>} />
          <Route path="/database" element={<ProtectedRoute><Layout><JobMonitorPage /></Layout></ProtectedRoute>} />
          
          <Route path="/evidence/:jobId" element={<ProtectedRoute><Layout><EvidenceDetailPage /></Layout></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Layout><SettingsPage /></Layout></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Layout><ProfilePage /></Layout></ProtectedRoute>} />

          {/* Feature Pages */}
          <Route path="/analytics" element={<ProtectedRoute><Layout><AnalyticsPage /></Layout></ProtectedRoute>} />
          <Route path="/scanner" element={<ProtectedRoute><Layout><ScannerPage /></Layout></ProtectedRoute>} />
          <Route path="/vulnerabilities" element={<ProtectedRoute><Layout><VulnerabilitiesPage /></Layout></ProtectedRoute>} />
          <Route path="/recon" element={<ProtectedRoute><Layout><ReconPage /></Layout></ProtectedRoute>} />
          <Route path="/chain-of-custody" element={<ProtectedRoute><Layout><PlaceholderPage title="Global Chain of Custody" /></Layout></ProtectedRoute>} />
          <Route path="/security" element={<ProtectedRoute><Layout><SettingsPage /></Layout></ProtectedRoute>} />
          <Route path="/help" element={<ProtectedRoute><Layout><HelpPage /></Layout></ProtectedRoute>} />
          <Route path="/docs" element={<ProtectedRoute><Layout><DocsPage /></Layout></ProtectedRoute>} />
          
          {/* 404 Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;


