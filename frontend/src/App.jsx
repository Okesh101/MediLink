import { Routes, Route, Navigate } from "react-router-dom";

import AuthPage from "./pages/auth/AuthPage";

import HospitalDashboard from "./pages/hospital/HospitalDashboard";
import PatientDashboard from "./pages/patient/PatientDashboard";

import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRoute from "./routes/RoleRoute";
import "./App.css"

const App = () => {
  return (
    <Routes>
      {/* Auth */}
      <Route path="/auth" element={<AuthPage />} />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        {/* Hospital */}
        <Route element={<RoleRoute allowedRole="hospital" />}>
          <Route path="/hospital/dashboard" element={<HospitalDashboard />} />
        </Route>

        {/* Patient */}
        <Route element={<RoleRoute allowedRole="patient" />}>
          <Route path="/patient/dashboard" element={<PatientDashboard />} />
        </Route>
      </Route>

      {/* Default */}
      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  );
};

export default App;
