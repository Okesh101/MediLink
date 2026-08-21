export function Input({
  label,
  hint,
  error,
  id,
  className = "",
  ...props
}) {
  const inputId = id || props.name;
  return (
    <label className={`block space-y-1.5 ${className}`}>
      {label ? (
        <span className="text-sm font-medium text-ink/90">{label}</span>
      ) : null}
      <input
        id={inputId}
        className={`w-full h-11 rounded-xl border bg-white px-3.5 text-sm text-ink placeholder:text-muted/70 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 ${
          error ? "border-rose-400" : "border-line"
        }`}
        {...props}
      />
      {error ? <span className="text-xs text-rose-600">{error}</span> : null}
      {!error && hint ? (
        <span className="text-xs text-muted">{hint}</span>
      ) : null}
    </label>
  );
}

export function Select({ label, error, id, children, className = "", ...props }) {
  const inputId = id || props.name;
  return (
    <label className={`block space-y-1.5 ${className}`}>
      {label ? (
        <span className="text-sm font-medium text-ink/90">{label}</span>
      ) : null}
      <select
        id={inputId}
        className={`w-full h-11 rounded-xl border bg-white px-3.5 text-sm text-ink outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 ${
          error ? "border-rose-400" : "border-line"
        }`}
        {...props}
      >
        {children}
      </select>
      {error ? <span className="text-xs text-rose-600">{error}</span> : null}
    </label>
  );
}

export function TextArea({ label, error, id, className = "", ...props }) {
  const inputId = id || props.name;
  return (
    <label className={`block space-y-1.5 ${className}`}>
      {label ? (
        <span className="text-sm font-medium text-ink/90">{label}</span>
      ) : null}
      <textarea
        id={inputId}
        className={`w-full min-h-28 rounded-xl border bg-white px-3.5 py-3 text-sm text-ink placeholder:text-muted/70 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 ${
          error ? "border-rose-400" : "border-line"
        }`}
        {...props}
      />
      {error ? <span className="text-xs text-rose-600">{error}</span> : null}
    </label>
  );
}
