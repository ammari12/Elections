"use client";
import { useState } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { generateRegionRisks } from "@/data/mockData";
import { motion } from "framer-motion";

const risks = generateRegionRisks();
const riskColors: Record<string, string> = { high: "#EF4444", medium: "#F59E0B", low: "#22C55E" };

function latLngToSvg(lat: number, lng: number): { x: number; y: number } {
  const minLat = 21, maxLat = 36, minLng = -17, maxLng = -1;
  const x = ((lng - minLng) / (maxLng - minLng)) * 700 + 50;
  const y = ((maxLat - lat) / (maxLat - minLat)) * 500 + 25;
  return { x, y };
}

export function RiskMap() {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <GlassCard className="p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Cartographie des Risques</h3>
        <p className="text-sm text-gray-400">Répartition géographique des alertes par région</p>
      </div>

      <div className="flex gap-3 mb-4">
        {[{ label: "Élevé", color: "#EF4444" }, { label: "Moyen", color: "#F59E0B" }, { label: "Faible", color: "#22C55E" }].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: l.color }} />
            {l.label}
          </div>
        ))}
      </div>

      <svg viewBox="0 0 800 550" className="w-full h-auto">
        <defs>
          <radialGradient id="bg-glow">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.05" />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="800" height="550" fill="url(#bg-glow)" rx="16" />

        {risks.map((r) => {
          const { x, y } = latLngToSvg(r.lat, r.lng);
          const radius = Math.max(r.alertCount / 2, 12);
          const isHovered = hovered === r.id;
          const color = riskColors[r.riskLevel];

          return (
            <g key={r.id} onMouseEnter={() => setHovered(r.id)} onMouseLeave={() => setHovered(null)} className="cursor-pointer">
              <motion.circle
                cx={x} cy={y} r={radius + 8}
                fill={color} opacity={0.1}
                animate={{ r: [radius + 8, radius + 14, radius + 8] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
              <circle cx={x} cy={y} r={radius} fill={color} opacity={0.3} stroke={color} strokeWidth={2} />
              <circle cx={x} cy={y} r={4} fill={color} />

              <text x={x} y={y - radius - 8} textAnchor="middle" fill="#CBD5E1" fontSize={isHovered ? 12 : 10} fontWeight={isHovered ? 600 : 400}>
                {r.name.split("-")[0].trim()}
              </text>

              {isHovered && (
                <g>
                  <rect x={x - 90} y={y + radius + 8} width={180} height={72} rx={8} fill="#1E293B" stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
                  <text x={x} y={y + radius + 28} textAnchor="middle" fill="white" fontSize={11} fontWeight={600}>{r.name}</text>
                  <text x={x} y={y + radius + 44} textAnchor="middle" fill="#94A3B8" fontSize={10}>Alertes: {r.alertCount} | Critiques: {r.criticalCount}</text>
                  <text x={x} y={y + radius + 60} textAnchor="middle" fill="#94A3B8" fontSize={10}>{r.topCategory}</text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </GlassCard>
  );
}
