"use client";
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { SOCIAL_NETWORKS } from "@/data/constants";
import { motion } from "framer-motion";
import { Search, Radio, TrendingUp, Hash, Play, AlertCircle } from "lucide-react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import Link from "next/link";

const trendingTopics = [
  { tag: "#Elections2026", count: 45200, trend: "+12%" },
  { tag: "#MarocVote", count: 32100, trend: "+8%" },
  { tag: "#RéformeÉlectorale", count: 28700, trend: "+25%" },
  { tag: "#Jeunesse2026", count: 21300, trend: "+15%" },
  { tag: "#TransparenceÉlectorale", count: 18900, trend: "+5%" },
  { tag: "#DéveloppementRural", count: 15400, trend: "+18%" },
  { tag: "#NumériqueMaroc", count: 12800, trend: "+22%" },
  { tag: "#ParticipationCitoyenne", count: 11200, trend: "+9%" },
];

export default function VeillePage() {
  const { currentAnalysis, loadFromStorage } = useAnalysisStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSource, setSelectedSource] = useState<string | null>(null);

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  if (!currentAnalysis) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
            <h1 className="text-2xl font-bold flex items-center gap-2"><Radio className="text-blue-400" /> Veille OSINT</h1>
          </motion.div>
          <GlassCard className="flex flex-col items-center justify-center p-12 text-center">
            <AlertCircle size={48} className="mb-4 text-amber-400" />
            <h2 className="mb-2 text-lg font-bold">Aucune donnée disponible</h2>
            <p className="mb-6 text-sm text-gray-400">Lancez une analyse depuis le Dashboard pour alimenter la veille OSINT.</p>
            <Link href="/dashboard/"><Button><Play size={16} /> Aller au Dashboard</Button></Link>
          </GlassCard>
        </div>
      </DashboardLayout>
    );
  }

  const allItems = [
    ...currentAnalysis.alerts.map((a) => ({ ...a, type: "alert" as const })),
    ...currentAnalysis.articles.map((a) => ({ ...a, type: "article" as const, severity: undefined, timestamp: a.date })),
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const filtered = allItems.filter((item) => {
    if (selectedSource && item.source !== selectedSource) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      if (!item.title.toLowerCase().includes(q) && !((item as any).description || (item as any).excerpt || "").toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const sources = Array.from(new Set([...currentAnalysis.alerts.map((a) => a.source), ...currentAnalysis.articles.map((a) => a.source)]));

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Radio className="text-blue-400" /> Veille OSINT</h1>
          <p className="text-sm text-gray-400">Surveillance en temps réel — Analyse du {new Date(currentAnalysis.completedAt).toLocaleString("fr-FR")}</p>
        </motion.div>

        <GlassCard className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input type="text" placeholder="Rechercher..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500/50" />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant={!selectedSource ? "primary" : "secondary"} size="sm" onClick={() => setSelectedSource(null)}>Tous</Button>
              {sources.slice(0, 6).map((s) => (
                <Button key={s} variant={selectedSource === s ? "primary" : "secondary"} size="sm" onClick={() => setSelectedSource(s === selectedSource ? null : s)}>{s}</Button>
              ))}
            </div>
          </div>
        </GlassCard>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-lg font-semibold">Flux ({filtered.length} résultats)</h3>
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {filtered.slice(0, 20).map((item, i) => (
                <motion.div key={item.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                  <GlassCard className="p-4" hover>
                    <div className="flex items-start gap-3">
                      {item.type === "alert" && item.severity && (
                        <Badge variant={item.severity} pulse={item.severity === "critical"}>{item.severity}</Badge>
                      )}
                      {item.type === "article" && (
                        <Badge variant={item.sentiment === "positive" ? "low" : item.sentiment === "negative" ? "critical" : "info"}>
                          {item.sentiment === "positive" ? "+" : item.sentiment === "negative" ? "-" : "~"}
                        </Badge>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium mb-1">{item.title}</div>
                        <p className="text-xs text-gray-400 line-clamp-2">{(item as any).description || (item as any).excerpt}</p>
                        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                          <span>{item.source}</span>
                          <span className="text-gray-600">•</span>
                          <span>{new Date(item.timestamp).toLocaleDateString("fr-FR")}</span>
                          {item.type === "alert" && item.category && <span className="rounded-md bg-white/5 px-2 py-0.5">{item.category}</span>}
                          {item.type === "article" && item.parties?.map((p: string) => <span key={p} className="rounded-md bg-blue-500/10 px-2 py-0.5 text-blue-400">{p}</span>)}
                          {(item as any).url && (item as any).url !== "#" && (
                            <a href={(item as any).url} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">Source ↗</a>
                          )}
                          {(item as any).sourceUrl && (
                            <a href={(item as any).sourceUrl} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">Source ↗</a>
                          )}
                        </div>
                      </div>
                    </div>
                  </GlassCard>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <GlassCard className="p-4">
              <h3 className="mb-4 flex items-center gap-2 font-semibold"><Hash size={16} className="text-blue-400" /> Trending Topics</h3>
              <div className="space-y-3">
                {trendingTopics.map((t, i) => (
                  <motion.div key={t.tag} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center justify-between rounded-lg p-2 hover:bg-white/5 transition-colors">
                    <div>
                      <div className="text-sm font-medium text-blue-400">{t.tag}</div>
                      <div className="text-xs text-gray-500">{t.count.toLocaleString("fr-FR")} mentions</div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-emerald-400"><TrendingUp size={12} /> {t.trend}</div>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <GlassCard className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Évolution des Mentions</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={currentAnalysis.mentionsByDay}>
                <defs>
                  <linearGradient id="vp" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.3} /><stop offset="100%" stopColor="#8B5CF6" stopOpacity={0} /></linearGradient>
                  <linearGradient id="vs" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3B82F6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3B82F6" stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="#64748B" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="#64748B" fontSize={10} />
                <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
                <Legend />
                <Area type="monotone" dataKey="press" stroke="#8B5CF6" fill="url(#vp)" name="Presse" />
                <Area type="monotone" dataKey="social" stroke="#3B82F6" fill="url(#vs)" name="Social" />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>

          <GlassCard className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Sentiment par Parti</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={currentAnalysis.sentimentByParty} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" stroke="#64748B" fontSize={10} />
                <YAxis dataKey="party" type="category" stroke="#64748B" fontSize={11} width={55} />
                <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
                <Legend />
                <Bar dataKey="positive" stackId="a" fill="#22C55E" name="Positif" />
                <Bar dataKey="neutral" stackId="a" fill="#64748B" name="Neutre" />
                <Bar dataKey="negative" stackId="a" fill="#EF4444" name="Négatif" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </div>
      </div>
    </DashboardLayout>
  );
}
