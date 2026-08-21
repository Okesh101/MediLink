import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader, Spinner, Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { authApi } from "../../services/auth";
import { accessApi } from "../../services/access";
import { recordsApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import { displayName } from "../../lib/format";

export default function StaffOverview() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [counts, setCounts] = useState({ pending: 0, grants: 0, mine: 0 });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [me, pending, grants, mine] = await Promise.all([
          authApi.meStaff(),
          accessApi.listRequests("Pending"),
          accessApi.listGrants(),
          recordsApi.mine(),
        ]);
        if (cancelled) return;
        setUser(me.data.data);
        const grantList = grants.data.data || [];
        setCounts({
          pending: pending.data.count ?? (pending.data.data || []).length,
          grants: grantList.filter((g) => g.status === "Granted").length,
          mine: mine.data.count ?? (mine.data.data || []).length,
        });
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

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`Welcome, ${displayName(user)}`}
        description={`${user?.hospital_name || "Your hospital"} · Ask for the patient’s Health ID, confirm the name, request access, then open a digital folder.`}
        actions={
          <Link to="/staff/lookup">
            <Button>Look up Health ID</Button>
          </Link>
        }
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Pending requests" value={counts.pending} to="/staff/requests" />
        <Stat label="Active grants" value={counts.grants} to="/staff/requests" />
        <Stat label="Folders you opened" value={counts.mine} to="/staff/mine" />
      </div>
      <ol className="mt-10 space-y-4 text-sm text-muted">
        <li>
          <span className="font-display text-teal-800">1.</span> Patient shows
          their Health ID on their phone.
        </li>
        <li>
          <span className="font-display text-teal-800">2.</span> You confirm
          the name matches the person in front of you.
        </li>
        <li>
          <span className="font-display text-teal-800">3.</span> Send an access
          request. They approve. You read past folders (read-only from other
          hospitals).
        </li>
        <li>
          <span className="font-display text-teal-800">4.</span> Open a new
          immutable folder for this visit and file reports inside.
        </li>
      </ol>
    </div>
  );
}

function Stat({ label, value, to }) {
  return (
    <Link
      to={to}
      className="rounded-2xl border border-line bg-white px-5 py-4 hover:border-teal-400"
    >
      <p className="text-xs uppercase tracking-[0.14em] text-muted">{label}</p>
      <p className="mt-2 font-display text-3xl text-teal-900">{value}</p>
    </Link>
  );
}
