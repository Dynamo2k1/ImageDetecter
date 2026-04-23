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
  runNetworkScan: (data) => api.post('/scans/network', data),
  getAnalytics: (period) => api.get(`/analytics?period=${period}`),
  
  downloadReport: async (jobId) => {
    const response = await axios.get(`${API_BASE_URL}/jobs/${jobId}/report`, {
        responseType: 'blob'
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Forensic_Report_${jobId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};

export default api;
