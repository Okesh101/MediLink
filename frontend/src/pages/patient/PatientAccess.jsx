import { useEffect, useState } from "react";
import { PageHeader, Spinner, Alert, EmptyState, Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { accessApi } from "../../services/access";
import { getErrorMessage } from "../../services/api";
import { formatDateTime } from "../../lib/format";

export default function PatientAccess() {
  const [grants, setGrants] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(null);

  async function load() {
    const { data } = await accessApi.listGrants();
    setGrants(data.data || []);
  }

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function revoke(id) {
    setError("");
    setActing(id);
    try {
      await accessApi.revokeGrant(id);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Could not revoke access."));
    } finally {
      setActing(null);
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
      <PageHeader
        title="Who can see your folders"
        description="Active grants expire automatically. Revoke anytime if you no longer want that doctor to read your history."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {grants.length === 0 ? (
        <EmptyState
          title="No one has access"
          description="Approved requests show up here until they expire or you revoke them."
        />
      ) : (
        <ul className="space-y-3">
          {grants.map((g) => (
            <li
              key={g.id}
              className="rounded-2xl border border-line bg-white p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium">{g.staff_name}</p>
                  <p className="text-sm text-muted">{g.hospital_name}</p>
                </div>
                <Badge status={g.status}>{g.status}</Badge>
              </div>
              <p className="mt-2 text-xs text-muted">
                Expires {formatDateTime(g.expires_at)}
              </p>
              {g.status === "Granted" ? (
                <Button
                  size="sm"
                  variant="danger"
                  className="mt-3"
                  disabled={acting === g.id}
                  onClick={() => revoke(g.id)}
                >
                  {acting === g.id ? "Revoking…" : "Revoke access"}
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
