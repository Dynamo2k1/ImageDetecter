import React, { useState } from 'react';
import styled from 'styled-components';
import { FaNetworkWired, FaSpinner, FaShieldAlt } from 'react-icons/fa';
import { toast } from 'react-toastify';
import { forensicAPI } from '../../services/api';

const Container = styled.div`
  background: ${({ theme }) => theme.cardBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 8px;
  padding: 2rem;
`;

const Title = styled.h3`
  font-size: 1.5rem;
  color: ${({ theme }) => theme.text};
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  color: ${({ theme }) => theme.textSecondary};
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
`;

const Form = styled.form`
  display: grid;
  gap: 1rem;
`;

const Input = styled.input`
  background: ${({ theme }) => theme.background};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 4px;
  padding: 0.75rem 1rem;
  color: ${({ theme }) => theme.text};
  font-family: var(--font-mono);
`;

const SubmitButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  background: ${({ theme }) => theme.primary};
  color: ${({ theme }) => theme.cardBackground};
  border: none;
  border-radius: 4px;
  padding: 0.9rem 1.2rem;
  cursor: pointer;
  font-weight: 600;
  opacity: ${({ disabled }) => (disabled ? 0.6 : 1)};
`;

const ResultBox = styled.pre`
  margin-top: 1rem;
  background: ${({ theme }) => theme.background};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 6px;
  padding: 1rem;
  font-size: 0.75rem;
  color: ${({ theme }) => theme.textSecondary};
  overflow-x: auto;
`;

const SecurityNotice = styled.div`
  margin-top: 1rem;
  padding: 1rem;
  background: ${({ theme }) => theme.success}10;
  border: 1px solid ${({ theme }) => theme.success}20;
  border-radius: 4px;
  font-size: 0.75rem;
  color: ${({ theme }) => theme.success};
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const Spinner = styled.div`
  @keyframes spin { to { transform: rotate(360deg); } }
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
`;

const NetworkScanInput = ({ onSubmit }) => {
  const [target, setTarget] = useState('');
  const [caseNumber, setCaseNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await forensicAPI.runNetworkScan({
        target,
        case_number: caseNumber
      });
      setResult(response);
      if (onSubmit) onSubmit(response);
      toast.success('Network scan completed');
    } catch (err) {
      toast.error(`Scan failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Title><FaNetworkWired /> Network Scan</Title>
      <Subtitle>Scan a target IP/domain and map findings to case evidence.</Subtitle>
      <Form onSubmit={handleSubmit}>
        <Input
          type="text"
          placeholder="Target IP or domain (e.g., 192.168.1.10 or example.com)"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          required
        />
        <Input
          type="text"
          placeholder="Case Number (e.g., CASE-2026-001)"
          value={caseNumber}
          onChange={(e) => setCaseNumber(e.target.value)}
          required
        />
        <SubmitButton type="submit" disabled={!target || !caseNumber || loading}>
          {loading ? <><Spinner /> Scanning...</> : 'Run Nmap Scan'}
        </SubmitButton>
      </Form>

      {result && (
        <ResultBox>{JSON.stringify(result, null, 2)}</ResultBox>
      )}

      <SecurityNotice>
        <FaShieldAlt />
        Scan actions are logged in append-only forensic audit records.
      </SecurityNotice>
    </Container>
  );
};

export default NetworkScanInput;
