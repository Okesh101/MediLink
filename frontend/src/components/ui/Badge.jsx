import { statusTone } from "../../lib/format";

const tones = {
  teal: "bg-teal-50 text-teal-800 border-teal-200",
  amber: "bg-amber-50 text-amber-900 border-amber-200",
  rose: "bg-rose-50 text-rose-800 border-rose-200",
  slate: "bg-slate-50 text-slate-700 border-slate-200",
};

export function Badge({ children, status, className = "" }) {
  const tone = tones[statusTone(status)] || tones.slate;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${tone} ${className}`}
    >
      {children ?? status}
    </span>
  );
}

export function Alert({ tone = "error", children, className = "" }) {
  const map = {
    error: "border-rose-200 bg-rose-50 text-rose-900",
    success: "border-teal-200 bg-teal-50 text-teal-900",
    info: "border-sky-200 bg-sky-50 text-sky-900",
  };
  return (
    <div
      className={`rounded-xl border px-3.5 py-3 text-sm ${map[tone]} ${className}`}
      role="alert"
    >
      {children}
    </div>
  );
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-white/70 px-6 py-12 text-center">
      <h3 className="font-display text-lg text-ink">{title}</h3>
      {description ? (
        <p className="mt-2 text-sm text-muted max-w-md mx-auto">{description}</p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function Spinner({ className = "h-5 w-5" }) {
  return (
    <svg
      className={`animate-spin text-teal-700 ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z"
      />
    </svg>
  );
}

export function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-2xl sm:text-3xl text-ink">{title}</h1>
        {description ? (
          <p className="mt-1 text-sm text-muted max-w-2xl">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
