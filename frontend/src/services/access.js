import api from "./api";

export const accessApi = {
  request: (body) => api.post("/access/request", body),
  listRequests: (status) =>
    api.get("/access/requests", { params: status ? { status } : undefined }),
  getRequest: (id) => api.get(`/access/requests/${id}`),
  review: (id, status) =>
    api.post(`/access/requests/${id}/review`, { status }),
  listGrants: () => api.get("/access/grants"),
  revokeGrant: (id) => api.post(`/access/grants/${id}/revoke`),
};
