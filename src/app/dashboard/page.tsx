"use client";
import { useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { motion } from "framer-motion";
import { AlertTriangle, BarChart3, Clock, Eye, FileText, Globe, Play, Shield, TrendingUp, History, Trash2 } from "lucide-react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell } from "recharts";

export default function DashboardPage() {
  const { analyses, currentAnalysis, isAnalyzing, analysisProgress, analysisStep, startAnalysis, loadFromStorage, deleteAnalysis } = useAnalysisStore();

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  const kpis = currentAnalysis
    ? [
        { icon: Eye, label: "Mentions Totales", value: currentAnalysis.kpis.totalMentions, color: "from-blue-500 to-cyan-500" },
        { icon: AlertTriangle, label: "Alertes Détectées", value: currentAnalysis.kpis.totalAlerts, color: "from-red-500 to-orange-500" },
        { icon: Shield, label: "Alertes Critiques", value: currentAnalysis.kpis.criticalAlerts, color: "from-red-600 to-red-400" },
        { icon: Globe, label: "Sources Analysées", value: currentAnalysis.sources.total, color: "from-emerald-500 to-teal-500" },
        { icon: BarChart3, label: "Articles Presse", value: currentAnalysis.sources.press, color: "from-purple-500 to-pink-500" },
        { icon: FileText, label: "Mentions Sociales", value: currentAnalysis.sources.social, color: "from-amber-500 to-yellow-500" },
      ]
    : [];

  const alertsByCategory = currentAnalysis
    ? Object.entries(
        currentAnalysis.alerts.reduce((acc, a) => {
          acc[a.category] = (acc[a.category] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
      ).map(([name, value], i) => ({
        name: name.length > 14 ? name.slice(0, 14) + "…" : name,
        value,
        color: ["#EF4444", "#F59E0B", "#8B5CF6", "#EC4899", "#3B82F6", "#14B8A6", "#F97316"][i % 7],
      }))
    : [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header + Start Button */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-sm text-gray-400">
              {currentAnalysis
                ? `Dernière analyse : ${new Date(currentAnalysis.completedAt).toLocaleString("fr-FR")} — ${currentAnalysis.period}`
                : "Aucune analyse effectuée. Lancez votre première analyse."}
            </p>
          </div>
          <Button onClick={startAnalysis} disabled={isAnalyzing} size="lg" className="animate-pulse-glow">
            <Play size={18} />
            {isAnalyzing ? "Analyse en cours..." : "Démarrer l'Analyse"}
          </Button>
        </motion.div>

        {/* Analysis Progress */}
        {isAnalyzing && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <GlassCard className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} className="h-8 w-8 rounded-full border-2 border-blue-500 border-t-transparent" />
                <div>
                  <div className="font-semibold">Analyse en cours</div>
                  <div className="text-sm text-gray-400">{analysisStep}</div>
                </div>
              </div>
              <ProgressBar value={analysisProgress} color="from-blue-500 to-purple-500" />
            </GlassCard>
          </motion.div>
        )}

        {/* No Data State */}
        {!currentAnalysis && !isAnalyzing && (
          <GlassCard className="flex flex-col items-center justify-center p-16 text-center">
            <div className="mb-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 p-6">
              <Play size={48} className="text-blue-400" />
            </div>
            <h2 className="mb-2 text-xl font-bold">Bienvenue sur VeilleMaroc</h2>
            <p className="mb-6 max-w-md text-gray-400">
              Cliquez sur &quot;Démarrer l&apos;Analyse&quot; pour collecter et analyser les données des 53 sources de presse, réseaux sociaux et documents. Les résultats seront sauvegardés dans l&apos;historique.
            </p>
            <Button onClick={startAnalysis} size="lg">
              <Play size={18} /> Lancer la première analyse
            </Button>
          </GlassCard>
        )}

        {/* Dashboard with data */}
        {currentAnalysis && !isAnalyzing && (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
              {kpis.map((kpi, i) => (
                <GlassCard key={kpi.label} className="p-4" delay={i * 0.05}>
                  <div className={`mb-3 inline-flex rounded-lg bg-gradient-to-r ${kpi.color} p-2`}>
                    <kpi.icon size={18} className="text-white" />
                  </div>
                  <div className="text-2xl font-bold">
                    <AnimatedCounter target={kpi.value} />
                  </div>
                  <div className="text-xs text-gray-400">{kpi.label}</div>
                </GlassCard>
              ))}
            </div>

            {/* Charts */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Mentions Over Time */}
              <GlassCard className="p-6">
                <h3 className="mb-4 text-lg font-semibold">Évolution des Mentions</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={currentAnalysis.mentionsByDay}>
                    <defs>
                      <linearGradient id="gPress" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8B5CF6" stopOpacity={0.3} /><stop offset="100%" stopColor="#8B5CF6" stopOpacity={0} /></linearGradient>
                      <linearGradient id="gSocial" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3B82F6" stopOpacity={0.3} /><stop offset="100%" stopColor="#3B82F6" stopOpacity={0} /></linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" stroke="#64748B" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                    <YAxis stroke="#64748B" fontSize={10} />
                    <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
                    <Legend />
                    <Area type="monotone" dataKey="press" stroke="#8B5CF6" fill="url(#gPress)" name="Presse" />
                    <Area type="monotone" dataKey="social" stroke="#3B82F6" fill="url(#gSocial)" name="Réseaux sociaux" />
                  </AreaChart>
                </ResponsiveContainer>
              </GlassCard>

              {/* Sentiment by Party */}
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

            <div className="grid gap-6 lg:grid-cols-3">
              {/* Alerts Distribution */}
              <GlassCard className="p-6">
                <h3 className="mb-4 text-lg font-semibold">Alertes par Catégorie</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={alertsByCategory} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={4} dataKey="value">
                      {alertsByCategory.map((entry, i) => <Cell key={i} fill={entry.color} stroke="transparent" />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </GlassCard>

              {/* Recent Alerts */}
              <GlassCard className="col-span-2 p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Alertes Récentes</h3>
                  <Badge variant="critical" pulse>{currentAnalysis.kpis.criticalAlerts} critiques</Badge>
                </div>
                <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                  {currentAnalysis.alerts.slice(0, 8).map((alert, i) => (
                    <motion.div key={alert.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-colors hover:bg-white/5">
                      <Badge variant={alert.severity} pulse={alert.severity === "critical"}>{alert.severity}</Badge>
                      <div className="flex-1 min-w-0">
                        <div className="truncate text-sm font-medium">{alert.title}</div>
                        <div className="truncate text-xs text-gray-500">{alert.source} — {alert.region}</div>
                      </div>
                      <div className="text-xs text-gray-500 whitespace-nowrap">{new Date(alert.timestamp).toLocaleDateString("fr-FR")}</div>
                    </motion.div>
                  ))}
                </div>
              </GlassCard>
            </div>

            {/* Articles */}
            <GlassCard className="p-6">
              <h3 className="mb-4 text-lg font-semibold">Articles Clés Détectés ({currentAnalysis.articles.length})</h3>
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                {currentAnalysis.articles.slice(0, 10).map((article, i) => (
                  <motion.div key={article.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} className="rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/5 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium mb-1">{article.title}</div>
                        <div className="text-xs text-gray-500 mb-2">{article.excerpt}</div>
                        <div className="flex flex-wrap gap-2 text-xs">
                          <span className="text-gray-500">{article.source}</span>
                          <span className="text-gray-600">•</span>
                          <span className="text-gray-500">{article.date}</span>
                          <span className="text-gray-600">•</span>
                          <span className="rounded-md bg-white/5 px-2 py-0.5 text-gray-400">{article.category}</span>
                          {article.parties.map((p) => (
                            <span key={p} className="rounded-md bg-blue-500/10 px-2 py-0.5 text-blue-400">{p}</span>
                          ))}
                          {article.url && article.url !== "#" && (
                            <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">
                              Voir la source ↗
                            </a>
                          )}
                        </div>
                      </div>
                      <Badge variant={article.sentiment === "positive" ? "low" : article.sentiment === "negative" ? "critical" : "info"}>
                        {article.sentiment === "positive" ? "Positif" : article.sentiment === "negative" ? "Négatif" : "Neutre"}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </>
        )}

        {/* Analysis History */}
        {analyses.length > 0 && (
          <GlassCard className="p-6">
            <h3 className="mb-4 text-lg font-semibold flex items-center gap-2"><History size={18} /> Historique des Analyses ({analyses.length})</h3>
            <div className="space-y-3">
              {analyses.map((a, i) => (
                <motion.div key={a.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/5 transition-colors">
                  <div className="rounded-lg bg-emerald-500/20 p-2"><Clock size={16} className="text-emerald-400" /></div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium">Analyse du {new Date(a.completedAt).toLocaleString("fr-FR")}</div>
                    <div className="text-xs text-gray-500">
                      {a.kpis.totalMentions.toLocaleString("fr-FR")} mentions · {a.kpis.totalAlerts} alertes · {a.kpis.criticalAlerts} critiques · {a.sources.press} articles
                    </div>
                  </div>
                  <Badge variant="low">Terminée</Badge>
                  <button onClick={() => useAnalysisStore.getState().deleteAnalysis(a.id)} className="text-gray-500 hover:text-red-400 transition-colors p-1">
                    <Trash2 size={14} />
                  </button>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        )}
      </div>
    </DashboardLayout>
  );
}
