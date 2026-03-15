import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),

  setAuth: (user, token) => {
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('token', token);
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));

export const useAppStore = create((set) => ({
  // Comparison state
  scenarios: {},
  landmarks: {},
  selectedScenario: null,
  scenarioData: null,
  comparisonResult: null,
  isComparing: false,
  animationPhase: -1,

  setScenarios: (scenarios, landmarks) => set({ scenarios, landmarks }),
  setSelectedScenario: (scenario) => set({ selectedScenario: scenario }),
  setScenarioData: (data) => set({ scenarioData: data }),
  setComparisonResult: (result) => set({ comparisonResult: result, isComparing: false }),
  setIsComparing: (v) => set({ isComparing: v }),
  setAnimationPhase: (phase) => set({ animationPhase: phase }),

  // Ride requests
  rideRequests: [],
  setRideRequests: (rides) => set({ rideRequests: rides }),

  // Surge
  currentSurge: null,
  setCurrentSurge: (surge) => set({ currentSurge: surge }),

  // Carbon
  carbonSummary: null,
  setCarbonSummary: (summary) => set({ carbonSummary: summary }),

  // Heatmap zones
  heatmapZones: [],
  setHeatmapZones: (zones) => set({ heatmapZones: zones }),
}));
