"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface Nutritionist {
  id: string;
  full_name: string;
  email: string;
  clinic_name: string;
  status: string;
  created_at: string;
  approved_at: string | null;
}

interface Stats {
  nutritionists: Record<string, number>;
  clients: Record<string, number>;
  total_nutritionists: number;
  total_clients: number;
  pending_queries: number;
}

export default function AdminPage() {
  const { user, token, loading, login } = useAuth();
  const router = useRouter();
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [nutritionists, setNutritionists] = useState<Nutritionist[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loadingData, setLoadingData] = useState(false);
  const [loginError, setLoginError] = useState("");

  // If already logged in as admin, show panel
  const isAdmin = user?.role === "admin";
  const adminToken = token;

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    try {
      const data = await apiPost("/auth/admin/login", loginForm);
      // Use shared auth context
      login(data.token, { ...data.user, role: "admin" });
    } catch (err: any) {
      setLoginError(err.message);
    }
  };

  useEffect(() => {
    if (isAdmin && adminToken) {
      setLoadingData(true);
      Promise.all([
        apiGet("/admin/nutritionists", adminToken),
        apiGet("/admin/stats", adminToken),
      ])
        .then(([nuts, st]) => {
          setNutritionists(nuts);
          setStats(st);
        })
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [isAdmin, adminToken]);

  const handleApprove = async (id: string) => {
    if (!adminToken) return;
    try {
      await apiPatch(`/admin/nutritionists/${id}/approve`, {}, adminToken);
      setNutritionists(nutritionists.map((n) =>
        n.id === id ? { ...n, status: "active" } : n
      ));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handlePause = async (id: string) => {
    if (!adminToken) return;
    try {
      await apiPatch(`/admin/nutritionists/${id}/pause`, {}, adminToken);
      setNutritionists(nutritionists.map((n) =>
        n.id === id ? { ...n, status: "paused" } : n
      ));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleReactivate = async (id: string) => {
    if (!adminToken) return;
    try {
      await apiPatch(`/admin/nutritionists/${id}/reactivate`, {}, adminToken);
      setNutritionists(nutritionists.map((n) =>
        n.id === id ? { ...n, status: "active" } : n
      ));
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Not logged in or logged in as nutritionist — show admin login
  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
            <p className="text-sm text-gray-500 mt-1">Platform management</p>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            {loginError && (
              <div className="bg-red-50 border border-red-100 text-red-700 p-3 rounded-xl text-sm mb-4">
                {loginError}
              </div>
            )}

            <form onSubmit={handleAdminLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Admin Email</label>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm bg-gray-50 focus:bg-white"
                  required
                  suppressHydrationWarning
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm bg-gray-50 focus:bg-white"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full bg-gray-900 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-gray-800 transition-colors"
              >
                Login as Admin
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Admin is logged in — show panel
  return (
    <>
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-8">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 text-center">
              <p className="text-3xl font-bold text-emerald-600">{stats.total_nutritionists}</p>
              <p className="text-sm text-gray-500 mt-1">Nutritionists</p>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{stats.total_clients}</p>
              <p className="text-sm text-gray-500 mt-1">Clients</p>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{stats.pending_queries}</p>
              <p className="text-sm text-gray-500 mt-1">Pending Queries</p>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 text-center">
              <p className="text-3xl font-bold text-amber-600">{stats.nutritionists?.pending || 0}</p>
              <p className="text-sm text-gray-500 mt-1">Pending Approvals</p>
            </div>
          </div>
        )}

        {/* Nutritionists Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
          <div className="p-4 sm:p-5 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Nutritionists</h2>
          </div>
          {loadingData ? (
            <div className="p-5 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-3 sm:p-4 font-medium text-gray-600">Name</th>
                    <th className="text-left p-3 sm:p-4 font-medium text-gray-600 hidden sm:table-cell">Email</th>
                    <th className="text-left p-3 sm:p-4 font-medium text-gray-600 hidden md:table-cell">Clinic</th>
                    <th className="text-left p-3 sm:p-4 font-medium text-gray-600">Status</th>
                    <th className="text-left p-3 sm:p-4 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {nutritionists.map((nut) => (
                    <tr key={nut.id} className="border-t border-gray-100">
                      <td className="p-3 sm:p-4 font-medium text-gray-900">{nut.full_name}</td>
                      <td className="p-3 sm:p-4 text-gray-500 hidden sm:table-cell">{nut.email}</td>
                      <td className="p-3 sm:p-4 text-gray-500 hidden md:table-cell">{nut.clinic_name || "-"}</td>
                      <td className="p-3 sm:p-4">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                          nut.status === "active" ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20" :
                          nut.status === "pending" ? "bg-amber-50 text-amber-700 ring-amber-600/20" :
                          "bg-gray-50 text-gray-600 ring-gray-500/20"
                        }`}>
                          {nut.status}
                        </span>
                      </td>
                      <td className="p-3 sm:p-4">
                        <div className="flex gap-2">
                          {nut.status === "pending" && (
                            <button
                              onClick={() => handleApprove(nut.id)}
                              className="text-xs bg-emerald-600 text-white px-3 py-1.5 rounded-lg hover:bg-emerald-700 transition-colors font-medium"
                            >
                              Approve
                            </button>
                          )}
                          {nut.status === "active" && (
                            <button
                              onClick={() => handlePause(nut.id)}
                              className="text-xs bg-amber-500 text-white px-3 py-1.5 rounded-lg hover:bg-amber-600 transition-colors font-medium"
                            >
                              Pause
                            </button>
                          )}
                          {nut.status === "paused" && (
                            <button
                              onClick={() => handleReactivate(nut.id)}
                              className="text-xs bg-blue-500 text-white px-3 py-1.5 rounded-lg hover:bg-blue-600 transition-colors font-medium"
                            >
                              Reactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
