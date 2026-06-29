"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { generatePartyActivity } from "@/data/mockData";
import { motion } from "framer-motion";
import { Users, TrendingUp, TrendingDown, Activity, MessageCircle, MapPin } from "lucide-react";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from "recharts";

const parties = generatePartyActivity().sort((a, b) => b.score - a.score);

const radarData = [
  { subject: "Réseaux sociaux", PAM: 85, PJD: 75, RNI: 90, Istiqlal: 65 },
  { subject: "Presse", PAM: 70, PJD: 80, RNI: 75, Istiqlal: 85 },
  { subject: "Terrain", PAM: 60, PJD: 90, RNI: 55, Istiqlal: 80 },
  { subject: "Jeunesse", PAM: 75, PJD: 60, RNI: 85, Istiqlal: 50 },
  { subject: "Rural", PAM: 50, PJD: 70, RNI: 45, Istiqlal: 75 },
  { subject: "Digital", PAM: 80, PJD: 55, RNI: 95, Istiqlal: 45 },
];

export default function PartisPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Users className="text-purple-400" /> Partis Politiques</h1>
          <p className="text-sm text-gray-400">Suivi de l&apos;activité des 12 partis politiques majeurs</p>
        </motion.div>

        {/* Ranking */}
        <GlassCard className="p-6">
          <h3 className="mb-6 text-lg font-semibold">Classement par Score d&apos;Activité</h3>
          <div className="space-y-4">
            {parties.map((party, i) => (
              <motion.div key={party.id} initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center gap-4">
                <span className="w-6 text-center text-lg font-bold text-gray-500">{i + 1}</span>
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: party.color }} />
                <div className="w-24 font-medium text-sm">{party.name}</div>
                <div className="flex-1">
                  <ProgressBar value={party.score} showLabel={false} color={`from-[${party.color}] to-[${party.color}]`} />
                </div>
                <div className="w-12 text-right text-sm font-bold">{party.score}</div>
                <div className={`flex items-center gap-1 text-xs ${party.trend === "up" ? "text-emerald-400" : "text-red-400"}`}>
                  {party.trend === "up" ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  {party.trendValue}%
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Radar Chart */}
          <GlassCard className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Analyse Comparative des Stratégies</h3>
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="subject" stroke="#64748B" fontSize={11} />
                <PolarRadiusAxis stroke="rgba(255,255,255,0.1)" />
                <Radar name="PAM" dataKey="PAM" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.15} />
                <Radar name="PJD" dataKey="PJD" stroke="#EF4444" fill="#EF4444" fillOpacity={0.15} />
                <Radar name="RNI" dataKey="RNI" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.15} />
                <Radar name="Istiqlal" dataKey="Istiqlal" stroke="#22C55E" fill="#22C55E" fillOpacity={0.15} />
                <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
              </RadarChart>
            </ResponsiveContainer>
          </GlassCard>

          {/* Party Cards */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Activités Récentes</h3>
            {parties.slice(0, 4).map((party, i) => (
              <GlassCard key={party.id} className="p-4" delay={i * 0.05}>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: party.color }} />
                  <span className="font-semibold text-sm">{party.fullName}</span>
                  <span className="text-xs text-gray-500">({party.name})</span>
                </div>
                <div className="flex gap-4 mb-3 text-xs text-gray-400">
                  <span className="flex items-center gap-1"><MessageCircle size={12} /> <AnimatedCounter target={party.mentions} /> mentions</span>
                  <span className="flex items-center gap-1"><Activity size={12} /> Score: {party.score}</span>
                </div>
                <div className="space-y-2">
                  {party.activities.slice(0, 2).map((act, j) => (
                    <div key={j} className="flex items-start gap-2 text-xs text-gray-400 rounded-lg bg-white/[0.02] p-2">
                      <MapPin size={12} className="mt-0.5 shrink-0 text-blue-400" />
                      <div>
                        <span className="text-gray-300">{act.type}</span> — {act.description}
                        <div className="text-gray-500 mt-0.5">{act.date} · {act.location}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
