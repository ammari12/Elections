"use client";
import { useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAnalysisStore } from "@/stores/useAnalysisStore";
import { motion } from "framer-motion";
import { Users, TrendingUp, TrendingDown, MessageCircle, Play } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import Link from "next/link";

export default function PartisPage() {
  const { currentAnalysis, loadFromStorage } = useAnalysisStore();

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  if (!currentAnalysis) {
    return (
      <DashboardLayout>
        <GlassCard className="flex flex-col items-center justify-center p-16 text-center">
          <Users size={48} className="mb-4 text-purple-400" />
          <h2 className="mb-2 text-xl font-bold">Aucune analyse disponible</h2>
          <p className="mb-6 max-w-md text-gray-400">Lancez une analyse depuis le Dashboard pour voir l&apos;activité réelle des partis détectée dans la presse.</p>
          <Link href="/dashboard/"><span className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 px-5 py-2.5 text-sm font-medium"><Play size={16} /> Aller au Dashboard</span></Link>
        </GlassCard>
      </DashboardLayout>
    );
  }

  const parties = currentAnalysis.partyScores;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Users className="text-purple-400" /> Partis Politiques</h1>
          <p className="text-sm text-gray-400">Mentions et sentiment détectés par mot-clé dans les {currentAnalysis.sources.press} articles de presse réels analysés</p>
        </motion.div>

        {parties.length === 0 ? (
          <GlassCard className="p-12 text-center text-sm text-gray-500">Aucune mention de parti détectée dans les articles de cette analyse.</GlassCard>
        ) : (
          <>
            <GlassCard className="p-6">
              <h3 className="mb-6 text-lg font-semibold">Classement par Nombre de Mentions</h3>
              <div className="space-y-4">
                {parties.map((party, i) => (
                  <motion.div key={party.id} initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-4">
                    <span className="w-6 text-center text-lg font-bold text-gray-500">{i + 1}</span>
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: party.color }} />
                    <div className="w-24 font-medium text-sm">{party.name}</div>
                    <div className="flex-1">
                      <ProgressBar value={(party.mentions / parties[0].mentions) * 100} showLabel={false} />
                    </div>
                    <div className="w-12 text-right text-sm font-bold">{party.mentions}</div>
                    <div className={`flex items-center gap-1 text-xs ${party.trend === "up" ? "text-emerald-400" : "text-red-400"}`}>
                      {party.trend === "up" ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {party.sentiment >= 0 ? "+" : ""}{(party.sentiment * 100).toFixed(0)}%
                    </div>
                  </motion.div>
                ))}
              </div>
            </GlassCard>

            <div className="grid gap-6 lg:grid-cols-2">
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

              <div className="space-y-4 max-h-[350px] overflow-y-auto pr-1">
                <h3 className="text-lg font-semibold">Articles Récents par Parti</h3>
                {parties.slice(0, 4).map((party, i) => {
                  const partyArticles = currentAnalysis.articles.filter((a) => a.parties.includes(party.name)).slice(0, 2);
                  return (
                    <GlassCard key={party.id} className="p-4" delay={i * 0.05}>
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: party.color }} />
                        <span className="font-semibold text-sm">{party.fullName}</span>
                        <span className="text-xs text-gray-500">({party.name})</span>
                      </div>
                      <div className="flex gap-4 mb-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1"><MessageCircle size={12} /> <AnimatedCounter target={party.mentions} /> mentions</span>
                      </div>
                      <div className="space-y-2">
                        {partyArticles.map((a) => (
                          <div key={a.id} className="rounded-lg bg-white/[0.02] p-2 text-xs text-gray-400">
                            <div className="text-gray-300">{a.title}</div>
                            <div className="mt-1 flex items-center gap-2 text-gray-500">
                              <span>{a.source}</span>
                              {a.url && a.url !== "#" && (
                                <a href={a.url} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">Source ↗</a>
                              )}
                            </div>
                          </div>
                        ))}
                        {partyArticles.length === 0 && <div className="text-xs text-gray-500">Aucun article récent.</div>}
                      </div>
                    </GlassCard>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
