import { Link } from "react-router-dom";

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
  backTo = "/",
}) {
  return (
    <div className="min-h-screen paper-texture flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md animate-rise">
        <Link
          to={backTo}
          className="mb-6 inline-flex text-sm text-teal-800 hover:text-teal-950"
        >
          ← Back
        </Link>
        <div className="rounded-2xl border border-line bg-white p-6 sm:p-8 shadow-[0_20px_50px_-28px_rgba(15,118,110,0.35)]">
          <p className="font-display text-2xl text-teal-900">MediLink</p>
          <h1 className="mt-3 font-display text-xl text-ink">{title}</h1>
          {subtitle ? (
            <p className="mt-1 text-sm text-muted">{subtitle}</p>
          ) : null}
          <div className="mt-6">{children}</div>
          {footer ? <div className="mt-6 text-sm text-muted">{footer}</div> : null}
        </div>
      </div>
    </div>
  );
}
