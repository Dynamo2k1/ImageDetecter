import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import {
  FaSearch, FaSpinner, FaGlobe, FaServer, FaShieldAlt,
  FaNetworkWired, FaCertificate, FaMapMarkerAlt, FaList,
  FaCheckCircle, FaExclamationTriangle, FaTimesCircle,
  FaChevronDown, FaChevronUp, FaCopy, FaInfoCircle
} from 'react-icons/fa';
import { reconAPI } from '../services/api';

// ─── Animations ──────────────────────────────────────────────────────────────
const fadeIn = keyframes`from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); }`;
const spin = keyframes`from { transform: rotate(0deg); } to { transform: rotate(360deg); }`;
const pulse = keyframes`0%, 100% { opacity: 1; } 50% { opacity: 0.5; }`;
const scanLine = keyframes`0% { left: -100%; } 100% { left: 100%; }`;

// ─── Layout ───────────────────────────────────────────────────────────────────
const Page = styled.div`max-width: 1300px; margin: 0 auto; padding: 1rem 0; animation: ${fadeIn} 0.4s ease;`;

const Header = styled.div`margin-bottom: 2rem;`;
const Title = styled.h1`
  font-size: 2rem; font-weight: 800; margin-bottom: 0.4rem;
  display: flex; align-items: center; gap: 0.75rem;
  color: ${({ theme }) => theme.text};
  span { color: ${({ theme }) => theme.primary}; }
`;
const Subtitle = styled.p`color: ${({ theme }) => theme.textSecondary}; font-size: 0.95rem; margin: 0;`;

const TwoCol = styled.div`
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 1.75rem;
  @media (max-width: 1000px) { grid-template-columns: 1fr; }
`;

const Card = styled.div`
  background: ${({ theme }) => theme.cardBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 14px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
`;

const CardTitle = styled.h2`
  font-size: 1rem; font-weight: 700;
  color: ${({ theme }) => theme.text};
  display: flex; align-items: center; gap: 0.5rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder};
`;

// ─── Tool Tabs ─────────────────────────────────────────────────────────────────
const ToolGrid = styled.div`display: flex; flex-direction: column; gap: 0.5rem;`;

const ToolBtn = styled.button`
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  border: 1px solid ${({ active, theme }) => active ? theme.primary : theme.cardBorder};
  background: ${({ active, theme }) => active ? `${theme.primary}18` : 'transparent'};
  color: ${({ active, theme }) => active ? theme.primary : theme.textSecondary};
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: ${({ active }) => active ? '600' : '400'};
  text-align: left;
  transition: all 0.2s;
  &:hover { border-color: ${({ theme }) => theme.primary}; color: ${({ theme }) => theme.primary}; background: ${({ theme }) => theme.primary}12; }
  svg { flex-shrink: 0; }
`;

const ToolBadge = styled.span`
  margin-left: auto;
  font-size: 0.7rem;
  padding: 2px 7px;
  border-radius: 20px;
  background: ${({ type }) => ({
    passive: '#10b98120', active: '#f59e0b20', intel: '#8b5cf620'
  }[type] || '#6b728020')};
  color: ${({ type }) => ({
    passive: '#10b981', active: '#f59e0b', intel: '#8b5cf6'
  }[type] || '#6b7280')};
`;

// ─── Input Area ────────────────────────────────────────────────────────────────
const InputGroup = styled.div`display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1rem;`;
const Label = styled.label`font-size: 0.8rem; font-weight: 600; color: ${({ theme }) => theme.textSecondary}; text-transform: uppercase; letter-spacing: 0.05em;`;
const Input = styled.input`
  width: 100%;
  padding: 0.7rem 1rem;
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.cardBorder};
  background: ${({ theme }) => theme.background};
  color: ${({ theme }) => theme.text};
  font-size: 0.95rem;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
  &:focus { border-color: ${({ theme }) => theme.primary}; }
`;
const RunBtn = styled.button`
  width: 100%;
  padding: 0.8rem;
  border-radius: 10px;
  border: none;
  background: ${({ theme }) => theme.primary};
  color: white;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  transition: all 0.2s;
  opacity: ${({ disabled }) => disabled ? 0.6 : 1};
  &:hover:not(:disabled) { filter: brightness(1.1); transform: translateY(-1px); }
  &:active:not(:disabled) { transform: translateY(0); }
`;

// ─── Result Panel ─────────────────────────────────────────────────────────────
const ResultArea = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  animation: ${fadeIn} 0.3s ease;
`;

const EmptyState = styled.div`
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 4rem 2rem; gap: 1rem;
  color: ${({ theme }) => theme.textSecondary};
  text-align: center;
  svg { font-size: 3rem; opacity: 0.3; }
  h3 { font-size: 1.1rem; margin: 0; color: ${({ theme }) => theme.text}; }
  p { margin: 0; font-size: 0.9rem; }
`;

const Loader = styled.div`
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 1rem; padding: 4rem 2rem;
  color: ${({ theme }) => theme.primary};
  svg { animation: ${spin} 1s linear infinite; font-size: 2rem; }
  p { margin: 0; animation: ${pulse} 1.5s ease infinite; color: ${({ theme }) => theme.textSecondary}; }
`;

// ─── Result Display Components ─────────────────────────────────────────────────
const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
`;

const SummaryCard = styled.div`
  background: ${({ theme }) => theme.background};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
`;

const SummaryValue = styled.div`
  font-size: 1.75rem;
  font-weight: 800;
  color: ${({ color }) => color || 'inherit'};
  margin-bottom: 0.25rem;
`;

const SummaryLabel = styled.div`
  font-size: 0.75rem;
  color: ${({ theme }) => theme.textSecondary};
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;

const Section = styled.div``;
const SectionTitle = styled.h3`
  font-size: 0.85rem; font-weight: 700;
  color: ${({ theme }) => theme.textSecondary};
  text-transform: uppercase; letter-spacing: 0.07em;
  margin: 0 0 0.75rem 0;
`;

const Table = styled.table`width: 100%; border-collapse: collapse; font-size: 0.88rem;`;
const Th = styled.th`text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid ${({ theme }) => theme.cardBorder}; color: ${({ theme }) => theme.textSecondary}; font-weight: 600; font-size: 0.78rem; text-transform: uppercase;`;
const Td = styled.td`padding: 0.5rem 0.75rem; border-bottom: 1px solid ${({ theme }) => theme.cardBorder}30; color: ${({ theme }) => theme.text}; word-break: break-all;`;
const Tr = styled.tr`&:hover { background: ${({ theme }) => theme.primary}08; }`;

const Badge = styled.span`
  display: inline-flex; align-items: center;
  padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600;
  background: ${({ color }) => `${color}20`};
  color: ${({ color }) => color};
`;

const GradeCircle = styled.div`
  width: 80px; height: 80px;
  border-radius: 50%;
  border: 4px solid ${({ grade }) => ({
    A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#ef4444', F: '#dc2626'
  }[grade] || '#6b7280')};
  display: flex; align-items: center; justify-content: center;
  font-size: 2rem; font-weight: 900;
  color: ${({ grade }) => ({ A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#ef4444', F: '#dc2626' }[grade] || '#6b7280')};
  margin: 0 auto 1rem;
`;

const IssueItem = styled.div`
  display: flex; align-items: flex-start; gap: 0.75rem;
  padding: 0.75rem; border-radius: 8px;
  background: ${({ sev }) => ({
    Critical: '#dc262610', High: '#ef444410', Medium: '#f59e0b10', Low: '#3b82f610', Informational: '#6b728010'
  }[sev] || '#6b728010')};
  margin-bottom: 0.5rem;
`;

const IssueText = styled.div``;
const IssueTitle = styled.div`font-size: 0.88rem; font-weight: 600; color: ${({ theme }) => theme.text};`;
const IssueDetail = styled.div`font-size: 0.8rem; color: ${({ theme }) => theme.textSecondary}; margin-top: 2px;`;

const sevColor = (sev) => ({ Critical: '#dc2626', High: '#ef4444', Medium: '#f59e0b', Low: '#3b82f6', Informational: '#6b7280' }[sev] || '#6b7280');

const InfoRow = styled.div`
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder}40;
  font-size: 0.88rem;
  &:last-child { border-bottom: none; }
`;
const InfoKey = styled.span`color: ${({ theme }) => theme.textSecondary}; font-weight: 500;`;
const InfoVal = styled.span`color: ${({ theme }) => theme.text}; font-weight: 600; text-align: right; max-width: 60%; word-break: break-all;`;

const RiskGauge = styled.div`
  position: relative;
  width: 100%; height: 8px;
  background: ${({ theme }) => theme.cardBorder};
  border-radius: 8px;
  overflow: hidden;
  margin: 0.5rem 0;
`;
const RiskFill = styled.div`
  height: 100%;
  width: ${({ score }) => score}%;
  background: ${({ score }) => score >= 75 ? '#dc2626' : score >= 35 ? '#f59e0b' : '#10b981'};
  border-radius: 8px;
  transition: width 0.8s ease;
`;

const VerdictBanner = styled.div`
  padding: 1rem 1.5rem;
  border-radius: 12px;
  background: ${({ verdict }) => ({
    Malicious: '#dc262612', Suspicious: '#f59e0b12', Clean: '#10b98112'
  }[verdict] || '#6b728012')};
  border: 1px solid ${({ verdict }) => ({
    Malicious: '#dc262640', Suspicious: '#f59e0b40', Clean: '#10b98140'
  }[verdict] || '#6b728040')};
  display: flex; align-items: center; gap: 1rem;
`;

const VerdictIcon = styled.div`
  font-size: 2rem;
  color: ${({ verdict }) => ({ Malicious: '#dc2626', Suspicious: '#f59e0b', Clean: '#10b981' }[verdict] || '#6b7280')};
`;

const VerdictText = styled.div``;
const VerdictTitle = styled.div`font-size: 1.1rem; font-weight: 800; color: ${({ theme }) => theme.text};`;
const VerdictSub = styled.div`font-size: 0.85rem; color: ${({ theme }) => theme.textSecondary};`;

const Mono = styled.code`
  font-family: 'Courier New', monospace;
  font-size: 0.82rem;
  background: ${({ theme }) => theme.background};
  padding: 2px 6px;
  border-radius: 4px;
`;

// ─── Tool Config ───────────────────────────────────────────────────────────────
const TOOLS = [
  { id: 'dns', label: 'DNS Recon', icon: <FaGlobe />, type: 'active', placeholder: 'e.g. example.com', desc: 'Query all DNS record types', inputLabel: 'Domain' },
  { id: 'whois', label: 'WHOIS Lookup', icon: <FaInfoCircle />, type: 'passive', placeholder: 'e.g. example.com', desc: 'Registration & expiry info', inputLabel: 'Domain' },
  { id: 'subdomains', label: 'Subdomain Enum', icon: <FaNetworkWired />, type: 'active', placeholder: 'e.g. example.com', desc: 'Brute-force discover subdomains', inputLabel: 'Domain' },
  { id: 'headers', label: 'HTTP Headers', icon: <FaShieldAlt />, type: 'active', placeholder: 'e.g. example.com', desc: 'Security header analysis', inputLabel: 'Domain / URL' },
  { id: 'ssl', label: 'SSL Inspector', icon: <FaCertificate />, type: 'active', placeholder: 'e.g. example.com', desc: 'TLS certificate & cipher analysis', inputLabel: 'Hostname' },
  { id: 'geoip', label: 'GeoIP Lookup', icon: <FaMapMarkerAlt />, type: 'passive', placeholder: 'e.g. 8.8.8.8', desc: 'Geographic & ASN info', inputLabel: 'IP / Domain' },
  { id: 'threat-intel', label: 'Threat Intel', icon: <FaServer />, type: 'intel', placeholder: 'IP, domain, or SHA256 hash', desc: 'IoC reputation lookup', inputLabel: 'IoC (IP / Domain / Hash)' },
];

// ─── Component ─────────────────────────────────────────────────────────────────
export default function ReconPage() {
  const [activeTool, setActiveTool] = useState('dns');
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const tool = TOOLS.find(t => t.id === activeTool);

  const handleRun = async () => {
    if (!target.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      let data;
      const t = target.trim();
      switch (activeTool) {
        case 'dns': data = await reconAPI.dnsRecon(t); break;
        case 'whois': data = await reconAPI.whoisLookup(t); break;
        case 'subdomains': data = await reconAPI.subdomainEnum(t); break;
        case 'headers': data = await reconAPI.headerAnalysis(t); break;
        case 'ssl': data = await reconAPI.sslInspection(t, 443); break;
        case 'geoip': data = await reconAPI.geoipLookup(t); break;
        case 'threat-intel': data = await reconAPI.threatIntelLookup(t); break;
        default: break;
      }
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter') handleRun(); };

  return (
    <Page>
      <Header>
        <Title><FaSearch /> Red Team <span>Recon</span></Title>
        <Subtitle>Passive & active reconnaissance tools for authorized penetration testing and forensic investigations.</Subtitle>
      </Header>

      <TwoCol>
        {/* ── Left: Tool Selector + Input ─────────────────────────── */}
        <div>
          <Card style={{ marginBottom: '1.25rem' }}>
            <CardTitle><FaList /> Recon Tools</CardTitle>
            <ToolGrid>
              {TOOLS.map(t => (
                <ToolBtn key={t.id} active={activeTool === t.id} onClick={() => { setActiveTool(t.id); setResult(null); setError(null); }}>
                  {t.icon}
                  <div>
                    <div>{t.label}</div>
                    <div style={{ fontSize: '0.72rem', opacity: 0.65 }}>{t.desc}</div>
                  </div>
                  <ToolBadge type={t.type}>{t.type}</ToolBadge>
                </ToolBtn>
              ))}
            </ToolGrid>
          </Card>

          <Card>
            <CardTitle>{tool?.icon} {tool?.label}</CardTitle>
            <InputGroup>
              <Label>{tool?.inputLabel}</Label>
              <Input
                id={`recon-input-${activeTool}`}
                placeholder={tool?.placeholder}
                value={target}
                onChange={e => setTarget(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </InputGroup>
            <RunBtn onClick={handleRun} disabled={loading || !target.trim()} id={`recon-run-${activeTool}`}>
              {loading ? <><FaSpinner style={{ animation: 'spin 1s linear infinite' }} /> Running...</> : <><FaSearch /> Run {tool?.label}</>}
            </RunBtn>
          </Card>
        </div>

        {/* ── Right: Results Panel ────────────────────────────────── */}
        <Card>
          {loading && (
            <Loader>
              <FaSpinner />
              <p>Running {tool?.label} on <strong>{target}</strong>...</p>
            </Loader>
          )}

          {!loading && error && (
            <EmptyState>
              <FaTimesCircle style={{ color: '#ef4444', opacity: 1 }} />
              <h3>Recon Failed</h3>
              <p style={{ color: '#ef4444' }}>{error}</p>
            </EmptyState>
          )}

          {!loading && !result && !error && (
            <EmptyState>
              {tool?.icon}
              <h3>{tool?.label}</h3>
              <p>Enter a {tool?.inputLabel?.toLowerCase()} and click Run to begin reconnaissance.</p>
            </EmptyState>
          )}

          {!loading && result && (
            <ResultArea>
              {/* DNS Results */}
              {activeTool === 'dns' && <DnsResult data={result} />}
              {/* WHOIS Results */}
              {activeTool === 'whois' && <WhoisResult data={result} />}
              {/* Subdomain Results */}
              {activeTool === 'subdomains' && <SubdomainResult data={result} />}
              {/* Header Results */}
              {activeTool === 'headers' && <HeaderResult data={result} />}
              {/* SSL Results */}
              {activeTool === 'ssl' && <SslResult data={result} />}
              {/* GeoIP Results */}
              {activeTool === 'geoip' && <GeoipResult data={result} />}
              {/* Threat Intel Results */}
              {activeTool === 'threat-intel' && <ThreatIntelResult data={result} />}
            </ResultArea>
          )}
        </Card>
      </TwoCol>
    </Page>
  );
}

// ─── DNS Result ────────────────────────────────────────────────────────────────
function DnsResult({ data }) {
  const s = data.summary;
  const recordColors = { A: '#3b82f6', AAAA: '#8b5cf6', MX: '#10b981', NS: '#f59e0b', TXT: '#6b7280', SOA: '#ec4899', CNAME: '#14b8a6' };

  return (
    <>
      <CardTitle><FaGlobe /> DNS Records — {data.domain}</CardTitle>
      <SummaryGrid>
        <SummaryCard><SummaryValue color="#3b82f6">{s.total_records_found}</SummaryValue><SummaryLabel>Total Records</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={s.has_ipv6 ? '#10b981' : '#6b7280'}>{s.has_ipv6 ? '✓' : '✗'}</SummaryValue><SummaryLabel>IPv6</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={s.has_spf_record ? '#10b981' : '#ef4444'}>{s.has_spf_record ? '✓' : '✗'}</SummaryValue><SummaryLabel>SPF</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={s.has_dmarc_record ? '#10b981' : '#ef4444'}>{s.has_dmarc_record ? '✓' : '✗'}</SummaryValue><SummaryLabel>DMARC</SummaryLabel></SummaryCard>
      </SummaryGrid>

      {Object.entries(data.records).map(([type, records]) => (
        records.length > 0 && (
          <Section key={type}>
            <SectionTitle><Badge color={recordColors[type] || '#6b7280'}>{type}</Badge></SectionTitle>
            <Table>
              <tbody>
                {records.map((r, i) => (
                  <Tr key={i}><Td><Mono>{r}</Mono></Td></Tr>
                ))}
              </tbody>
            </Table>
          </Section>
        )
      ))}

      {Object.keys(data.errors).length > 0 && (
        <Section>
          <SectionTitle>Errors</SectionTitle>
          {Object.entries(data.errors).map(([type, err]) => (
            <IssueItem key={type} sev="Low">
              <FaExclamationTriangle color="#f59e0b" />
              <IssueText>
                <IssueTitle>{type}: {err}</IssueTitle>
              </IssueText>
            </IssueItem>
          ))}
        </Section>
      )}
    </>
  );
}

// ─── WHOIS Result ──────────────────────────────────────────────────────────────
function WhoisResult({ data }) {
  if (data.error) return <EmptyState><FaTimesCircle style={{ color: '#ef4444', opacity: 1 }} /><h3>WHOIS Failed</h3><p>{data.error}</p></EmptyState>;
  return (
    <>
      <CardTitle><FaInfoCircle /> WHOIS — {data.domain}</CardTitle>
      <SummaryGrid>
        <SummaryCard><SummaryValue color="#3b82f6">{data.domain_age_days?.toLocaleString() ?? 'N/A'}</SummaryValue><SummaryLabel>Domain Age (days)</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={data.days_until_expiry > 30 ? '#10b981' : '#ef4444'}>{data.days_until_expiry ?? 'N/A'}</SummaryValue><SummaryLabel>Days until Expiry</SummaryLabel></SummaryCard>
      </SummaryGrid>
      <Section>
        <SectionTitle>Registration Info</SectionTitle>
        {[
          ['Registrar', data.registrar],
          ['Org', data.registrant_org],
          ['Country', data.registrant_country],
          ['Created', data.creation_date?.split('T')[0]],
          ['Expires', data.expiration_date?.split('T')[0]],
          ['Updated', data.updated_date?.split('T')[0]],
          ['DNSSEC', data.dnssec],
        ].map(([k, v]) => v && <InfoRow key={k}><InfoKey>{k}</InfoKey><InfoVal>{v}</InfoVal></InfoRow>)}
      </Section>
      {data.nameservers?.length > 0 && (
        <Section>
          <SectionTitle>Nameservers</SectionTitle>
          {data.nameservers.map(ns => <div key={ns} style={{ marginBottom: '4px' }}><Mono>{ns}</Mono></div>)}
        </Section>
      )}
      {data.emails?.length > 0 && (
        <Section>
          <SectionTitle>Contact Emails</SectionTitle>
          {data.emails.map(e => <div key={e} style={{ marginBottom: '4px' }}><Mono>{e}</Mono></div>)}
        </Section>
      )}
    </>
  );
}

// ─── Subdomain Result ──────────────────────────────────────────────────────────
function SubdomainResult({ data }) {
  return (
    <>
      <CardTitle><FaNetworkWired /> Subdomain Enum — {data.domain}</CardTitle>
      <SummaryGrid>
        <SummaryCard><SummaryValue color="#3b82f6">{data.words_checked}</SummaryValue><SummaryLabel>Words Checked</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={data.subdomains_found > 0 ? '#10b981' : '#6b7280'}>{data.subdomains_found}</SummaryValue><SummaryLabel>Subdomains Found</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color="#f59e0b">{data.elapsed_seconds}s</SummaryValue><SummaryLabel>Elapsed</SummaryLabel></SummaryCard>
      </SummaryGrid>
      {data.subdomains?.length > 0 ? (
        <Section>
          <SectionTitle>Discovered Subdomains</SectionTitle>
          <Table>
            <thead><Tr><Th>Subdomain</Th><Th>IP Addresses</Th></Tr></thead>
            <tbody>
              {data.subdomains.map(sub => (
                <Tr key={sub.subdomain}>
                  <Td><Mono>{sub.subdomain}</Mono></Td>
                  <Td>{sub.ips.join(', ')}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </Section>
      ) : (
        <EmptyState><FaGlobe /><h3>No Subdomains Found</h3><p>No subdomains resolved from the built-in wordlist.</p></EmptyState>
      )}
    </>
  );
}

// ─── HTTP Header Result ────────────────────────────────────────────────────────
function HeaderResult({ data }) {
  const gradeColors = { A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#ef4444', F: '#dc2626' };
  return (
    <>
      <CardTitle><FaShieldAlt /> HTTP Headers — {data.target}</CardTitle>
      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <GradeCircle grade={data.security_grade}>{data.security_grade}</GradeCircle>
        <SummaryGrid style={{ flex: 1 }}>
          <SummaryCard><SummaryValue color="#3b82f6">{data.status_code}</SummaryValue><SummaryLabel>HTTP Status</SummaryLabel></SummaryCard>
          <SummaryCard><SummaryValue color={data.used_https ? '#10b981' : '#ef4444'}>{data.used_https ? 'HTTPS' : 'HTTP'}</SummaryValue><SummaryLabel>Protocol</SummaryLabel></SummaryCard>
          <SummaryCard><SummaryValue color="#10b981">{data.summary.security_headers_present}</SummaryValue><SummaryLabel>Headers OK</SummaryLabel></SummaryCard>
          <SummaryCard><SummaryValue color="#ef4444">{data.summary.security_headers_missing}</SummaryValue><SummaryLabel>Missing</SummaryLabel></SummaryCard>
        </SummaryGrid>
      </div>
      {data.security_headers.missing.length > 0 && (
        <Section>
          <SectionTitle>Missing Security Headers</SectionTitle>
          {data.security_headers.missing.map(h => (
            <IssueItem key={h.header} sev={h.severity}>
              <FaExclamationTriangle color={sevColor(h.severity)} style={{ flexShrink: 0, marginTop: 2 }} />
              <IssueText>
                <IssueTitle>{h.header} <Badge color={sevColor(h.severity)}>{h.severity}</Badge></IssueTitle>
                <IssueDetail>{h.description}</IssueDetail>
              </IssueText>
            </IssueItem>
          ))}
        </Section>
      )}
      {data.security_headers.present.length > 0 && (
        <Section>
          <SectionTitle>Present Security Headers</SectionTitle>
          {data.security_headers.present.map(h => (
            <IssueItem key={h.header} sev="Clean" style={{ background: '#10b98110', borderColor: '#10b98140' }}>
              <FaCheckCircle color="#10b981" style={{ flexShrink: 0, marginTop: 2 }} />
              <IssueText>
                <IssueTitle>{h.header}</IssueTitle>
                <IssueDetail><Mono>{h.value.substring(0, 80)}{h.value.length > 80 ? '...' : ''}</Mono></IssueDetail>
              </IssueText>
            </IssueItem>
          ))}
        </Section>
      )}
      {data.sensitive_headers?.length > 0 && (
        <Section>
          <SectionTitle>⚠ Information Disclosure</SectionTitle>
          {data.sensitive_headers.map(h => (
            <InfoRow key={h.header}><InfoKey>{h.header}</InfoKey><InfoVal style={{ color: '#f59e0b' }}>{h.value}</InfoVal></InfoRow>
          ))}
        </Section>
      )}
    </>
  );
}

// ─── SSL Result ────────────────────────────────────────────────────────────────
function SslResult({ data }) {
  const cert = data.certificate;
  const ok = data.summary?.tls_ok;
  return (
    <>
      <CardTitle><FaCertificate /> SSL/TLS — {data.hostname}</CardTitle>
      {data.error && <IssueItem sev="Critical"><FaTimesCircle color="#dc2626" /><IssueText><IssueTitle>Connection Error</IssueTitle><IssueDetail>{data.error}</IssueDetail></IssueText></IssueItem>}
      {!data.error && (
        <>
          <SummaryGrid>
            <SummaryCard><SummaryValue color={ok ? '#10b981' : '#f59e0b'}>{data.tls_version || 'N/A'}</SummaryValue><SummaryLabel>TLS Version</SummaryLabel></SummaryCard>
            <SummaryCard><SummaryValue color={cert?.days_remaining > 30 ? '#10b981' : '#ef4444'}>{cert?.days_remaining ?? 'N/A'}</SummaryValue><SummaryLabel>Days Remaining</SummaryLabel></SummaryCard>
            <SummaryCard><SummaryValue color={data.cipher_suite?.is_weak ? '#ef4444' : '#10b981'}>{data.cipher_suite?.bits ?? 'N/A'}</SummaryValue><SummaryLabel>Key Bits</SummaryLabel></SummaryCard>
            <SummaryCard><SummaryValue color={data.issues?.length ? '#ef4444' : '#10b981'}>{data.issues?.length ?? 0}</SummaryValue><SummaryLabel>Issues</SummaryLabel></SummaryCard>
          </SummaryGrid>
          <Section>
            <SectionTitle>Certificate Details</SectionTitle>
            {[
              ['Subject CN', cert?.subject?.commonName],
              ['Issuer', cert?.issuer?.organizationName],
              ['Serial', cert?.serial_number],
              ['Valid From', cert?.not_before?.split('T')[0]],
              ['Valid Until', cert?.not_after?.split('T')[0]],
              ['Cipher', data.cipher_suite?.name],
            ].map(([k, v]) => v && <InfoRow key={k}><InfoKey>{k}</InfoKey><InfoVal><Mono>{v}</Mono></InfoVal></InfoRow>)}
          </Section>
          {cert?.subject_alt_names?.length > 0 && (
            <Section>
              <SectionTitle>Subject Alternative Names ({cert.subject_alt_names.length})</SectionTitle>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {cert.subject_alt_names.map(san => <Badge key={san} color="#3b82f6">{san}</Badge>)}
              </div>
            </Section>
          )}
          {data.issues?.length > 0 && (
            <Section>
              <SectionTitle>Issues</SectionTitle>
              {data.issues.map((iss, i) => (
                <IssueItem key={i} sev={iss.severity}>
                  <FaExclamationTriangle color={sevColor(iss.severity)} style={{ flexShrink: 0 }} />
                  <IssueText>
                    <IssueTitle>{iss.issue} <Badge color={sevColor(iss.severity)}>{iss.severity}</Badge></IssueTitle>
                    {iss.detail && <IssueDetail>{iss.detail}</IssueDetail>}
                  </IssueText>
                </IssueItem>
              ))}
            </Section>
          )}
        </>
      )}
    </>
  );
}

// ─── GeoIP Result ──────────────────────────────────────────────────────────────
function GeoipResult({ data }) {
  if (data.error) return <EmptyState><FaTimesCircle style={{ color: '#ef4444', opacity: 1 }} /><h3>GeoIP Failed</h3><p>{data.error}</p></EmptyState>;
  const d = data.data;
  return (
    <>
      <CardTitle><FaMapMarkerAlt /> GeoIP — {data.target}</CardTitle>
      <SummaryGrid>
        <SummaryCard><SummaryValue color="#3b82f6">{d?.country_code || 'N/A'}</SummaryValue><SummaryLabel>Country</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={d?.is_proxy ? '#ef4444' : '#10b981'}>{d?.is_proxy ? 'VPN/Proxy' : 'Direct'}</SummaryValue><SummaryLabel>Connection</SummaryLabel></SummaryCard>
        <SummaryCard><SummaryValue color={d?.is_hosting ? '#f59e0b' : '#10b981'}>{d?.is_hosting ? 'Datacenter' : 'Residential'}</SummaryValue><SummaryLabel>IP Type</SummaryLabel></SummaryCard>
      </SummaryGrid>
      <Section>
        <SectionTitle>Location & Network</SectionTitle>
        {[
          ['IP Address', d?.ip],
          ['Country', d?.country],
          ['Region', d?.region],
          ['City', d?.city],
          ['ZIP', d?.zip],
          ['Timezone', d?.timezone],
          ['ISP', d?.isp],
          ['Organization', d?.organization],
          ['ASN', d?.asn],
          ['ASN Name', d?.asn_name],
          ['Reverse DNS', d?.reverse_dns],
          ['Coordinates', d?.latitude && `${d?.latitude}, ${d?.longitude}`],
        ].map(([k, v]) => v && <InfoRow key={k}><InfoKey>{k}</InfoKey><InfoVal>{v}</InfoVal></InfoRow>)}
      </Section>
      {data.risk_flags?.length > 0 && (
        <Section>
          <SectionTitle>Risk Flags</SectionTitle>
          {data.risk_flags.map(f => (
            <IssueItem key={f} sev="Medium">
              <FaExclamationTriangle color="#f59e0b" />
              <IssueText><IssueTitle>{f}</IssueTitle></IssueText>
            </IssueItem>
          ))}
        </Section>
      )}
    </>
  );
}

// ─── Threat Intel Result ───────────────────────────────────────────────────────
function ThreatIntelResult({ data }) {
  const verdictIcon = { Malicious: <FaTimesCircle />, Suspicious: <FaExclamationTriangle />, Clean: <FaCheckCircle /> };
  return (
    <>
      <CardTitle><FaServer /> Threat Intel — <Mono>{data.ioc}</Mono></CardTitle>
      <VerdictBanner verdict={data.overall_verdict}>
        <VerdictIcon verdict={data.overall_verdict}>{verdictIcon[data.overall_verdict]}</VerdictIcon>
        <VerdictText>
          <VerdictTitle>{data.overall_verdict}</VerdictTitle>
          <VerdictSub>IoC Type: {data.ioc_type} · Risk Score: {data.risk_score}/100</VerdictSub>
        </VerdictText>
      </VerdictBanner>
      <Section>
        <SectionTitle>Risk Score</SectionTitle>
        <RiskGauge><RiskFill score={data.risk_score} /></RiskGauge>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280' }}>
          <span>0 — Clean</span><span>35 — Suspicious</span><span>75 — Malicious</span>
        </div>
      </Section>
      <Section>
        <SectionTitle>Intelligence Findings ({data.findings?.length})</SectionTitle>
        {data.findings?.map((f, i) => (
          <IssueItem key={i} sev={f.verdict === 'Malicious' ? 'High' : f.verdict === 'Suspicious' ? 'Medium' : 'Low'}>
            <div style={{ flexShrink: 0 }}>
              {f.verdict === 'Malicious' ? <FaTimesCircle color="#ef4444" /> :
               f.verdict === 'Suspicious' ? <FaExclamationTriangle color="#f59e0b" /> :
               <FaCheckCircle color="#10b981" />}
            </div>
            <IssueText>
              <IssueTitle>{f.source} — <Badge color={f.verdict === 'Malicious' ? '#ef4444' : f.verdict === 'Suspicious' ? '#f59e0b' : '#10b981'}>{f.verdict}</Badge></IssueTitle>
              {f.detail && <IssueDetail>{f.detail}</IssueDetail>}
            </IssueText>
          </IssueItem>
        ))}
      </Section>
      <Section>
        <SectionTitle>Sources</SectionTitle>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <Badge color="#3b82f6">FEAS Offline Feed</Badge>
          {data.online_sources_available?.abuseipdb && <Badge color="#10b981">AbuseIPDB</Badge>}
          {data.online_sources_available?.virustotal && <Badge color="#8b5cf6">VirusTotal</Badge>}
          {!data.online_sources_available?.abuseipdb && <Badge color="#6b7280">AbuseIPDB (no key)</Badge>}
          {!data.online_sources_available?.virustotal && <Badge color="#6b7280">VirusTotal (no key)</Badge>}
        </div>
      </Section>
    </>
  );
}
