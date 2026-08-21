export function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function displayName(user) {
  if (!user) return "";
  if (user.name) return user.name;
  if (user.firstname || user.lastname) {
    return [user.firstname, user.lastname].filter(Boolean).join(" ");
  }
  return user.email || user.phone || "Account";
}

export function statusTone(status) {
  const s = String(status || "").toLowerCase();
  if (["pending", "granted", "approved", "success"].includes(s)) {
    if (s === "pending") return "amber";
    return "teal";
  }
  if (["denied", "revoked", "expired", "rejected"].includes(s)) return "rose";
  return "slate";
}
