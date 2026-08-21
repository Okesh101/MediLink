import { Routes, Route, Navigate } from "react-router-dom";

import LandingPage from "./pages/landing/LandingPage";
import AuthHub from "./pages/auth/AuthHub";
import PatientAuth from "./pages/auth/PatientAuth";
import HospitalAuth from "./pages/auth/HospitalAuth";
import StaffAuth from "./pages/auth/StaffAuth";

import HospitalLayout from "./pages/hospital/HospitalLayout";
import HospitalOverview from "./pages/hospital/HospitalOverview";
import HospitalDoctors from "./pages/hospital/HospitalDoctors";
import OnboardDoctor from "./pages/hospital/OnboardDoctor";
import HospitalProfile from "./pages/hospital/HospitalProfile";

import StaffLayout from "./pages/staff/StaffLayout";
import StaffOverview from "./pages/staff/StaffOverview";
import PatientLookup from "./pages/staff/PatientLookup";
import PatientRecords from "./pages/staff/PatientRecords";
import PatientDashboard from "./pages/staff/PatientDashboard";
import PatientAISummary from "./pages/staff/PatientAISummary";
import CreateRecord from "./pages/staff/CreateRecord";
import StaffRecordDetail from "./pages/staff/StaffRecordDetail";
import StaffRequests from "./pages/staff/StaffRequests";
import StaffMine from "./pages/staff/StaffMine";
import StaffProfile from "./pages/staff/StaffProfile";

import PatientLayout from "./pages/patient/PatientLayout";
import PatientHome from "./pages/patient/PatientHome";
import PatientRequests from "./pages/patient/PatientRequests";
import PatientAccess from "./pages/patient/PatientAccess";
import PatientRecordsList from "./pages/patient/PatientRecords";
import PatientRecordDetail from "./pages/patient/PatientRecordDetail";
import PatientProfile from "./pages/patient/PatientProfile";
import PatientAI from "./pages/patient/PatientAI";

import ProtectedRoute from "./routes/ProtectedRoute";
import ActorRoute from "./routes/ActorRoute";
import GuestRoute from "./routes/GuestRoute";
import "./App.css";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />

      <Route element={<GuestRoute />}>
        <Route path="/auth" element={<AuthHub />} />
        <Route path="/auth/patient" element={<PatientAuth />} />
        <Route path="/auth/hospital" element={<HospitalAuth />} />
        <Route path="/auth/staff" element={<StaffAuth />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<ActorRoute allowed="hospital_admin" />}>
          <Route path="/hospital" element={<HospitalLayout />}>
            <Route index element={<HospitalOverview />} />
            <Route path="doctors" element={<HospitalDoctors />} />
            <Route path="doctors/new" element={<OnboardDoctor />} />
            <Route path="profile" element={<HospitalProfile />} />
          </Route>
        </Route>

        <Route element={<ActorRoute allowed="staff" />}>
          <Route path="/staff" element={<StaffLayout />}>
            <Route index element={<StaffOverview />} />
            <Route path="lookup" element={<PatientLookup />} />
            <Route path="requests" element={<StaffRequests />} />
            <Route path="mine" element={<StaffMine />} />
            <Route path="patients/:publicId" element={<PatientRecords />} />
            <Route path="patients/:publicId/dashboard" element={<PatientDashboard />} />
            <Route path="patients/:publicId/ai-summary" element={<PatientAISummary />} />
            <Route path="patients/:publicId/new" element={<CreateRecord />} />
            <Route path="records/:recordId" element={<StaffRecordDetail />} />
            <Route path="profile" element={<StaffProfile />} />
          </Route>
        </Route>

        <Route element={<ActorRoute allowed="patient" />}>
          <Route path="/patient" element={<PatientLayout />}>
            <Route index element={<PatientHome />} />
            <Route path="requests" element={<PatientRequests />} />
            <Route path="access" element={<PatientAccess />} />
            <Route path="records" element={<PatientRecordsList />} />
            <Route path="records/:recordId" element={<PatientRecordDetail />} />
            <Route path="ai" element={<PatientAI />} />
            <Route path="profile" element={<PatientProfile />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
