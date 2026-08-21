import { useEffect, useState } from "react";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import { RecordFolder } from "../../components/records/RecordFolder";
import { patientApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function PatientRecords() {
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await patientApi.myRecords();
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
    <div className="mx-auto max-w-lg">
      <PageHeader
        title="My folders"
        description="Every encounter hospitals filed for you. View only—nothing here can be deleted."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-7 w-7" />
        </div>
      ) : records.length === 0 ? (
        <EmptyState
          title="No folders yet"
          description="After a hospital treats you and files a digital folder, it appears here."
        />
      ) : (
        <div className="grid gap-3">
          {records.map((r) => (
            <RecordFolder
              key={r.id}
              record={r}
              href={`/patient/records/${r.id}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
