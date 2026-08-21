import api from "./api";
import { useAuthStore } from "../store/authStore";

function applyLogin(payload, actorType, userKey) {
  const user = payload[userKey] || payload.data;
  useAuthStore.getState().login({
    user,
    actorType,
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
  });
  return user;
}

export const authApi = {
  // Patient
  registerPatient: (body) => api.post("/auth/patient/register", body),
  loginPatient: async (body) => {
    const { data } = await api.post("/auth/patient/login", body);
    return applyLogin(data, "patient", "patient");
  },
  mePatient: () => api.get("/auth/patient/me"),
  logoutPatient: () => {
    const { accessToken, refreshToken } = useAuthStore.getState();
    return api.post(
      "/auth/patient/logout",
      {},
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          ...(refreshToken ? { "X-Refresh-Token": refreshToken } : {}),
        },
      },
    );
  },

  // Hospital
  registerHospital: (body) => api.post("/auth/hospital/register", body),
  loginHospital: async (body) => {
    const { data } = await api.post("/auth/hospital/login", body);
    return applyLogin(data, "hospital_admin", "hospital");
  },
  meHospital: () => api.get("/auth/hospital/me"),
  logoutHospital: () => {
    const { accessToken, refreshToken } = useAuthStore.getState();
    return api.post(
      "/auth/hospital/logout",
      {},
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          ...(refreshToken ? { "X-Refresh-Token": refreshToken } : {}),
        },
      },
    );
  },

  // Staff
  loginStaff: async (body) => {
    const { data } = await api.post("/auth/staff/login", body);
    return applyLogin(data, "staff", "staff");
  },
  meStaff: () => api.get("/auth/staff/me"),
  logoutStaff: () => {
    const { accessToken, refreshToken } = useAuthStore.getState();
    return api.post(
      "/auth/staff/logout",
      {},
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          ...(refreshToken ? { "X-Refresh-Token": refreshToken } : {}),
        },
      },
    );
  },
};

export async function logoutCurrent() {
  const { actorType, logout } = useAuthStore.getState();
  try {
    if (actorType === "hospital_admin") await authApi.logoutHospital();
    else if (actorType === "staff") await authApi.logoutStaff();
    else if (actorType === "patient") await authApi.logoutPatient();
  } catch {
    // still clear local session
  } finally {
    logout();
  }
}
