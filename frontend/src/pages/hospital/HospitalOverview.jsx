import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { staffApi } from "../../services/staff";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import { formatDate } from "../../lib/format";

export default function HospitalOverview() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [staff, setStaff] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [me, list] = await Promise.all([
          authApi.meHospital(),
          staffApi.list(),
        ]);
        if (cancelled) return;
        setUser(me.data.data);
        setStaff(list.data.data || []);
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
        title={user?.name || "Hospital"}
        description="Onboard doctors, then they sign in on the staff portal to look up Health IDs and open digital folders."
        actions={
          <Link to="/hospital/doctors/new">
            <Button>Onboard a doctor</Button>
          </Link>
        }
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Doctors onboarded" value={staff.length} />
        <Stat label="Reg. no." value={user?.reg_no || "—"} />
        <Stat label="Verified" value={user?.is_verified ? "Yes" : "Pending"} />
      </div>

      <section className="mt-10">
        <h2 className="font-display text-xl">Recent doctors</h2>
        {staff.length === 0 ? (
          <EmptyState
            title="No doctors yet"
            description="Create a doctor account. They will sign in separately and run the clinical flow."
            action={
              <Link to="/hospital/doctors/new">
                <Button>Add first doctor</Button>
              </Link>
            }
          />
        ) : (
          <ul className="mt-4 divide-y divide-line rounded-2xl border border-line bg-white">
            {staff.slice(0, 6).map((d) => (
              <li key={d.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="font-medium">{d.name}</p>
                  <p className="text-xs text-muted">{d.email}</p>
                </div>
                <p className="text-xs text-muted">{formatDate(d.created_at)}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-2xl border border-line bg-white px-5 py-4">
      <p className="text-xs uppercase tracking-[0.14em] text-muted">{label}</p>
      <p className="mt-2 font-display text-2xl text-teal-900">{value}</p>
    </div>
  );
}
