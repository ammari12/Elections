import Parser from "rss-parser";
import { RSS_SOURCES } from "./rssSources";

export interface RealArticle {
  id: string;
  title: string;
  excerpt: string;
  source: string;
  sourceUrl: string;
  category: string;
  date: string;
}

const parser = new Parser({ timeout: 8000 });

export async function fetchRealArticles(): Promise<RealArticle[]> {
  const results = await Promise.allSettled(
    RSS_SOURCES.map(async (src) => {
      const feed = await parser.parseURL(src.url);
      return (feed.items || []).slice(0, 8).map((item, i) => ({
        id: `${src.name}-${i}-${item.guid || item.link || item.title}`,
        title: item.title || "",
        excerpt: (item.contentSnippet || item.content || "").slice(0, 240),
        source: src.name,
        sourceUrl: item.link || src.url,
        category: src.category,
        date: item.isoDate || item.pubDate || new Date().toISOString(),
      }));
    })
  );

  const articles: RealArticle[] = [];
  for (const r of results) {
    if (r.status === "fulfilled") articles.push(...r.value);
  }
  return articles.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}
