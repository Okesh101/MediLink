import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Spinner, Alert } from "../../components/ui/Badge";
import { RecordDetailView } from "../../components/records/RecordFolder";
import { patientApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function PatientRecordDetail() {
  const { recordId } = useParams();
  const [record, setRecord] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await patientApi.getRecord(recordId);
        if (!cancelled) setRecord(data.data);
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [recordId]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }
  if (error) return <Alert>{error}</Alert>;
  if (!record) return null;

  return (
    <div className="mx-auto max-w-lg">
      <RecordDetailView
        record={record}
        note="This folder is permanent. You can read it; you cannot change or delete it."
      />
    </div>
  );
}
