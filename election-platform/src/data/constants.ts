export const PARTIES = [
  { id: "pam", name: "PAM", fullName: "Parti Authenticité et Modernité", color: "#3B82F6" },
  { id: "pjd", name: "PJD", fullName: "Parti de la Justice et du Développement", color: "#EF4444" },
  { id: "istiqlal", name: "Istiqlal", fullName: "Parti de l'Istiqlal", color: "#22C55E" },
  { id: "pps", name: "PPS", fullName: "Parti du Progrès et du Socialisme", color: "#F59E0B" },
  { id: "usfp", name: "USFP", fullName: "Union Socialiste des Forces Populaires", color: "#EC4899" },
  { id: "rni", name: "RNI", fullName: "Rassemblement National des Indépendants", color: "#8B5CF6" },
  { id: "mp", name: "MP", fullName: "Mouvement Populaire", color: "#14B8A6" },
  { id: "uc", name: "UC", fullName: "Union Constitutionnelle", color: "#F97316" },
  { id: "pads", name: "PADS", fullName: "Parti de l'Action Démocratique et Sociale", color: "#06B6D4" },
  { id: "mds", name: "MDS", fullName: "Mouvement Démocratique et Social", color: "#84CC16" },
  { id: "psd", name: "PSD", fullName: "Parti Socialiste Démocratique", color: "#A855F7" },
  { id: "fgd", name: "FGD", fullName: "Fédération de la Gauche Démocratique", color: "#E11D48" },
] as const;

export const REGIONS = [
  { id: "tanger", name: "Tanger-Tétouan-Al Hoceïma", lat: 35.7595, lng: -5.834 },
  { id: "oriental", name: "Oriental", lat: 34.6814, lng: -1.9086 },
  { id: "fes", name: "Fès-Meknès", lat: 34.0181, lng: -5.0078 },
  { id: "rabat", name: "Rabat-Salé-Kénitra", lat: 34.0209, lng: -6.8416 },
  { id: "beni", name: "Béni Mellal-Khénifra", lat: 32.3373, lng: -6.3498 },
  { id: "casablanca", name: "Casablanca-Settat", lat: 33.5731, lng: -7.5898 },
  { id: "marrakech", name: "Marrakech-Safi", lat: 31.6295, lng: -7.9811 },
  { id: "draa", name: "Drâa-Tafilalet", lat: 31.9314, lng: -5.3625 },
  { id: "souss", name: "Souss-Massa", lat: 30.4278, lng: -9.5981 },
  { id: "guelmim", name: "Guelmim-Oued Noun", lat: 28.9833, lng: -10.0578 },
  { id: "laayoune", name: "Laâyoune-Sakia El Hamra", lat: 27.1253, lng: -13.1625 },
  { id: "dakhla", name: "Dakhla-Oued Ed-Dahab", lat: 23.6848, lng: -15.957 },
] as const;

export const PRESS_SOURCES = {
  dailyFr: ["Le Matin", "L'Opinion", "Libération", "Aujourd'hui le Maroc", "L'Économiste", "Les Inspirations ÉCO", "Al Bayane", "Le Soir Échos", "Aufait"],
  dailyAr: ["Al Massae", "Assabah", "Al Ittihad al Ichtiraki", "Bayane Al Yaoume", "Al Alam", "Al Moharrir", "Akhbar Al Youm"],
  weekly: ["TelQuel", "La Vie Éco", "Challenge Hebdo", "Maroc Hebdo International", "L'Observateur du Maroc", "La Nouvelle Tribune", "Le Canard Libéré", "Le Journal Hebdomadaire", "Le Temps", "Zamane", "Femmes du Maroc", "Alousboue Assahafi", "Nichane", "Al Massae Arriadi", "Anoual"],
  digital: ["Hespress", "Morocco World News", "Le Desk", "Article19.ma", "Médias24", "Demainonline.com", "Goud.ma", "Labass.net", "Lakome.com", "Lareleve.ma", "Telexpresse.com", "H24info", "Chouf TV", "Barlamane"],
} as const;

export const SOCIAL_NETWORKS = ["Twitter/X", "Facebook", "Instagram", "TikTok", "YouTube"] as const;

export const ALERT_CATEGORIES = [
  "Injures",
  "Diffamation",
  "Désinformation",
  "Appels à la violence",
  "Discours de haine",
  "Manipulation",
  "Fraude électorale",
] as const;
