"use client";
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { motion } from "framer-motion";
import { FileText, Download, CheckCircle, Settings, Eye, Trash2, AlertCircle, Play } from "lucide-react";
import Link from "next/link";

const sections = [
  { id: "intro", label: "Introduction et Synthèse Générale", pages: "5-7" },
  { id: "osint", label: "Veille OSINT et Analyse Réseaux Sociaux", pages: "9-10" },
  { id: "security", label: "Analyse Globale de la Sécurité Électorale", pages: "12-14" },
  { id: "parties", label: "Activité des Partis Politiques", pages: "6-7" },
  { id: "press", label: "Analyse Presse Écrite et Électronique", pages: "6-7" },
  { id: "uploads", label: "Analyse des Documents Uploadés", pages: "3-4" },
  { id: "synthesis", label: "Synthèse Globale et Recommandations", pages: "5-6" },
  { id: "annexes", label: "Annexes", pages: "6-8" },
];

export default function ReportingPage() {
  const { currentAnalysis, analyses, reports, addReport, updateReport, deleteReport, loadFromStorage } = useAnalysisStore();
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [genStep, setGenStep] = useState("");
  const [checked, setChecked] = useState(sections.map((_, i) => i < 7));

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  const handleGenerate = async () => {
    if (!currentAnalysis) return;
    setGenerating(true);
    setProgress(0);

    const reportId = `report-${Date.now()}`;
    const selectedSections = sections.filter((_, i) => checked[i]).map((s) => s.label);
    const totalPages = checked.reduce((acc, v, i) => {
      if (!v) return acc;
      const range = sections[i].pages.split("-");
      return acc + Math.floor((parseInt(range[0]) + parseInt(range[1] || range[0])) / 2);
    }, 0);

    addReport({
      id: reportId,
      name: `Rapport Veille - ${new Date().toLocaleDateString("fr-FR")}`,
      date: new Date().toISOString(),
      analysisId: currentAnalysis.id,
      sections: selectedSections,
      status: "generating",
      pages: totalPages,
      size: `${(totalPages * 0.2).toFixed(1)} Mo`,
    });

    const steps = [
      { p: 15, s: "Collecte des données d'analyse..." },
      { p: 30, s: "Génération de la synthèse exécutive..." },
      { p: 45, s: "Création des graphiques et visualisations..." },
      { p: 55, s: "Analyse de sentiment et nuage de mots..." },
      { p: 65, s: "Cartographie des risques régionaux..." },
      { p: 75, s: "Génération des tableaux de données..." },
      { p: 85, s: "Mise en page du document PDF..." },
      { p: 95, s: "Finalisation et indexation..." },
    ];

    for (const step of steps) {
      await new Promise((r) => setTimeout(r, 600 + Math.random() * 400));
      setProgress(step.p);
      setGenStep(step.s);
    }

    updateReport(reportId, { status: "ready" });
    setProgress(100);
    setGenStep("Rapport généré avec succès !");
    setGenerating(false);
  };

  const hasAnalysis = !!currentAnalysis;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><FileText className="text-indigo-400" /> Génération de Rapports PDF</h1>
          <p className="text-sm text-gray-400">Rapports professionnels basés sur les données d&apos;analyse collectées</p>
        </motion.div>

        {!hasAnalysis && (
          <GlassCard className="flex flex-col items-center justify-center p-12 text-center">
            <AlertCircle size={48} className="mb-4 text-amber-400" />
            <h2 className="mb-2 text-lg font-bold">Aucune analyse disponible</h2>
            <p className="mb-6 text-sm text-gray-400">Vous devez d&apos;abord lancer une analyse depuis le Dashboard pour pouvoir générer un rapport.</p>
            <Link href="/dashboard/"><Button><Play size={16} /> Aller au Dashboard</Button></Link>
          </GlassCard>
        )}

        {hasAnalysis && (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <GlassCard className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold flex items-center gap-2"><Settings size={18} /> Sections du Rapport</h3>
                  <div className="text-xs text-gray-500">
                    Basé sur l&apos;analyse du {new Date(currentAnalysis!.completedAt).toLocaleDateString("fr-FR")}
                  </div>
                </div>
                <div className="space-y-3">
                  {sections.map((s, i) => (
                    <motion.label key={s.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }} className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-colors hover:bg-white/5">
                      <input type="checkbox" checked={checked[i]} onChange={() => setChecked((c) => c.map((v, j) => (j === i ? !v : v)))} className="h-4 w-4 rounded border-white/20 bg-white/5 text-blue-500 focus:ring-blue-500/50" />
                      <div className="flex-1"><div className="text-sm font-medium">{s.label}</div></div>
                      <span className="text-xs text-gray-500">{s.pages} pages</span>
                    </motion.label>
                  ))}
                </div>

                <div className="mt-6">
                  {generating ? (
                    <div className="space-y-3">
                      <div className="text-sm text-gray-300">{genStep}</div>
                      <ProgressBar value={progress} />
                    </div>
                  ) : (
                    <Button onClick={handleGenerate} size="lg" className="w-full" disabled={!checked.some(Boolean)}>
                      <FileText size={18} /> Générer le Rapport PDF
                    </Button>
                  )}
                </div>
              </GlassCard>
            </div>

            <GlassCard className="p-6">
              <h3 className="mb-4 text-lg font-semibold">Aperçu</h3>
              <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-center">
                <div className="mx-auto mb-4 h-48 w-36 rounded-lg border border-white/10 bg-gradient-to-b from-white/5 to-transparent p-4">
                  <div className="mb-3 text-[6px] font-bold text-gray-400">RAPPORT DE VEILLE ÉLECTORALE</div>
                  <div className="mb-1 text-[5px] text-gray-500">Maroc 2026</div>
                  <div className="mb-2 text-[4px] text-blue-400">{new Date().toLocaleDateString("fr-FR")}</div>
                  <div className="space-y-1">
                    {sections.filter((_, i) => checked[i]).map((s, i) => (
                      <div key={i} className="h-0.5 w-full rounded bg-white/10" />
                    ))}
                  </div>
                </div>
                <div className="text-sm font-medium">{checked.filter(Boolean).length} sections</div>
                <div className="text-xs text-gray-500">
                  ~{checked.reduce((acc, v, i) => acc + (v ? parseInt(sections[i].pages) : 0), 0)}-
                  {checked.reduce((acc, v, i) => acc + (v ? parseInt(sections[i].pages.split("-")[1] || sections[i].pages) : 0), 0)} pages
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  {currentAnalysis!.kpis.totalMentions.toLocaleString("fr-FR")} mentions · {currentAnalysis!.kpis.totalAlerts} alertes
                </div>
              </div>
            </GlassCard>
          </div>
        )}

        {/* Reports History */}
        <GlassCard className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Historique des Rapports Générés ({reports.length})</h3>
          {reports.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-500">Aucun rapport généré pour le moment.</div>
          ) : (
            <div className="space-y-3">
              {reports.map((r, i) => (
                <motion.div key={r.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/5 transition-colors">
                  <FileText size={20} className="text-indigo-400" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{r.name}</div>
                    <div className="text-xs text-gray-500">
                      {new Date(r.date).toLocaleString("fr-FR")} · {r.pages} pages · {r.size} · {r.sections.length} sections
                    </div>
                  </div>
                  <Badge variant={r.status === "ready" ? "low" : r.status === "generating" ? "info" : "critical"}>
                    {r.status === "ready" ? <><CheckCircle size={12} /> Prêt</> : r.status === "generating" ? "En cours" : "Erreur"}
                  </Badge>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm"><Eye size={14} /></Button>
                    <Button variant="ghost" size="sm"><Download size={14} /></Button>
                    <button onClick={() => deleteReport(r.id)} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors">
                      <Trash2 size={14} />
                    </button>
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
