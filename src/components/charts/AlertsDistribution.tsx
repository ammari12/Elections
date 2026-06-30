"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { GlassCard } from "@/components/ui/GlassCard";

const COLORS = ["#EF4444", "#F59E0B", "#8B5CF6", "#EC4899", "#3B82F6", "#14B8A6", "#F97316"];

export function AlertsDistribution({ data: rawData }: { data?: { category: string }[] }) {
  const counts: Record<string, number> = {};
  for (const a of rawData || []) counts[a.category] = (counts[a.category] || 0) + 1;
  const data = Object.entries(counts).map(([name, value], i) => ({ name, value, color: COLORS[i % COLORS.length] }));

  return (
    <GlassCard className="p-6">
      <h3 className="mb-4 text-lg font-semibold">Répartition des Alertes</h3>
      {data.length === 0 ? (
        <p className="text-sm text-gray-500">Aucune alerte détectée.</p>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={4} dataKey="value">
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}
    </GlassCard>
  );
}
