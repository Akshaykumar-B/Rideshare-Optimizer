import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const login = (email, password) => api.post('/auth/login', { email, password });
export const register = (data) => api.post('/auth/register', data);
export const firebaseLogin = (token) => api.post('/auth/firebase-login', { token });
export const getMe = () => api.get('/auth/me');

// Admin
export const promoteToDriver = (userId) => api.put(`/admin/promote/${userId}`);
export const demoteToRider = (userId) => api.put(`/admin/demote/${userId}`);
export const getUsers = () => api.get('/admin/users');

// Rides
export const createRideRequest = (data) => api.post('/rides/request', data);
export const getMyRequests = () => api.get('/rides/my-requests');
export const cancelRide = (id) => api.put(`/rides/${id}/cancel`);

// Drivers
export const updateDriverLocation = (lat, lng) => api.put('/drivers/location', { lat, lng });
export const toggleAvailability = (isAvailable) => api.put('/drivers/availability', { is_available: isAvailable });
export const getCurrentTrip = () => api.get('/drivers/current-trip');

// Analytics
export const runComparison = (data) => api.post('/analytics/compare', data);
export const getHeatmap = () => api.get('/analytics/heatmap');
export const getCarbonSummary = () => api.get('/analytics/carbon-summary');

// Surge
export const getSurgeStatus = (lat, lng) => api.get(`/surge/status?lat=${lat}&lng=${lng}`);

// Demo
export const getScenarios = () => api.get('/demo/scenarios');
export const loadScenario = (scenario) => api.post('/demo/load', { scenario });
export const seedDemo = () => api.post('/demo/seed');
export const resetDemo = () => api.post('/demo/reset');

// Trips
export const getTrip = (id) => api.get(`/trips/${id}`);
export const completeTrip = (id) => api.put(`/trips/${id}/complete`);

export default api;
