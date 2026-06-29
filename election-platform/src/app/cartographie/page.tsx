"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { RiskMap } from "@/components/maps/RiskMap";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { generateRegionRisks } from "@/data/mockData";
import { motion } from "framer-motion";
import { Map, AlertTriangle } from "lucide-react";

const risks = generateRegionRisks().sort((a, b) => b.alertCount - a.alertCount);

export default function CartographiePage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Map className="text-emerald-400" /> Cartographie des Risques</h1>
          <p className="text-sm text-gray-400">Visualisation géographique des alertes sur les 12 régions du Maroc</p>
        </motion.div>

        <RiskMap />

        <GlassCard className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Classement des Régions par Risque</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 text-left text-gray-400">
                  <th className="pb-3 font-medium">#</th>
                  <th className="pb-3 font-medium">Région</th>
                  <th className="pb-3 font-medium">Niveau</th>
                  <th className="pb-3 font-medium">Alertes</th>
                  <th className="pb-3 font-medium">Critiques</th>
                  <th className="pb-3 font-medium">Catégorie principale</th>
                </tr>
              </thead>
              <tbody>
                {risks.map((r, i) => (
                  <motion.tr key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-3 text-gray-500">{i + 1}</td>
                    <td className="py-3 font-medium">{r.name}</td>
                    <td className="py-3"><Badge variant={r.riskLevel === "high" ? "critical" : r.riskLevel === "medium" ? "medium" : "low"}>{r.riskLevel === "high" ? "Élevé" : r.riskLevel === "medium" ? "Moyen" : "Faible"}</Badge></td>
                    <td className="py-3">{r.alertCount}</td>
                    <td className="py-3">{r.criticalCount > 0 && <span className="text-red-400">{r.criticalCount}</span>}{r.criticalCount === 0 && <span className="text-gray-500">0</span>}</td>
                    <td className="py-3 text-gray-400">{r.topCategory}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      </div>
    </DashboardLayout>
  );
}
