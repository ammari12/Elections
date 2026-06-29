"use client";
import { useEffect, useState } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { generateRegionRisks } from "@/data/mockData";

const risks = generateRegionRisks();

export function RiskMap() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  if (!mounted) {
    return (
      <GlassCard className="flex h-[500px] items-center justify-center">
        <div className="text-gray-400">Chargement de la carte...</div>
      </GlassCard>
    );
  }

  return <RiskMapClient />;
}

function RiskMapClient() {
  const [L, setL] = useState<any>(null);

  useEffect(() => {
    import("react-leaflet").then(setL);
  }, []);

  if (!L) return <GlassCard className="flex h-[500px] items-center justify-center"><div className="text-gray-400">Chargement...</div></GlassCard>;

  const { MapContainer, TileLayer, CircleMarker, Popup } = L;

  const riskColors: Record<string, string> = { high: "#EF4444", medium: "#F59E0B", low: "#22C55E" };

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
