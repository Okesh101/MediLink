import { Outlet } from "react-router-dom";
import {
  Home,
  Search,
  ShieldQuestion,
  FolderOpen,
  UserRound,
  Brain,
} from "lucide-react";
import { AppShell } from "../../components/layout/AppShell";

const navItems = [
  { to: "/staff", label: "Overview", icon: <Home className="h-4 w-4" />, end: true },
  { to: "/staff/lookup", label: "Find patient", icon: <Search className="h-4 w-4" /> },
  { to: "/staff/requests", label: "Access requests", icon: <ShieldQuestion className="h-4 w-4" /> },
  { to: "/staff/mine", label: "Folders I opened", icon: <FolderOpen className="h-4 w-4" /> },
  { to: "/staff/profile", label: "Profile", icon: <UserRound className="h-4 w-4" /> },
];

export default function StaffLayout() {
  return (
    <AppShell title="Clinical staff" navItems={navItems}>
      <Outlet />
    </AppShell>
  );
}
