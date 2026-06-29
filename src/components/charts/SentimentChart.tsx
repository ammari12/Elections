"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { generateSentimentData } from "@/data/mockData";
import { GlassCard } from "@/components/ui/GlassCard";

const data = generateSentimentData();

export function SentimentChart() {
  return (
    <GlassCard className="p-6">
      <h3 className="mb-4 text-lg font-semibold">Analyse de Sentiment par Parti</h3>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis type="number" stroke="#64748B" fontSize={10} />
          <YAxis dataKey="party" type="category" stroke="#64748B" fontSize={11} width={60} />
          <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
          <Legend />
          <Bar dataKey="positive" stackId="a" fill="#22C55E" name="Positif" radius={[0, 0, 0, 0]} />
          <Bar dataKey="neutral" stackId="a" fill="#64748B" name="Neutre" />
          <Bar dataKey="negative" stackId="a" fill="#EF4444" name="Négatif" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}
