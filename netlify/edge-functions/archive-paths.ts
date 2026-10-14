// Category and tag archives were retired with Squarespace; _redirects sends
// them to their section, but its matching is case-sensitive. This catches
// mixed-case variants (/Blog/Category/City+Pop/) so they 301 instead of 404.
const SECTIONS = ["blog", "latest-news", "news1", "podcast", "vinyl"];

export default async (req: Request) => {
  const url = new URL(req.url);
  const [section, kind] = url.pathname.toLowerCase().split("/").filter(Boolean);
  if (!SECTIONS.includes(section) || (kind !== "category" && kind !== "tag")) return;
  return new Response(null, { status: 301, headers: { Location: `${url.origin}/${section}` } });
};

export const config = {
  pattern: "^/[A-Za-z0-9-]+/([Cc][Aa][Tt][Ee][Gg][Oo][Rr][Yy]|[Tt][Aa][Gg])(/.*)?$",
};
