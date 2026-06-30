"use client";
import { create } from "zustand";

export interface AnalysisResult {
  id: string;
  startedAt: string;
  completedAt: string;
  period: string;
  status: "completed" | "failed";
  sources: {
    press: number;
    social: number;
    total: number;
  };
  kpis: {
    totalMentions: number;
    totalAlerts: number;
    criticalAlerts: number;
    sentimentScore: number;
    topParty: string;
    topRegion: string;
  };
  articles: ArticleData[];
  alerts: AlertData[];
  partyScores: PartyScore[];
  sentimentByParty: SentimentData[];
  mentionsByDay: DailyMentions[];
  regionRisks: RegionRisk[];
}

export interface RegionRisk {
  id: string;
  name: string;
  lat: number;
  lng: number;
  alertCount: number;
  criticalCount: number;
  riskLevel: "high" | "medium" | "low";
  topCategory: string;
}

export const REGION_COORDS: Record<string, { id: string; lat: number; lng: number }> = {
  "Tanger-Tétouan-Al Hoceïma": { id: "tanger", lat: 35.7595, lng: -5.834 },
  "Oriental": { id: "oriental", lat: 34.6814, lng: -1.9086 },
  "Fès-Meknès": { id: "fes", lat: 34.0181, lng: -5.0078 },
  "Rabat-Salé-Kénitra": { id: "rabat", lat: 34.0209, lng: -6.8416 },
  "Béni Mellal-Khénifra": { id: "beni", lat: 32.3373, lng: -6.3498 },
  "Casablanca-Settat": { id: "casablanca", lat: 33.5731, lng: -7.5898 },
  "Marrakech-Safi": { id: "marrakech", lat: 31.6295, lng: -7.9811 },
  "Drâa-Tafilalet": { id: "draa", lat: 31.9314, lng: -5.3625 },
  "Souss-Massa": { id: "souss", lat: 30.4278, lng: -9.5981 },
  "Guelmim-Oued Noun": { id: "guelmim", lat: 28.9833, lng: -10.0578 },
  "Laâyoune-Sakia El Hamra": { id: "laayoune", lat: 27.1253, lng: -13.1625 },
  "Dakhla-Oued Ed-Dahab": { id: "dakhla", lat: 23.6848, lng: -15.957 },
  "National": { id: "national", lat: 31.7917, lng: -7.0926 },
};

export interface ArticleData {
  id: string;
  title: string;
  source: string;
  url: string;
  date: string;
  sentiment: "positive" | "negative" | "neutral";
  parties: string[];
  category: string;
  excerpt: string;
}

const PARTY_KEYWORDS: Record<string, string[]> = {
  RNI: ["rni", "rassemblement national des indépendants", "akhannouch"],
  PAM: ["pam", "authenticité et modernité"],
  Istiqlal: ["istiqlal"],
  PJD: ["pjd", "justice et développement"],
  USFP: ["usfp", "union socialiste"],
  MP: ["mouvement populaire"],
  PPS: ["pps", "progrès et socialisme"],
  UC: ["union constitutionnelle"],
  FGD: ["fgd", "gauche démocratique"],
};

const NEGATIVE_WORDS = ["crise", "tension", "scandale", "polémique", "critique", "échec", "violence", "fraude", "corruption", "désinformation", "haine", "menace"];
const POSITIVE_WORDS = ["succès", "victoire", "réussite", "avancée", "accord", "soutien", "progrès", "lancement", "réforme positive"];

export const REGION_KEYWORDS: Record<string, string[]> = {
  "Tanger-Tétouan-Al Hoceïma": ["tanger", "tétouan", "al hoceïma", "hoceima", "tetouan"],
  "Oriental": ["oujda", "nador", "berkane", "oriental"],
  "Fès-Meknès": ["fès", "fes", "meknès", "meknes", "ifrane"],
  "Rabat-Salé-Kénitra": ["rabat", "salé", "sale", "kénitra", "kenitra", "témara"],
  "Béni Mellal-Khénifra": ["béni mellal", "beni mellal", "khénifra", "khenifra"],
  "Casablanca-Settat": ["casablanca", "settat", "mohammedia", "berrechid"],
  "Marrakech-Safi": ["marrakech", "safi", "essaouira"],
  "Drâa-Tafilalet": ["ouarzazate", "errachidia", "tafilalet", "drâa", "zagora"],
  "Souss-Massa": ["agadir", "souss", "massa", "taroudant"],
  "Guelmim-Oued Noun": ["guelmim", "tan-tan", "sidi ifni"],
  "Laâyoune-Sakia El Hamra": ["laâyoune", "laayoune", "boujdour"],
  "Dakhla-Oued Ed-Dahab": ["dakhla"],
};

function detectRegion(text: string): string {
  const lower = text.toLowerCase();
  const hit = Object.entries(REGION_KEYWORDS).find(([, kws]) => kws.some((k) => lower.includes(k)));
  return hit ? hit[0] : "National";
}

function detectParties(text: string): string[] {
  const lower = text.toLowerCase();
  return Object.entries(PARTY_KEYWORDS)
    .filter(([, kws]) => kws.some((k) => lower.includes(k)))
    .map(([name]) => name);
}

function detectSentiment(text: string): "positive" | "negative" | "neutral" {
  const lower = text.toLowerCase();
  const neg = NEGATIVE_WORDS.some((w) => lower.includes(w));
  const pos = POSITIVE_WORDS.some((w) => lower.includes(w));
  if (neg && !pos) return "negative";
  if (pos && !neg) return "positive";
  return "neutral";
}

const ALERT_KEYWORDS: { match: string[]; category: string; severity: "critical" | "high" | "medium" | "low" }[] = [
  { match: ["désinformation", "fake news", "rumeur"], category: "Désinformation", severity: "high" },
  { match: ["violence", "menace"], category: "Appels à la violence", severity: "critical" },
  { match: ["haine", "discrimination"], category: "Discours de haine", severity: "high" },
  { match: ["fraude", "corruption"], category: "Fraude électorale", severity: "critical" },
  { match: ["diffamation", "injure", "insulte"], category: "Diffamation", severity: "medium" },
  { match: ["manipulation", "scandale"], category: "Manipulation", severity: "medium" },
];

function detectAlertFromArticle(article: ArticleData): AlertData | null {
  const lower = (article.title + " " + article.excerpt).toLowerCase();
  const hit = ALERT_KEYWORDS.find((k) => k.match.some((m) => lower.includes(m)));
  if (!hit) return null;
  return {
    id: `alert-${article.id}`,
    title: article.title,
    description: article.excerpt,
    severity: hit.severity,
    category: hit.category,
    source: article.source,
    sourceUrl: article.url,
    region: detectRegion(article.title + " " + article.excerpt),
    party: article.parties[0] || "",
    timestamp: article.date,
    status: "new",
  };
}

export interface AlertData {
  id: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  source: string;
  sourceUrl: string;
  region: string;
  party: string;
  timestamp: string;
  status: "new" | "investigating" | "resolved";
}

export interface PartyScore {
  id: string;
  name: string;
  fullName: string;
  color: string;
  score: number;
  mentions: number;
  sentiment: number;
  trend: "up" | "down";
  trendValue: number;
}

export interface SentimentData {
  party: string;
  positive: number;
  neutral: number;
  negative: number;
  color: string;
}

export interface DailyMentions {
  date: string;
  press: number;
  social: number;
  total: number;
}

export interface GeneratedReport {
  id: string;
  name: string;
  date: string;
  analysisId: string;
  sections: string[];
  status: "generating" | "ready" | "failed";
  pages: number;
  size: string;
  content?: string;
}

interface AnalysisState {
  analyses: AnalysisResult[];
  currentAnalysis: AnalysisResult | null;
  isAnalyzing: boolean;
  analysisProgress: number;
  analysisStep: string;
  reports: GeneratedReport[];
  loadFromStorage: () => void;
  startAnalysis: () => Promise<void>;
  addReport: (report: GeneratedReport) => void;
  updateReport: (id: string, updates: Partial<GeneratedReport>) => void;
  deleteReport: (id: string) => void;
  deleteAnalysis: (id: string) => void;
}

function saveToStorage(key: string, data: any) {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch {}
}

function loadFromStorageRaw<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  analyses: [],
  currentAnalysis: null,
  isAnalyzing: false,
  analysisProgress: 0,
  analysisStep: "",
  reports: [],

  loadFromStorage: () => {
    const analyses = loadFromStorageRaw<AnalysisResult[]>("veille_analyses", []);
    const reports = loadFromStorageRaw<GeneratedReport[]>("veille_reports", []);
    const currentAnalysis = analyses.length > 0 ? analyses[0] : null;
    set({ analyses, reports, currentAnalysis });
  },

  startAnalysis: async () => {
    set({ isAnalyzing: true, analysisProgress: 0, analysisStep: "Initialisation de l'analyse..." });

    const analysisId = `analysis-${Date.now()}`;
    const startedAt = new Date().toISOString();

    const steps = [
      { progress: 10, step: "Collecte des articles de presse..." },
      { progress: 25, step: "Analyse des sources francophones..." },
      { progress: 40, step: "Analyse des sources arabophones..." },
      { progress: 55, step: "Analyse de sentiment NLP..." },
      { progress: 65, step: "Détection des alertes et menaces..." },
      { progress: 75, step: "Analyse de l'activité des partis..." },
      { progress: 85, step: "Cartographie des risques régionaux..." },
      { progress: 95, step: "Génération des indicateurs KPI..." },
    ];

    let rawArticles: { id: string; title: string; excerpt: string; source: string; sourceUrl: string; category: string; date: string }[] = [];
    try {
      const res = await fetch("/api/articles");
      const data = await res.json();
      rawArticles = (data.articles || []).map((a: any) => ({ ...a, sourceUrl: a.sourceUrl }));
    } catch {
      rawArticles = [];
    }

    for (const s of steps) {
      await new Promise((r) => setTimeout(r, 500 + Math.random() * 400));
      set({ analysisProgress: s.progress, analysisStep: s.step });
    }

    const articles: ArticleData[] = rawArticles.map((a, i) => {
      const text = `${a.title} ${a.excerpt}`;
      return {
        id: `art-${i}-${a.source}`,
        title: a.title,
        source: a.source,
        url: a.sourceUrl,
        date: a.date,
        sentiment: detectSentiment(text),
        parties: detectParties(text),
        category: a.category,
        excerpt: a.excerpt,
      };
    });

    const alerts: AlertData[] = articles
      .map((a) => detectAlertFromArticle(a))
      .filter((a): a is AlertData => a !== null);

    const partyScores = computePartyScores(articles);
    const sentimentByParty = computeSentimentByParty(articles, partyScores);
    const mentionsByDay = computeMentionsByDay(articles);
    const regionCounts: Record<string, number> = {};
    for (const a of alerts) regionCounts[a.region] = (regionCounts[a.region] || 0) + 1;
    const topRegion = Object.entries(regionCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "National";
    const regionRisks = computeRegionRisks(alerts);

    const result: AnalysisResult = {
      id: analysisId,
      startedAt,
      completedAt: new Date().toISOString(),
      period: "Flux RSS en direct",
      status: "completed",
      sources: {
        press: articles.length,
        social: 0,
        total: articles.length,
      },
      kpis: {
        totalMentions: articles.length,
        totalAlerts: alerts.length,
        criticalAlerts: alerts.filter((a) => a.severity === "critical").length,
        sentimentScore: articles.length
          ? +((articles.filter((a) => a.sentiment === "positive").length - articles.filter((a) => a.sentiment === "negative").length) / articles.length).toFixed(2)
          : 0,
        topParty: partyScores[0]?.name || "—",
        topRegion,
      },
      articles,
      alerts,
      partyScores,
      sentimentByParty,
      mentionsByDay,
      regionRisks,
    };

    const analyses = [result, ...get().analyses].slice(0, 20);
    saveToStorage("veille_analyses", analyses);

    set({
      isAnalyzing: false,
      analysisProgress: 100,
      analysisStep: "Analyse terminée",
      analyses,
      currentAnalysis: result,
    });
  },

  addReport: (report) => {
    const reports = [report, ...get().reports];
    saveToStorage("veille_reports", reports);
    set({ reports });
  },

  updateReport: (id, updates) => {
    const reports = get().reports.map((r) => (r.id === id ? { ...r, ...updates } : r));
    saveToStorage("veille_reports", reports);
    set({ reports });
  },

  deleteReport: (id) => {
    const reports = get().reports.filter((r) => r.id !== id);
    saveToStorage("veille_reports", reports);
    set({ reports });
  },

  deleteAnalysis: (id) => {
    const analyses = get().analyses.filter((a) => a.id !== id);
    saveToStorage("veille_analyses", analyses);
    const currentAnalysis = analyses.length > 0 ? analyses[0] : null;
    set({ analyses, currentAnalysis });
  },
}));


const PARTY_META: Record<string, { fullName: string; color: string }> = {
  RNI: { fullName: "Rassemblement National des Indépendants", color: "#8B5CF6" },
  PAM: { fullName: "Parti Authenticité et Modernité", color: "#3B82F6" },
  Istiqlal: { fullName: "Parti de l'Istiqlal", color: "#22C55E" },
  PJD: { fullName: "Parti de la Justice et du Développement", color: "#EF4444" },
  USFP: { fullName: "Union Socialiste des Forces Populaires", color: "#EC4899" },
  MP: { fullName: "Mouvement Populaire", color: "#14B8A6" },
  PPS: { fullName: "Parti du Progrès et du Socialisme", color: "#F59E0B" },
  UC: { fullName: "Union Constitutionnelle", color: "#F97316" },
  FGD: { fullName: "Fédération de la Gauche Démocratique", color: "#E11D48" },
};

function computePartyScores(articles: ArticleData[]): PartyScore[] {
  const counts: Record<string, { mentions: number; positive: number; negative: number }> = {};
  for (const a of articles) {
    for (const p of a.parties) {
      if (!counts[p]) counts[p] = { mentions: 0, positive: 0, negative: 0 };
      counts[p].mentions += 1;
      if (a.sentiment === "positive") counts[p].positive += 1;
      if (a.sentiment === "negative") counts[p].negative += 1;
    }
  }
  return Object.entries(counts)
    .map(([name, c]) => ({
      id: name.toLowerCase(),
      name,
      fullName: PARTY_META[name]?.fullName || name,
      color: PARTY_META[name]?.color || "#64748B",
      score: c.mentions,
      mentions: c.mentions,
      sentiment: c.mentions ? +((c.positive - c.negative) / c.mentions).toFixed(2) : 0,
      trend: c.positive >= c.negative ? ("up" as const) : ("down" as const),
      trendValue: c.mentions,
    }))
    .sort((a, b) => b.mentions - a.mentions);
}

function computeSentimentByParty(articles: ArticleData[], scores: PartyScore[]): SentimentData[] {
  return scores.map((s) => {
    const partyArticles = articles.filter((a) => a.parties.includes(s.name));
    return {
      party: s.name,
      positive: partyArticles.filter((a) => a.sentiment === "positive").length,
      neutral: partyArticles.filter((a) => a.sentiment === "neutral").length,
      negative: partyArticles.filter((a) => a.sentiment === "negative").length,
      color: s.color,
    };
  });
}

function computeRegionRisks(alerts: AlertData[]): RegionRisk[] {
  const byRegion: Record<string, AlertData[]> = {};
  for (const a of alerts) {
    if (!byRegion[a.region]) byRegion[a.region] = [];
    byRegion[a.region].push(a);
  }
  return Object.entries(byRegion).map(([name, regionAlerts]) => {
    const criticalCount = regionAlerts.filter((a) => a.severity === "critical").length;
    const categoryCounts: Record<string, number> = {};
    for (const a of regionAlerts) categoryCounts[a.category] = (categoryCounts[a.category] || 0) + 1;
    const topCategory = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "—";
    const riskLevel: "high" | "medium" | "low" = criticalCount > 0 ? "high" : regionAlerts.length >= 2 ? "medium" : "low";
    const coords = REGION_COORDS[name] || REGION_COORDS["National"];
    return {
      id: coords.id,
      name,
      lat: coords.lat,
      lng: coords.lng,
      alertCount: regionAlerts.length,
      criticalCount,
      riskLevel,
      topCategory,
    };
  }).sort((a, b) => b.alertCount - a.alertCount);
}

function computeMentionsByDay(articles: ArticleData[]): DailyMentions[] {
  const days: DailyMentions[] = [];
  for (let i = 13; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split("T")[0];
    const press = articles.filter((a) => a.date.startsWith(dateStr)).length;
    days.push({ date: dateStr, press, social: 0, total: press });
  }
  return days;
}
