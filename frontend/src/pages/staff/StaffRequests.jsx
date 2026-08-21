import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader, Spinner, Alert, EmptyState, Badge } from "../../components/ui/Badge";
import { accessApi } from "../../services/access";
import { getErrorMessage } from "../../services/api";
import { formatDateTime } from "../../lib/format";

export default function StaffRequests() {
  const [requests, setRequests] = useState([]);
  const [grants, setGrants] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [req, g] = await Promise.all([
          accessApi.listRequests(),
          accessApi.listGrants(),
        ]);
        if (cancelled) return;
        setRequests(req.data.data || []);
        setGrants(g.data.data || []);
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
        title="Access"
        description="Requests you sent and grants the patient approved. Access expires; they can also revoke it."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}

      <h2 className="font-display text-lg">Requests</h2>
      {requests.length === 0 ? (
        <EmptyState
          title="No requests yet"
          description="Look up a Health ID to send your first request."
        />
      ) : (
        <ul className="mt-3 space-y-2">
          {requests.map((r) => (
            <li
              key={r.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-line bg-white px-4 py-3"
            >
              <div>
                <p className="public-id text-sm font-medium">{r.patient_public_id}</p>
                <p className="text-xs text-muted">
                  {r.reason || "No reason given"} · {formatDateTime(r.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge status={r.status}>{r.status}</Badge>
                {r.status === "Approved" ? (
                  <Link
                    to={`/staff/patients/${encodeURIComponent(r.patient_public_id)}`}
                    className="text-sm text-teal-800"
                  >
                    Open folders
                  </Link>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}

      <h2 className="mt-10 font-display text-lg">Grants</h2>
      {grants.length === 0 ? (
        <p className="mt-2 text-sm text-muted">No grants yet.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {grants.map((g) => (
            <li
              key={g.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-line bg-white px-4 py-3"
            >
              <div>
                <p className="public-id text-sm font-medium">{g.patient_public_id}</p>
                <p className="text-xs text-muted">
                  Expires {formatDateTime(g.expires_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge status={g.status}>{g.status}</Badge>
                {g.status === "Granted" ? (
                  <Link
                    to={`/staff/patients/${encodeURIComponent(g.patient_public_id)}`}
                    className="text-sm text-teal-800"
                  >
                    Open folders
                  </Link>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
