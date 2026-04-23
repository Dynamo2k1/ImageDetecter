import React, { useState } from 'react';
import styled from 'styled-components';
import { FaGlobe, FaUpload, FaCheckCircle, FaShieldAlt, FaNetworkWired } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import URLInput from './URLInput';
import FileUpload from './FileUpload';
import NetworkScanInput from './NetworkScanInput';

const Container = styled.div` background: ${({ theme }) => theme.cardBackground}; border: 1px solid ${({ theme }) => theme.cardBorder}; border-radius: 12px; overflow: hidden; `;
const TabsHeader = styled.div` display: flex; border-bottom: 1px solid ${({ theme }) => theme.cardBorder}; background: ${({ theme }) => theme.background}; `;
const Tab = styled.button` flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 1.5rem; background: transparent; border: none; color: ${({ active, theme }) => active ? theme.primary : theme.textSecondary}; font-weight: 600; cursor: pointer; border-bottom: 3px solid ${({ active, theme }) => active ? theme.primary : 'transparent'}; &:hover { background: ${({ theme }) => theme.primary}10; } `;
const TabContent = styled.div` padding: 2rem; `;
const SuccessMessage = styled.div` text-align: center; padding: 3rem; background: ${({ theme }) => theme.success}10; border: 1px solid ${({ theme }) => theme.success}20; border-radius: 8px; `;
const SuccessTitle = styled.h3` color: ${({ theme }) => theme.text}; margin: 1rem 0; font-size: 1.5rem; `;
const JobInfo = styled.div` margin: 2rem 0; font-family: var(--font-mono); background: ${({ theme }) => theme.background}; padding: 1rem; border-radius: 8px; `;
const Button = styled.button` background: ${({ theme }) => theme.primary}; color: ${({ theme }) => theme.cardBackground}; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; font-weight: 600; cursor: pointer; margin: 0.5rem; `;

const SubmissionTabs = () => {
  const [activeTab, setActiveTab] = useState('url');
  const [submissionResult, setSubmissionResult] = useState(null);
  const navigate = useNavigate();

  // This function is passed to children (URLInput/FileUpload) which perform the API call
  const handleSubmissionSuccess = (response) => {
    setSubmissionResult(response);
  };

  const handleReset = () => {
    setSubmissionResult(null);
  };

  return (
    <Container>
      {!submissionResult ? (
        <>
          <TabsHeader>
            <Tab active={activeTab === 'url'} onClick={() => setActiveTab('url')}><FaGlobe /> URL Acquisition</Tab>
            <Tab active={activeTab === 'upload'} onClick={() => setActiveTab('upload')}><FaUpload /> Local Upload</Tab>
            <Tab active={activeTab === 'scan'} onClick={() => setActiveTab('scan')}><FaNetworkWired /> Network Scan</Tab>
          </TabsHeader>
          <TabContent>
            {activeTab === 'url' ? (
              <URLInput onSubmit={handleSubmissionSuccess} />
            ) : activeTab === 'scan' ? (
              <NetworkScanInput onSubmit={handleSubmissionSuccess} />
            ) : (
              <FileUpload onSubmit={handleSubmissionSuccess} />
            )}
          </TabContent>
        </>
      ) : (
        <TabContent>
          <SuccessMessage>
            <FaCheckCircle size={50} color="#10b981" />
            <SuccessTitle>Evidence Submitted Successfully</SuccessTitle>
            <p>Processing has started. The chain of custody has been initialized.</p>
            
            <JobInfo>
              <div>Job ID: <strong>{submissionResult.job_id}</strong></div>
              <div>Status: <span style={{ color: '#3b82f6' }}>{submissionResult.status.toUpperCase()}</span></div>
              <div>Timestamp: {new Date(submissionResult.created_at).toLocaleString()}</div>
            </JobInfo>
            
            <div>
              <Button onClick={() => navigate('/monitor')}><FaShieldAlt /> Monitor Job</Button>
              <Button onClick={handleReset} style={{ background: 'transparent', border: '1px solid currentColor', color: 'inherit' }}>Submit New Evidence</Button>
            </div>
          </SuccessMessage>
        </TabContent>
      )}
    </Container>
  );
};

export default SubmissionTabs;
