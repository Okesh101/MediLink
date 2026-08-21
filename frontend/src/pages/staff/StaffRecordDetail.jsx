import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Spinner, Alert } from "../../components/ui/Badge";
import { RecordDetailView } from "../../components/records/RecordFolder";
import { recordsApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function StaffRecordDetail() {
  const { recordId } = useParams();
  const [record, setRecord] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await recordsApi.get(recordId);
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
    <RecordDetailView
      record={record}
      note="Read-only. Records cannot be edited or deleted by any hospital or the patient."
    />
  );
}
