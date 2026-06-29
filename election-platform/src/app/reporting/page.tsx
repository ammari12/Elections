"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Download, Clock, CheckCircle, Settings, Eye, Trash2 } from "lucide-react";
import { useState } from "react";

const sections = [
  { id: "intro", label: "Introduction et Synthèse", pages: "5-7", checked: true },
  { id: "osint", label: "Veille OSINT et Réseaux Sociaux", pages: "9-10", checked: true },
  { id: "security", label: "Analyse Sécurité Électorale", pages: "12-14", checked: true },
  { id: "parties", label: "Activité des Partis Politiques", pages: "6-7", checked: true },
  { id: "press", label: "Analyse Presse", pages: "6-7", checked: true },
  { id: "uploads", label: "Documents Uploadés", pages: "3-4", checked: true },
  { id: "synthesis", label: "Synthèse et Recommandations", pages: "5-6", checked: true },
  { id: "annexes", label: "Annexes", pages: "6-8", checked: false },
];

const history = [
  { id: "1", name: "Rapport Veille - Juin 2026", date: "2026-06-28", pages: 68, size: "14.2 Mo", status: "ready" },
  { id: "2", name: "Rapport Hebdo - S25", date: "2026-06-21", pages: 42, size: "9.8 Mo", status: "ready" },
  { id: "3", name: "Rapport Sécurité - Casablanca", date: "2026-06-15", pages: 35, size: "7.5 Mo", status: "ready" },
  { id: "4", name: "Rapport Flash - Incident Rabat", date: "2026-06-10", pages: 12, size: "3.2 Mo", status: "ready" },
];

export default function ReportingPage() {
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [checked, setChecked] = useState(sections.map((s) => s.checked));

  const handleGenerate = () => {
    setGenerating(true);
    setProgress(0);
    const timer = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) { clearInterval(timer); setGenerating(false); return 100; }
        return p + 2;
      });
    }, 100);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><FileText className="text-indigo-400" /> Génération de Rapports PDF</h1>
          <p className="text-sm text-gray-400">Rapports professionnels de 55-75 pages avec visualisations et recommandations</p>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Config */}
          <div className="lg:col-span-2 space-y-6">
            <GlassCard className="p-6">
              <h3 className="mb-4 text-lg font-semibold flex items-center gap-2"><Settings size={18} /> Sections du Rapport</h3>
              <div className="space-y-3">
                {sections.map((s, i) => (
                  <motion.label key={s.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }} className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-colors hover:bg-white/5">
                    <input type="checkbox" checked={checked[i]} onChange={() => setChecked(c => c.map((v, j) => j === i ? !v : v))} className="h-4 w-4 rounded border-white/20 bg-white/5 text-blue-500 focus:ring-blue-500/50" />
                    <div className="flex-1">
                      <div className="text-sm font-medium">{s.label}</div>
                    </div>
                    <span className="text-xs text-gray-500">{s.pages} pages</span>
                  </motion.label>
                ))}
              </div>

              <div className="mt-6">
                {generating ? (
                  <div className="space-y-3">
                    <div className="text-sm text-gray-300">Génération en cours...</div>
                    <ProgressBar value={progress} />
                    <div className="text-xs text-gray-500">
                      {progress < 30 ? "Collecte des données..." : progress < 60 ? "Génération des graphiques..." : progress < 90 ? "Mise en page du PDF..." : "Finalisation..."}
                    </div>
                  </div>
                ) : (
                  <Button onClick={handleGenerate} size="lg" className="w-full"><FileText size={18} /> Générer le Rapport PDF</Button>
                )}
              </div>
            </GlassCard>
          </div>

          {/* Preview */}
          <GlassCard className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Aperçu</h3>
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-center">
              <div className="mx-auto mb-4 h-48 w-36 rounded-lg border border-white/10 bg-gradient-to-b from-white/5 to-transparent p-4">
                <div className="mb-3 text-[6px] font-bold text-gray-400">RAPPORT DE VEILLE ÉLECTORALE</div>
                <div className="mb-2 text-[5px] text-gray-500">Maroc 2026</div>
                <div className="space-y-1">
                  {[...Array(8)].map((_, i) => (<div key={i} className="h-0.5 w-full rounded bg-white/10" />))}
                </div>
              </div>
              <div className="text-sm font-medium">{checked.filter(Boolean).length} sections</div>
              <div className="text-xs text-gray-500">~{checked.reduce((acc, v, i) => acc + (v ? parseInt(sections[i].pages) : 0), 0)}-{checked.reduce((acc, v, i) => acc + (v ? parseInt(sections[i].pages.split("-")[1] || sections[i].pages) : 0), 0)} pages</div>
            </div>
          </GlassCard>
        </div>

        {/* History */}
        <GlassCard className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Historique des Rapports</h3>
          <div className="space-y-3">
            {history.map((r, i) => (
              <motion.div key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/5 transition-colors">
                <FileText size={20} className="text-indigo-400" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{r.name}</div>
                  <div className="text-xs text-gray-500">{r.date} · {r.pages} pages · {r.size}</div>
                </div>
                <Badge variant="low"><CheckCircle size={12} /> Prêt</Badge>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm"><Eye size={14} /></Button>
                  <Button variant="ghost" size="sm"><Download size={14} /></Button>
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      </div>
    </DashboardLayout>
  );
}
