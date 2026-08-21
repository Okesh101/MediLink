import { useEffect, useState } from "react";
import { PageHeader, Spinner, Alert } from "../../components/ui/Badge";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import { formatDate } from "../../lib/format";

export default function HospitalProfile() {
  const setUser = useAuthStore((s) => s.setUser);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await authApi.meHospital();
        if (cancelled) return;
        setProfile(data.data);
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

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  return (
    <div className="max-w-xl">
      <PageHeader
        title="Hospital profile"
        description="Facility details on this MediLink account."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {profile ? (
        <dl className="divide-y divide-line rounded-2xl border border-line bg-white">
          <Row label="Name" value={profile.name} />
          <Row label="Registration no." value={profile.reg_no} />
          <Row label="Email" value={profile.email} />
          <Row label="Phone" value={profile.phone} />
          <Row label="Address" value={profile.address} />
          <Row
            label="Verified"
            value={profile.is_verified ? "Verified" : "Not verified"}
          />
          <Row label="Joined" value={formatDate(profile.created_at)} />
        </dl>
      ) : null}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="px-5 py-3.5 sm:flex sm:gap-6">
      <dt className="w-40 shrink-0 text-xs uppercase tracking-wider text-muted">
        {label}
      </dt>
      <dd className="mt-1 text-sm sm:mt-0">{value || "—"}</dd>
    </div>
  );
}
