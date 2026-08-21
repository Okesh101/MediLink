import { useEffect, useState } from "react";
import { PageHeader, Spinner, Alert } from "../../components/ui/Badge";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import { formatDate } from "../../lib/format";

export default function PatientProfile() {
  const setUser = useAuthStore((s) => s.setUser);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await authApi.mePatient();
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
    <div className="mx-auto max-w-lg">
      <PageHeader title="Profile" description="Your MediLink patient account." />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {profile ? (
        <dl className="divide-y divide-line rounded-2xl border border-line bg-white">
          <Row label="Health ID" value={profile.public_id} mono />
          <Row label="Name" value={`${profile.firstname} ${profile.lastname}`} />
          <Row label="Sex" value={profile.sex} />
          <Row label="Date of birth" value={profile.dob} />
          <Row label="Phone" value={profile.phone} />
          <Row label="Email" value={profile.email} />
          <Row label="Allergies" value={profile.allergies} />
          <Row label="Blood Group" value={profile.blood_group} />
          <Row label="Genotype" value={profile.genotype} />
          <Row label="Joined" value={formatDate(profile.created_at)} />
        </dl>
      ) : null}
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="px-5 py-3.5">
      <dt className="text-xs uppercase tracking-wider text-muted">{label}</dt>
      <dd className={`mt-1 text-sm ${mono ? "public-id text-teal-800" : ""}`}>
        {value || "—"}
      </dd>
    </div>
  );
}
