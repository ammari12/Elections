import type { AnalysisResult } from "@/stores/useAnalysisStore";

export function buildReportHtml(analysis: AnalysisResult, sectionIds: string[]): string {
  const date = new Date(analysis.completedAt).toLocaleString("fr-FR");

  const sectionHtml: Record<string, string> = {
    intro: `
      <h2>Introduction et Synthèse Générale</h2>
      <p>Analyse réalisée le ${date}, basée sur ${analysis.sources.press} articles de presse réels collectés via flux RSS.</p>
      <ul>
        <li>Mentions totales : ${analysis.kpis.totalMentions}</li>
        <li>Alertes détectées : ${analysis.kpis.totalAlerts} (dont ${analysis.kpis.criticalAlerts} critiques)</li>
        <li>Score de sentiment global : ${analysis.kpis.sentimentScore}</li>
        <li>Parti le plus mentionné : ${analysis.kpis.topParty}</li>
        <li>Région la plus concernée par des alertes : ${analysis.kpis.topRegion}</li>
      </ul>`,
    security: `
      <h2>Analyse Globale de la Sécurité Électorale</h2>
      ${analysis.alerts.length === 0 ? "<p>Aucune alerte détectée.</p>" : `
      <table>
        <tr><th>Catégorie</th><th>Gravité</th><th>Source</th><th>Titre</th></tr>
        ${analysis.alerts.map((a) => `<tr><td>${esc(a.category)}</td><td>${esc(a.severity)}</td><td>${esc(a.source)}</td><td>${esc(a.title)}</td></tr>`).join("")}
      </table>`}`,
    parties: `
      <h2>Activité des Partis Politiques</h2>
      ${analysis.partyScores.length === 0 ? "<p>Aucune mention de parti détectée.</p>" : `
      <table>
        <tr><th>Parti</th><th>Mentions</th><th>Sentiment</th></tr>
        ${analysis.partyScores.map((p) => `<tr><td>${esc(p.fullName)} (${esc(p.name)})</td><td>${p.mentions}</td><td>${p.sentiment}</td></tr>`).join("")}
      </table>`}`,
    press: `
      <h2>Analyse Presse Écrite et Électronique</h2>
      <table>
        <tr><th>Titre</th><th>Source</th><th>Date</th><th>Sentiment</th><th>Lien</th></tr>
        ${analysis.articles.map((a) => `<tr><td>${esc(a.title)}</td><td>${esc(a.source)}</td><td>${esc(a.date)}</td><td>${esc(a.sentiment)}</td><td>${a.url && a.url !== "#" ? `<a href="${esc(a.url)}">source</a>` : "—"}</td></tr>`).join("")}
      </table>`,
    synthesis: `
      <h2>Synthèse Globale et Recommandations</h2>
      <p>Sur la période analysée, ${analysis.kpis.totalAlerts} alertes ont été détectées dont ${analysis.kpis.criticalAlerts} de gravité critique.
      La région ${analysis.kpis.topRegion} concentre le plus d'alertes. Le parti ${analysis.kpis.topParty} est le plus mentionné dans la presse.</p>`,
    annexes: `
      <h2>Annexes</h2>
      <p>Sources de presse consultées lors de cette analyse :</p>
      <ul>${Array.from(new Set(analysis.articles.map((a) => a.source))).map((s) => `<li>${esc(s)}</li>`).join("")}</ul>`,
  };

  const body = sectionIds.map((id) => sectionHtml[id] || "").join("\n");

  return `<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<title>Rapport de Veille Électorale — ${date}</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
  h1 { border-bottom: 3px solid #2563eb; padding-bottom: 12px; }
  h2 { color: #2563eb; margin-top: 32px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
  th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: left; }
  th { background: #f1f5f9; }
  .meta { color: #666; font-size: 13px; }
</style>
</head>
<body>
  <h1>Rapport de Veille Électorale — Maroc 2026</h1>
  <p class="meta">Généré le ${new Date().toLocaleString("fr-FR")} — basé sur l'analyse du ${date}</p>
  ${body}
</body>
</html>`;
}

function esc(s: string): string {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c] as string));
}
