import { ShieldCheck, HeartPulse, LockKeyhole } from "lucide-react";

const AuthLayout = ({ children, mode, setMode }) => {
  return (
    <div className="min-h-screen bg-slate-50 flex">

      {/* Left side */}
      <div className="hidden lg:flex lg:w-1/2 bg-indigo-700 text-white relative overflow-hidden">

        <div className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-indigo-500 opacity-40" />

        <div className="absolute -bottom-32 -left-20 w-80 h-80 rounded-full bg-indigo-800 opacity-50" />

        <div className="relative z-10 flex flex-col justify-center px-16 xl:px-24">

          <div className="flex items-center gap-3 mb-10">
            <div className="w-11 h-11 rounded-xl bg-white/15 flex items-center justify-center">
              <HeartPulse size={25} />
            </div>

            <span className="text-xl font-bold">
              MediVault
            </span>
          </div>

          <h1 className="text-4xl xl:text-5xl font-bold leading-tight mb-6">
            Secure access to
            <br />
            better healthcare.
          </h1>

          <p className="text-indigo-100 text-lg max-w-md leading-relaxed">
            A secure healthcare platform that allows hospitals
            and patients to manage and share medical records
            with the right people.
          </p>

          <div className="mt-10 space-y-5">

            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                <ShieldCheck size={20} />
              </div>

              <div>
                <p className="font-semibold">
                  Secure medical records
                </p>

                <p className="text-sm text-indigo-200">
                  Your health information stays protected.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                <LockKeyhole size={20} />
              </div>

              <div>
                <p className="font-semibold">
                  Controlled access
                </p>

                <p className="text-sm text-indigo-200">
                  Patients control who can access their records.
                </p>
              </div>
            </div>

          </div>

        </div>
      </div>

      {/* Right side */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-5 py-10">

        <div className="w-full max-w-md">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center justify-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center">
              <HeartPulse size={22} />
            </div>

            <span className="font-bold text-xl text-gray-900">
              MediVault
            </span>
          </div>

          {/* Tabs */}
          <div className="flex bg-gray-100 rounded-xl p-1 mb-8">

            <button
              onClick={() => setMode("login")}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition ${
                mode === "login"
                  ? "bg-white text-indigo-700 shadow-sm"
                  : "text-gray-500"
              }`}
            >
              Login
            </button>

            <button
              onClick={() => setMode("register")}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition ${
                mode === "register"
                  ? "bg-white text-indigo-700 shadow-sm"
                  : "text-gray-500"
              }`}
            >
              Register
            </button>

          </div>

          {children}

        </div>

      </div>

    </div>
  );
};

export default AuthLayout;