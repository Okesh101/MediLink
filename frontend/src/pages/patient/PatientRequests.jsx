import { useEffect, useState } from "react";
import { PageHeader, Spinner, Alert, EmptyState, Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { accessApi } from "../../services/access";
import { getErrorMessage } from "../../services/api";
import { formatDateTime } from "../../lib/format";

export default function PatientRequests() {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(null);

  async function load() {
    const { data } = await accessApi.listRequests();
    setRequests(data.data || []);
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

  async function review(id, status) {
    setError("");
    setActing(id + status);
    try {
      await accessApi.review(id, status);
      await load();
    } catch (err) {
      setError(getErrorMessage(err, "Could not update request."));
    } finally {
      setActing(null);
    }
  }

  const pending = requests.filter((r) => r.status === "Pending");
  const others = requests.filter((r) => r.status !== "Pending");

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
        title="Access requests"
        description="A doctor who searched your Health ID is asking to read your past folders for a limited time."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}

      {pending.length === 0 && others.length === 0 ? (
        <EmptyState
          title="Nothing waiting"
          description="When a hospital looks you up, their request appears here."
        />
      ) : null}

      {pending.length > 0 ? (
        <ul className="space-y-3">
          {pending.map((r) => (
            <li
              key={r.id}
              className="rounded-2xl border border-amber-200 bg-amber-50/50 p-4"
            >
              <p className="font-display text-lg">{r.staff_name}</p>
              <p className="text-sm text-muted">{r.hospital_name}</p>
              {r.reason ? (
                <p className="mt-2 text-sm">{r.reason}</p>
              ) : (
                <p className="mt-2 text-sm text-muted">No reason given.</p>
              )}
              <p className="mt-2 text-xs text-muted">
                {formatDateTime(r.created_at)}
              </p>
              <div className="mt-4 flex gap-2">
                <Button
                  size="sm"
                  disabled={!!acting}
                  onClick={() => review(r.id, "approved")}
                >
                  {acting === r.id + "approved" ? "…" : "Approve"}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={!!acting}
                  onClick={() => review(r.id, "denied")}
                >
                  {acting === r.id + "denied" ? "…" : "Deny"}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {others.length > 0 ? (
        <ul className="mt-8 space-y-2">
          {others.map((r) => (
            <li
              key={r.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-line bg-white px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium">{r.staff_name}</p>
                <p className="text-xs text-muted">{r.hospital_name}</p>
              </div>
              <Badge status={r.status}>{r.status}</Badge>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
