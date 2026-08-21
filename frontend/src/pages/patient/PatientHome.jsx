import { useEffect, useState } from "react";
import { Copy, Check } from "lucide-react";
import { Spinner, Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import { displayName } from "../../lib/format";

export default function PatientHome() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await authApi.mePatient();
        if (cancelled) return;
        setUser(data.data);
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setUser]);

  async function copyId() {
    if (!user?.public_id) return;
    try {
      await navigator.clipboard.writeText(user.public_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setError("Could not copy. Long-press the ID instead.");
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg">
      <p className="text-sm text-muted">Hello, {displayName(user)}</p>
      <h1 className="mt-1 font-display text-2xl sm:text-3xl">Your Health ID</h1>
      <p className="mt-2 text-sm text-muted">
        Show this to the doctor when you arrive. They use it to ask permission
        to read your past folders.
      </p>

      {error ? <Alert className="mt-4">{error}</Alert> : null}

      <div className="mt-6 overflow-hidden rounded-3xl bg-teal-950 text-white shadow-xl shadow-teal-900/20">
        <div className="px-5 pt-6 pb-2 text-xs uppercase tracking-[0.2em] text-teal-300">
          MediLink · Universal ID
        </div>
        <p className="public-id px-5 py-6 text-center text-3xl sm:text-4xl tracking-[0.18em]">
          {user?.public_id}
        </p>
        <div className="flex items-center justify-between border-t border-white/10 px-5 py-4 text-sm text-teal-100/80">
          <span>
            {user?.firstname} {user?.lastname}
          </span>
          <Button
            size="sm"
            className="bg-white/10 text-white hover:bg-white/15"
            onClick={copyId}
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>
      </div>

      <p className="mt-6 text-sm leading-relaxed text-muted">
        You approve or deny each request. Grants can be revoked. Folders stay
        forever—you can view them, never delete them.
      </p>
    </div>
  );
}
