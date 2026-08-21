import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader, Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, Select } from "../../components/ui/Input";
import { staffApi } from "../../services/staff";
import { getErrorMessage } from "../../services/api";

export default function OnboardDoctor() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    const form = new FormData(e.currentTarget);
    try {
      await staffApi.onboardDoctor({
        name: form.get("name"),
        email: form.get("email"),
        phone: String(form.get("phone")).trim(),
        nin: String(form.get("nin")).trim(),
        sex: form.get("sex"),
        password: form.get("password"),
      });
      setSuccess("Doctor account created. They can now sign in on the staff portal.");
      setTimeout(() => navigate("/hospital/doctors"), 900);
    } catch (err) {
      setError(getErrorMessage(err, "Could not onboard doctor."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl">
      <PageHeader
        title="Onboard a doctor"
        description="Creates a staff account under this hospital. Share the email and password with the doctor—they use the Doctor portal, not this admin login."
      />
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      {success ? (
        <Alert tone="success" className="mb-4">
          {success}
        </Alert>
      ) : null}
      <form
        className="space-y-3 rounded-2xl border border-line bg-white p-5 sm:p-6"
        onSubmit={onSubmit}
      >
        <Input label="Full name" name="name" required placeholder="Dr. Ada Okonkwo" />
        <Input label="Email" name="email" type="email" required />
        <Input
          label="Phone"
          name="phone"
          inputMode="numeric"
          required
          maxLength={11}
          hint="Exactly 11 digits"
        />
        <Input
          label="NIN"
          name="nin"
          inputMode="numeric"
          required
          maxLength={11}
        />
        <Select label="Sex" name="sex" required defaultValue="">
          <option value="" disabled>
            Select
          </option>
          <option value="male">Male</option>
          <option value="female">Female</option>
        </Select>
        <Input
          label="Temporary password"
          name="password"
          type="password"
          required
        />
        <Button type="submit" disabled={loading}>
          {loading ? "Saving…" : "Create doctor account"}
        </Button>
      </form>
    </div>
  );
}
