"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { apiGet, apiPost, apiDelete, apiPatch } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface Rule {
  id: string;
  category: string;
  rule_text: string;
  is_active: boolean;
}

const CATEGORIES = [
  { value: "tone", label: "Tone" },
  { value: "language", label: "Language" },
  { value: "medical", label: "Medical" },
  { value: "other", label: "Other" },
];

export default function RulesPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [rules, setRules] = useState<Rule[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newRule, setNewRule] = useState({ category: "tone", rule_text: "" });

  useEffect(() => {
    if (!loading && !token) router.push("/auth/login");
  }, [loading, token, router]);

  useEffect(() => {
    if (token) {
      apiGet("/rules", token)
        .then(setRules)
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [token]);

  const handleAdd = async () => {
    if (!token || !newRule.rule_text.trim()) return;
    try {
      const data = await apiPost("/rules", newRule, token);
      setRules([data.rule, ...rules]);
      setNewRule({ category: "tone", rule_text: "" });
      setShowAdd(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (!token || !confirm("Delete this rule?")) return;
    try {
      await apiDelete(`/rules/${ruleId}`, token);
      setRules(rules.filter((r) => r.id !== ruleId));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggle = async (ruleId: string) => {
    if (!token) return;
    try {
      await apiPatch(`/rules/${ruleId}/toggle`, {}, token);
      setRules(rules.map((r) => r.id === ruleId ? { ...r, is_active: !r.is_active } : r));
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">AI Rules</h1>
              <p className="text-sm text-gray-500">Customize AI behavior</p>
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

        <div className="px-4 mt-4">
          {/* Add Rule Form */}
          {showAdd && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-4">
              <h3 className="font-semibold text-gray-900 text-sm mb-3">New Rule</h3>
              <select
                value={newRule.category}
                onChange={(e) => setNewRule({ ...newRule, category: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50 mb-3"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
              <textarea
                value={newRule.rule_text}
                onChange={(e) => setNewRule({ ...newRule, rule_text: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50 mb-3"
                rows={3}
                placeholder="Rule text..."
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setShowAdd(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-xl text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAdd}
                  className="flex-1 bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-medium"
                >
                  Save
                </button>
              </div>
            </div>
          )}

          {/* Rules List */}
          {loadingData ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                  <div className="h-4 bg-gray-100 rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : rules.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-1">No rules yet</p>
              <p className="text-sm text-gray-400">Add rules to customize AI</p>
            </div>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className={`bg-white rounded-2xl shadow-sm border border-gray-100 p-4 ${!rule.is_active ? "opacity-60" : ""}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-lg text-gray-600">{rule.category}</span>
                        {!rule.is_active && <span className="text-xs text-gray-400">off</span>}
                      </div>
                      <p className="text-sm text-gray-700">{rule.rule_text}</p>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button
                        onClick={() => handleToggle(rule.id)}
                        className={`text-xs px-2 py-1 rounded-lg font-medium ${rule.is_active ? "text-amber-600" : "text-emerald-600"}`}
                      >
                        {rule.is_active ? "Off" : "On"}
                      </button>
                      <button
                        onClick={() => handleDelete(rule.id)}
                        className="text-xs text-red-500 px-2 py-1 rounded-lg font-medium"
                      >
                        Del
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
