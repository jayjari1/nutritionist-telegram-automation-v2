"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import Navbar from "@/components/Navbar";

interface ConfigEntry {
  key: string;
  value: string;
  category: string;
  description: string;
  is_secret: boolean;
  updated_at: string;
}

const CATEGORIES = [
  { value: "telegram", label: "Telegram", icon: "📱" },
  { value: "supabase", label: "Supabase", icon: "🗄️" },
  { value: "ai", label: "AI / Gemini", icon: "🤖" },
  { value: "auth", label: "Auth", icon: "🔐" },
  { value: "admin", label: "Admin", icon: "👤" },
  { value: "general", label: "General", icon: "⚙️" },
];

export default function ConfigPage() {
  const { user, token, loading, login } = useAuth();
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [loginError, setLoginError] = useState("");
  const [configs, setConfigs] = useState<ConfigEntry[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newConfig, setNewConfig] = useState({
    key: "",
    value: "",
    category: "general",
    description: "",
    is_secret: false,
  });
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [showSecrets, setShowSecrets] = useState<Set<string>>(new Set());

  const isAdmin = user?.role === "admin";

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    try {
      const data = await apiPost("/auth/admin/login", loginForm);
      login(data.token, { ...data.user, role: "admin", full_name: "Admin", status: "active" });
    } catch (err: any) {
      setLoginError(err.message);
    }
  };

  useEffect(() => {
    if (isAdmin && token) {
      setLoadingData(true);
      apiGet("/config/raw", token)
        .then(setConfigs)
        .catch(console.error)
        .finally(() => setLoadingData(false));
    }
  }, [isAdmin, token]);

  const handleSave = async (key: string) => {
    if (!token) return;
    try {
      const existing = configs.find((c) => c.key === key);
      await apiPost("/config", {
        key,
        value: editValue,
        category: existing?.category || "general",
        description: existing?.description || "",
        is_secret: existing?.is_secret || false,
      }, token);
      setConfigs(configs.map((c) => (c.key === key ? { ...c, value: editValue } : c)));
      setEditingKey(null);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (key: string) => {
    if (!token || !confirm(`Delete config '${key}'?`)) return;
    try {
      await apiDelete(`/config/${key}`, token);
      setConfigs(configs.filter((c) => c.key !== key));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleAdd = async () => {
    if (!token || !newConfig.key.trim()) return;
    try {
      await apiPost("/config", newConfig, token);
      setConfigs([...configs, { ...newConfig, updated_at: new Date().toISOString() }]);
      setNewConfig({ key: "", value: "", category: "general", description: "", is_secret: false });
      setShowAdd(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleSyncEnv = async () => {
    if (!token) return;
    try {
      const result = await apiPost("/config/sync-env", {}, token);
      alert(result.message);
      const fresh = await apiGet("/config/raw", token);
      setConfigs(fresh);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const toggleSecret = (key: string) => {
    setShowSecrets((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const maskValue = (entry: ConfigEntry) => {
    if (!entry.is_secret) return entry.value;
    if (showSecrets.has(entry.key)) return entry.value;
    const val = entry.value;
    if (val.length > 8) return val.slice(0, 4) + "*".repeat(val.length - 8) + val.slice(-4);
    return "****";
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="h-6 w-6 border-2 border-gray-300 border-t-emerald-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-gray-900 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Config Settings</h1>
            <p className="text-sm text-gray-500 mt-1">Admin access required</p>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            {loginError && (
              <div className="bg-red-50 border border-red-100 text-red-700 p-3 rounded-xl text-sm mb-4">{loginError}</div>
            )}
            <form onSubmit={handleAdminLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
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
              <button type="submit" className="w-full bg-gray-900 text-white py-2.5 rounded-xl text-sm font-medium">
                Login
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  const filteredConfigs = activeCategory === "all"
    ? configs
    : configs.filter((c) => c.category === activeCategory);

  const groupedByCategory = CATEGORIES.map((cat) => ({
    ...cat,
    items: configs.filter((c) => c.category === cat.value),
  })).filter((g) => g.items.length > 0);

  return (
    <>
      <Navbar />
      <main className="pb-20">
        <div className="bg-white border-b border-gray-100 px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Config</h1>
              <p className="text-sm text-gray-500">App settings & secrets</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSyncEnv}
                className="bg-gray-100 text-gray-700 px-3 py-2 rounded-xl text-xs font-medium"
              >
                Sync .env
              </button>
              <button
                onClick={() => setShowAdd(!showAdd)}
                className="bg-emerald-600 text-white w-10 h-10 rounded-full flex items-center justify-center"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div className="px-4 mt-4">
          {showAdd && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-4">
              <h3 className="font-semibold text-gray-900 text-sm mb-3">New Config</h3>
              <input
                type="text"
                value={newConfig.key}
                onChange={(e) => setNewConfig({ ...newConfig, key: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50 mb-2"
                placeholder="KEY_NAME"
              />
              <input
                type="text"
                value={newConfig.value}
                onChange={(e) => setNewConfig({ ...newConfig, value: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50 mb-2"
                placeholder="Value"
              />
              <div className="flex gap-2 mb-2">
                <select
                  value={newConfig.category}
                  onChange={(e) => setNewConfig({ ...newConfig, category: e.target.value })}
                  className="flex-1 border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>{cat.icon} {cat.label}</option>
                  ))}
                </select>
                <label className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm">
                  <input
                    type="checkbox"
                    checked={newConfig.is_secret}
                    onChange={(e) => setNewConfig({ ...newConfig, is_secret: e.target.checked })}
                    className="rounded"
                  />
                  Secret
                </label>
              </div>
              <input
                type="text"
                value={newConfig.description}
                onChange={(e) => setNewConfig({ ...newConfig, description: e.target.value })}
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm bg-gray-50 mb-3"
                placeholder="Description (optional)"
              />
              <div className="flex gap-3">
                <button onClick={() => setShowAdd(false)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-xl text-sm font-medium">
                  Cancel
                </button>
                <button onClick={handleAdd} className="flex-1 bg-emerald-600 text-white py-2.5 rounded-xl text-sm font-medium">
                  Save
                </button>
              </div>
            </div>
          )}

          <div className="flex gap-2 overflow-x-auto pb-3 -mx-4 px-4 mb-4">
            <button
              onClick={() => setActiveCategory("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                activeCategory === "all" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600"
              }`}
            >
              All ({configs.length})
            </button>
            {groupedByCategory.map((cat) => (
              <button
                key={cat.value}
                onClick={() => setActiveCategory(cat.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  activeCategory === cat.value ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600"
                }`}
              >
                {cat.icon} {cat.label} ({cat.items.length})
              </button>
            ))}
          </div>

          {loadingData ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                  <div className="h-4 bg-gray-100 rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredConfigs.map((config) => (
                <div key={config.key} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-lg font-mono text-gray-600">{config.key}</span>
                        {config.is_secret && (
                          <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">secret</span>
                        )}
                      </div>
                      {config.description && (
                        <p className="text-xs text-gray-500 mb-2">{config.description}</p>
                      )}
                      {editingKey === config.key ? (
                        <div className="flex gap-2">
                          <input
                            type={config.is_secret ? "password" : "text"}
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono bg-gray-50"
                          />
                          <button onClick={() => handleSave(config.key)} className="text-emerald-600 text-xs font-medium px-3">
                            Save
                          </button>
                          <button onClick={() => setEditingKey(null)} className="text-gray-400 text-xs px-2">
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-mono text-gray-800 truncate">{maskValue(config)}</p>
                          {config.is_secret && (
                            <button onClick={() => toggleSecret(config.key)} className="text-gray-400 text-xs">
                              {showSecrets.has(config.key) ? "Hide" : "Show"}
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button
                        onClick={() => { setEditingKey(config.key); setEditValue(config.value); }}
                        className="text-xs text-blue-600 px-2 py-1 rounded-lg"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(config.key)}
                        className="text-xs text-red-500 px-2 py-1 rounded-lg"
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
