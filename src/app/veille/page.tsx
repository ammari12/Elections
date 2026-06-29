"use client";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { MentionsChart } from "@/components/charts/MentionsChart";
import { SentimentChart } from "@/components/charts/SentimentChart";
import { generateAlerts } from "@/data/mockData";
import { SOCIAL_NETWORKS } from "@/data/constants";
import { motion } from "framer-motion";
import { Search, Filter, Radio, TrendingUp, Hash, MessageCircle } from "lucide-react";
import { useState } from "react";

const alerts = generateAlerts(30);

const trendingTopics = [
  { tag: "#Elections2026", count: 45200, trend: "+12%" },
  { tag: "#MarocVote", count: 32100, trend: "+8%" },
  { tag: "#RéformeÉlectorale", count: 28700, trend: "+25%" },
  { tag: "#Jeunesse2026", count: 21300, trend: "+15%" },
  { tag: "#TransparenceÉlectorale", count: 18900, trend: "+5%" },
  { tag: "#DéveloppementRural", count: 15400, trend: "+18%" },
  { tag: "#NumériqueMaroc", count: 12800, trend: "+22%" },
  { tag: "#ParticipationCitoyenne", count: 11200, trend: "+9%" },
];

export default function VeillePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedNetwork, setSelectedNetwork] = useState<string | null>(null);

  const filtered = alerts.filter((a) => {
    if (selectedNetwork && a.source !== selectedNetwork) return false;
    if (searchQuery && !a.title.toLowerCase().includes(searchQuery.toLowerCase()) && !a.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Radio className="text-blue-400" /> Veille OSINT</h1>
          <p className="text-sm text-gray-400">Surveillance en temps réel des réseaux sociaux et de la presse</p>
        </motion.div>

        {/* Search & Filters */}
        <GlassCard className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="text"
                placeholder="Rechercher dans les alertes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50"
              />
            </div>
            <div className="flex gap-2">
              <Button variant={!selectedNetwork ? "primary" : "secondary"} size="sm" onClick={() => setSelectedNetwork(null)}>Tous</Button>
              {SOCIAL_NETWORKS.map((n) => (
                <Button key={n} variant={selectedNetwork === n ? "primary" : "secondary"} size="sm" onClick={() => setSelectedNetwork(n === selectedNetwork ? null : n)}>{n}</Button>
              ))}
            </div>
          </div>
        </GlassCard>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Feed */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-lg font-semibold">Flux des alertes ({filtered.length})</h3>
            {filtered.map((alert, i) => (
              <motion.div key={alert.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                <GlassCard className="p-4 cursor-pointer" hover>
                  <div className="flex items-start gap-3">
                    <Badge variant={alert.severity as any} pulse={alert.severity === "critical"}>{alert.severity}</Badge>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{alert.title}</span>
                        <span className="text-xs text-gray-500">{alert.source}</span>
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-2">{alert.description}</p>
                      <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                        <span>{new Date(alert.timestamp).toLocaleDateString("fr-FR")}</span>
                        <span>{alert.region}</span>
                        <span className="rounded-md bg-white/5 px-2 py-0.5">{alert.category}</span>
                      </div>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <GlassCard className="p-4">
              <h3 className="mb-4 flex items-center gap-2 font-semibold"><Hash size={16} className="text-blue-400" /> Trending Topics</h3>
              <div className="space-y-3">
                {trendingTopics.map((t, i) => (
                  <motion.div key={t.tag} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-center justify-between rounded-lg p-2 hover:bg-white/5 transition-colors">
                    <div>
                      <div className="text-sm font-medium text-blue-400">{t.tag}</div>
                      <div className="text-xs text-gray-500">{t.count.toLocaleString("fr-FR")} mentions</div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-emerald-400">
                      <TrendingUp size={12} /> {t.trend}
                    </div>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>

        {/* Charts */}
        <div className="grid gap-6 lg:grid-cols-2">
          <MentionsChart />
          <SentimentChart />
        </div>
      </div>
    </DashboardLayout>
  );
}
