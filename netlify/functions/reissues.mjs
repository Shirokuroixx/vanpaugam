// Serves the City Pop Wiki reissue feed from this site's own origin.
// Fetching server-side follows the wiki's redirects and avoids CORS.
export default async () => {
  const sources = ["https://www.citypopwiki.org/api/reissues", "https://citypopwiki.org/api/reissues"];
  for (const url of sources) {
    try {
      const r = await fetch(url, { redirect: "follow", headers: { "User-Agent": "vanpaugam.com feed", Accept: "application/json" } });
      if (!r.ok) continue;
      const data = await r.json();
      if (!data || !Array.isArray(data.items) || !data.items.length) continue;
      return new Response(JSON.stringify(data), {
        headers: { "Content-Type": "application/json", "Cache-Control": "public, max-age=300, s-maxage=3600" },
      });
    } catch (e) { /* try next */ }
  }
  return new Response(JSON.stringify({ items: [] }), { status: 502, headers: { "Content-Type": "application/json" } });
};
export const config = { path: "/api/reissues" };
