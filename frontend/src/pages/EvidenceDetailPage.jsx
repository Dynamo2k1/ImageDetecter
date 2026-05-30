import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  FaFingerprint, 
  FaFileAlt, 
  FaHistory, 
  FaDownload,
  FaGlobe, 
  FaUpload, 
  FaExclamationTriangle,
  FaLock,
  FaUnlock,
  FaCheckCircle,
  FaCogs,
  FaBug,
  FaClock,
  FaSearch,
  FaShieldAlt,
  FaChevronDown,
  FaExternalLinkAlt
} from 'react-icons/fa';
import { format } from 'date-fns';
import SHA256Display from '../components/evidence/SHA256Display';
import VerifyIntegrityButton from '../components/evidence/VerifyIntegrityButton';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { forensicAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';

/* ---- Styled Components ---- */

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 0;
`;

const HeaderArea = styled.div`
  margin: 1.5rem 0 2.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
`;

const TitleContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const Title = styled.h1`
  font-size: 1.75rem;
  font-weight: 700;
  color: ${({ theme }) => theme.text};
  display: flex;
  align-items: center;
  gap: 0.75rem;
`;

const JobIdBadge = styled.code`
  background: ${({ theme }) => theme.bodyBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  padding: 0.25rem 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: ${({ theme }) => theme.primary};
  border-radius: 4px;
`;

const LockBadge = styled.span`
  background: ${({ isEncrypted, theme }) => isEncrypted ? '#fed7d7' : '#e2e8f0'};
  color: ${({ isEncrypted, theme }) => isEncrypted ? '#9b2c2c' : '#4a5568'};
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
`;

const TabsHeader = styled.div`
  display: flex;
  gap: 1rem;
  border-bottom: 2px solid ${({ theme }) => theme.cardBorder};
  margin-bottom: 2rem;
`;

const TabButton = styled.button`
  background: transparent;
  border: none;
  color: ${({ active, theme }) => active ? theme.primary : theme.textSecondary};
  font-weight: 600;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 3px solid ${({ active, theme }) => active ? theme.primary : 'transparent'};
  transition: all 0.2s;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    color: ${({ theme }) => theme.primary};
  }
`;

const TabContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const MetadataGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
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
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder};
  padding-bottom: 0.75rem;
  color: ${({ theme }) => theme.primary};
  font-size: 1.15rem;
  font-weight: 600;
`;

const MetadataList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const MetadataItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const MetadataLabel = styled.span`
  color: ${({ theme }) => theme.textSecondary};
  font-size: 0.875rem;
`;

const MetadataValue = styled.span`
  color: ${({ theme }) => theme.text};
  font-weight: 600;
  font-size: 0.875rem;
  font-family: ${({ mono }) => (mono ? 'var(--font-mono)' : 'inherit')};
  text-align: right;
`;

/* Timeline Styling */
const TimelineContainer = styled.div`
  position: relative;
  padding-left: 2rem;
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  
  &::before {
    content: '';
    position: absolute;
    top: 5px;
    left: 7px;
    bottom: 5px;
    width: 2px;
    background: ${({ theme }) => theme.cardBorder};
  }
`;

const TimelineEvent = styled.div`
  position: relative;
`;

const TimelineDot = styled.div`
  position: absolute;
  top: 4px;
  left: -2rem;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: ${({ theme }) => theme.cardBackground};
  border: 3px solid ${({ type, theme }) => {
    if (type === 'compromised' || type === 'failed' || type === 'unauth') return theme.error;
    if (type === 'success' || type === 'verified') return theme.success;
    return theme.primary;
  }};
  z-index: 1;
`;

const EventHeader = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 0.825rem;
  color: ${({ theme }) => theme.textSecondary};
  margin-bottom: 0.25rem;
`;

const EventTitle = styled.div`
  font-weight: 600;
  color: ${({ theme }) => theme.text};
  font-size: 0.9rem;
`;

const EventDetails = styled.div`
  font-size: 0.8rem;
  color: ${({ theme }) => theme.textSecondary};
  background: ${({ theme }) => theme.bodyBackground};
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  margin-top: 0.25rem;
  border: 1px solid ${({ theme }) => theme.cardBorder};
`;

/* PDF Customization Section */
const CustomPdfBox = styled.div`
  background: ${({ theme }) => theme.bodyBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: ${({ theme }) => theme.text};
  cursor: pointer;
  
  input {
    cursor: pointer;
  }
`;

/* Risk assessment details */
const RiskScoreMeter = styled.div`
  height: 16px;
  background: ${({ theme }) => theme.bodyBackground};
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  border: 1px solid ${({ theme }) => theme.cardBorder};
`;

const RiskScoreFill = styled.div`
  height: 100%;
  width: ${({ score }) => score}%;
  background: ${({ score }) => {
    if (score >= 75) return '#ef4444';
    if (score >= 50) return '#f97316';
    if (score >= 25) return '#eab308';
    return '#10b981';
  }};
  transition: width 0.5s ease;
`;

const FlagCard = styled.div`
  background: ${({ severity }) => {
    if (severity === 'CRITICAL' || severity === 'HIGH') return '#fed7d7';
    return '#feebc8';
  }};
  color: ${({ severity }) => {
    if (severity === 'CRITICAL' || severity === 'HIGH') return '#742a2a';
    return '#744210';
  }};
  border: 1px solid ${({ severity }) => {
    if (severity === 'CRITICAL' || severity === 'HIGH') return '#feb2b2';
    return '#fbd38d';
  }};
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
`;

const HypothesesList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const HypothesisItem = styled.div`
  border-left: 4px solid ${({ prob }) => {
    if (prob === 'Critical' || prob === 'High') return '#ef4444';
    if (prob === 'Medium') return '#f97316';
    return '#10b981';
  }};
  padding-left: 1rem;
`;

const spin = keyframes`
  to { transform: rotate(360deg); }
`;

const Spinner = styled(FaSpinner)`
  animation: ${spin} 1s linear infinite;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  flex-wrap: wrap;
`;

const PrimaryButton = styled.button`
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
  gap: 0.5rem;
  transition: opacity 0.2s;
  
  &:hover:not(:disabled) {
    opacity: 0.95;
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const EvidenceDetailPage = () => {
  const { jobId } = useParams();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('metadata');
  
  // Custom PDF Options
  const [includeCustody, setIncludeCustody] = useState(true);
  const [includeScans, setIncludeScans] = useState(true);
  const [includeVulns, setIncludeVulns] = useState(true);
  const [includeCorrelation, setIncludeCorrelation] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);

  // Job query
  const { data: job, isLoading: isJobLoading, error } = useQuery(
    ['jobDetails', jobId],
    () => forensicAPI.getJobDetails(jobId),
    { enabled: !!jobId }
  );

  // Scan query
  const { data: scans } = useQuery(
    ['jobScans', jobId],
    () => forensicAPI.getJobScans(jobId),
    { enabled: !!jobId && activeTab === 'scans' }
  );

  // Vulnerability query
  const { data: vulnerabilities } = useQuery(
    ['jobVulns', jobId],
    () => forensicAPI.getJobVulnerabilities(jobId),
    { enabled: !!jobId && (activeTab === 'scans' || activeTab === 'correlation') }
  );

  // Correlation query
  const { data: correlation, isLoading: isCorrLoading } = useQuery(
    ['jobCorrelation', jobId],
    () => forensicAPI.getCorrelationReport(jobId),
    { enabled: !!jobId && activeTab === 'correlation', retry: false }
  );

  // Run correlation mutation
  const runCorrelationMutation = useMutation(
    () => forensicAPI.runCorrelationAnalysis(jobId, user?.id || 'system'),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['jobCorrelation', jobId]);
      },
      onError: (err) => {
        alert(err.response?.data?.detail || 'Failed to run correlation analysis.');
      }
    }
  );

  const handleDownloadReport = async () => {
    setIsDownloading(true);
    try {
      await forensicAPI.downloadReport(jobId, {
        include_custody: includeCustody,
        include_scans: includeScans,
        include_vulnerabilities: includeVulns,
        include_correlation: includeCorrelation
      });
    } catch (err) {
      alert("Failed to download PDF report.");
      console.error(err);
    } finally {
      setIsDownloading(false);
    }
  };

  if (isJobLoading) {
    return <LoadingSpinner text="Fetching forensic evidence details..." />;
  }

  if (error || !job) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#ef4444' }}>
        <FaExclamationTriangle size={50} />
        <h2>Evidence Not Found</h2>
        <p>{error?.message || 'Access Denied — you are not the owner of this evidence'}</p>
      </div>
    );
  }

  return (
    <PageContainer>
      <HeaderArea>
        <TitleContainer>
          <Title>
            <FaFingerprint /> Evidence details
          </Title>
          <JobIdBadge>{job.job_id}</JobIdBadge>
          <LockBadge isEncrypted={job.is_encrypted}>
            {job.is_encrypted ? (
              <>
                <FaLock /> Secured (AES-256)
              </>
            ) : (
              <>
                <FaUnlock /> Plaintext
              </>
            )}
          </LockBadge>
        </TitleContainer>

        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ 
            color: job.integrity_status === 'VERIFIED' ? '#10b981' : '#ef4444',
            fontWeight: 'bold',
            fontSize: '0.875rem'
          }}>
            {job.integrity_status === 'VERIFIED' ? '✓ INTEGRITY VERIFIED' : '✗ COMPROMISED'}
          </span>
          <span style={{ 
            color: job.status === 'completed' ? '#10b981' : '#f59e0b',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            fontSize: '0.875rem'
          }}>
            {job.status}
          </span>
        </div>
      </HeaderArea>

      {/* Tabs */}
      <TabsHeader>
        <TabButton active={activeTab === 'metadata'} onClick={() => setActiveTab('metadata')}>
          <FaFileAlt /> Evidence Info
        </TabButton>
        <TabButton active={activeTab === 'scans'} onClick={() => setActiveTab('scans')}>
          <FaSearch /> Scanner & Vulns
        </TabButton>
        <TabButton active={activeTab === 'correlation'} onClick={() => setActiveTab('correlation')}>
          <FaShieldAlt /> Security Correlation
        </TabButton>
      </TabsHeader>

      <TabContent>
        {activeTab === 'metadata' && (
          <>
            {/* Hashing Integrity Badges */}
            <SHA256Display hash={job.metadata?.sha256_hash} jobId={job.job_id} integrityStatus={job.integrity_status} />

            <MetadataGrid>
              <Card>
                <CardHeader>
                  <FaFileAlt /> File Info
                </CardHeader>
                <MetadataList>
                  <MetadataItem>
                    <MetadataLabel>Filename</MetadataLabel>
                    <MetadataValue mono>{job.metadata?.file_name || 'N/A'}</MetadataValue>
                  </MetadataItem>
                  <MetadataItem>
                    <MetadataLabel>File Size</MetadataLabel>
                    <MetadataValue>
                      {job.metadata?.file_size ? `${(job.metadata.file_size / (1024 * 1024)).toFixed(2)} MB` : 'N/A'}
                    </MetadataValue>
                  </MetadataItem>
                  <MetadataItem>
                    <MetadataLabel>MIME Type</MetadataLabel>
                    <MetadataValue mono>{job.metadata?.mime_type || 'N/A'}</MetadataValue>
                  </MetadataItem>
                  <MetadataItem>
                    <MetadataLabel>Evidence Acquisition</MetadataLabel>
                    <MetadataValue>
                      {job.source === 'url' ? (
                        <>
                          <FaGlobe /> URL Ingestion
                        </>
                      ) : (
                        <>
                          <FaUpload /> Local Upload
                        </>
                      )}
                    </MetadataValue>
                  </MetadataItem>
                </MetadataList>
              </Card>

              <Card>
                <CardHeader>
                  <FaDownload /> Customized PDF Report Export
                </CardHeader>
                <CustomPdfBox>
                  <CheckboxLabel>
                    <input 
                      type="checkbox" 
                      checked={includeCustody} 
                      onChange={(e) => setIncludeCustody(e.target.checked)} 
                    />
                    Include Chain of Custody Logs
                  </CheckboxLabel>
                  <CheckboxLabel>
                    <input 
                      type="checkbox" 
                      checked={includeScans} 
                      onChange={(e) => setIncludeScans(e.target.checked)} 
                    />
                    Include Network Scanner Results
                  </CheckboxLabel>
                  <CheckboxLabel>
                    <input 
                      type="checkbox" 
                      checked={includeVulns} 
                      onChange={(e) => setIncludeVulns(e.target.checked)} 
                    />
                    Include CVE Vulnerability Mappings
                  </CheckboxLabel>
                  <CheckboxLabel>
                    <input 
                      type="checkbox" 
                      checked={includeCorrelation} 
                      onChange={(e) => setIncludeCorrelation(e.target.checked)} 
                    />
                    Include Security Correlation Analysis
                  </CheckboxLabel>
                </CustomPdfBox>
                <PrimaryButton onClick={handleDownloadReport} disabled={isDownloading || job.status !== 'completed'}>
                  {isDownloading ? <Spinner /> : <FaDownload />}
                  Export Forensic PDF Report
                </PrimaryButton>
              </Card>
            </MetadataGrid>

            {/* Chain of Custody Event Logs */}
            <Card>
              <CardHeader>
                <FaHistory /> Chain of Custody Logs
              </CardHeader>
              {job.chain_of_custody && job.chain_of_custody.length > 0 ? (
                <TimelineContainer>
                  {job.chain_of_custody.map((log, index) => {
                    const lType = log.event.toLowerCase();
                    const isAlert = lType.includes('compromised') || lType.includes('failed') || lType.includes('unauth');
                    const isSuccess = lType.includes('success') || lType.includes('verified') || lType.includes('completed');
                    
                    return (
                      <TimelineEvent key={index}>
                        <TimelineDot type={isAlert ? 'compromised' : isSuccess ? 'success' : 'custody'} />
                        <EventHeader>
                          <span>{format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss UTC')}</span>
                          <span>Investigator: {log.investigator_id}</span>
                        </EventHeader>
                        <EventTitle>{log.event}</EventTitle>
                        {log.details && (
                          <EventDetails>
                            {typeof log.details === 'object' 
                              ? Object.entries(log.details).map(([k, v]) => <div key={k}><strong>{k}:</strong> {String(v)}</div>)
                              : log.details
                            }
                          </EventDetails>
                        )}
                      </TimelineEvent>
                    );
                  })}
                </TimelineContainer>
              ) : (
                <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No chain of custody entries.</div>
              )}
            </Card>

            <ActionButtons>
              <VerifyIntegrityButton jobId={job.job_id} />
            </ActionButtons>
          </>
        )}

        {activeTab === 'scans' && (
          <>
            <Card>
              <CardHeader>
                <FaSearch /> Associated Scan History
              </CardHeader>
              {scans && scans.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {scans.map(scan => (
                    <div key={scan.scan_id} style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <strong>Target: {scan.target}</strong>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          Scan #{scan.scan_id} ({scan.status})
                        </span>
                      </div>
                      
                      {scan.status === 'completed' && scan.result?.hosts?.map((host, hIdx) => (
                        <div key={hIdx} style={{ background: 'var(--body-background)', border: '1px solid var(--card-border)', borderRadius: '8px', padding: '0.75rem', marginTop: '0.5rem' }}>
                          <div><strong>IP:</strong> {host.ip} | <strong>Hostname:</strong> {host.hostname || 'N/A'} | <strong>OS:</strong> {host.os_detection || 'Unknown'}</div>
                          
                          {host.ports && host.ports.length > 0 ? (
                            <table style={{ width: '100%', marginTop: '0.5rem', fontSize: '0.8rem' }}>
                              <thead>
                                <tr style={{ borderBottom: '1px solid var(--card-border)', textAlign: 'left' }}>
                                  <th>Port</th>
                                  <th>Protocol</th>
                                  <th>State</th>
                                  <th>Service</th>
                                  <th>Version</th>
                                </tr>
                              </thead>
                              <tbody>
                                {host.ports.map((p, pIdx) => (
                                  <tr key={pIdx}>
                                    <td>{p.port}</td>
                                    <td>{p.protocol}</td>
                                    <td>{p.state}</td>
                                    <td>{p.service}</td>
                                    <td>{p.version}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          ) : (
                            <div style={{ fontStyle: 'italic', fontSize: '0.8rem', marginTop: '0.25rem' }}>No open ports.</div>
                          )}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', textAlign: 'center', padding: '1rem' }}>
                  No scans associated with this job yet. Run a scan in the Network Scanner tab.
                </div>
              )}
            </Card>

            <Card>
              <CardHeader>
                <FaBug /> Vulnerabilities Mapped ({vulnerabilities?.length || 0})
              </CardHeader>
              {vulnerabilities && vulnerabilities.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {vulnerabilities.map(v => (
                    <div key={v.id} style={{ background: 'var(--body-background)', border: '1px solid var(--card-border)', borderRadius: '8px', padding: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                        <strong>{v.cve_id} ({v.port}/{v.service})</strong>
                        <span style={{ fontWeight: 'bold' }}>{v.severity} (CVSS {v.cvss_score})</span>
                      </div>
                      <div style={{ fontSize: '0.85rem' }}>{v.description}</div>
                      {v.nvd_url && (
                        <a href={v.nvd_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem', color: 'var(--primary)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.5rem', textDecoration: 'none' }}>
                          View in NVD <FaExternalLinkAlt style={{ fontSize: '0.65rem' }} />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', textAlign: 'center', padding: '1rem' }}>
                  No vulnerabilities mapped.
                </div>
              )}
            </Card>
          </>
        )}

        {activeTab === 'correlation' && (
          <>
            {isCorrLoading ? (
              <Spinner style={{ fontSize: '2rem', margin: '4rem auto', display: 'block' }} />
            ) : correlation ? (
              <>
                <Card>
                  <CardHeader>
                    <FaShieldAlt /> Correlation Analysis Summary
                  </CardHeader>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <strong>Case Risk Score: {correlation.result_json?.score} / 100</strong>
                      <RiskScoreMeter style={{ marginTop: '0.5rem' }}>
                        <RiskScoreFill score={correlation.result_json?.score} />
                      </RiskScoreMeter>
                    </div>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <strong>High Risk Flags Detected:</strong>
                      {correlation.result_json?.flags && correlation.result_json.flags.length > 0 ? (
                        correlation.result_json.flags.map((flag, idx) => (
                          <FlagCard key={idx} severity={flag.severity}>
                            <FaExclamationTriangle style={{ marginTop: '0.15rem' }} />
                            <div>
                              <strong>{flag.title}</strong>
                              <div>{flag.description}</div>
                            </div>
                          </FlagCard>
                        ))
                      ) : (
                        <div style={{ color: '#10b981', fontWeight: 600 }}>✓ No system warning flags.</div>
                      )}
                    </div>
                  </div>
                </Card>

                <Card>
                  <CardHeader>
                    <FaBug /> Generated Attack Hypotheses
                  </CardHeader>
                  {correlation.result_json?.attack_hypotheses && correlation.result_json.attack_hypotheses.length > 0 ? (
                    <HypothesesList>
                      {correlation.result_json.attack_hypotheses.map((h, idx) => (
                        <HypothesisItem key={idx} prob={h.probability}>
                          <strong>Hypothesis #{idx+1}: {h.scenario}</strong> (Probability: {h.probability})
                          <p style={{ fontSize: '0.875rem', marginTop: '0.25rem', color: 'var(--text-secondary)' }}>
                            {h.description}
                          </p>
                        </HypothesisItem>
                      ))}
                    </HypothesesList>
                  ) : (
                    <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No attack paths hypothesized. No vulnerabilities were detected on target services.</div>
                  )}
                </Card>

                <Card>
                  <CardHeader>
                    <FaClock /> Unified Incident Timeline
                  </CardHeader>
                  {correlation.result_json?.timeline && correlation.result_json.timeline.length > 0 ? (
                    <TimelineContainer>
                      {correlation.result_json.timeline.map((item, index) => {
                        const isAlert = item.event.includes('COMPROMISED') || item.event.includes('FAILED') || item.event.includes('ATTEMPT');
                        const isSuccess = item.event.includes('VERIFIED') || item.event.includes('COMPLETED') || item.event.includes('STORED');
                        
                        return (
                          <TimelineEvent key={index}>
                            <TimelineDot type={isAlert ? 'compromised' : isSuccess ? 'success' : 'custody'} />
                            <EventHeader>
                              <span>{format(new Date(item.timestamp), 'yyyy-MM-dd HH:mm:ss UTC')}</span>
                              <span>Actor: {item.investigator_id}</span>
                            </EventHeader>
                            <EventTitle>{item.event}</EventTitle>
                            {item.details && (
                              <EventDetails>
                                {typeof item.details === 'object'
                                  ? Object.entries(item.details).map(([k, v]) => <div key={k}><strong>{k}:</strong> {String(v)}</div>)
                                  : item.details
                                }
                              </EventDetails>
                            )}
                          </TimelineEvent>
                        );
                      })}
                    </TimelineContainer>
                  ) : (
                    <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No events recorded.</div>
                  )}
                </Card>
                
                <ActionButtons>
                  <PrimaryButton 
                    onClick={() => runCorrelationMutation.mutate()} 
                    disabled={runCorrelationMutation.isLoading}
                  >
                    {runCorrelationMutation.isLoading ? <Spinner /> : <FaCogs />}
                    Re-Run Correlation Engine
                  </PrimaryButton>
                </ActionButtons>
              </>
            ) : (
              <Card style={{ alignItems: 'center', padding: '3rem', textAlign: 'center' }}>
                <FaCogs style={{ fontSize: '3rem', opacity: 0.3 }} />
                <h3>Correlation Engine Not Run</h3>
                <p>Run the correlation engine to build the unified incident timeline, calculate case risk score, and generate attack hypotheses.</p>
                <PrimaryButton 
                  onClick={() => runCorrelationMutation.mutate()} 
                  disabled={runCorrelationMutation.isLoading}
                  style={{ marginTop: '1rem' }}
                >
                  {runCorrelationMutation.isLoading ? <Spinner /> : <FaPlay />}
                  Run Correlation Analysis
                </PrimaryButton>
              </Card>
            )}
          </>
        )}
      </TabContent>
    </PageContainer>
  );
};

export default EvidenceDetailPage;
