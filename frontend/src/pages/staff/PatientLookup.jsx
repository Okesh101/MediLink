import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { recordsApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function PatientLookup() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResults([]);
    setSearched(true);

    try {
      const { data } = await recordsApi.lookupPatient(query.trim());
      setResults([data.data]);
    } catch (err) {
      setError(getErrorMessage(err, "Patient not found. Check the Health ID and try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Find patient"
        description="Ask for the patient's Health ID and enter it below to look up their records."
      />
      <form onSubmit={handleSearch} className="max-w-md">
        <div className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter Health ID (e.g., ABC123456789)"
            className="flex-1"
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </Button>
        </div>
      </form>

      {error && <Alert className="mt-4">{error}</Alert>}

      {searched && results.length === 0 && !loading && !error && (
        <EmptyState
          title="No patient found"
          description="No patient matches this Health ID. Double-check the ID with the patient."
        />
      )}

      {results.length > 0 && (
        <div className="mt-6 space-y-3">
          {results.map((patient) => (
            <div
              key={patient.public_id}
              className="bg-white border border-line rounded-xl p-4 hover:border-teal-400 cursor-pointer transition-colors"
              onClick={() => navigate(`/staff/patients/${encodeURIComponent(patient.public_id)}/dashboard`)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">
                    {patient.firstname} {patient.lastname}
                  </h3>
                  <p className="text-sm text-muted mt-1">ID: {patient.public_id}</p>
                </div>
                <div className="text-right text-sm text-muted">
                  {patient.dob && (
                    <div>DOB: {new Date(patient.dob).toLocaleDateString()}</div>
                  )}
                  {patient.sex && <div>Sex: {patient.sex}</div>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
