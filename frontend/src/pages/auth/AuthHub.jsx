import { Link } from "react-router-dom";
import { Building2, Stethoscope, UserRound } from "lucide-react";

const portals = [
  {
    to: "/auth/patient",
    title: "Patient",
    desc: "Get your Health ID, approve access, view lifelong records.",
    icon: UserRound,
  },
  {
    to: "/auth/hospital",
    title: "Hospital",
    desc: "Register your facility and onboard doctors.",
    icon: Building2,
  },
  {
    to: "/auth/staff",
    title: "Doctor / Staff",
    desc: "Sign in with credentials issued by your hospital.",
    icon: Stethoscope,
  },
];

export default function AuthHub() {
  return (
    <div className="min-h-screen paper-texture flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-3xl animate-rise">
        <Link to="/" className="text-sm text-teal-800 hover:text-teal-950">
          ← Home
        </Link>
        <h1 className="mt-4 font-display text-3xl text-ink">Choose your portal</h1>
        <p className="mt-2 text-muted text-sm max-w-lg">
          MediLink keeps hospital admin, clinical staff, and patients on
          separate sign-in flows—matching how accounts are created in the API.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {portals.map((p) => (
            <Link
              key={p.to}
              to={p.to}
              className="group rounded-2xl border border-line bg-white p-5 transition hover:border-teal-400 hover:shadow-lg hover:shadow-teal-900/5"
            >
              <p.icon className="h-7 w-7 text-teal-700" />
              <h2 className="mt-4 font-display text-lg group-hover:text-teal-800">
                {p.title}
              </h2>
              <p className="mt-2 text-sm text-muted leading-relaxed">{p.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
