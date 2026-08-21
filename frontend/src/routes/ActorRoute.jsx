import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

const HOME = {
  hospital_admin: "/hospital",
  staff: "/staff",
  patient: "/patient",
};

export default function ActorRoute({ allowed }) {
  const actorType = useAuthStore((s) => s.actorType);
  const allowedList = Array.isArray(allowed) ? allowed : [allowed];

  if (!allowedList.includes(actorType)) {
    return <Navigate to={HOME[actorType] || "/auth"} replace />;
  }

  return <Outlet />;
}
