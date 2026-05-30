import React, { useState } from 'react';
import styled from 'styled-components';
import { useQuery } from 'react-query';
import { 
  FaShieldAlt, 
  FaBug, 
  FaSearch, 
  FaFilter, 
  FaExternalLinkAlt, 
  FaSpinner, 
  FaChevronRight,
  FaFileCsv
} from 'react-icons/fa';
import { forensicAPI } from '../services/api';
import { Link } from 'react-router-dom';

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

const Card = styled.div`
  background: ${({ theme }) => theme.cardBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const ControlsRow = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
`;

const SearchContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: ${({ theme }) => theme.bodyBackground};
  border: 1px solid ${({ theme }) => theme.cardBorder};
  border-radius: 8px;
  padding: 0.5rem 1rem;
  flex: 1;
  max-width: 400px;
  min-width: 250px;
  
  svg {
    color: ${({ theme }) => theme.textSecondary};
  }
`;

const SearchInput = styled.input`
  border: none;
  background: transparent;
  color: ${({ theme }) => theme.text};
  font-size: 0.875rem;
  outline: none;
  width: 100%;
`;

const FiltersContainer = styled.div`
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
`;

const SelectFilter = styled.select`
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.cardBorder};
  background: ${({ theme }) => theme.bodyBackground};
  color: ${({ theme }) => theme.text};
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
  
  &:focus {
    border-color: ${({ theme }) => theme.primary};
  }
`;

const ExportButton = styled.button`
  background: ${({ theme }) => theme.primary}10;
  color: ${({ theme }) => theme.primary};
  border: 1px solid ${({ theme }) => theme.primary}30;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  
  &:hover {
    background: ${({ theme }) => theme.primary};
    color: white;
  }
`;

const TableContainer = styled.div`
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.cardBorder};
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  text-align: left;
`;

const Th = styled.th`
  padding: 1rem;
  background: ${({ theme }) => theme.bodyBackground};
  border-bottom: 2px solid ${({ theme }) => theme.cardBorder};
  color: ${({ theme }) => theme.textSecondary};
  font-weight: 600;
`;

const Td = styled.td`
  padding: 1rem;
  border-bottom: 1px solid ${({ theme }) => theme.cardBorder};
  color: ${({ theme }) => theme.text};
  vertical-align: middle;
`;

const Tr = styled.tr`
  transition: background 0.15s;
  
  &:hover {
    background: ${({ theme }) => theme.bodyBackground}50;
  }
`;

const SeverityBadge = styled.span`
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  text-transform: uppercase;
  
  ${({ level }) => {
    switch (level.toLowerCase()) {
      case 'critical':
        return `background: #fed7d7; color: #9b2c2c;`;
      case 'high':
        return `background: #feebc8; color: #c05621;`;
      case 'medium':
        return `background: #fefcbf; color: #744210;`;
      case 'low':
        return `background: #e2e8f0; color: #4a5568;`;
      default:
        return `background: #ebf8ff; color: #2b6cb0;`;
    }
  }}
`;

const JobLink = styled(Link)`
  color: ${({ theme }) => theme.primary};
  text-decoration: none;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  
  &:hover {
    text-decoration: underline;
  }
`;

const DescriptionCell = styled.div`
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.825rem;
  color: ${({ theme }) => theme.textSecondary};
`;

const NvdLink = styled.a`
  color: ${({ theme }) => theme.textSecondary};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  
  &:hover {
    color: ${({ theme }) => theme.primary};
  }
`;

const SpinnerContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4rem 0;
  font-size: 2rem;
  color: ${({ theme }) => theme.primary};
  
  svg {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const VulnerabilitiesPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');

  // Fetch all jobs to fetch vulnerabilities for each job
  const { data: jobs, isLoading: isJobsLoading } = useQuery('jobsList', forensicAPI.getAllJobs);

  // We can query vulnerabilities across all jobs
  // For safety and compatibility, we will fetch vulnerabilities for all completed jobs in parallel
  // using query options or a simple combine. However, we also added `GET /api/v1/scanner/vulnerabilities`
  // mapping across all scans of a job, or we can fetch them for all jobs.
  // Let's check which jobs have vulnerabilities.
  const completedJobs = jobs?.filter(j => j.status === 'completed') || [];

  const { data: allVulnerabilities, isLoading: isVulnsLoading } = useQuery(
    ['allVulnerabilities', completedJobs.map(j => j.job_id).join(',')],
    async () => {
      const allFindings = [];
      for (const job of completedJobs) {
        try {
          const findings = await forensicAPI.getJobVulnerabilities(job.job_id);
          // Attach job file/source context to each finding
          findings.forEach(f => {
            f.jobName = job.filename || `Evidence URL (${job.job_id.substring(0, 8)})`;
          });
          allFindings.push(...findings);
        } catch (e) {
          console.error(`Failed to load vulns for job ${job.job_id}:`, e);
        }
      }
      // Sort by CVSS Score desc
      return allFindings.sort((a, b) => (b.cvss_score || 0) - (a.cvss_score || 0));
    },
    { enabled: completedJobs.length > 0 }
  );

  const isLoading = isJobsLoading || isVulnsLoading;

  // Extract unique services for filtering dropdown
  const uniqueServices = Array.from(
    new Set(allVulnerabilities?.map(v => (v.service || '').toLowerCase()).filter(Boolean) || [])
  );

  // Filter vulnerabilities
  const filteredVulns = allVulnerabilities?.filter(v => {
    const matchesSearch = 
      (v.cve_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (v.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (v.jobName || '').toLowerCase().includes(searchTerm.toLowerCase());
      
    const matchesSeverity = !severityFilter || (v.severity || '').toLowerCase() === severityFilter.toLowerCase();
    const matchesService = !serviceFilter || (v.service || '').toLowerCase() === serviceFilter.toLowerCase();
    
    return matchesSearch && matchesSeverity && matchesService;
  }) || [];

  // Export to CSV helper
  const exportToCSV = () => {
    if (filteredVulns.length === 0) return;
    
    const headers = ['CVE ID', 'CVSS Score', 'Severity', 'Port', 'Service', 'Version', 'Job Reference', 'NVD URL', 'Description'];
    const rows = filteredVulns.map(v => [
      v.cve_id || 'N/A',
      v.cvss_score !== null ? v.cvss_score : 'N/A',
      v.severity || 'Unknown',
      v.port || 'N/A',
      v.service || 'N/A',
      v.version || 'N/A',
      v.jobName,
      v.nvd_url || '',
      `"${(v.description || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `FEAS_Vulnerability_Report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <PageContainer>
      <PageHeader>
        <PageTitle>
          <FaShieldAlt /> Global <span>Vulnerabilities</span> Dashboard
        </PageTitle>
        <PageSubtitle>
          Aggregated database of CVE vulnerability findings mapped across all digital evidence targets.
        </PageSubtitle>
      </PageHeader>

      <Card>
        <ControlsRow>
          <SearchContainer>
            <FaSearch />
            <SearchInput 
              type="text" 
              placeholder="Search by CVE, Description, or Job..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </SearchContainer>

          <FiltersContainer>
            <SelectFilter 
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <option value="">-- All Severities --</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFORMATIONAL">Info</option>
            </SelectFilter>

            <SelectFilter
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
            >
              <option value="">-- All Services --</option>
              {uniqueServices.map(svc => (
                <option key={svc} value={svc}>{svc.toUpperCase()}</option>
              ))}
            </SelectFilter>

            <ExportButton onClick={exportToCSV} disabled={filteredVulns.length === 0}>
              <FaFileCsv /> Export CSV
            </ExportButton>
          </FiltersContainer>
        </ControlsRow>

        {isLoading ? (
          <SpinnerContainer>
            <FaSpinner />
          </SpinnerContainer>
        ) : filteredVulns.length > 0 ? (
          <TableContainer>
            <Table>
              <thead>
                <tr>
                  <Th>CVE ID</Th>
                  <Th>CVSS</Th>
                  <Th>Severity</Th>
                  <Th>Target Port/Svc</Th>
                  <Th>Evidence Case Source</Th>
                  <Th>Description</Th>
                  <Th style={{ textAlign: 'center' }}>Details</Th>
                </tr>
              </thead>
              <tbody>
                {filteredVulns.map(v => (
                  <Tr key={v.id}>
                    <Td style={{ fontWeight: 600, color: 'var(--text)' }}>{v.cve_id}</Td>
                    <Td style={{ fontWeight: 600 }}>{v.cvss_score !== null ? v.cvss_score : 'N/A'}</Td>
                    <Td>
                      <SeverityBadge level={v.risk_level}>{v.severity}</SeverityBadge>
                    </Td>
                    <Td>
                      {v.port}/{v.service} {v.version && `(${v.version})`}
                    </Td>
                    <Td>
                      <JobLink to={`/evidence/${v.job_id}`}>
                        {v.jobName} <FaChevronRight style={{ fontSize: '0.6rem' }} />
                      </JobLink>
                    </Td>
                    <Td>
                      <DescriptionCell title={v.description}>{v.description}</DescriptionCell>
                    </Td>
                    <Td style={{ textAlign: 'center' }}>
                      {v.nvd_url ? (
                        <NvdLink href={v.nvd_url} target="_blank" rel="noopener noreferrer" title="View NVD CVE database">
                          <FaExternalLinkAlt />
                        </NvdLink>
                      ) : 'N/A'}
                    </Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </TableContainer>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
            No vulnerability mappings found matching active filter criteria.
          </div>
        )}
      </Card>
    </PageContainer>
  );
};

export default VulnerabilitiesPage;
