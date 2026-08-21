import { useState } from "react";
import {
  Eye,
  EyeOff,
  Lock,
  Mail,
  User,
  Building2,
  Phone,
  Loader2,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import RoleSelector from "./RoleSelector";
import api from "../../services/api";

const RegisterForm = () => {
  const navigate = useNavigate();

  const [role, setRole] = useState("patient");

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    phone: "",
    hospitalName: "",
    licenseNumber: "",
  });

  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const payload = {
        ...formData,
        role,
      };

      const response = await api.post(
        "/auth/register",
        payload
      );

      setSuccess(
        response.data?.message ||
          "Account created successfully."
      );

      /*
        Usually registration should redirect
        to login instead of automatically logging
        the user in.
      */

      setTimeout(() => {
        navigate("/auth");
      }, 1500);

    } catch (err) {
      setError(
        err.response?.data?.message ||
          "Unable to create account."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>

      <div className="mb-7">

        <h2 className="text-2xl font-bold text-gray-900">
          Create your account
        </h2>

        <p className="text-gray-500 mt-2">
          Choose your account type to get started.
        </p>

      </div>

      <RoleSelector
        role={role}
        setRole={setRole}
      />

      {error && (
        <div className="mb-5 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-5 rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-600">
          {success}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="space-y-4"
      >

        {/* Name */}
        <div>

          <label className="block text-sm font-medium text-gray-700 mb-2">
            {role === "hospital"
              ? "Administrator name"
              : "Full name"}
          </label>

          <div className="relative">

            <User
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder={
                role === "hospital"
                  ? "Administrator name"
                  : "Your full name"
              }
              required
              className="w-full rounded-xl border border-gray-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />

          </div>

        </div>

        {/* Hospital fields */}
        {role === "hospital" && (
          <>
            <div>

              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hospital name
              </label>

              <div className="relative">

                <Building2
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  type="text"
                  name="hospitalName"
                  value={formData.hospitalName}
                  onChange={handleChange}
                  placeholder="Hospital name"
                  required
                  className="w-full rounded-xl border border-gray-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                />

              </div>

            </div>

            <div>

              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hospital license number
              </label>

              <input
                type="text"
                name="licenseNumber"
                value={formData.licenseNumber}
                onChange={handleChange}
                placeholder="License number"
                required
                className="w-full rounded-xl border border-gray-200 py-3 px-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />

            </div>
          </>
        )}

        {/* Email */}
        <div>

          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email address
          </label>

          <div className="relative">

            <Mail
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              required
              className="w-full rounded-xl border border-gray-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />

          </div>

        </div>

        {/* Phone */}
        <div>

          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone number
          </label>

          <div className="relative">

            <Phone
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+234..."
              required
              className="w-full rounded-xl border border-gray-200 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />

          </div>

        </div>

        {/* Password */}
        <div>

          <label className="block text-sm font-medium text-gray-700 mb-2">
            Password
          </label>

          <div className="relative">

            <Lock
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              type={showPassword ? "text" : "password"}
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a strong password"
              required
              minLength={8}
              className="w-full rounded-xl border border-gray-200 py-3 pl-10 pr-11 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />

            <button
              type="button"
              onClick={() =>
                setShowPassword(!showPassword)
              }
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              {showPassword ? (
                <EyeOff size={18} />
              ) : (
                <Eye size={18} />
              )}
            </button>

          </div>

        </div>

        {/* Terms */}
        <div className="flex items-start gap-2 pt-1">

          <input
            type="checkbox"
            required
            className="mt-1 accent-indigo-600"
          />

          <p className="text-xs text-gray-500 leading-relaxed">
            I agree to the platform's terms of service
            and privacy policy.
          </p>

        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-indigo-600 py-3.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-60 flex items-center justify-center gap-2"
        >

          {loading ? (
            <>
              <Loader2
                size={18}
                className="animate-spin"
              />
              Creating account...
            </>
          ) : (
            "Create account"
          )}

        </button>

      </form>

    </div>
  );
};

export default RegisterForm;