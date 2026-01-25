import { NextRequest, NextResponse } from "next/server";
import { searchVerses } from "@/lib/search";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("q");
  const limit = parseInt(searchParams.get("limit") || "10", 10);
  const offset = parseInt(searchParams.get("offset") || "0", 10);

  if (!query || query.trim().length < 3) {
    return NextResponse.json(
      { error: "Query must be at least 3 characters" },
      { status: 400 }
    );
  }

  // Clamp limit to reasonable bounds
  const safeLimit = Math.min(Math.max(1, limit), 50);
  const safeOffset = Math.max(0, offset);

  const { results, total, hasMore } = searchVerses(query, {
    limit: safeLimit,
    offset: safeOffset,
  });

  return NextResponse.json({ results, total, hasMore, query });
}
