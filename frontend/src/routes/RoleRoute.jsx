import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

const RoleRoute = ({ allowedRole }) => {
  const user = useAuthStore(
    (state) => state.user
  );

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  if (user.role !== allowedRole) {

    if (user.role === "hospital") {
      return (
        <Navigate
          to="/hospital/dashboard"
          replace
        />
      );
    }

    if (user.role === "patient") {
      return (
        <Navigate
          to="/patient/dashboard"
          replace
        />
      );
    }

    return <Navigate to="/auth" replace />;
  }

  return <Outlet />;
};

export default RoleRoute;