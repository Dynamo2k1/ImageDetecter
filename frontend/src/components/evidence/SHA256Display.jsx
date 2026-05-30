import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  FaFingerprint, 
  FaCopy, 
  FaCheck,
  FaShieldAlt,
  FaLock,
  FaEye,
  FaEyeSlash 
} from 'react-icons/fa';
import { toast } from 'react-toastify';

const Container = styled.div`
  background: ${({ theme }) => theme.cardBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 12px;
  padding: 2rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #00ffff 0%, #0088ff 100%);
  }
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const Icon = styled.div`
  font-size: 2rem;
  color: ${({ theme }) => theme.primary};
`;

const Title = styled.h3`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${({ theme }) => theme.text};
  
  span {
    color: ${({ theme }) => theme.primary};
  }
`;

const HashContainer = styled.div`
  background: ${({ theme }) => theme.background};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  position: relative;
  font-family: var(--font-mono);
`;

const HashValue = styled.div`
  color: ${({ theme }) => theme.text};
  font-size: 1.125rem;
  font-weight: 600;
  word-break: break-all;
  line-height: 1.6;
  padding-right: 120px;
  
  @media (max-width: 768px) {
    padding-right: 0;
    margin-bottom: 1rem;
  }
`;

const CopyButton = styled.button`
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: ${({ theme }) => theme.primary};
  color: ${({ theme }) => theme.cardBackground};
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.875rem;
  
  &:hover {
    transform: translateY(-50%) translateY(-2px);
    box-shadow: 0 8px 30px ${({ theme }) => theme.primary}40;
  }
  
  @media (max-width: 768px) {
    position: relative;
    right: auto;
    top: auto;
    transform: none;
    width: 100%;
    justify-content: center;
  }
`;

const Properties = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const Property = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const PropertyLabel = styled.span`
  font-size: 0.75rem;
  color: ${({ theme }) => theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: var(--font-mono);
`;

const PropertyValue = styled.span`
  font-size: 0.875rem;
  color: ${({ theme }) => theme.text};
  font-weight: 600;
  font-family: var(--font-mono);
`;

const Explanation = styled.div`
  padding: 1rem;
  background: ${({ theme }) => theme.primary}10;
  border: 1px solid ${({ theme }) => theme.primary}20;
  border-radius: 8px;
  font-size: 0.875rem;
  color: ${({ theme }) => theme.text};
  line-height: 1.6;
`;

const SecurityFeatures = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
`;

const SecurityFeature = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: ${({ theme }) => theme.success}10;
  border: 1px solid ${({ theme }) => theme.success}20;
  border-radius: 4px;
  color: ${({ theme }) => theme.success};
  font-family: var(--font-mono);
  font-size: 0.75rem;
`;

const VisibilityToggle = styled.button`
  position: absolute;
  right: 1rem;
  top: 1rem;
  background: transparent;
  border: none;
  color: ${({ theme }) => theme.textSecondary};
  font-size: 1rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
  
  &:hover {
    color: ${({ theme }) => theme.primary};
    background: ${({ theme }) => theme.primary}10;
  }
`;

const StatusBadge = styled.span`
  margin-left: auto;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  text-transform: uppercase;
  background: ${({ status, theme }) => status === 'VERIFIED' ? '#c6f6d5' : '#fed7d7'};
  color: ${({ status, theme }) => status === 'VERIFIED' ? '#22543d' : '#9b2c2c'};
  border: 1px solid ${({ status }) => status === 'VERIFIED' ? '#c6f6d5' : '#feb2b2'};
`;

const SHA256Display = ({ hash, jobId, integrityStatus = 'VERIFIED' }) => {
  const [copied, setCopied] = useState(false);
  const [visible, setVisible] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopied(true);
      toast.success('Hash copied to clipboard');
      
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error('Failed to copy hash');
      console.error('Failed to copy:', err);
    }
  };

  const formatHash = (hash) => {
    if (!hash) return 'No hash available';
    
    if (!visible) {
      return '•'.repeat(64);
    }
    
    // Format as groups of 8 characters
    const groups = [];
    for (let i = 0; i < hash.length; i += 8) {
      groups.push(hash.substring(i, i + 8));
    }
    return groups.join(' ');
  };

  const toggleVisibility = () => {
    setVisible(!visible);
  };

  return (
    <Container>
      <Header>
        <Icon>
          <FaFingerprint />
        </Icon>
        <Title>
          SHA-256 <span>Digital Fingerprint</span>
        </Title>
        <StatusBadge status={integrityStatus}>
          {integrityStatus === 'VERIFIED' ? '✓ Integrity Verified' : '✗ Compromised'}
        </StatusBadge>
      </Header>
      
      <HashContainer>
        <VisibilityToggle 
          onClick={toggleVisibility}
          title={visible ? 'Hide hash' : 'Show hash'}
        >
          {visible ? <FaEyeSlash /> : <FaEye />}
        </VisibilityToggle>
        
        <HashValue>
          {formatHash(hash)}
        </HashValue>
        
        <CopyButton onClick={copyToClipboard}>
          {copied ? <FaCheck /> : <FaCopy />}
          {copied ? 'Copied!' : 'Copy Hash'}
        </CopyButton>
      </HashContainer>
      
      <Properties>
        <Property>
          <PropertyLabel>Algorithm</PropertyLabel>
          <PropertyValue>SHA-256 (Secure Hash Algorithm 256-bit)</PropertyValue>
        </Property>
        
        <Property>
          <PropertyLabel>Length</PropertyLabel>
          <PropertyValue>64 hexadecimal characters (256 bits)</PropertyValue>
        </Property>
        
        <Property>
          <PropertyLabel>Collision Resistance</PropertyLabel>
          <PropertyValue>Extremely High (2¹²⁸ operations)</PropertyValue>
        </Property>
        
        <Property>
          <PropertyLabel>Job Reference</PropertyLabel>
          <PropertyValue>{jobId || 'N/A'}</PropertyValue>
        </Property>
      </Properties>
      
      <Explanation>
        This SHA-256 hash serves as a unique digital fingerprint of the evidence.
        Any modification to the file—even a single bit—will result in a completely different hash,
        making it ideal for verifying evidence integrity throughout the chain of custody.
        The hash is computed using the NIST-standard SHA-256 algorithm, providing
        cryptographic security and collision resistance.
      </Explanation>
      
      <SecurityFeatures>
        <SecurityFeature>
          <FaShieldAlt />
          Cryptographic Security
        </SecurityFeature>
        <SecurityFeature>
          <FaLock />
          Chain of Custody Verification
        </SecurityFeature>
        <SecurityFeature>
          <FaFingerprint />
          Unique Digital Fingerprint
        </SecurityFeature>
      </SecurityFeatures>
    </Container>
  );
};

export default SHA256Display;