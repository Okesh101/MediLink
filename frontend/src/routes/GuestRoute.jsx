import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export default function GuestRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const homePath = useAuthStore((s) => s.homePath);

  if (isAuthenticated) {
    return <Navigate to={homePath()} replace />;
  }

  return <Outlet />;
}
