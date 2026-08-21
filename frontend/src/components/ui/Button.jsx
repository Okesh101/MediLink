export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  type = "button",
  disabled,
  ...props
}) {
  const base =
    "inline-flex items-center justify-center gap-2 font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/40 disabled:opacity-50 disabled:pointer-events-none";

  const sizes = {
    sm: "h-9 px-3 text-sm rounded-lg",
    md: "h-11 px-4 text-sm rounded-xl",
    lg: "h-12 px-5 text-base rounded-xl",
  };

  const variants = {
    primary:
      "bg-teal-700 text-white hover:bg-teal-800 shadow-sm shadow-teal-900/10",
    secondary:
      "bg-white text-teal-900 border border-line hover:border-teal-300 hover:bg-teal-50/60",
    ghost: "text-teal-800 hover:bg-teal-50",
    danger: "bg-rose-700 text-white hover:bg-rose-800",
    soft: "bg-teal-50 text-teal-900 hover:bg-teal-100",
  };

  return (
    <button
      type={type}
      disabled={disabled}
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
