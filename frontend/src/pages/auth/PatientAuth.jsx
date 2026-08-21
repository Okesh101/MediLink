import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthCard } from "../../components/auth/AuthCard";
import { Alert } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Input, Select } from "../../components/ui/Input";
import { authApi } from "../../services/auth";
import { getErrorMessage } from "../../services/api";

export default function PatientAuth() {
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
      await authApi.loginPatient({
        phone: String(form.get("phone")).trim(),
        password: form.get("password"),
      });
      navigate("/patient");
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
      await authApi.registerPatient({
        firstname: form.get("firstname"),
        lastname: form.get("lastname"),
        sex: form.get("sex"),
        phone: String(form.get("phone")).trim(),
        dob: form.get("dob"),
        nin: String(form.get("nin")).trim(),
        email: form.get("email") || undefined,
        password: form.get("password"),
      });
      await authApi.loginPatient({
        phone: String(form.get("phone")).trim(),
        password: form.get("password"),
      });
      navigate("/patient");
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title={mode === "login" ? "Patient sign in" : "Create patient account"}
      subtitle={
        mode === "login"
          ? "Use the phone number you registered with."
          : "You’ll receive a universal Health ID after signup."
      }
      footer={
        mode === "login" ? (
          <>
            No account?{" "}
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
            Have an account?{" "}
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
          <Input
            label="Phone"
            name="phone"
            inputMode="numeric"
            placeholder="11-digit phone"
            required
            maxLength={11}
          />
          <Input
            label="Password"
            name="password"
            type="password"
            required
            autoComplete="current-password"
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      ) : (
        <form className="space-y-3" onSubmit={onRegister}>
          <div className="grid grid-cols-2 gap-3">
            <Input label="First name" name="firstname" required />
            <Input label="Last name" name="lastname" required />
          </div>
          <Select label="Sex" name="sex" required defaultValue="">
            <option value="" disabled>
              Select
            </option>
            <option value="male">Male</option>
            <option value="female">Female</option>
          </Select>
          <Input label="Date of birth" name="dob" type="date" required />
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
            hint="National Identity Number"
          />
          <Input label="Email (optional)" name="email" type="email" />
          <Input
            label="Password"
            name="password"
            type="password"
            required
            minLength={6}
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating…" : "Create account"}
          </Button>
        </form>
      )}
    </AuthCard>
  );
}
