import axios from "axios";
import { useAuthStore } from "../store/authStore";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

let refreshPromise = null;

api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    const headers = config.headers;
    if (headers && typeof headers.delete === "function") {
      headers.delete("Content-Type");
    } else if (headers) {
      delete headers["Content-Type"];
    }
  }

  const { accessToken } = useAuthStore.getState();
  if (accessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const { refreshToken, logout, setAccessToken } = useAuthStore.getState();

    const isAuthRoute =
      original?.url?.includes("/auth/") &&
      (original.url.includes("/login") ||
        original.url.includes("/register") ||
        original.url.includes("/refresh"));

    if (status !== 401 || !refreshToken || original?._retry || isAuthRoute) {
      if (status === 401 && !isAuthRoute && !refreshToken) {
        logout();
      }
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post(
            "/api/v1/auth/" + actorRefreshPath(),
            {},
            {
              headers: { Authorization: `Bearer ${refreshToken}` },
            },
          )
          .then((res) => {
            const next = res.data?.access_token;
            if (!next) throw new Error("No access token on refresh");
            setAccessToken(next);
            return next;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const nextToken = await refreshPromise;
      original.headers.Authorization = `Bearer ${nextToken}`;
      return api(original);
    } catch {
      logout();
      return Promise.reject(error);
    }
  },
);

function actorRefreshPath() {
  const { actorType } = useAuthStore.getState();
  if (actorType === "hospital_admin") return "hospital/refresh";
  if (actorType === "staff") return "staff/refresh";
  return "patient/refresh";
}

export function getErrorMessage(error, fallback = "Something went wrong.") {
  return (
    error?.response?.data?.message ||
    error?.message ||
    fallback
  );
}

export default api;
