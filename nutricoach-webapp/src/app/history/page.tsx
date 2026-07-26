"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiGet } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface Query {
  id: string;
  client_id: string;
  client_message: string;
  ai_assessment: string;
  ai_interim_reply: string;
  doctor_reply: string | null;
  status: string;
  created_at: string;
  resolved_at: string | null;
  clients: { full_name: string; program_type: string } | null;
}

interface Client {
  id: string;
  full_name: string;
  program_type: string;
}

interface Message {
  id: string;
  client_id: string;
  sender_role: string;
  sender_name: string;
  content: string;
  sent_at: string;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-red-100 text-red-700",
    resolved: "bg-emerald-100 text-emerald-700",
    ai_handled: "bg-blue-100 text-blue-700",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${styles[status] || "bg-gray-100 text-gray-600"}`}>
      {status === "ai_handled" ? "AI" : status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export default function HistoryPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [view, setView] = useState<"queries" | "messages">("queries");
  const [queries, setQueries] = useState<Query[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedClient, setSelectedClient] = useState<string>("");
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    if (!loading && !token) router.push("/auth/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (token) {
      Promise.all([
        apiGet("/queries/all", token),
        apiGet("/clients", token),
      ])
        .then(([q, c]) => { setQueries(q); setClients(c); })
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [token]);

  useEffect(() => {
    if (token && selectedClient && view === "messages") {
      setLoadingData(true);
      apiGet(`/clients/${selectedClient}/messages`, token)
        .then(setMessages)
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [token, selectedClient, view]);

  if (loading || !token) return null;

  return (
    <>
      <Navbar />
      <main className="pb-20">
        {/* Header */}
        <div className="bg-white border-b border-gray-100 px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">History</h1>
        </div>

        {/* View Toggle */}
        <div className="px-4 mt-4">
          <div className="flex bg-gray-100 rounded-xl p-1">
            <button
              onClick={() => setView("queries")}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${
                view === "queries" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
              }`}
            >
              All Queries
            </button>
            <button
              onClick={() => setView("messages")}
              className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${
                view === "messages" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
              }`}
            >
              Client History
            </button>
          </div>
        </div>

        <div className="px-4 mt-4">
          {/* Queries View */}
          {view === "queries" && (
            loadingData ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                    <div className="h-12 bg-gray-100 rounded-xl" />
                  </div>
                ))}
              </div>
            ) : queries.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No queries yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {queries.map((q) => (
                  <div key={q.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h3 className="font-semibold text-gray-900 text-sm">{q.clients?.full_name || "Unknown"}</h3>
                        <p className="text-xs text-gray-500">{new Date(q.created_at).toLocaleDateString()}</p>
                      </div>
                      <StatusBadge status={q.status} />
                    </div>
                    <div className="bg-gray-50 p-3 rounded-xl text-sm mb-2">
                      <p>{q.client_message}</p>
                    </div>
                    {q.doctor_reply && (
                      <div className="bg-emerald-50 p-3 rounded-xl text-sm">
                        <p className="text-xs text-emerald-600 mb-1">Doctor replied</p>
                        <p>{q.doctor_reply}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )
          )}

          {/* Messages View */}
          {view === "messages" && (
            <>
              <select
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50 mb-4"
              >
                <option value="">Select a client...</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.full_name}</option>
                ))}
              </select>

              {!selectedClient ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">Select a client to view history</p>
                </div>
              ) : loadingData ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
                      <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
                      <div className="h-8 bg-gray-100 rounded" />
                    </div>
                  ))}
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">No messages yet</p>
                </div>
              ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-3">
                  <div className="space-y-2 max-h-[500px] overflow-y-auto">
                    {messages.map((m) => (
                      <div
                        key={m.id}
                        className={`p-3 rounded-2xl text-sm ${
                          m.sender_role === "client"
                            ? "bg-gray-100 ml-6"
                            : m.sender_role === "ai"
                            ? "bg-emerald-50 mr-6"
                            : m.sender_role === "nutritionist"
                            ? "bg-blue-50 mr-6"
                            : "bg-purple-50 mr-6"
                        }`}
                      >
                        <p className="text-xs font-medium text-gray-500 mb-1">
                          {m.sender_role === "client" ? m.sender_name :
                           m.sender_role === "ai" ? "AI" :
                           m.sender_role === "nutritionist" ? "Doctor" : "Caretaker"}
                        </p>
                        <p className="text-gray-800">{m.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </>
  );
}
