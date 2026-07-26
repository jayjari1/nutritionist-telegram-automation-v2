"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { apiGet, apiPost } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface Client {
  id: string;
  full_name: string;
  program_type: string;
  status: string;
  program_end: string;
  telegram_group_id: number | null;
  invite_code?: string;
}

function daysRemaining(endDate: string): number {
  const end = new Date(endDate);
  const now = new Date();
  const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return Math.max(0, diff);
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: "bg-emerald-500",
    paused: "bg-amber-500",
    expired: "bg-red-500",
  };
  return <span className={`w-2 h-2 rounded-full ${colors[status] || "bg-gray-400"}`} />;
}

function getInviteCode(clientId: string): string {
  const clean = clientId.replace(/-/g, "").slice(0, 8).toUpperCase();
  return `NC-${clean}`;
}

export default function DashboardPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [clients, setClients] = useState<Client[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newClient, setNewClient] = useState({
    full_name: "",
    program_type: "General Nutrition",
    program_duration: 30,
    diet_chart: "",
    checkin_time: "19:00:00",
  });

  useEffect(() => {
    if (!loading && !token) router.push("/auth/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (token) {
      apiGet("/clients", token)
        .then(setClients)
        .catch(console.error)
        .finally(() => setLoadingClients(false));
    }
  }, [token]);

  const handleAddClient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const data = await apiPost("/clients", newClient, token);
      setClients([data.client, ...clients]);
      setShowAdd(false);
      setNewClient({
        full_name: "",
        program_type: "General Nutrition",
        program_duration: 30,
        diet_chart: "",
        checkin_time: "19:00:00",
      });
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading || !token) return null;

  return (
    <>
      <Navbar />
      <main className="pb-20">
        {/* Header Section */}
        <div className="bg-white border-b border-gray-100 px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">My Clients</h1>
              <p className="text-sm text-gray-500">{clients.length} total</p>
            </div>
            <button
              onClick={() => setShowAdd(!showAdd)}
              className="bg-emerald-600 text-white w-10 h-10 rounded-full flex items-center justify-center shadow-lg shadow-emerald-600/30 active:scale-95 transition-transform"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>

        <div className="px-4">
          {/* Add Client Form */}
          {showAdd && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mt-4">
              <h3 className="font-semibold text-gray-900 mb-3">New Client</h3>
              <form onSubmit={handleAddClient} className="space-y-3">
                <input
                  type="text"
                  value={newClient.full_name}
                  onChange={(e) => setNewClient({ ...newClient, full_name: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm bg-gray-50 focus:bg-white"
                  placeholder="Full name"
                  required
                />
                <input
                  type="text"
                  value={newClient.program_type}
                  onChange={(e) => setNewClient({ ...newClient, program_type: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm bg-gray-50 focus:bg-white"
                  placeholder="Program type"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="number"
                    value={newClient.program_duration}
                    onChange={(e) => setNewClient({ ...newClient, program_duration: Number(e.target.value) })}
                    className="rounded-xl border border-gray-200 px-4 py-3 text-sm bg-gray-50 focus:bg-white"
                    placeholder="Days"
                  />
                  <input
                    type="time"
                    value={newClient.checkin_time}
                    onChange={(e) => setNewClient({ ...newClient, checkin_time: e.target.value })}
                    className="rounded-xl border border-gray-200 px-4 py-3 text-sm bg-gray-50 focus:bg-white"
                  />
                </div>
                <textarea
                  value={newClient.diet_chart}
                  onChange={(e) => setNewClient({ ...newClient, diet_chart: e.target.value })}
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm bg-gray-50 focus:bg-white"
                  rows={3}
                  placeholder="Diet chart (optional)"
                />
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowAdd(false)}
                    className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-xl text-sm font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 bg-emerald-600 text-white py-3 rounded-xl text-sm font-medium"
                  >
                    Create
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Client List */}
          {loadingClients ? (
            <div className="space-y-3 mt-4">
              {[1, 2].map((i) => (
                <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-200 rounded-full" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                      <div className="h-3 bg-gray-100 rounded w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <p className="text-gray-500 mb-1">No clients yet</p>
              <button
                onClick={() => setShowAdd(true)}
                className="text-emerald-600 text-sm font-medium"
              >
                Add your first client
              </button>
            </div>
          ) : (
            <div className="space-y-3 mt-4">
              {clients.map((client) => {
                const code = getInviteCode(client.id);
                const days = daysRemaining(client.program_end);
                return (
                  <Link
                    key={client.id}
                    href={`/dashboard/${client.id}`}
                    className="block bg-white rounded-2xl shadow-sm border border-gray-100 p-4 active:scale-[0.98] transition-transform"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-11 h-11 bg-emerald-50 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-emerald-700 font-semibold text-sm">
                          {client.full_name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-900 truncate">{client.full_name}</h3>
                          <StatusDot status={client.status} />
                        </div>
                        <p className="text-sm text-gray-500">{client.program_type}</p>
                      </div>
                      <svg className="w-5 h-5 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">
                        {client.status === "active"
                          ? `${days} days left`
                          : client.status === "expired"
                          ? "Ended"
                          : "Paused"}
                      </span>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          navigator.clipboard.writeText(`/join ${code}`);
                          alert("Copied!");
                        }}
                        className="bg-gray-100 text-gray-600 px-3 py-1.5 rounded-lg text-xs font-mono active:bg-gray-200"
                      >
                        /join {code}
                      </button>
                    </div>

                    {!client.telegram_group_id && (
                      <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-amber-500 rounded-full" />
                        Not linked
                      </p>
                    )}
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
