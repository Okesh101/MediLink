import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader, Spinner, Alert, EmptyState } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { staffApi } from "../../services/staff";
import { getErrorMessage } from "../../services/api";
import { formatDate } from "../../lib/format";

export default function HospitalDoctors() {
  const [staff, setStaff] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await staffApi.list();
        if (!cancelled) setStaff(data.data || []);
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
        title="Doctors"
        description="Staff you have onboarded. They sign in at the doctor portal with the email and password you set."
        actions={
          <Link to="/hospital/doctors/new">
            <Button>Onboard doctor</Button>
          </Link>
        }
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-7 w-7" />
        </div>
      ) : staff.length === 0 ? (
        <EmptyState
          title="No staff on file"
          description="Doctors cannot self-register. Add them here first."
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-white">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wider text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Phone</th>
                <th className="px-4 py-3 font-medium">Sex</th>
                <th className="px-4 py-3 font-medium">Added</th>
              </tr>
            </thead>
            <tbody>
              {staff.map((d) => (
                <tr key={d.id} className="border-b border-line last:border-0">
                  <td className="px-4 py-3 font-medium">{d.name}</td>
                  <td className="px-4 py-3">{d.email}</td>
                  <td className="px-4 py-3">{d.phone}</td>
                  <td className="px-4 py-3">{d.sex}</td>
                  <td className="px-4 py-3 text-muted">{formatDate(d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
