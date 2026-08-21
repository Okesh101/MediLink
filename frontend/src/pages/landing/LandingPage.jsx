import { Link, Navigate } from "react-router-dom";
import {
  ArrowRight,
  Building2,
  FileLock2,
  IdCard,
  ShieldCheck,
  Stethoscope,
  Users,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { useAuthStore } from "../../store/authStore";

const steps = [
  {
    title: "Patient shows Health ID",
    body: "Every patient gets a universal public ID on their phone. No paper folder to dig up.",
    icon: IdCard,
  },
  {
    title: "Doctor requests access",
    body: "Staff look up the ID, confirm the name, and send a time-bound view request.",
    icon: Stethoscope,
  },
  {
    title: "Patient approves",
    body: "The patient sees who asked and why, then approves or denies from their portal.",
    icon: ShieldCheck,
  },
  {
    title: "Create a digital folder",
    body: "After diagnosis, the doctor opens a new immutable record and files reports inside.",
    icon: FileLock2,
  },
];

const plans = [
  {
    name: "Starter",
    price: "Free",
    blurb: "For clinics starting to leave paper behind.",
    features: [
      "Up to 3 doctor accounts",
      "Patient Health ID lookup",
      "Access request & grant flow",
      "Create immutable encounter records",
      "Upload up to 20 documents / month",
      "Read-only history from other hospitals",
    ],
    cta: "Start free",
    href: "/auth/hospital",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "₦45,000",
    period: "/ month",
    blurb: "Built for busy outpatient departments.",
    features: [
      "Up to 25 doctor accounts",
      "Unlimited document uploads",
      "Full patient history under active grant",
      "Hospital staff directory",
      "Priority support (business hours)",
      "Immutable audit trail on every record",
    ],
    cta: "Choose Pro",
    href: "/auth/hospital",
    highlighted: true,
  },
  {
    name: "Business",
    price: "₦120,000",
    period: "/ month",
    blurb: "For multi-ward hospitals and networks.",
    features: [
      "Unlimited doctor accounts",
      "Multi-department onboarding",
      "Dedicated success manager",
      "Custom retention & export policy",
      "SLA-backed uptime",
      "Everything in Pro",
    ],
    cta: "Talk to us",
    href: "/auth/hospital",
    highlighted: false,
  },
];

export default function LandingPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const homePath = useAuthStore((s) => s.homePath);

  if (isAuthenticated) {
    return <Navigate to={homePath()} replace />;
  }

  return (
    <div className="min-h-screen bg-surface text-ink">
      <header className="relative overflow-hidden mesh-bg text-white">
        <div className="pointer-events-none absolute inset-0 grid-fade" />
        <div className="relative mx-auto max-w-6xl px-4 sm:px-6">
          <nav className="flex items-center justify-between py-5">
            <span className="font-display text-2xl tracking-tight">MediLink</span>
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                to="/auth"
                className="hidden sm:inline text-sm text-teal-100 hover:text-white"
              >
                Sign in
              </Link>
              <Link to="/auth/hospital">
                <Button className="bg-white text-teal-900 hover:bg-teal-50">
                  For hospitals
                </Button>
              </Link>
            </div>
          </nav>

          <div className="pb-20 pt-10 sm:pb-28 sm:pt-16 max-w-3xl">
            <p className="animate-rise font-display text-5xl sm:text-6xl lg:text-7xl leading-[0.95] tracking-tight">
              MediLink
            </p>
            <h1 className="animate-rise-delay mt-5 text-xl sm:text-2xl font-medium text-teal-50/95 max-w-xl">
              One Health ID. Digital folders that replace the paper file room.
            </h1>
            <p className="animate-rise-delay-2 mt-4 max-w-lg text-base text-teal-100/80">
              Patients carry a universal ID. Doctors request access, read past
              reports they cannot edit, and open a new immutable record—the
              same flow as a physical folder, without the delay.
            </p>
            <div className="animate-rise-delay-2 mt-8 flex flex-wrap gap-3">
              <Link to="/auth/patient">
                <Button size="lg" className="bg-teal-400 text-teal-950 hover:bg-teal-300">
                  Patient portal
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link to="/auth/staff">
                <Button
                  size="lg"
                  variant="secondary"
                  className="border-white/20 bg-white/10 text-white hover:bg-white/15"
                >
                  Doctor sign in
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">
          How it works
        </p>
        <h2 className="mt-2 font-display text-3xl sm:text-4xl text-ink max-w-xl">
          Digitize the folder, not invent a new hospital ritual.
        </h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, i) => (
            <div key={step.title} className="relative pt-1">
              <span className="font-display text-4xl text-teal-100">{`0${i + 1}`}</span>
              <step.icon className="mt-3 h-6 w-6 text-teal-700" />
              <h3 className="mt-3 font-display text-lg">{step.title}</h3>
              <p className="mt-2 text-sm text-muted leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-white">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">
                Why hospitals switch
              </p>
              <h2 className="mt-2 font-display text-3xl text-ink">
                Faster diagnosis. No more hunting for last hospital’s envelope.
              </h2>
              <ul className="mt-6 space-y-4 text-sm text-muted">
                <li className="flex gap-3">
                  <Users className="mt-0.5 h-5 w-5 shrink-0 text-teal-700" />
                  Onboard doctors under your hospital account—they sign in on
                  their own screen.
                </li>
                <li className="flex gap-3">
                  <FileLock2 className="mt-0.5 h-5 w-5 shrink-0 text-teal-700" />
                  Records are immutable. Other hospitals can read what you
                  uploaded; nobody edits or deletes it—not even the patient.
                </li>
                <li className="flex gap-3">
                  <Building2 className="mt-0.5 h-5 w-5 shrink-0 text-teal-700" />
                  See every encounter your facility opened for a patient, with
                  the reports filed inside.
                </li>
              </ul>
            </div>
            <div className="rounded-3xl border border-line bg-teal-950 p-6 text-teal-50 sm:p-8">
              <p className="font-display text-2xl">Records stay read-only</p>
              <p className="mt-3 text-sm text-teal-100/80 leading-relaxed">
                When another facility uploads a scan or lab report, your doctors
                can open it under an approved grant—but they cannot change or
                remove it. That keeps trust across hospitals and mirrors a
                sealed paper chart.
              </p>
              <div className="mt-8 grid grid-cols-3 gap-3 text-center">
                {[
                  ["Read", "History"],
                  ["Write", "Your visits"],
                  ["Never", "Delete"],
                ].map(([k, v]) => (
                  <div
                    key={k}
                    className="rounded-2xl bg-white/5 px-2 py-4 border border-white/10"
                  >
                    <p className="font-display text-lg text-teal-300">{k}</p>
                    <p className="mt-1 text-xs text-teal-100/70">{v}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="pricing" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">
          Pricing for hospitals
        </p>
        <h2 className="mt-2 font-display text-3xl sm:text-4xl">
          Plans that replace filing cabinets
        </h2>
        <p className="mt-3 max-w-2xl text-muted text-sm sm:text-base">
          Patients always use MediLink free. Hospitals pick a plan based on
          staff size and upload volume.
        </p>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`flex flex-col rounded-2xl border p-6 ${
                plan.highlighted
                  ? "border-teal-600 bg-teal-900 text-white shadow-xl shadow-teal-900/20"
                  : "border-line bg-white"
              }`}
            >
              <p
                className={`text-sm font-semibold uppercase tracking-wider ${
                  plan.highlighted ? "text-teal-200" : "text-teal-700"
                }`}
              >
                {plan.name}
              </p>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="font-display text-4xl">{plan.price}</span>
                {plan.period ? (
                  <span
                    className={`text-sm ${
                      plan.highlighted ? "text-teal-200" : "text-muted"
                    }`}
                  >
                    {plan.period}
                  </span>
                ) : null}
              </div>
              <p
                className={`mt-2 text-sm ${
                  plan.highlighted ? "text-teal-100/80" : "text-muted"
                }`}
              >
                {plan.blurb}
              </p>
              <ul className="mt-6 flex-1 space-y-2.5 text-sm">
                {plan.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span
                      className={
                        plan.highlighted ? "text-teal-300" : "text-teal-600"
                      }
                    >
                      ✓
                    </span>
                    <span
                      className={
                        plan.highlighted ? "text-teal-50" : "text-ink/80"
                      }
                    >
                      {f}
                    </span>
                  </li>
                ))}
              </ul>
              <Link to={plan.href} className="mt-8 block">
                <Button
                  className={`w-full ${
                    plan.highlighted
                      ? "bg-white text-teal-900 hover:bg-teal-50"
                      : ""
                  }`}
                  variant={plan.highlighted ? "primary" : "secondary"}
                >
                  {plan.cta}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-10 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="font-display text-xl text-teal-900">MediLink</p>
            <p className="mt-1 text-sm text-muted">
              Universal Health ID for Nigeria’s clinics and hospitals.
            </p>
          </div>
          <div className="flex flex-wrap gap-4 text-sm text-teal-800">
            <Link to="/auth/patient">Patients</Link>
            <Link to="/auth/hospital">Hospitals</Link>
            <Link to="/auth/staff">Doctors</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
