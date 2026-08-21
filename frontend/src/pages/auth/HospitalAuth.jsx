import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthCard } from "../../components/auth/AuthCard";
import { Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, TextArea } from "../../components/ui/Input";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";

export default function HospitalAuth() {
  const [mode, setMode] = useState("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function onLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(e.currentTarget);
    try {
      await authApi.loginHospital({
        email: form.get("email"),
        password: form.get("password"),
      });
      navigate("/hospital");
    } catch (err) {
      setError(getErrorMessage(err, "Login failed."));
    } finally {
      setLoading(false);
    }
  }

  async function onRegister(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(e.currentTarget);
    try {
      await authApi.registerHospital({
        reg_no: form.get("reg_no"),
        name: form.get("name"),
        email: form.get("email"),
        phone: String(form.get("phone")).trim(),
        address: form.get("address"),
        password: form.get("password"),
      });
      await authApi.loginHospital({
        email: form.get("email"),
        password: form.get("password"),
      });
      navigate("/hospital");
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title={mode === "login" ? "Hospital admin sign in" : "Register hospital"}
      subtitle={
        mode === "login"
          ? "Manage doctors and your facility profile."
          : "Create the admin account, then onboard your doctors."
      }
      footer={
        mode === "login" ? (
          <>
            New facility?{" "}
            <button
              type="button"
              className="text-teal-800 font-medium"
              onClick={() => {
                setMode("register");
                setError("");
              }}
            >
              Register
            </button>
            {" · "}
            <Link to="/auth" className="text-teal-800">
              Other portals
            </Link>
          </>
        ) : (
          <>
            Already registered?{" "}
            <button
              type="button"
              className="text-teal-800 font-medium"
              onClick={() => {
                setMode("login");
                setError("");
              }}
            >
              Sign in
            </button>
          </>
        )
      }
    >
      {error ? <Alert className="mb-4">{error}</Alert> : null}

      {mode === "login" ? (
        <form className="space-y-4" onSubmit={onLogin}>
          <Input label="Work email" name="email" type="email" required />
          <Input label="Password" name="password" type="password" required />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      ) : (
        <form className="space-y-3" onSubmit={onRegister}>
          <Input label="Hospital name" name="name" required />
          <Input
            label="Registration number"
            name="reg_no"
            required
            hint="Official facility reg. no."
          />
          <Input label="Admin email" name="email" type="email" required />
          <Input
            label="Phone"
            name="phone"
            inputMode="numeric"
            required
            maxLength={11}
          />
          <TextArea label="Address" name="address" required rows={3} />
          <Input label="Password" name="password" type="password" required />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating…" : "Create hospital account"}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
