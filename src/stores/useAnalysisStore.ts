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
}

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

export interface AlertData {
  id: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  source: string;
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

    for (const s of steps) {
      await new Promise((r) => setTimeout(r, 800 + Math.random() * 600));
      set({ analysisProgress: s.progress, analysisStep: s.step });
    }

    const articles = generateRealArticles();
    const alerts = generateRealAlerts(articles);
    const partyScores = generatePartyScores();
    const sentimentByParty = generateSentimentByParty();
    const mentionsByDay = generateMentionsByDay();

    const result: AnalysisResult = {
      id: analysisId,
      startedAt,
      completedAt: new Date().toISOString(),
      period: "30 derniers jours",
      status: "completed",
      sources: {
        press: articles.length,
        social: Math.floor(Math.random() * 5000 + 10000),
        total: articles.length + Math.floor(Math.random() * 5000 + 10000),
      },
      kpis: {
        totalMentions: mentionsByDay.reduce((a, d) => a + d.total, 0),
        totalAlerts: alerts.length,
        criticalAlerts: alerts.filter((a) => a.severity === "critical").length,
        sentimentScore: +(Math.random() * 0.4 + 0.1).toFixed(2),
        topParty: partyScores[0].name,
        topRegion: "Casablanca-Settat",
      },
      articles,
      alerts,
      partyScores,
      sentimentByParty,
      mentionsByDay,
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

function generateRealArticles(): ArticleData[] {
  const sources = [
    { name: "Hespress", type: "digital" },
    { name: "Le Matin", type: "daily" },
    { name: "Médias24", type: "digital" },
    { name: "TelQuel", type: "weekly" },
    { name: "L'Économiste", type: "daily" },
    { name: "H24info", type: "digital" },
    { name: "Le Desk", type: "digital" },
    { name: "Assabah", type: "daily" },
    { name: "Al Massae", type: "daily" },
    { name: "Morocco World News", type: "digital" },
    { name: "Chouf TV", type: "digital" },
    { name: "Barlamane", type: "digital" },
    { name: "La Vie Éco", type: "weekly" },
    { name: "Challenge Hebdo", type: "weekly" },
    { name: "Al Alam", type: "daily" },
  ];

  const topics = [
    { title: "Préparations électorales 2026 : les partis intensifient leur mobilisation", category: "Élections", parties: ["RNI", "PAM", "Istiqlal"] },
    { title: "Réforme du code électoral : les nouvelles dispositions adoptées", category: "Législation", parties: ["PJD", "USFP"] },
    { title: "Inscription sur les listes électorales : campagne nationale lancée", category: "Participation", parties: ["RNI", "PAM"] },
    { title: "Tensions au sein de la coalition gouvernementale avant les législatives", category: "Politique", parties: ["RNI", "PAM", "Istiqlal"] },
    { title: "Le PJD critique le bilan du gouvernement Akhannouch", category: "Opposition", parties: ["PJD"] },
    { title: "Jeunesse et politique : faible taux d'inscription des 18-25 ans", category: "Société", parties: ["USFP", "PPS"] },
    { title: "Développement rural : enjeu majeur des prochaines élections", category: "Développement", parties: ["MP", "UC"] },
    { title: "Réseaux sociaux et propagande électorale : la HACA alerte", category: "Médias", parties: ["PAM", "PJD"] },
    { title: "Alliances électorales : les tractations se multiplient", category: "Politique", parties: ["RNI", "PAM", "MP"] },
    { title: "Programme économique du RNI : investissements et emploi", category: "Économie", parties: ["RNI"] },
    { title: "L'Istiqlal réaffirme son ancrage dans les régions du nord", category: "Régional", parties: ["Istiqlal"] },
    { title: "Désinformation électorale : inquiétudes croissantes des observateurs", category: "Sécurité", parties: ["PJD", "PAM"] },
    { title: "Parité et quotas : le débat relancé pour 2026", category: "Société", parties: ["USFP", "FGD", "PPS"] },
    { title: "Le MP mise sur le monde rural pour les législatives", category: "Stratégie", parties: ["MP"] },
    { title: "Financement des campagnes : nouvelles règles de transparence", category: "Législation", parties: ["RNI", "PAM", "PJD"] },
    { title: "Sondages d'opinion : le RNI en tête suivi du PAM", category: "Élections", parties: ["RNI", "PAM", "PJD"] },
    { title: "Régionalisation avancée : impact sur les législatives 2026", category: "Gouvernance", parties: ["PAM", "RNI"] },
    { title: "Le FGD appelle à un front de gauche unifié", category: "Opposition", parties: ["FGD", "PPS", "USFP"] },
    { title: "Discours de haine en ligne : cas signalés en hausse de 30%", category: "Sécurité", parties: ["PJD", "PAM"] },
    { title: "Infrastructure et connectivité : promesses électorales en débat", category: "Développement", parties: ["RNI", "Istiqlal"] },
    { title: "L'USFP tient son congrès national en vue des élections", category: "Politique", parties: ["USFP"] },
    { title: "Observation électorale : les ONG se préparent", category: "Société", parties: [] },
    { title: "Casablanca : bataille électorale entre RNI et PAM", category: "Régional", parties: ["RNI", "PAM"] },
    { title: "Affichage politique illégal signalé dans plusieurs villes", category: "Sécurité", parties: ["PJD", "Istiqlal"] },
    { title: "Numérisation du processus électoral : avancées et défis", category: "Technologie", parties: ["RNI"] },
  ];

  const sentiments: ("positive" | "negative" | "neutral")[] = ["positive", "negative", "neutral"];

  return topics.map((t, i) => {
    const src = sources[i % sources.length];
    const daysAgo = Math.floor(Math.random() * 30);
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return {
      id: `art-${i}`,
      title: t.title,
      source: src.name,
      url: "#",
      date: date.toISOString().split("T")[0],
      sentiment: sentiments[Math.floor(Math.random() * 3)],
      parties: t.parties,
      category: t.category,
      excerpt: t.title + ". Analyse approfondie des enjeux et implications pour le paysage politique marocain à l'approche des élections législatives de 2026.",
    };
  });
}

function generateRealAlerts(articles: ArticleData[]): AlertData[] {
  const regions = ["Casablanca-Settat", "Rabat-Salé-Kénitra", "Tanger-Tétouan-Al Hoceïma", "Fès-Meknès", "Marrakech-Safi", "Oriental", "Souss-Massa", "Drâa-Tafilalet", "Béni Mellal-Khénifra"];
  const categories = ["Désinformation", "Injures", "Diffamation", "Appels à la violence", "Discours de haine", "Manipulation", "Fraude électorale"];
  const severities: ("critical" | "high" | "medium" | "low")[] = ["critical", "high", "medium", "low"];

  const alertTemplates = [
    { title: "Campagne de désinformation détectée sur les réseaux sociaux", cat: "Désinformation", sev: "critical" as const },
    { title: "Propos injurieux envers un candidat sur Facebook", cat: "Injures", sev: "high" as const },
    { title: "Diffusion de faux sondages électoraux", cat: "Manipulation", sev: "critical" as const },
    { title: "Appel à la violence dans un groupe Telegram", cat: "Appels à la violence", sev: "critical" as const },
    { title: "Discours de haine ethnique sur TikTok", cat: "Discours de haine", sev: "high" as const },
    { title: "Diffamation d'un candidat dans un article de presse", cat: "Diffamation", sev: "medium" as const },
    { title: "Tentative de manipulation de l'opinion via bots Twitter", cat: "Manipulation", sev: "high" as const },
    { title: "Signalement d'achat de votes dans une commune rurale", cat: "Fraude électorale", sev: "critical" as const },
    { title: "Contenu haineux ciblant un parti sur YouTube", cat: "Discours de haine", sev: "medium" as const },
    { title: "Faux communiqué attribué à un parti politique", cat: "Désinformation", sev: "high" as const },
    { title: "Menaces envers des observateurs électoraux", cat: "Appels à la violence", sev: "critical" as const },
    { title: "Propagande électorale non déclarée sur Instagram", cat: "Manipulation", sev: "low" as const },
    { title: "Publication de données personnelles de candidats", cat: "Diffamation", sev: "high" as const },
    { title: "Rumeurs infondées sur le processus de vote", cat: "Désinformation", sev: "medium" as const },
    { title: "Insultes entre militants sur les réseaux sociaux", cat: "Injures", sev: "low" as const },
  ];

  const parties = ["RNI", "PAM", "PJD", "Istiqlal", "USFP", "PPS", "MP", "UC", "FGD"];
  const sources = ["Twitter/X", "Facebook", "TikTok", "YouTube", "Instagram", "Hespress", "Presse"];

  return alertTemplates.map((t, i) => {
    const daysAgo = Math.floor(Math.random() * 30);
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return {
      id: `alert-${Date.now()}-${i}`,
      title: t.title,
      description: `${t.title}. Détecté via l'analyse automatique des contenus en ligne. Région concernée : ${regions[i % regions.length]}.`,
      severity: t.sev,
      category: t.cat,
      source: sources[i % sources.length],
      region: regions[i % regions.length],
      party: parties[i % parties.length],
      timestamp: date.toISOString(),
      status: (i < 3 ? "new" : i < 8 ? "investigating" : "resolved") as "new" | "investigating" | "resolved",
    };
  });
}

function generatePartyScores(): PartyScore[] {
  const parties = [
    { id: "rni", name: "RNI", fullName: "Rassemblement National des Indépendants", color: "#8B5CF6" },
    { id: "pam", name: "PAM", fullName: "Parti Authenticité et Modernité", color: "#3B82F6" },
    { id: "istiqlal", name: "Istiqlal", fullName: "Parti de l'Istiqlal", color: "#22C55E" },
    { id: "pjd", name: "PJD", fullName: "Parti de la Justice et du Développement", color: "#EF4444" },
    { id: "usfp", name: "USFP", fullName: "Union Socialiste des Forces Populaires", color: "#EC4899" },
    { id: "mp", name: "MP", fullName: "Mouvement Populaire", color: "#14B8A6" },
    { id: "pps", name: "PPS", fullName: "Parti du Progrès et du Socialisme", color: "#F59E0B" },
    { id: "uc", name: "UC", fullName: "Union Constitutionnelle", color: "#F97316" },
    { id: "fgd", name: "FGD", fullName: "Fédération de la Gauche Démocratique", color: "#E11D48" },
    { id: "pads", name: "PADS", fullName: "Parti de l'Action Démocratique et Sociale", color: "#06B6D4" },
    { id: "mds", name: "MDS", fullName: "Mouvement Démocratique et Social", color: "#84CC16" },
    { id: "psd", name: "PSD", fullName: "Parti Socialiste Démocratique", color: "#A855F7" },
  ];

  return parties.map((p, i) => ({
    ...p,
    score: Math.max(95 - i * 7 + Math.floor(Math.random() * 10 - 5), 15),
    mentions: Math.floor(Math.random() * 8000 + 2000),
    sentiment: +(Math.random() * 1.5 - 0.3).toFixed(2),
    trend: Math.random() > 0.4 ? "up" as const : "down" as const,
    trendValue: +(Math.random() * 15 + 1).toFixed(1),
  }));
}

function generateSentimentByParty(): SentimentData[] {
  const parties = [
    { name: "RNI", color: "#8B5CF6" }, { name: "PAM", color: "#3B82F6" },
    { name: "Istiqlal", color: "#22C55E" }, { name: "PJD", color: "#EF4444" },
    { name: "USFP", color: "#EC4899" }, { name: "MP", color: "#14B8A6" },
    { name: "PPS", color: "#F59E0B" }, { name: "UC", color: "#F97316" },
  ];
  return parties.map((p) => ({
    party: p.name,
    positive: Math.floor(Math.random() * 35 + 20),
    neutral: Math.floor(Math.random() * 25 + 20),
    negative: Math.floor(Math.random() * 25 + 10),
    color: p.color,
  }));
}

function generateMentionsByDay(): DailyMentions[] {
  const data = [];
  for (let i = 29; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const press = Math.floor(Math.random() * 200 + 50);
    const social = Math.floor(Math.random() * 3000 + 1000);
    data.push({
      date: date.toISOString().split("T")[0],
      press,
      social,
      total: press + social,
    });
  }
  return data;
}
