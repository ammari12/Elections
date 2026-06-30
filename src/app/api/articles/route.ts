import { NextResponse } from "next/server";
import { fetchRealArticles } from "@/lib/fetchArticles";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const articles = await fetchRealArticles();
    return NextResponse.json({ articles, fetchedAt: new Date().toISOString() });
  } catch (err) {
    return NextResponse.json({ error: "fetch_failed", message: String(err) }, { status: 500 });
  }
}
