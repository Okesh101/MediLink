import api from "./api";

export const recordsApi = {
  lookupPatient: (publicId) =>
    api.get(`/records/patient/${encodeURIComponent(publicId)}/lookup`),
  getPatientRecords: (publicId) =>
    api.get(`/records/patient/${encodeURIComponent(publicId)}`),
  create: (formData) => api.post("/records", formData),
  mine: () => api.get("/records/mine"),
  get: (recordId) => api.get(`/records/${recordId}`),
};

export const patientApi = {
  myRecords: () => api.get("/patient/records"),
  getRecord: (recordId) => api.get(`/patient/records/${recordId}`),
};
