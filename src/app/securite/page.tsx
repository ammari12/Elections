"use client";
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { Badge } from "@/components/ui/Badge";
import { AlertsDistribution } from "@/components/charts/AlertsDistribution";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { motion } from "framer-motion";
import { Shield, AlertTriangle, Eye, CheckCircle, Play, X } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import Link from "next/link";

export default function SecuritePage() {
  const { currentAnalysis, loadFromStorage } = useAnalysisStore();
  const [detail, setDetail] = useState<null | { label: string; items: { title: string; source: string; sourceUrl: string }[] }>(null);

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  if (!currentAnalysis) {
    return (
      <DashboardLayout>
        <GlassCard className="flex flex-col items-center justify-center p-16 text-center">
          <Shield size={48} className="mb-4 text-amber-400" />
          <h2 className="mb-2 text-xl font-bold">Aucune analyse disponible</h2>
          <p className="mb-6 max-w-md text-gray-400">Lancez une analyse depuis le Dashboard pour voir les alertes de sécurité réelles.</p>
          <Link href="/dashboard/"><span className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 px-5 py-2.5 text-sm font-medium"><Play size={16} /> Aller au Dashboard</span></Link>
        </GlassCard>
      </DashboardLayout>
    );
  }

  const alerts = currentAnalysis.alerts;
  const criticalAlerts = alerts.filter((a) => a.severity === "critical");

  const severityData = [
    { name: "Critique", count: alerts.filter((a) => a.severity === "critical").length, fill: "#EF4444" },
    { name: "Élevée", count: alerts.filter((a) => a.severity === "high").length, fill: "#F59E0B" },
    { name: "Moyenne", count: alerts.filter((a) => a.severity === "medium").length, fill: "#ECC94B" },
    { name: "Faible", count: alerts.filter((a) => a.severity === "low").length, fill: "#22C55E" },
  ];

  const toItems = (list: typeof alerts) => list.map((a) => ({ title: a.title, source: a.source, sourceUrl: a.sourceUrl }));

  const securityKpis = [
    { icon: AlertTriangle, label: "Alertes Totales", value: alerts.length, color: "text-red-400", items: toItems(alerts) },
    { icon: Shield, label: "Alertes Critiques", value: criticalAlerts.length, color: "text-orange-400", items: toItems(criticalAlerts) },
    { icon: Eye, label: "En Investigation", value: alerts.filter((a) => a.status === "investigating").length, color: "text-blue-400", items: toItems(alerts.filter((a) => a.status === "investigating")) },
    { icon: CheckCircle, label: "Résolues", value: alerts.filter((a) => a.status === "resolved").length, color: "text-emerald-400", items: toItems(alerts.filter((a) => a.status === "resolved")) },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Shield className="text-red-400" /> Sécurité Électorale</h1>
          <p className="text-sm text-gray-400">Détection et suivi des menaces, injures, et désinformation — basé sur {currentAnalysis.sources.press} articles de presse réels</p>
        </motion.div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {securityKpis.map((kpi, i) => (
            <button key={kpi.label} onClick={() => setDetail({ label: kpi.label, items: kpi.items })} className="text-left">
              <GlassCard className="p-4 cursor-pointer transition-colors hover:bg-white/5" delay={i * 0.05}>
                <kpi.icon size={20} className={kpi.color + " mb-2"} />
                <div className="text-2xl font-bold"><AnimatedCounter target={kpi.value} /></div>
                <div className="text-xs text-gray-400">{kpi.label}</div>
              </GlassCard>
            </button>
          ))}
        </div>

        {detail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setDetail(null)}>
            <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#0F172A] p-6" onClick={(e) => e.stopPropagation()}>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{detail.label} ({detail.items.length})</h3>
                <button onClick={() => setDetail(null)} className="text-gray-400 hover:text-white"><X size={20} /></button>
              </div>
              {detail.items.length === 0 ? (
                <p className="text-sm text-gray-500">Aucun élément dans cette catégorie.</p>
              ) : (
                <div className="space-y-2">
                  {detail.items.map((it, i) => (
                    <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-3 text-sm">
                      <div className="mb-1 font-medium">{it.title}</div>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>{it.source}</span>
                        {it.sourceUrl && it.sourceUrl !== "#" && (
                          <a href={it.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">Voir la source ↗</a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <GlassCard className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Alertes par Gravité</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={severityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} />
                <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {severityData.map((entry, i) => (
                    <motion.rect key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>

          <AlertsDistribution data={alerts} />
        </div>

        <GlassCard className="p-6">
          <h3 className="mb-4 text-lg font-semibold flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-400" /> Incidents Critiques
          </h3>
          {criticalAlerts.length === 0 ? (
            <p className="text-sm text-gray-500">Aucun incident critique détecté dans cette analyse.</p>
          ) : (
            <div className="space-y-3">
              {criticalAlerts.slice(0, 5).map((alert, i) => (
                <motion.div key={alert.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="critical" pulse>{alert.category}</Badge>
                        <span className="text-xs text-gray-500">{alert.source}</span>
                      </div>
                      <h4 className="font-medium text-sm mb-1">{alert.title}</h4>
                      <p className="text-xs text-gray-400">{alert.description}</p>
                      <div className="mt-2 flex gap-3 text-xs text-gray-500">
                        <span>{alert.region}</span>
                        <span>{new Date(alert.timestamp).toLocaleDateString("fr-FR")}</span>
                        {alert.sourceUrl && alert.sourceUrl !== "#" && (
                          <a href={alert.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">Source ↗</a>
                        )}
                      </div>
                    </div>
                    <Badge variant={alert.status === "resolved" ? "low" : alert.status === "investigating" ? "info" : "high"}>
                      {alert.status === "resolved" ? "Résolu" : alert.status === "investigating" ? "Investigation" : "Nouveau"}
                    </Badge>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </DashboardLayout>
  );
}
