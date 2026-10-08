import { meta as waiverReview } from "./content/stablecoinx-lock-up-waiver-2026-10-05.mjs";
import { meta as payAdoptionReview } from "./content/ethenapay-adoption-2026-10-05.mjs";
import { meta as septemberReview } from "./content/usde-september-2026.mjs";
export const ORIGIN = "https://ethenadash.com";
export const AUTHOR = {
  "@type": "Person",
  "@id": ORIGIN + "/about/#author",
  name: "Qorban Ferrell",
  alternateName: "@Degenerate_DeFi",
  url: ORIGIN + "/about/",
  sameAs: ["https://x.com/Degenerate_DeFi"],
};
export const PAGES = {
  [waiverReview.path]: waiverReview,
  [payAdoptionReview.path]: payAdoptionReview,
  [septemberReview.path]: septemberReview,
  "/stablecoinx/": {
    title: "StablecoinX NAV Tracker: ENA Holdings & mNAV | EthenaDash",
    description:
      "Track StablecoinX (USDE) against its reported ENA treasury. Explore token NAV per share, mNAV, market history, USDEW warrants and SEC filings.",
    name: "StablecoinX NAV tracker",
    page: "sx",
  },
  "/ethenapay/": {
    title: "EthenaPay Analytics: USDe Card Spend & Wallets | EthenaDash",
    description:
      "Explore EthenaPay on Avalanche: USDe card spending, successful spend events, funded wallets, deposits, cashback and balance yield.",
    name: "EthenaPay analytics",
    page: "pay",
  },
  "/research/": {
    title: "Ethena & StablecoinX Research and Analysis | EthenaDash",
    description:
      "Original StablecoinX market reviews and sourced guides to ENA treasury valuation, USDEW warrants and EthenaPay on-chain spending.",
    name: "Research",
  },
  "/research/stablecoinx-mnav/": {
    title: "StablecoinX mNAV Explained: ENA Treasury vs Share Price",
    description:
      "How to calculate StablecoinX token NAV, ENA per share and mNAV, and why a discount to reported token assets is not a guaranteed return.",
    name: "StablecoinX mNAV explained",
    article: true,
  },
  "/research/usdew-warrants/": {
    title: "USDEW Warrants Explained: Payoff, Dilution & Redemption",
    description:
      "Understand StablecoinX USDEW warrants: exercise-price mechanics, expiry payoff, dilution and why redemption terms matter before expiration.",
    name: "USDEW warrants explained",
    article: true,
  },
  "/research/ethenapay-spend-events/": {
    title: "How EthenaPay Spending Is Measured On-Chain | EthenaDash",
    description:
      "Why EthenaPay card analytics count AllowanceSpent log events rather than transaction hashes, include both settlement addresses and exclude the issuer hop.",
    name: "Measuring EthenaPay spending",
    article: true,
  },
  "/methodology/": {
    title: "Data Sources & Calculation Methodology | EthenaDash",
    description:
      "Definitions, source timestamps and limitations for StablecoinX token NAV, market quotes, warrants and EthenaPay card activity.",
    name: "Methodology",
  },
  "/about/": {
    title: "About Qorban Ferrell & EthenaDash",
    description:
      "EthenaDash is created and maintained by Qorban Ferrell (@Degenerate_DeFi), covering StablecoinX treasury valuation and EthenaPay on-chain activity.",
    name: "About EthenaDash",
  },
};
export const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export const safeJSON = (v) => JSON.stringify(v).replace(/</g, "\\u003c");
export function canonicalPath(path) {
  if (path === "/" || path === "/index.html") return "/stablecoinx/";
  if (PAGES[path]) return path;
  if (PAGES[path + "/"]) return path + "/";
  return null;
}
export function graph(path, modified) {
  const p = PAGES[path],
    url = ORIGIN + path;
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": ORIGIN + "/#website",
        url: ORIGIN + "/",
        name: "EthenaDash",
        publisher: { "@id": ORIGIN + "/about/#author" },
      },
      AUTHOR,
      {
        "@type": p.article ? "Article" : "WebPage",
        "@id": url + "#page",
        url,
        name: p.name,
        headline: p.headline || p.title,
        description: p.description,
        isPartOf: { "@id": ORIGIN + "/#website" },
        author: { "@id": ORIGIN + "/about/#author" },
        ...(p.article
          ? {
              datePublished: p.datePublished || "2026-10-05",
              dateModified: p.dateModified || "2026-10-05",
              mainEntityOfPage: url,
              ...(p.image ? { image: ORIGIN + p.image } : {}),
            }
          : modified
          ? { dateModified: modified }
          : {}),
        breadcrumb: { "@id": url + "#breadcrumb" },
      },
      {
        "@type": "BreadcrumbList",
        "@id": url + "#breadcrumb",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: "EthenaDash",
            item: ORIGIN + "/stablecoinx/",
          },
          ...(p.article
            ? [
                {
                  "@type": "ListItem",
                  position: 2,
                  name: "Research",
                  item: ORIGIN + "/research/",
                },
              ]
            : []),
          {
            "@type": "ListItem",
            position: p.article ? 3 : 2,
            name: p.name,
            item: url,
          },
        ],
      },
    ],
  };
}
export function extraHead(path, modified) {
  const page = PAGES[path];
  const image = page.image
    ? `<meta property="og:image" content="${
        ORIGIN + esc(page.image)
      }"><meta property="og:image:alt" content="${esc(
        page.imageAlt,
      )}"><meta name="twitter:image" content="${
        ORIGIN + esc(page.image)
      }"><meta name="twitter:image:alt" content="${esc(page.imageAlt)}">`
    : "";
  return `<meta name="google-site-verification" content="sOjYC81rnJ1CgZWbrKyOYYKMBcG3Xmq5SJ4AEpVOZk4"><meta name="author" content="Qorban Ferrell"><meta property="og:type" content="${
    page.article ? "article" : "website"
  }"><meta property="og:site_name" content="EthenaDash"><meta name="twitter:card" content="${
    page.image ? "summary_large_image" : "summary"
  }"><meta name="twitter:creator" content="@Degenerate_DeFi">${image}<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg"><script type="application/ld+json">${safeJSON(
    graph(path, modified),
  )}</script>`;
}
export function nav(path) {
  return `<header class="sx-nav"><a class="sx-brand" href="/stablecoinx/" aria-label="EthenaDash home">ethena<span>dash</span></a><nav class="sx-nav-items" aria-label="Dashboard"><a class="full-nav-button" href="/stablecoinx/" ${
    path === "/stablecoinx/" ? 'aria-current="page"' : ""
  }>StablecoinX</a><a class="full-nav-button" href="/ethenapay/" ${
    path === "/ethenapay/" ? 'aria-current="page"' : ""
  }>EthenaPay</a><a class="full-nav-button" href="/research/" ${
    path.startsWith("/research/") ? 'aria-current="page"' : ""
  }>Research</a></nav></header>`;
}
export function footer() {
  return `<footer class="full-footer"><span>ethenadash</span><nav class="full-footer-links" aria-label="Site information"><a href="/research/">Research</a><a href="/methodology/">Methodology</a><a href="/about/">About</a><a href="https://x.com/Degenerate_DeFi" target="_blank" rel="noopener noreferrer">By @Degenerate_DeFi ↗</a></nav></footer>`;
}
export function documentPage(path, content, status = 200) {
  const p = PAGES[path];
  return new Response(
    `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0d1116"><title>${esc(
      p.title,
    )}</title><meta name="description" content="${esc(
      p.description,
    )}"><link rel="canonical" href="${
      ORIGIN + path
    }"><meta property="og:title" content="${esc(
      p.title,
    )}"><meta property="og:description" content="${esc(
      p.description,
    )}"><meta property="og:url" content="${
      ORIGIN + path
    }"><link rel="stylesheet" href="/assets/dashboard.css">${extraHead(
      path,
    )}</head><body><div id="sx-studio"><div class="sx-shell">${nav(
      path,
    )}<main class="editorial"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/stablecoinx/">EthenaDash</a><span>/</span>${
      p.article ? '<a href="/research/">Research</a><span>/</span>' : ""
    }<span aria-current="page">${esc(
      p.name,
    )}</span></nav>${content}</main>${footer()}</div></div></body></html>`,
    {
      status,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, max-age=60",
        "X-Content-Type-Options": "nosniff",
      },
    },
  );
}
export function sitemap() {
  return (
    '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
    Object.keys(PAGES)
      .map((p) => "<url><loc>" + ORIGIN + p + "</loc></url>")
      .join("") +
    "</urlset>"
  );
}
