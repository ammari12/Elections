"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { Badge } from "@/components/ui/Badge";
import { AlertsDistribution } from "@/components/charts/AlertsDistribution";
import { generateAlerts } from "@/data/mockData";
import { motion } from "framer-motion";
import { Shield, AlertTriangle, Eye, Clock, CheckCircle, XCircle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const alerts = generateAlerts(50);
const criticalAlerts = alerts.filter((a) => a.severity === "critical");

const severityData = [
  { name: "Critique", count: alerts.filter(a => a.severity === "critical").length, fill: "#EF4444" },
  { name: "Élevée", count: alerts.filter(a => a.severity === "high").length, fill: "#F59E0B" },
  { name: "Moyenne", count: alerts.filter(a => a.severity === "medium").length, fill: "#ECC94B" },
  { name: "Faible", count: alerts.filter(a => a.severity === "low").length, fill: "#22C55E" },
];

const securityKpis = [
  { icon: AlertTriangle, label: "Alertes Totales", value: 1247, color: "text-red-400" },
  { icon: Shield, label: "Alertes Critiques", value: 23, color: "text-orange-400" },
  { icon: Eye, label: "En Investigation", value: 45, color: "text-blue-400" },
  { icon: CheckCircle, label: "Résolues", value: 892, color: "text-emerald-400" },
];

export default function SecuritePage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Shield className="text-red-400" /> Sécurité Électorale</h1>
          <p className="text-sm text-gray-400">Détection et suivi des menaces, injures, et désinformation</p>
        </motion.div>

        {/* KPIs */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {securityKpis.map((kpi, i) => (
            <GlassCard key={kpi.label} className="p-4" delay={i * 0.05}>
              <kpi.icon size={20} className={kpi.color + " mb-2"} />
              <div className="text-2xl font-bold"><AnimatedCounter target={kpi.value} /></div>
              <div className="text-xs text-gray-400">{kpi.label}</div>
            </GlassCard>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Severity Distribution */}
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

          <AlertsDistribution />
        </div>

        {/* Critical Alerts Detail */}
        <GlassCard className="p-6">
          <h3 className="mb-4 text-lg font-semibold flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-400" /> Incidents Critiques
          </h3>
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
                    </div>
                  </div>
                  <Badge variant={alert.status === "resolved" ? "low" : alert.status === "investigating" ? "info" : "high"}>
                    {alert.status === "resolved" ? "Résolu" : alert.status === "investigating" ? "Investigation" : "Nouveau"}
                  </Badge>
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      </div>
    </DashboardLayout>
  );
}
