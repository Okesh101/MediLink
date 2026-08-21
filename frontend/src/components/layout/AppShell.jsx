import { NavLink, useNavigate } from "react-router-dom";
import { LogOut, Menu, X } from "lucide-react";
import { useState } from "react";
import { displayName } from "../../lib/format";
import { logoutCurrent } from "../../services/auth";
import { useAuthStore } from "../../store/authStore";
import { Button } from "../ui/Button";

export function AppShell({
  title,
  navItems,
  children,
  mobileFirst = false,
}) {
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  async function handleLogout() {
    await logoutCurrent();
    navigate("/");
  }

  const nav = (
    <nav className="flex flex-col gap-1 p-3">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
              isActive
                ? "bg-teal-700 text-white shadow-sm"
                : "text-teal-950/80 hover:bg-teal-50"
            }`
          }
        >
          {item.icon}
          {item.label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className={`min-h-screen paper-texture ${mobileFirst ? "pb-20 md:pb-0" : ""}`}>
      <div className="mx-auto flex min-h-screen max-w-[1400px]">
        {/* Desktop sidebar */}
        <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-line bg-white/80 backdrop-blur">
          <div className="border-b border-line px-5 py-5">
            <p className="font-display text-xl text-teal-900">MediLink</p>
            <p className="mt-0.5 text-xs uppercase tracking-[0.16em] text-muted">
              {title}
            </p>
          </div>
          <div className="flex-1 overflow-y-auto">{nav}</div>
          <div className="border-t border-line p-4">
            <p className="truncate text-sm font-medium text-ink">
              {displayName(user)}
            </p>
            <p className="truncate text-xs text-muted">
              {user?.email || user?.phone || ""}
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-3 w-full justify-start px-2"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          {/* Mobile top bar */}
          <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-white/90 px-4 py-3 backdrop-blur md:hidden">
            <div>
              <p className="font-display text-lg text-teal-900">MediLink</p>
              <p className="text-[11px] uppercase tracking-[0.14em] text-muted">
                {title}
              </p>
            </div>
            {!mobileFirst ? (
              <button
                type="button"
                className="rounded-lg p-2 text-teal-900 hover:bg-teal-50"
                onClick={() => setOpen((v) => !v)}
                aria-label="Toggle menu"
              >
                {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            ) : (
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
              </Button>
            )}
          </header>

          {open && !mobileFirst ? (
            <div className="border-b border-line bg-white md:hidden">{nav}</div>
          ) : null}

          <main className="flex-1 px-4 py-5 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>

      {/* Patient mobile bottom nav */}
      {mobileFirst ? (
        <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-white/95 backdrop-blur md:hidden">
          <div className="mx-auto flex max-w-lg items-stretch justify-around px-1 py-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-xl px-1 py-2 text-[11px] font-medium ${
                    isActive ? "text-teal-700" : "text-muted"
                  }`
                }
              >
                <span className="[&>svg]:h-5 [&>svg]:w-5">{item.icon}</span>
                <span className="truncate">{item.short || item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
      ) : null}
    </div>
  );
}
