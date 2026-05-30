import axios from 'axios';

// FIX: Point to correct backend port
const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const authData = localStorage.getItem('auth-storage');
  if (authData) {
    try {
      const { state } = JSON.parse(authData);
      if (state?.token) {
        config.headers.Authorization = `Bearer ${state.token}`;
      }
    } catch (e) {
      console.error('Error parsing auth token:', e);
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response || error.message);
    if (error.message === 'Network Error') {
        alert("Cannot connect to server. Is Backend running on port 8000?");
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  register: (data) => api.post('/auth/register', data),
  
  getCurrentUser: () => api.get('/auth/me'),
  
  logout: () => api.post('/auth/logout'),
};

export const profileAPI = {
  getProfile: () => api.get('/profile/'),
  updateProfile: (data) => api.patch('/profile/', data),
};

export const forensicAPI = {
  submitURLJob: (data) => api.post('/jobs/url', data),
  
  // FIX: Explicitly set multipart header
  submitUploadJob: (formData) => api.post('/jobs/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  getAllJobs: () => api.get('/jobs'),
  getJobStatus: (id) => api.get(`/jobs/${id}/status`),
  getJobDetails: (id) => api.get(`/jobs/${id}/details`),
  verifyIntegrity: (id) => api.post(`/jobs/${id}/verify`),
  getAnalytics: (period) => api.get(`/analytics?period=${period}`),
  
  downloadReport: async (jobId, options = {}) => {
    const {
      include_custody = true,
      include_scans = true,
      include_vulnerabilities = true,
      include_correlation = true
    } = options;
    
    // Retrieve the authorization token from localStorage if available
    const authData = localStorage.getItem('auth-storage');
    let headers = {};
    if (authData) {
      try {
        const { state } = JSON.parse(authData);
        if (state?.token) {
          headers.Authorization = `Bearer ${state.token}`;
        }
      } catch (e) {
        console.error('Error parsing auth token for custom download:', e);
      }
    }

    const response = await axios.get(
      `${API_BASE_URL}/jobs/${jobId}/report?include_custody=${include_custody}&include_scans=${include_scans}&include_vulnerabilities=${include_vulnerabilities}&include_correlation=${include_correlation}`,
      {
        responseType: 'blob',
        headers
      }
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Forensic_Report_${jobId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Scanner APIs
  startScan: (target, jobId, investigatorId) => api.post('/scanner/scan', { 
    target, 
    job_id: jobId, 
    investigator_id: investigatorId 
  }),
  getScanStatus: (scanId) => api.get(`/scanner/scan/${scanId}`),
  getJobScans: (jobId) => api.get(`/scanner/scans?job_id=${jobId}`),
  getScanVulnerabilities: (scanId) => api.get(`/scanner/scan/${scanId}/vulnerabilities`),
  getJobVulnerabilities: (jobId) => api.get(`/scanner/vulnerabilities?job_id=${jobId}`),

  // Correlation APIs
  runCorrelationAnalysis: (jobId, investigatorId) => api.post('/correlation/analyze', { 
    job_id: jobId, 
    investigator_id: investigatorId 
  }),
  getCorrelationReport: (jobId) => api.get(`/correlation/${jobId}`)
};

// Recon APIs (Red Team Intelligence Module)
export const reconAPI = {
  dnsRecon: (target, jobId) => api.post('/recon/dns', { target, job_id: jobId }),
  whoisLookup: (target, jobId) => api.post('/recon/whois', { target, job_id: jobId }),
  subdomainEnum: (target, jobId) => api.post('/recon/subdomains', { target, job_id: jobId }),
  headerAnalysis: (target, jobId) => api.post('/recon/headers', { target, job_id: jobId }),
  sslInspection: (hostname, port, jobId) => api.post('/recon/ssl', { hostname, port: port || 443, job_id: jobId }),
  geoipLookup: (target, jobId) => api.get(`/recon/geoip/${encodeURIComponent(target)}${jobId ? `?job_id=${jobId}` : ''}`),
  threatIntelLookup: (ioc, jobId, abuseipdb_key, vt_key) => api.post('/recon/threat-intel', { 
    ioc, job_id: jobId, abuseipdb_key: abuseipdb_key || null, vt_key: vt_key || null 
  }),
  getHistory: (reconType, limit) => api.get(`/recon/history${reconType ? `?recon_type=${reconType}` : ''}${limit ? `&limit=${limit}` : ''}`),
};

export default api;