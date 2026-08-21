import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { PageHeader, Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, TextArea } from "../../components/ui/Input";
import { recordsApi } from "../../services/records";
import { getErrorMessage } from "../../services/api";

export default function CreateRecord() {
  const { publicId } = useParams();
  const decoded = decodeURIComponent(publicId);
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function onFiles(e) {
    setFiles(Array.from(e.target.files || []));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const form = e.currentTarget;
    const fd = new FormData();
    fd.append("patient_public_id", decoded);
    fd.append("diagnosis", form.diagnosis.value.trim());
    if (form.chief_complaint.value.trim()) {
      fd.append("chief_complaint", form.chief_complaint.value.trim());
    }
    if (form.doctor_notes.value.trim()) {
      fd.append("doctor_notes", form.doctor_notes.value.trim());
    }
    files.forEach((file, i) => {
      fd.append("documents", file);
      const titleInput = form.querySelector(`[name="title_${i}"]`);
      fd.append("document_titles", titleInput?.value?.trim() || file.name);
    });
    try {
      const { data } = await recordsApi.create(fd);
      navigate(`/staff/records/${data.data.id}`);
    } catch (err) {
      setError(getErrorMessage(err, "Could not create folder."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <PageHeader
        title="New encounter folder"
        description={`Same as pulling a new paper file for ${decoded}. Once saved, this folder cannot be edited or deleted.`}
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      <form
        className="space-y-4 rounded-2xl border border-line bg-white p-5 sm:p-6"
        onSubmit={onSubmit}
      >
        <Input
          label="Diagnosis"
          name="diagnosis"
          required
          placeholder="Working diagnosis"
        />
        <TextArea
          label="Chief complaint"
          name="chief_complaint"
          placeholder="Why they presented today"
        />
        <TextArea
          label="Doctor notes"
          name="doctor_notes"
          placeholder="Clinical notes for this visit"
        />
        <label className="block space-y-1.5">
          <span className="text-sm font-medium">Files (reports, scans, labs)</span>
          <input
            type="file"
            multiple
            onChange={onFiles}
            className="block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-teal-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-teal-900"
          />
        </label>
        {files.length > 0 ? (
          <ul className="space-y-2">
            {files.map((file, i) => (
              <li key={`${file.name}-${i}`}>
                <Input
                  label={`Title for ${file.name}`}
                  name={`title_${i}`}
                  defaultValue={file.name.replace(/\.[^.]+$/, "")}
                />
              </li>
            ))}
          </ul>
        ) : null}
        <Button type="submit" disabled={loading}>
          {loading ? "Saving folder…" : "Save immutable folder"}
        </Button>
      </form>
    </div>
  );
}
