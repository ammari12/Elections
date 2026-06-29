"use client";
import { useEffect, useState } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { generateRegionRisks } from "@/data/mockData";

const risks = generateRegionRisks();
const riskColors: Record<string, string> = { high: "#EF4444", medium: "#F59E0B", low: "#22C55E" };

export function RiskMap() {
  const [mounted, setMounted] = useState(false);
  const [L, setL] = useState<any>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setMounted(true);
    import("react-leaflet")
      .then(setL)
      .catch(() => setError(true));
  }, []);

  if (!mounted || (!L && !error)) {
    return (
      <GlassCard className="flex h-[500px] items-center justify-center">
        <div className="text-gray-400">Chargement de la carte...</div>
      </GlassCard>
    );
  }

  if (error || !L) {
    return (
      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold mb-4">Cartographie des Risques</h3>
        <div className="space-y-2">
          {risks.sort((a, b) => b.alertCount - a.alertCount).map((r) => (
            <div key={r.id} className="flex items-center justify-between rounded-lg bg-white/[0.03] p-3">
              <span className="text-sm font-medium">{r.name}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400">{r.alertCount} alertes</span>
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: riskColors[r.riskLevel] }} />
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    );
  }

  const { MapContainer, TileLayer, CircleMarker, Popup } = L;

  return (
    <GlassCard className="overflow-hidden p-0">
      <div className="p-4 pb-0">
        <h3 className="text-lg font-semibold">Cartographie des Risques</h3>
        <p className="text-sm text-gray-400">Répartition géographique des alertes par région</p>
      </div>
      <div className="h-[500px]">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <MapContainer center={[31.7917, -7.0926]} zoom={5} style={{ height: "100%", width: "100%", background: "#0A0E1A" }} zoomControl={false}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" attribution="CartoDB" />
          {risks.map((r) => (
            <CircleMarker key={r.id} center={[r.lat, r.lng]} radius={Math.max(r.alertCount / 2, 8)} pathOptions={{ color: riskColors[r.riskLevel], fillColor: riskColors[r.riskLevel], fillOpacity: 0.4, weight: 2 }}>
              <Popup>
                <div className="text-sm">
                  <strong>{r.name}</strong><br />
                  Alertes: {r.alertCount}<br />
                  Critiques: {r.criticalCount}<br />
                  Catégorie: {r.topCategory}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </GlassCard>
  );
}
