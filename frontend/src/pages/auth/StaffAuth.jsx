import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthCard } from "../../components/auth/AuthCard";
import { Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";

export default function StaffAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function onLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(e.currentTarget);
    try {
      await authApi.loginStaff({
        email: form.get("email"),
        password: form.get("password"),
      });
      navigate("/staff");
    } catch (err) {
      setError(getErrorMessage(err, "Login failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="Doctor / staff sign in"
      subtitle="Use the email and password your hospital admin created for you. There is no self-registration."
      footer={
        <>
          Hospital admin?{" "}
          <Link to="/auth/hospital" className="text-teal-800 font-medium">
            Sign in here
          </Link>
          {" · "}
          <Link to="/auth" className="text-teal-800">
            Other portals
          </Link>
        </>
      }
    >
      {error ? <Alert className="mb-4">{error}</Alert> : null}
      <form className="space-y-4" onSubmit={onLogin}>
        <Input label="Email" name="email" type="email" required />
        <Input label="Password" name="password" type="password" required />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthCard>
  );
}
