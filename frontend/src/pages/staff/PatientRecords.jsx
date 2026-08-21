import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import DataTable from "../../components/ai/DataTable";
import { recordsApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function PatientRecords() {
  const { publicId } = useParams();
  const decoded = decodeURIComponent(publicId);
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [lookup, setLookup] = useState(null);
  const [error, setError] = useState("");
  const [accessMeta, setAccessMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      setAccessMeta(null);
      try {
        const [hist, id] = await Promise.all([
          recordsApi.getPatientRecords(decoded),
          recordsApi.lookupPatient(decoded),
        ]);
        if (cancelled) return;
        setRecords(hist.data.data || []);
        setLookup(id.data.data);
      } catch (err) {
        if (cancelled) return;
        const body = err.response?.data;
        if (body?.access_required) {
          setAccessMeta(body);
          try {
            const id = await recordsApi.lookupPatient(decoded);
            if (!cancelled) setLookup(id.data.data);
          } catch {
            /* lookup may still work */
          }
        } else {
          setError(getErrorMessage(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [decoded]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  const name = lookup
    ? `${lookup.firstname} ${lookup.lastname}`
    : decoded;

  const columns = [
    {
      key: "hospital_name",
      label: "Hospital",
      sortable: true,
      filterable: true
    },
    {
      key: "diagnosis",
      label: "Diagnosis",
      sortable: true,
      render: (value) => value || "N/A"
    },
    {
      key: "doctor_name",
      label: "Doctor",
      sortable: true,
      filterable: true
    },
    {
      key: "created_at",
      label: "Date",
      sortable: true,
      render: (value) => new Date(value).toLocaleDateString()
    },
    {
      key: "status",
      label: "Status",
      sortable: true,
      filterable: true,
      render: (value) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          value === "completed" 
            ? "bg-green-100 text-green-700" 
            : "bg-yellow-100 text-yellow-700"
        }`}>
          {value || "Active"}
        </span>
      )
    }
  ];

  const handleRowClick = (record) => {
    navigate(`/staff/records/${record.id}`);
  };

  return (
    <div>
      <PageHeader
        title={name}
        description="Past folders from every hospital that treated this patient. You can read them; you cannot edit or delete them. Open a new folder for today's visit."
        actions={
          !accessMeta ? (
            <Link to={`/staff/patients/${encodeURIComponent(decoded)}/new`}>
              <Button>Open new folder</Button>
            </Link>
          ) : (
            <Button variant="secondary" onClick={() => navigate("/staff/lookup")}>
              Back to lookup
            </Button>
          )
        }
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {accessMeta ? (
        <Alert className="mb-4">
          {accessMeta.message}
          {accessMeta.has_pending_request
            ? " A request is already pending."
            : " Request access from Find patient."}
        </Alert>
      ) : null}

      {!accessMeta && records.length === 0 ? (
        <EmptyState
          title="No prior folders"
          description="This patient has no uploaded records yet. Create the first digital folder for this visit."
          action={
            <Link to={`/staff/patients/${encodeURIComponent(decoded)}/new`}>
              <Button>Create folder</Button>
            </Link>
          }
        />
      ) : (
        <DataTable
          data={records}
          columns={columns}
          onRowClick={handleRowClick}
          searchable={true}
          filterable={true}
        />
      )}
    </div>
  );
}
