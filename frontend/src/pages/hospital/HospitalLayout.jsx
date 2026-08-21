import { Outlet } from "react-router-dom";
import {
  Home,
  UserPlus,
  Users,
  UserRound,
} from "lucide-react";
import { AppShell } from "../../components/layout/AppShell";

const navItems = [
  { to: "/hospital", label: "Overview", icon: <Home className="h-4 w-4" />, end: true },
  { to: "/hospital/doctors", label: "Doctors", icon: <Users className="h-4 w-4" /> },
  { to: "/hospital/doctors/new", label: "Onboard doctor", icon: <UserPlus className="h-4 w-4" /> },
  { to: "/hospital/profile", label: "Hospital profile", icon: <UserRound className="h-4 w-4" /> },
];

export default function HospitalLayout() {
  return (
    <AppShell title="Hospital admin" navItems={navItems}>
      <Outlet />
    </AppShell>
  );
}
