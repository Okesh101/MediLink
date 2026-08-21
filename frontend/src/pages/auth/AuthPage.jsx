import { useState } from "react";

import AuthLayout from "../../components/auth/AuthLayout";
import LoginForm from "../../components/auth/LoginForm";
import RegisterForm from "../../components/auth/RegisterForm";

const AuthPage = () => {
  const [mode, setMode] = useState("login");

  return (
    <AuthLayout
      mode={mode}
      setMode={setMode}
    >
      {mode === "login" ? (
        <LoginForm />
      ) : (
        <RegisterForm />
      )}
    </AuthLayout>
  );
};

export default AuthPage;