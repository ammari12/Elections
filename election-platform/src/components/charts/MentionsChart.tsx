"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { generateDailyMentions } from "@/data/mockData";
import { GlassCard } from "@/components/ui/GlassCard";

const data = generateDailyMentions();

export function MentionsChart() {
  return (
    <GlassCard className="p-6">
      <h3 className="mb-4 text-lg font-semibold">Évolution des Mentions</h3>
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="tw" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1DA1F2" stopOpacity={0.3} /><stop offset="100%" stopColor="#1DA1F2" stopOpacity={0} /></linearGradient>
            <linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4267B2" stopOpacity={0.3} /><stop offset="100%" stopColor="#4267B2" stopOpacity={0} /></linearGradient>
            <linearGradient id="ig" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#E1306C" stopOpacity={0.3} /><stop offset="100%" stopColor="#E1306C" stopOpacity={0} /></linearGradient>
            <linearGradient id="tt" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#00F2EA" stopOpacity={0.3} /><stop offset="100%" stopColor="#00F2EA" stopOpacity={0} /></linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="date" stroke="#64748B" fontSize={10} tickFormatter={(v) => v.slice(5)} />
          <YAxis stroke="#64748B" fontSize={10} />
          <Tooltip contentStyle={{ background: "#1E293B", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12 }} />
          <Legend />
          <Area type="monotone" dataKey="twitter" stroke="#1DA1F2" fill="url(#tw)" name="Twitter/X" />
          <Area type="monotone" dataKey="facebook" stroke="#4267B2" fill="url(#fb)" name="Facebook" />
          <Area type="monotone" dataKey="instagram" stroke="#E1306C" fill="url(#ig)" name="Instagram" />
          <Area type="monotone" dataKey="tiktok" stroke="#00F2EA" fill="url(#tt)" name="TikTok" />
        </AreaChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}
