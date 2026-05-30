import React from 'react';
import styled from 'styled-components';
import { NavLink } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  FaHome, 
  FaUpload, 
  FaListAlt, 
  FaSearch, 
  FaCog, 
  FaDatabase,
  FaShieldAlt,
  FaHistory,
  FaChartLine,
  FaQuestionCircle,
  FaBook,
  FaTimes,
  FaGlobe,
  FaServer
} from 'react-icons/fa';
import { forensicAPI } from '../../services/api';

const SidebarContainer = styled.aside`
  width: 250px;
  background: ${({ theme }) => theme.cardBackground};
  border-right: 1px solid ${({ theme }) => theme.cardBorder};
  position: fixed;
  top: 0;
  left: ${({ isOpen }) => (isOpen ? '0' : '-250px')};
  bottom: 0;
  z-index: 1000;
  transition: left 0.3s ease;
  overflow-y: auto;
  
  @media (max-width: 768px) {
    left: ${({ isOpen }) => (isOpen ? '0' : '-250px')};
    box-shadow: ${({ isOpen }) => 
      isOpen ? '4px 0 20px rgba(0, 0, 0, 0.3)' : 'none'};
  }
`;

const SidebarHeader = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder};
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const SidebarTitle = styled.h2`
  font-size: 1rem;
  font-weight: 600;
  color: ${({ theme }) => theme.text};
  text-transform: uppercase;
  letter-spacing: 2px;
  
  span {
    color: ${({ theme }) => theme.primary};
  }
`;

const CloseButton = styled.button`
  background: transparent;
  border: none;
  color: ${({ theme }) => theme.text};
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  display: none;
  
  @media (max-width: 768px) {
    display: block;
  }
  
  &:hover {
    color: ${({ theme }) => theme.primary};
  }
`;

const NavSection = styled.div`
  padding: 1.5rem 0;
`;

const SectionTitle = styled.h3`
  padding: 0 1.5rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: ${({ theme }) => theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const NavList = styled.ul`
  list-style: none;
`;

const NavItem = styled.li`
  margin-bottom: 0.25rem;
`;

const StyledNavLink = styled(NavLink)`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  color: ${({ theme }) => theme.text};
  text-decoration: none;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
  
  &:hover {
    background: ${({ theme }) => theme.primary}10;
    color: ${({ theme }) => theme.primary};
    border-left-color: ${({ theme }) => theme.primary}50;
  }
  
  &.active {
    background: ${({ theme }) => theme.primary}20;
    color: ${({ theme }) => theme.primary};
    border-left-color: ${({ theme }) => theme.primary};
    
    svg {
      color: ${({ theme }) => theme.primary};
    }
  }
  
  svg {
    font-size: 1rem;
    color: ${({ theme }) => theme.textSecondary};
  }
`;

const NavText = styled.span`
  font-size: 0.875rem;
  font-weight: 500;
`;

const Badge = styled.span`
  margin-left: auto;
  background: ${({ theme }) => theme.primary};
  color: ${({ theme }) => theme.cardBackground};
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
  border-radius: 10px;
  font-weight: 600;
`;

const SidebarFooter = styled.div`
  padding: 1.5rem;
  border-top: 1px solid ${({ theme }) => theme.cardBorder};
  margin-top: auto;
`;

const SystemInfo = styled.div`
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: ${({ theme }) => theme.textSecondary};
  
  div {
    margin-bottom: 0.25rem;
  }
`;

const Version = styled.div`
  color: ${({ theme }) => theme.primary};
  font-weight: 600;
`;

const StatusIndicator = styled.span`
  color: ${({ status }) => status === 'ok' ? '#10b981' : '#ef4444'};
`;

const Sidebar = ({ isOpen, toggleSidebar }) => {
  // Fetch real-time stats for sidebar footer
  const { data: stats } = useQuery('sidebarStats', () => forensicAPI.getAnalytics('7d'), {
    refetchInterval: 30000,
    placeholderData: { pending_jobs: 0, total_jobs: 0 }
  });

  const navItems = [
    {
      section: 'Main',
      items: [
        { path: '/dashboard', icon: <FaHome />, text: 'Dashboard' },
        { path: '/submit', icon: <FaUpload />, text: 'Acquire Evidence', badge: 'NEW' },
        { path: '/monitor', icon: <FaListAlt />, text: 'Job Monitor' },
        { path: '/database', icon: <FaSearch />, text: 'Evidence Browser' },
      ]
    },
    {
      section: 'Analysis',
      items: [
        { path: '/analytics', icon: <FaChartLine />, text: 'Analytics' },
        { path: '/chain-of-custody', icon: <FaHistory />, text: 'Chain of Custody' },
        { path: '/scanner', icon: <FaSearch />, text: 'Network Scanner' },
        { path: '/vulnerabilities', icon: <FaShieldAlt />, text: 'Vulnerabilities' },
      ]
    },
    {
      section: 'Red Team',
      items: [
        { path: '/recon', icon: <FaGlobe />, text: 'Recon Module' },
      ]
    },
    {
      section: 'System',
      items: [
        { path: '/settings', icon: <FaCog />, text: 'Settings' },
        { path: '/security', icon: <FaShieldAlt />, text: 'Security' },
        { path: '/help', icon: <FaQuestionCircle />, text: 'Help' },
        { path: '/docs', icon: <FaBook />, text: 'Documentation' },
      ]
    }
  ];

  const activeJobs = stats?.pending_jobs || 0;
  const totalJobs = stats?.total_jobs || 0;

  return (
    <SidebarContainer isOpen={isOpen}>
      <SidebarHeader>
        <SidebarTitle>
          <span>FEAS</span>
        </SidebarTitle>
        <CloseButton onClick={toggleSidebar}>
          <FaTimes />
        </CloseButton>
      </SidebarHeader>
      
      {navItems.map((section, idx) => (
        <NavSection key={idx}>
          <SectionTitle>{section.section}</SectionTitle>
          <NavList>
            {section.items.map((item, itemIdx) => (
              <NavItem key={itemIdx}>
                <StyledNavLink to={item.path} onClick={() => window.innerWidth < 768 && toggleSidebar()}>
                  {item.icon}
                  <NavText>{item.text}</NavText>
                  {item.badge && <Badge>{item.badge}</Badge>}
                </StyledNavLink>
              </NavItem>
            ))}
          </NavList>
        </NavSection>
      ))}
      
      <SidebarFooter>
        <SystemInfo>
          <div>System: <StatusIndicator status="ok">OPERATIONAL</StatusIndicator></div>
          <div>Active Jobs: {activeJobs}</div>
          <div>Total Jobs: {totalJobs}</div>
          <Version>v1.0.0 | FEAS</Version>
        </SystemInfo>
      </SidebarFooter>
    </SidebarContainer>
  );
};

export default Sidebar;