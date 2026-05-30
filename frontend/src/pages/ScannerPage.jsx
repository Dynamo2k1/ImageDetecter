import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  FaSearch, 
  FaSpinner, 
  FaServer, 
  FaShieldAlt, 
  FaBug, 
  FaPlay, 
  FaCheckCircle, 
  FaExclamationTriangle,
  FaExternalLinkAlt,
  FaFileAlt
} from 'react-icons/fa';
import { forensicAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 0;
`;

const PageHeader = styled.div`
  margin-bottom: 2rem;
`;

const PageTitle = styled.h1`
  font-size: 2rem;
  font-weight: 700;
  color: ${({ theme }) => theme.text};
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  span {
    color: ${({ theme }) => theme.primary};
  }
`;

const PageSubtitle = styled.p`
  color: ${({ theme }) => theme.textSecondary};
  font-size: 1rem;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 2rem;
  
  @media (max-width: 992px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background: ${({ theme }) => theme.cardBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  height: fit-content;
`;

const CardTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  color: ${({ theme }) => theme.text};
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder};
  padding-bottom: 0.75rem;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Label = styled.label`
  font-size: 0.875rem;
  font-weight: 600;
  color: ${({ theme }) => theme.text};
`;

const Input = styled.input`
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.cardBorder};
  background: ${({ theme }) => theme.bodyBackground};
  color: ${({ theme }) => theme.text};
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: ${({ theme }) => theme.primary};
  }
`;

const Select = styled.select`
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.cardBorder};
  background: ${({ theme }) => theme.bodyBackground};
  color: ${({ theme }) => theme.text};
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: ${({ theme }) => theme.primary};
  }
`;

const Button = styled.button`
  background: ${({ theme }) => theme.primary};
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: opacity 0.2s, transform 0.1s;
  
  &:hover:not(:disabled) {
    opacity: 0.9;
    transform: translateY(-1px);
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
  }
  
  &:disabled {
    background: ${({ theme }) => theme.textSecondary};
    cursor: not-allowed;
  }
`;

const List = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 0.25rem;
`;

const ListItem = styled.div`
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: ${({ active, theme }) => active ? `${theme.primary}15` : theme.bodyBackground};
  border: 1px solid ${({ active, theme }) => active ? theme.primary : theme.cardBorder};
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
  
  &:hover {
    border-color: ${({ theme }) => theme.primary};
  }
`;

const ScanInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const ScanTarget = styled.span`
  font-size: 0.875rem;
  font-weight: 600;
  color: ${({ theme }) => theme.text};
`;

const ScanDate = styled.span`
  font-size: 0.75rem;
  color: ${({ theme }) => theme.textSecondary};
`;

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const SpinnerIcon = styled(FaSpinner)`
  animation: ${spin} 1s linear infinite;
`;

const StatusBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  text-transform: uppercase;
  
  ${({ status, theme }) => {
    if (status === 'completed') {
      return `background: ${theme.success}20; color: ${theme.success};`;
    }
    if (status === 'running' || status === 'pending') {
      return `background: ${theme.primary}20; color: ${theme.primary};`;
    }
    return `background: ${theme.error}20; color: ${theme.error};`;
  }}
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: ${({ theme }) => theme.textSecondary};
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  border: 1px dashed ${({ theme }) => theme.cardBorder};
  border-radius: 12px;
  background: ${({ theme }) => theme.cardBackground};
`;

const HostCard = styled.div`
  background: ${({ theme }) => theme.bodyBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const HostInfoTitle = styled.div`
  font-size: 0.95rem;
  font-weight: 600;
  color: ${({ theme }) => theme.text};
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5rem;
  font-size: 0.825rem;
`;

const Th = styled.th`
  text-align: left;
  padding: 0.5rem;
  border-bottom: 2px solid ${({ theme }) => theme.cardBorder};
  color: ${({ theme }) => theme.textSecondary};
  font-weight: 600;
`;

const Td = styled.td`
  padding: 0.5rem;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder};
  color: ${({ theme }) => theme.text};
`;

const RiskSummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
`;

const RiskBox = styled.div`
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  border: 1px solid;
  
  ${({ level, theme }) => {
    switch (level.toLowerCase()) {
      case 'critical':
        return `background: #fed7d7; color: #9b2c2c; border-color: #feb2b2;`;
      case 'high':
        return `background: #feebc8; color: #c05621; border-color: #fbd38d;`;
      case 'medium':
        return `background: #fefcbf; color: #744210; border-color: #faf089;`;
      case 'low':
        return `background: #e2e8f0; color: #4a5568; border-color: #cbd5e0;`;
      default:
        return `background: #ebf8ff; color: #2b6cb0; border-color: #bee3f8;`;
    }
  }}
`;

const SeverityBadge = styled.span`
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  
  ${({ level }) => {
    switch (level.toLowerCase()) {
      case 'critical':
        return `background: #9b2c2c; color: white;`;
      case 'high':
        return `background: #c05621; color: white;`;
      case 'medium':
        return `background: #dd6b20; color: white;`;
      case 'low':
        return `background: #4a5568; color: white;`;
      default:
        return `background: #2b6cb0; color: white;`;
    }
  }}
`;

const SeverityContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
`;

const SeverityItem = styled.div`
  padding: 1rem;
  border-radius: 8px;
  background: ${({ theme }) => theme.bodyBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const SeverityHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const SeverityTitle = styled.div`
  font-weight: 600;
  font-size: 0.875rem;
  color: ${({ theme }) => theme.text};
`;

const NvdLink = styled.a`
  font-size: 0.75rem;
  color: ${({ theme }) => theme.primary};
  display: flex;
  align-items: center;
  gap: 0.25rem;
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
`;

const ScannerPage = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [selectedJobId, setSelectedJobId] = useState('');
  const [targetHost, setTargetHost] = useState('');
  const [selectedScanId, setSelectedScanId] = useState(null);

  // Fetch all jobs
  const { data: jobs } = useQuery('jobsList', forensicAPI.getAllJobs);

  // Fetch scans for selected job
  const { data: scans } = useQuery(
    ['jobScans', selectedJobId],
    () => forensicAPI.getJobScans(selectedJobId),
    { enabled: !!selectedJobId }
  );

  // Fetch vulnerabilities for selected scan
  const { data: vulnerabilities } = useQuery(
    ['scanVulns', selectedScanId],
    () => forensicAPI.getScanVulnerabilities(selectedScanId),
    { enabled: !!selectedScanId }
  );

  // Mutation to start scan
  const startScanMutation = useMutation(
    ({ target, jobId, investigatorId }) => forensicAPI.startScan(target, jobId, investigatorId),
    {
      onSuccess: (data) => {
        setTargetHost('');
        queryClient.invalidateQueries(['jobScans', selectedJobId]);
        setSelectedScanId(data.scan_id);
      },
      onError: (err) => {
        alert(err.response?.data?.detail || 'Failed to initiate network scan.');
      }
    }
  );

  // Auto-poll if selected scan is running/pending
  const activeScan = scans?.find(s => s.scan_id === selectedScanId);
  const isRunning = activeScan?.status === 'running' || activeScan?.status === 'pending';

  useEffect(() => {
    let interval;
    if (isRunning && selectedScanId) {
      interval = setInterval(() => {
        queryClient.invalidateQueries(['jobScans', selectedJobId]);
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [isRunning, selectedScanId, selectedJobId, queryClient]);

  const handleStartScan = (e) => {
    e.preventDefault();
    if (!targetHost.trim()) return;
    if (!selectedJobId) {
      alert('Please select an evidence job to associate this scan with.');
      return;
    }
    startScanMutation.mutate({
      target: targetHost.trim(),
      jobId: selectedJobId,
      investigatorId: user?.id || 'system'
    });
  };

  // Group vulnerabilities by risk level
  const vulnCounts = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0
  };

  if (vulnerabilities) {
    vulnerabilities.forEach(v => {
      const level = (v.risk_level || 'informational').toLowerCase();
      if (level === 'critical') vulnCounts.critical++;
      else if (level === 'high') vulnCounts.high++;
      else if (level === 'medium') vulnCounts.medium++;
      else if (level === 'low') vulnCounts.low++;
      else vulnCounts.info++;
    });
  }

  return (
    <PageContainer>
      <PageHeader>
        <PageTitle>
          <FaSearch /> Controlled Network <span>Scanner</span>
        </PageTitle>
        <PageSubtitle>
          Scan target hosts related to acquisition jobs and map network services to known CVE vulnerabilities.
        </PageSubtitle>
      </PageHeader>

      <Grid>
        {/* Left Column: Form & History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <Card>
            <CardTitle>
              <FaPlay style={{ fontSize: '1rem' }} /> Launch Scan
            </CardTitle>
            <form onSubmit={handleStartScan} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <FormGroup>
                <Label>Associate with Evidence Job</Label>
                <Select 
                  value={selectedJobId} 
                  onChange={(e) => {
                    setSelectedJobId(e.target.value);
                    setSelectedScanId(null);
                  }}
                  required
                >
                  <option value="">-- Select Job Reference --</option>
                  {jobs?.map(job => (
                    <option key={job.job_id} value={job.job_id}>
                      {job.filename || job.source} ({job.job_id.substring(0, 8)}...)
                    </option>
                  ))}
                </Select>
              </FormGroup>

              <FormGroup>
                <Label>Target IP or Hostname</Label>
                <Input 
                  type="text" 
                  placeholder="e.g. scanme.nmap.org or 8.8.8.8"
                  value={targetHost}
                  onChange={(e) => setTargetHost(e.target.value)}
                  disabled={startScanMutation.isLoading}
                  required
                />
              </FormGroup>

              <Button 
                type="submit" 
                disabled={startScanMutation.isLoading || !selectedJobId || !targetHost.trim()}
              >
                {startScanMutation.isLoading ? <SpinnerIcon /> : <FaSearch />}
                Start Controlled Scan
              </Button>
            </form>
          </Card>

          {selectedJobId && (
            <Card>
              <CardTitle>Scan History</CardTitle>
              {scans && scans.length > 0 ? (
                <List>
                  {scans.map(scan => (
                    <ListItem 
                      key={scan.scan_id} 
                      active={scan.scan_id === selectedScanId}
                      onClick={() => setSelectedScanId(scan.scan_id)}
                    >
                      <ScanInfo>
                        <ScanTarget>{scan.target}</ScanTarget>
                        <ScanDate>Scan #{scan.scan_id}</ScanDate>
                      </ScanInfo>
                      <StatusBadge status={scan.status}>{scan.status}</StatusBadge>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'center', padding: '1rem 0' }}>
                  No scans run for this job yet.
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Right Column: Results & Vulnerabilities */}
        <div>
          {activeScan ? (
            <Card style={{ width: '100%' }}>
              <CardTitle style={{ justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FaServer /> Scan #{activeScan.scan_id} Results
                </span>
                <StatusBadge status={activeScan.status}>{activeScan.status}</StatusBadge>
              </CardTitle>

              {activeScan.status === 'running' || activeScan.status === 'pending' ? (
                <div style={{ textAlign: 'center', padding: '3rem 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                  <SpinnerIcon style={{ fontSize: '2.5rem', color: 'var(--primary)' }} />
                  <div>Scan is executing in the background...</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>This can take up to 2 minutes. Results will load automatically.</div>
                </div>
              ) : activeScan.status === 'failed' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', color: 'var(--error)', border: '1px solid var(--error-border)', borderRadius: '8px', padding: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}>
                    <FaExclamationTriangle /> Scan Execution Failed
                  </div>
                  <div style={{ fontSize: '0.875rem' }}>{activeScan.error || 'An unexpected error occurred during nmap execution.'}</div>
                </div>
              ) : (
                <>
                  {/* Completed Scan Info */}
                  <div style={{ fontSize: '0.875rem' }}>
                    <strong>Target:</strong> {activeScan.target}
                  </div>

                  {activeScan.result?.hosts?.map((host, hIdx) => (
                    <HostCard key={hIdx}>
                      <HostInfoTitle>
                        <FaServer /> Host: {host.ip} {host.hostname && `(${host.hostname})`}
                      </HostInfoTitle>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        <strong>State:</strong> {host.state} | <strong>OS Detection:</strong> {host.os_detection || 'Unknown'}
                      </div>
                      
                      {host.ports && host.ports.length > 0 ? (
                        <Table>
                          <thead>
                            <tr>
                              <Th>Port</Th>
                              <Th>Protocol</Th>
                              <Th>State</Th>
                              <Th>Service</Th>
                              <Th>Version</Th>
                            </tr>
                          </thead>
                          <tbody>
                            {host.ports.map((p, pIdx) => (
                              <tr key={pIdx}>
                                <Td style={{ fontWeight: 600 }}>{p.port}</Td>
                                <Td>{p.protocol}</Td>
                                <Td>
                                  <span style={{ color: p.state === 'open' ? '#10b981' : 'inherit' }}>
                                    {p.state}
                                  </span>
                                </Td>
                                <Td>{p.service}</Td>
                                <Td>{p.version || 'N/A'}</Td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      ) : (
                        <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                          No open ports discovered.
                        </div>
                      )}
                    </HostCard>
                  ))}

                  {/* Vulnerability Summary */}
                  <CardTitle style={{ marginTop: '1.5rem' }}>
                    <FaShieldAlt /> Vulnerability Findings ({vulnerabilities?.length || 0})
                  </CardTitle>

                  <RiskSummaryGrid>
                    <RiskBox level="critical">
                      <span>{vulnCounts.critical}</span>
                      <span style={{ fontSize: '0.65rem' }}>CRITICAL</span>
                    </RiskBox>
                    <RiskBox level="high">
                      <span>{vulnCounts.high}</span>
                      <span style={{ fontSize: '0.65rem' }}>HIGH</span>
                    </RiskBox>
                    <RiskBox level="medium">
                      <span>{vulnCounts.medium}</span>
                      <span style={{ fontSize: '0.65rem' }}>MEDIUM</span>
                    </RiskBox>
                    <RiskBox level="low">
                      <span>{vulnCounts.low}</span>
                      <span style={{ fontSize: '0.65rem' }}>LOW</span>
                    </RiskBox>
                    <RiskBox level="info">
                      <span>{vulnCounts.info}</span>
                      <span style={{ fontSize: '0.65rem' }}>INFO</span>
                    </RiskBox>
                  </RiskSummaryGrid>

                  {vulnerabilities && vulnerabilities.length > 0 ? (
                    <SeverityContainer>
                      {vulnerabilities.map(v => (
                        <SeverityItem key={v.id}>
                          <SeverityHeader>
                            <SeverityTitle>
                              {v.cve_id} <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>({v.port}/{v.service})</span>
                            </SeverityTitle>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              {v.cvss_score !== null && (
                                <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>CVSS {v.cvss_score}</span>
                              )}
                              <SeverityBadge level={v.risk_level}>{v.severity}</SeverityBadge>
                            </div>
                          </SeverityHeader>
                          <div style={{ fontSize: '0.825rem', lineHeight: 1.4 }}>
                            {v.description}
                          </div>
                          {v.nvd_url && (
                            <NvdLink href={v.nvd_url} target="_blank" rel="noopener noreferrer">
                              View in NVD <FaExternalLinkAlt style={{ fontSize: '0.65rem' }} />
                            </NvdLink>
                          )}
                        </SeverityItem>
                      ))}
                    </SeverityContainer>
                  ) : (
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textAlign: 'center', padding: '1rem 0' }}>
                      No vulnerabilities mapped for this scan.
                    </div>
                  )}
                </>
              )}
            </Card>
          ) : (
            <EmptyState>
              <FaSearch style={{ fontSize: '3rem', opacity: 0.3 }} />
              <h3>No Scan Selected</h3>
              <p>Select a job and a scan from the history list, or launch a new scan target.</p>
            </EmptyState>
          )}
        </div>
      </Grid>
    </PageContainer>
  );
};

export default ScannerPage;
