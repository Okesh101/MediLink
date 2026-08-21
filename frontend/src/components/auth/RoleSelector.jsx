import { Building2, UserRound } from "lucide-react";

const RoleSelector = ({ role, setRole }) => {
  return (
    <div className="grid grid-cols-2 gap-3 mb-6">

      <button
        type="button"
        onClick={() => setRole("hospital")}
        className={`flex flex-col items-center justify-center gap-2 rounded-xl border p-4 transition ${
          role === "hospital"
            ? "border-indigo-600 bg-indigo-50 text-indigo-700"
            : "border-gray-200 text-gray-500 hover:border-gray-300"
        }`}
      >
        <Building2 size={24} />

        <span className="text-sm font-medium">
          Hospital
        </span>
      </button>

      <button
        type="button"
        onClick={() => setRole("patient")}
        className={`flex flex-col items-center justify-center gap-2 rounded-xl border p-4 transition ${
          role === "patient"
            ? "border-indigo-600 bg-indigo-50 text-indigo-700"
            : "border-gray-200 text-gray-500 hover:border-gray-300"
        }`}
      >
        <UserRound size={24} />

        <span className="text-sm font-medium">
          Patient
        </span>
      </button>

    </div>
  );
};

export default RoleSelector;