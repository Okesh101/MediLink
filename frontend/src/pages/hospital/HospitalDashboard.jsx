import { Building2, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const HospitalDashboard = () => {
  const navigate = useNavigate();

  const user = useAuthStore(
    (state) => state.user
  );

  const logout = useAuthStore(
    (state) => state.logout
  );

  const handleLogout = () => {
    logout();
    navigate("/auth");
  };

  return (
    <div className="min-h-screen bg-gray-50">

      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-5 py-4 flex items-center justify-between">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center">
              <Building2 size={20} />
            </div>

            <div>
              <h1 className="font-bold text-gray-900">
                Hospital Dashboard
              </h1>

              <p className="text-xs text-gray-500">
                {user?.name}
              </p>
            </div>

          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600"
          >
            <LogOut size={18} />
            Logout
          </button>

        </div>
      </header>

      <main className="max-w-7xl mx-auto px-5 py-8">

        <h2 className="text-2xl font-bold text-gray-900">
          Welcome back 👋
        </h2>

        <p className="text-gray-500 mt-1">
          Your hospital overview will appear here.
        </p>

      </main>

    </div>
  );
};

export default HospitalDashboard;