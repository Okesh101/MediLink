import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader, Alert, Spinner } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, TextArea } from "../../components/ui/Input";
import { recordsApi } from "../../services/records";
import { accessApi } from "../../services/access";
import { getErrorMessage } from "../../services/api";

export default function PatientLookup() {
  const [query, setQuery] = useState("");
  const [patient, setPatient] = useState(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [looking, setLooking] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const navigate = useNavigate();

  async function onLookup(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setPatient(null);
    const publicId = query.trim();
    if (!publicId) return;
    setLooking(true);
    try {
      const { data } = await recordsApi.lookupPatient(publicId);
      setPatient(data.data);
    } catch (err) {
      setError(getErrorMessage(err, "Patient not found."));
    } finally {
      setLooking(false);
    }
  }

  async function onRequest() {
    if (!patient) return;
    setError("");
    setInfo("");
    setRequesting(true);
    try {
      await accessApi.request({
        patient_public_id: patient.public_id,
        reason: reason.trim() || undefined,
      });
      setInfo("Request sent. Wait for the patient to approve on their phone.");
      setPatient({ ...patient, has_pending_request: true });
    } catch (err) {
      setError(getErrorMessage(err, "Could not send request."));
    } finally {
      setRequesting(false);
    }
  }

  return (
    <div className="max-w-xl">
      <PageHeader
        title="Find a patient"
        description="Enter the Health ID they show you. Confirm it is the right person before requesting records."
      />

      <form
        className="flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={onLookup}
      >
        <Input
          className="flex-1"
          label="Health ID"
          name="public_id"
          value={query}
          onChange={(e) => setQuery(e.target.value.toUpperCase())}
          placeholder="BC4-DG7-MN9Z"
          required
        />
        <Button type="submit" disabled={looking}>
          {looking ? "Searching…" : "Search"}
        </Button>
      </form>

      {error ? <Alert className="mt-4">{error}</Alert> : null}
      {info ? (
        <Alert tone="success" className="mt-4">
          {info}
        </Alert>
      ) : null}

      {looking ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : null}

      {patient ? (
        <div className="mt-6 rounded-2xl border border-line bg-white p-5">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">
            Confirm identity
          </p>
          <p className="mt-2 font-display text-2xl">
            {patient.firstname} {patient.lastname}
          </p>
          <p className="mt-1 public-id text-sm text-teal-800">{patient.public_id}</p>
          <p className="mt-2 text-sm text-muted">
            {patient.sex} · Born {patient.dob}
          </p>

          {patient.has_active_grant ? (
            <div className="mt-5">
              <p className="text-sm text-teal-800">
                You already have active access to this patient’s folders.
              </p>
              <Button
                className="mt-3"
                onClick={() =>
                  navigate(`/staff/patients/${encodeURIComponent(patient.public_id)}`)
                }
              >
                Open folders
              </Button>
            </div>
          ) : patient.has_pending_request ? (
            <p className="mt-5 text-sm text-amber-800">
              A request is already waiting for this patient to approve.
            </p>
          ) : (
            <div className="mt-5 space-y-3">
              <TextArea
                label="Reason (optional)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Walk-in with chest pain"
              />
              <Button onClick={onRequest} disabled={requesting}>
                {requesting ? "Sending…" : "Request access"}
              </Button>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
