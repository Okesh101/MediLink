import { useEffect, useState } from "react";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import { RecordFolder } from "../../components/records/RecordFolder";
import { recordsApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function StaffMine() {
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await recordsApi.mine();
        if (!cancelled) setRecords(data.data || []);
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

  return (
    <div>
      <PageHeader
        title="Folders I opened"
        description="Encounter records you created at this hospital. Still immutable—view only after they are saved."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-7 w-7" />
        </div>
      ) : records.length === 0 ? (
        <EmptyState
          title="No folders yet"
          description="After a patient grants access, open a new folder from their chart."
        />
      ) : (
        <div className="grid gap-4">
          {records.map((r) => (
            <RecordFolder key={r.id} record={r} href={`/staff/records/${r.id}`} />
          ))}
        </div>
      )}
    </div>
  );
}
