export interface RssSource {
  name: string;
  url: string;
  category: string;
}

// Real, public RSS feeds from Moroccan press outlets.
export const RSS_SOURCES: RssSource[] = [
  { name: "Hespress", url: "https://www.hespress.com/feed", category: "Actualités" },
  { name: "Hespress FR", url: "https://fr.hespress.com/feed", category: "Actualités" },
  { name: "Le360", url: "https://www.le360.ma/rss", category: "Actualités" },
  { name: "Médias24", url: "https://medias24.com/feed/", category: "Économie" },
  { name: "H24info", url: "https://www.h24info.ma/feed/", category: "Actualités" },
  { name: "Yabiladi", url: "https://www.yabiladi.com/rss.xml", category: "Actualités" },
  { name: "Morocco World News", url: "https://www.moroccoworldnews.com/feed/", category: "International" },
  { name: "L'Économiste", url: "https://www.leconomiste.com/rss.xml", category: "Économie" },
  { name: "Telquel", url: "https://telquel.ma/feed", category: "Actualités" },
];
