"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiGet, apiPost } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface Query {
  id: string;
  client_id: string;
  client_message: string;
  ai_assessment: string;
  ai_interim_reply: string;
  status: string;
  created_at: string;
  clients: { full_name: string; program_type: string } | null;
}

export default function AlertsPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [queries, setQueries] = useState<Query[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyText, setReplyText] = useState("");

  useEffect(() => {
    if (!loading && !token) router.push("/auth/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (token) {
      apiGet("/queries", token)
        .then(setQueries)
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [token]);

  const handleResolve = async (queryId: string) => {
    if (!token) return;
    try {
      await apiPost(`/queries/${queryId}/resolve`, { doctor_reply: replyText || null }, token);
      setQueries(queries.filter((q) => q.id !== queryId));
      setReplyingTo(null);
      setReplyText("");
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading || !token) return null;

  return (
    <>
      <Navbar />
      <main className="pb-20">
        {/* Header */}
        <div className="bg-white border-b border-gray-100 px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">Pending Queries</h1>
          <p className="text-sm text-gray-500">{queries.length} pending</p>
        </div>

        <div className="px-4 mt-4">
          {loadingData ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
                  <div className="h-16 bg-gray-100 rounded-xl" />
                </div>
              ))}
            </div>
          ) : queries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-10 h-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-gray-900 font-medium">All clear!</p>
              <p className="text-sm text-gray-500">No pending queries</p>
            </div>
          ) : (
            <div className="space-y-3">
              {queries.map((q) => (
                <div key={q.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm">
                        {q.clients?.full_name || "Unknown"}
                      </h3>
                      <p className="text-xs text-gray-500">{q.clients?.program_type}</p>
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(q.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="bg-red-50 border border-red-100 p-3 rounded-xl text-sm mb-2">
                    <p className="text-xs text-red-600 mb-1">Client asked</p>
                    <p className="text-red-800">{q.client_message}</p>
                  </div>

                  {q.ai_interim_reply && (
                    <div className="bg-blue-50 border border-blue-100 p-3 rounded-xl text-sm mb-3">
                      <p className="text-xs text-blue-600 mb-1">AI told client</p>
                      <p className="text-blue-800">{q.ai_interim_reply}</p>
                    </div>
                  )}

                  {replyingTo === q.id ? (
                    <div className="mt-3">
                      <textarea
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm bg-gray-50"
                        rows={3}
                        placeholder="Your reply..."
                      />
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleResolve(q.id)}
                          className="flex-1 bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-medium"
                        >
                          Send & Resolve
                        </button>
                        <button
                          onClick={() => { setReplyText(""); handleResolve(q.id); }}
                          className="bg-gray-100 text-gray-700 px-4 py-2.5 rounded-xl text-sm font-medium"
                        >
                          Skip
                        </button>
                        <button
                          onClick={() => { setReplyingTo(null); setReplyText(""); }}
                          className="text-gray-500 px-3 py-2.5 text-sm"
                        >
                          X
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setReplyingTo(q.id)}
                      className="w-full bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-medium"
                    >
                      Reply & Resolve
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
