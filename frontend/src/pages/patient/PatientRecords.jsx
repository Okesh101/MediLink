import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import DataTable from "../../components/ai/DataTable";
import { patientApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function PatientRecords() {
  const navigate = useNavigate();
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
    navigate(`/patient/records/${record.id}`);
  };

  return (
    <div>
      <PageHeader
        title="My Medical Records"
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
