import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const getDevices = () => api.get('/api/devices/');
export const discoverDevices = (count = 5) => api.post(`/api/devices/discover?count=${count}`);
export const getDashboard = () => api.get('/api/risks/dashboard');
export const getRisks = (params) => api.get('/api/risks/', { params });
export const getHeatmap = () => api.get('/api/risks/heatmap');
export const runScan = () => api.post('/api/risks/scan');
export const getAlerts = () => api.get('/api/risks/alerts');
export const acknowledgeAlert = (id) => api.put(`/api/risks/alerts/${id}/acknowledge`);
export const getMLStatus = () => api.get('/api/ml/status');
export const trainModels = () => api.post('/api/ml/train');
export const executeTreatment = (data) => api.post('/api/treatment/execute', data);
export const getAuditLog = () => api.get('/api/treatment/audit-log');
export const downloadReport = () => api.get('/api/reports/pdf', { responseType: 'blob' });

export default api;
