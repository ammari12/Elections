"use client";
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { RiskMap } from "@/components/maps/RiskMap";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { useAnalysisStore, type RegionRisk } from "@/stores/useAnalysisStore";
import { motion } from "framer-motion";
import { Map, Play, X } from "lucide-react";
import Link from "next/link";

export default function CartographiePage() {
  const { currentAnalysis, loadFromStorage } = useAnalysisStore();
  const [selected, setSelected] = useState<RegionRisk | null>(null);

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  if (!currentAnalysis) {
    return (
      <DashboardLayout>
        <GlassCard className="flex flex-col items-center justify-center p-16 text-center">
          <Map size={48} className="mb-4 text-emerald-400" />
          <h2 className="mb-2 text-xl font-bold">Aucune analyse disponible</h2>
          <p className="mb-6 max-w-md text-gray-400">Lancez une analyse depuis le Dashboard pour voir la cartographie des risques réelle.</p>
          <Link href="/dashboard/"><span className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 px-5 py-2.5 text-sm font-medium"><Play size={16} /> Aller au Dashboard</span></Link>
        </GlassCard>
      </DashboardLayout>
    );
  }

  const risks = currentAnalysis.regionRisks;
  const selectedAlerts = selected
    ? currentAnalysis.alerts.filter((a) => a.region === selected.name)
    : [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Map className="text-emerald-400" /> Cartographie des Risques</h1>
          <p className="text-sm text-gray-400">Région détectée à partir du texte des articles réels analysés. Cliquez sur une zone ou une ligne pour voir le détail.</p>
        </motion.div>

        <RiskMap risks={risks} onSelect={setSelected} />

        {selected && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setSelected(null)}>
            <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#0F172A] p-6" onClick={(e) => e.stopPropagation()}>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{selected.name} ({selectedAlerts.length} alertes)</h3>
                <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-white"><X size={20} /></button>
              </div>
              <p className="mb-3 text-xs text-gray-500">Niveau de risque calculé : {selected.criticalCount > 0 ? "Élevé (au moins une alerte critique)" : selected.alertCount >= 2 ? "Moyen (2+ alertes)" : "Faible"}.</p>
              {selectedAlerts.length === 0 ? (
                <p className="text-sm text-gray-500">Aucune alerte source disponible.</p>
              ) : (
                <div className="space-y-2">
                  {selectedAlerts.map((a) => (
                    <div key={a.id} className="rounded-lg border border-white/5 bg-white/[0.02] p-3 text-sm">
                      <div className="mb-1 flex items-center gap-2">
                        <Badge variant={a.severity}>{a.category}</Badge>
                      </div>
                      <div className="font-medium">{a.title}</div>
                      <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                        <span>{a.source}</span>
                        {a.sourceUrl && a.sourceUrl !== "#" && (
                          <a href={a.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">Voir la source ↗</a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <GlassCard className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Classement des Régions par Risque</h3>
          {risks.length === 0 ? (
            <p className="text-sm text-gray-500">Aucune région détectée dans cette analyse.</p>
          ) : (
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
                    <motion.tr key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} onClick={() => setSelected(r)} className="cursor-pointer border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="py-3 text-gray-500">{i + 1}</td>
                      <td className="py-3 font-medium">{r.name}</td>
                      <td className="py-3"><Badge variant={r.riskLevel === "high" ? "critical" : r.riskLevel === "medium" ? "medium" : "low"}>{r.riskLevel === "high" ? "Élevé" : r.riskLevel === "medium" ? "Moyen" : "Faible"}</Badge></td>
                      <td className="py-3">{r.alertCount}</td>
                      <td className="py-3">{r.criticalCount > 0 ? <span className="text-red-400">{r.criticalCount}</span> : <span className="text-gray-500">0</span>}</td>
                      <td className="py-3 text-gray-400">{r.topCategory}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </GlassCard>
      </div>
    </DashboardLayout>
  );
}
