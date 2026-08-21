import { Outlet } from "react-router-dom";
import {
  Home,
  Inbox,
  FolderOpen,
  Shield,
  UserRound,
} from "lucide-react";
import { AppShell } from "../../components/layout/AppShell";

const navItems = [
  {
    to: "/patient",
    label: "Health ID",
    short: "ID",
    icon: <Home className="h-4 w-4" />,
    end: true,
  },
  {
    to: "/patient/requests",
    label: "Requests",
    short: "Inbox",
    icon: <Inbox className="h-4 w-4" />,
  },
  {
    to: "/patient/records",
    label: "My folders",
    short: "Records",
    icon: <FolderOpen className="h-4 w-4" />,
  },
  {
    to: "/patient/access",
    label: "Who can see",
    short: "Access",
    icon: <Shield className="h-4 w-4" />,
  },
  {
    to: "/patient/profile",
    label: "Profile",
    short: "Me",
    icon: <UserRound className="h-4 w-4" />,
  },
];

export default function PatientLayout() {
  return (
    <AppShell title="Patient" navItems={navItems} mobileFirst>
      <Outlet />
    </AppShell>
  );
}
