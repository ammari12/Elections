"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { Badge } from "@/components/ui/Badge";
import { MentionsChart } from "@/components/charts/MentionsChart";
import { SentimentChart } from "@/components/charts/SentimentChart";
import { AlertsDistribution } from "@/components/charts/AlertsDistribution";
import { KPI_DATA, generateAlerts } from "@/data/mockData";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, BarChart3, Eye, FileText, Globe, Shield, TrendingUp } from "lucide-react";

const alerts = generateAlerts(10);

const kpis = [
  { icon: Eye, label: "Mentions Totales", value: KPI_DATA.totalMentions, color: "from-blue-500 to-cyan-500" },
  { icon: AlertTriangle, label: "Alertes Actives", value: KPI_DATA.totalAlerts, color: "from-red-500 to-orange-500" },
  { icon: Shield, label: "Alertes Critiques", value: KPI_DATA.criticalAlerts, color: "from-red-600 to-red-400" },
  { icon: Globe, label: "Sources Actives", value: KPI_DATA.activeSources, color: "from-emerald-500 to-teal-500" },
  { icon: BarChart3, label: "Partis Suivis", value: KPI_DATA.partiesMonitored, color: "from-purple-500 to-pink-500" },
  { icon: FileText, label: "Documents Traités", value: KPI_DATA.documentsProcessed, color: "from-amber-500 to-yellow-500" },
];

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-gray-400">Vue d&apos;ensemble de la veille électorale — Période : 30 derniers jours</p>
        </motion.div>

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

        {/* Charts Row */}
        <div className="grid gap-6 lg:grid-cols-2">
          <MentionsChart />
          <SentimentChart />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <AlertsDistribution />

          {/* Recent Alerts */}
          <GlassCard className="col-span-2 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Alertes Récentes</h3>
              <Badge variant="critical" pulse>
                {KPI_DATA.criticalAlerts} critiques
              </Badge>
            </div>
            <div className="space-y-3">
              {alerts.slice(0, 6).map((alert, i) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-colors hover:bg-white/5"
                >
                  <Badge variant={alert.severity as any} pulse={alert.severity === "critical"}>
                    {alert.severity}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <div className="truncate text-sm font-medium">{alert.title}</div>
                    <div className="truncate text-xs text-gray-500">{alert.description}</div>
                  </div>
                  <div className="text-xs text-gray-500 whitespace-nowrap">
                    {new Date(alert.timestamp).toLocaleDateString("fr-FR")}
                  </div>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </DashboardLayout>
  );
}
