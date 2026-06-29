"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { GlassCard } from "@/components/ui/GlassCard";

const data = [
  { name: "Désinformation", value: 35, color: "#EF4444" },
  { name: "Injures", value: 25, color: "#F59E0B" },
  { name: "Diffamation", value: 18, color: "#8B5CF6" },
  { name: "Appels violence", value: 12, color: "#EC4899" },
  { name: "Discours haine", value: 10, color: "#3B82F6" },
];

export function AlertsDistribution() {
  return (
    <GlassCard className="p-6">
      <h3 className="mb-4 text-lg font-semibold">Répartition des Alertes</h3>
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
    </GlassCard>
  );
}
