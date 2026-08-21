import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { User, FileText, Brain, Calendar, Activity, ArrowRight } from "lucide-react";
import { Spinner, Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import DataTable from "../../components/ai/DataTable";
import { recordsApi } from "../../services/records";
import { aiApi } from "../../services/ai";
import { getErrorMessage } from "../../services/api";

export default function PatientDashboard() {
  const { publicId } = useParams();
  const decoded = decodeURIComponent(publicId);
  const [patient, setPatient] = useState(null);
  const [records, setRecords] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [patientData, recordsData, summaryData] = await Promise.all([
          recordsApi.lookupPatient(decoded),
          recordsApi.getPatientRecords(decoded),
          aiApi.getPatientSummary(decoded).catch(() => ({ data: { data: null } }))
        ]);
        
        if (!cancelled) {
          setPatient(patientData.data.data);
          setRecords(recordsData.data.data || []);
          setAiSummary(summaryData.data.data);
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [decoded]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  if (error) {
    return <Alert>{error}</Alert>;
  }

  const recordColumns = [
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
    }
  ];

  return (
    <div className="space-y-6">
      {/* Patient Info Card */}
      <div className="bg-white rounded-2xl border border-line shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-teal-100 rounded-xl">
              <User className="h-6 w-6 text-teal-700" />
            </div>
            <div>
              <h2 className="font-display text-xl">
                {patient?.firstname} {patient?.lastname}
              </h2>
              <p className="text-sm text-muted mt-1">ID: {patient?.public_id}</p>
              <div className="flex gap-4 mt-3 text-sm">
                <div>
                  <span className="text-muted">Blood Group:</span>
                  <span className="ml-1 font-medium">{patient?.blood_group || "Unknown"}</span>
                </div>
                <div>
                  <span className="text-muted">Genotype:</span>
                  <span className="ml-1 font-medium">{patient?.genotype || "Unknown"}</span>
                </div>
                <div>
                  <span className="text-muted">Age:</span>
                  <span className="ml-1 font-medium">
                    {patient?.date_of_birth 
                      ? Math.floor((new Date() - new Date(patient.date_of_birth)) / (365.25 * 24 * 60 * 60 * 1000))
                      : "Unknown"}
                  </span>
                </div>
              </div>
              {patient?.allergies && (
                <div className="mt-2 text-sm">
                  <span className="text-muted">Allergies:</span>
                  <span className="ml-1 text-red-600 font-medium">{patient.allergies}</span>
                </div>
              )}
            </div>
          </div>
          <Link to={`/staff/patients/${encodeURIComponent(decoded)}/new`}>
            <Button>Create New Record</Button>
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link 
          to={`/staff/patients/${encodeURIComponent(decoded)}/ai-summary`}
          className="bg-white rounded-xl border border-line p-5 hover:border-teal-400 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="h-5 w-5 text-purple-700" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium">AI Summary</h3>
              <p className="text-xs text-muted mt-1">View AI-generated patient summary</p>
            </div>
            <ArrowRight className="h-4 w-4 text-muted" />
          </div>
        </Link>

        <Link 
          to={`/staff/patients/${encodeURIComponent(decoded)}`}
          className="bg-white rounded-xl border border-line p-5 hover:border-teal-400 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="h-5 w-5 text-blue-700" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium">All Records</h3>
              <p className="text-xs text-muted mt-1">View complete medical history</p>
            </div>
            <ArrowRight className="h-4 w-4 text-muted" />
          </div>
        </Link>

        <div className="bg-white rounded-xl border border-line p-5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Activity className="h-5 w-5 text-green-700" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium">Total Records</h3>
              <p className="text-2xl font-display text-teal-900 mt-1">{records.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* AI Summary Preview */}
      {aiSummary && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <Brain className="h-5 w-5 text-purple-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-purple-900">Latest AI Summary</h3>
              <p className="text-sm text-purple-700 mt-2 line-clamp-3">
                {aiSummary.summary}
              </p>
              <Link 
                to={`/staff/patients/${encodeURIComponent(decoded)}/ai-summary`}
                className="text-sm text-purple-600 font-medium mt-2 inline-flex items-center gap-1 hover:underline"
              >
                View full summary <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Recent Records Table */}
      <div className="bg-white rounded-2xl border border-line shadow-sm">
        <div className="px-6 py-4 border-b border-line">
          <h3 className="font-display text-lg">Recent Medical Records</h3>
          <p className="text-sm text-muted">Latest patient encounters</p>
        </div>
        <div className="p-6">
          <DataTable
            data={records.slice(0, 5)}
            columns={recordColumns}
            onRowClick={(record) => window.location.href = `/staff/records/${record.id}`}
            searchable={false}
            filterable={false}
          />
          {records.length > 5 && (
            <Link 
              to={`/staff/patients/${encodeURIComponent(decoded)}`}
              className="block text-center mt-4 text-sm text-teal-600 hover:underline"
            >
              View all {records.length} records
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
