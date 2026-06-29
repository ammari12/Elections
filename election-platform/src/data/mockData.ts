import { PARTIES, REGIONS, SOCIAL_NETWORKS } from "./constants";

export function generateDailyMentions(days: number = 30) {
  const data = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toISOString().split("T")[0],
      twitter: Math.floor(Math.random() * 5000 + 2000),
      facebook: Math.floor(Math.random() * 3000 + 1500),
      instagram: Math.floor(Math.random() * 2000 + 800),
      tiktok: Math.floor(Math.random() * 4000 + 1000),
      youtube: Math.floor(Math.random() * 1000 + 300),
    });
  }
  return data;
}

export function generateSentimentData() {
  return PARTIES.map((p) => ({
    party: p.name,
    positive: Math.floor(Math.random() * 40 + 20),
    neutral: Math.floor(Math.random() * 30 + 20),
    negative: Math.floor(Math.random() * 30 + 10),
    color: p.color,
  }));
}

export function generateAlerts(count: number = 50) {
  const severities = ["critical", "high", "medium", "low"] as const;
  const categories = ["Injures", "Diffamation", "Désinformation", "Appels à la violence", "Discours de haine"] as const;
  const sources = [...SOCIAL_NETWORKS, "Presse", "Document uploadé"];
  return Array.from({ length: count }, (_, i) => ({
    id: `alert-${i}`,
    title: `Alerte ${categories[i % categories.length]} détectée`,
    description: `Contenu problématique identifié sur ${sources[i % sources.length]} concernant ${PARTIES[i % PARTIES.length].name}`,
    severity: severities[i % severities.length],
    category: categories[i % categories.length],
    source: sources[i % sources.length],
    region: REGIONS[i % REGIONS.length].name,
    party: PARTIES[i % PARTIES.length].name,
    timestamp: new Date(Date.now() - Math.random() * 30 * 86400000).toISOString(),
    status: i % 3 === 0 ? "resolved" : i % 3 === 1 ? "investigating" : "new",
  }));
}

export function generatePartyActivity() {
  return PARTIES.map((p) => ({
    ...p,
    score: Math.floor(Math.random() * 50 + 50),
    mentions: Math.floor(Math.random() * 10000 + 2000),
    sentiment: +(Math.random() * 2 - 0.5).toFixed(2),
    trend: Math.random() > 0.5 ? "up" : "down",
    trendValue: +(Math.random() * 15).toFixed(1),
    activities: [
      { type: "Rassemblement", date: "2026-06-15", location: REGIONS[Math.floor(Math.random() * 12)].name, description: "Meeting électoral régional" },
      { type: "Communiqué", date: "2026-06-18", location: "National", description: "Publication du programme économique" },
      { type: "Campagne digitale", date: "2026-06-22", location: "National", description: "Lancement de la campagne sur les réseaux sociaux" },
    ],
  }));
}

export function generateRegionRisks() {
  return REGIONS.map((r) => ({
    ...r,
    riskLevel: Math.random() > 0.7 ? "high" : Math.random() > 0.4 ? "medium" : "low",
    alertCount: Math.floor(Math.random() * 30 + 5),
    criticalCount: Math.floor(Math.random() * 5),
    topCategory: ["Désinformation", "Injures", "Appels à la violence"][Math.floor(Math.random() * 3)],
  }));
}

export const KPI_DATA = {
  totalMentions: 187432,
  totalAlerts: 1247,
  criticalAlerts: 23,
  activeSources: 53,
  sentimentScore: 0.34,
  partiesMonitored: 12,
  regionsMonitored: 12,
  documentsProcessed: 342,
};
