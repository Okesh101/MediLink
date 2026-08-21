import api from "./api";

export const staffApi = {
  onboardDoctor: (body) => api.post("/staff/doctor", body),
  list: () => api.get("/staff"),
  get: (staffId) => api.get(`/staff/${staffId}`),
};
