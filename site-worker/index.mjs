import Ethena from "../docs/assets/data.js";
import { lighterResponse } from "./lighter.mjs";
import {
  ORIGIN,
  PAGES,
  canonicalPath,
  extraHead,
  nav,
  footer,
  documentPage,
  sitemap,
  safeJSON,
} from "./seo.mjs";
import { content } from "./content.mjs";
import {
  values,
  rows,
  chart,
  num,
  usd,
  pct,
  compact,
  stamp,
} from "./render.mjs";
const RAW = "https://raw.githubusercontent.com/QorbQuant/EthenaDAT/main/docs/";
export async function loadFeed(
  file,
  type,
  env,
  origin,
  ctx,
  fetcher = fetch,
  cache = globalThis.caches?.default,
) {
  const key = new Request(ORIGIN + "/__feed/" + file);
  let cached;
  try {
    cached = await cache?.match(key);
    if (cached) {
      const data = await cached.json();
      if (Ethena.valid(data, type)) return { data, fallback: false };
    }
  } catch {}
  try {
    const response = await fetcher(RAW + file, {
      signal: AbortSignal.timeout(4000),
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw Error("Feed HTTP " + response.status);
    const data = await response.json();
    if (!Ethena.valid(data, type)) throw Error("Invalid feed");
    if (cache)
      ctx.waitUntil(
        cache.put(
          key,
          new Response(JSON.stringify(data), {
            headers: {
              "Cache-Control": "public, max-age=300",
              "Content-Type": "application/json",
            },
          }),
        ),
      );
    return { data, fallback: false };
  } catch {}
  try {
    const response = await env.ASSETS.fetch(new Request(origin + "/" + file));
    const data = await response.json();
    if (Ethena.valid(data, type)) return { data, fallback: true };
  } catch {}
  return { data: null, fallback: true };
}
export function renderDashboard(template, path, feeds) {
  const page = PAGES[path],
    D = feeds.sx.data,
    P = feeds.pay.data ? Ethena.normalizePay(feeds.pay.data) : null,
    { ids, market } = values(D, P),
    active = page.page,
    modified = (active === "sx" ? D : P)?.generated_at;
  let rewriter = new HTMLRewriter()
    .on("title", {
      element(e) {
        e.setInnerContent(page.title);
      },
    })
    .on('meta[name="description"],meta[property="og:description"]', {
      element(e) {
        e.setAttribute("content", page.description);
      },
    })
    .on('meta[property="og:title"]', {
      element(e) {
        e.setAttribute("content", page.title);
      },
    })
    .on('meta[property="og:url"]', {
      element(e) {
        e.setAttribute("content", ORIGIN + path);
      },
    })
    .on('link[rel="canonical"]', {
      element(e) {
        e.setAttribute("href", ORIGIN + path);
      },
    })
    .on("head", {
      element(e) {
        e.append(extraHead(path, modified), { html: true });
      },
    })
    .on("header.sx-nav", {
      element(e) {
        e.replace(nav(path), { html: true });
      },
    })
    .on("footer.full-footer", {
      element(e) {
        e.replace(footer(), { html: true });
      },
    })
    .on("#full-" + active, {
      element(e) {
        e.removeAttribute("hidden");
        e.setAttribute("role", "main");
      },
    })
    .on("#full-" + (active === "sx" ? "pay" : "sx") + " h1", {
      element(e) {
        e.tagName = "h2";
      },
    })
    .on("[data-market]", {
      element(e) {
        e.setInnerContent(market[e.getAttribute("data-market")] ?? "—");
      },
    })
    .on("[data-pay]", {
      element(e) {
        e.setInnerContent(
          { num, usd, pct, compact }[e.getAttribute("data-format") || "num"](
            P?.headline[e.getAttribute("data-pay")],
          ),
        );
      },
    })
    .on("#sx-scenario-controls,#sx-map-legend", {
      element(e) {
        e.setAttribute("hidden", "");
      },
    })
    .on("#sx-history-controls,#sx-history-ranges", {
      element(e) {
        e.removeAttribute("hidden");
      },
    })
    .on("#full-data-rows", {
      element(e) {
        e.setInnerContent(rows(D, "sx"), { html: true });
      },
    })
    .on("#pay-data-rows", {
      element(e) {
        e.setInnerContent(rows(P, "pay"), { html: true });
      },
    })
    .on("body", {
      element(e) {
        e.append(
          `<script type="application/json" id="dashboard-bootstrap">${safeJSON({ sx: D, pay: P, feeds: { sx: { fallback: feeds.sx.fallback }, pay: { fallback: feeds.pay.fallback } } })}</script>`,
          { html: true },
        );
      },
    });
  // Bootstrap must precede deferred scripts; those execute only after parsing.
  for (const [id, value] of Object.entries(ids))
    rewriter = rewriter.on("#" + id, {
      element(e) {
        if (id === "sx-ratio")
          e.setInnerContent(value.replace("×", "<span>×</span>"), {
            html: true,
          });
        else if (id === "pay-tvl")
          e.setInnerContent(value.replace(/([KMB])$/, "<span>$1</span>"), {
            html: true,
          });
        else e.setInnerContent(value);
      },
    });
  for (const [key, data] of [
    ["sx", D],
    ["pay", P],
  ]) {
    rewriter = rewriter.on("#" + key + "-status", {
      element(e) {
        const age = data
          ? (Date.now() - Date.parse(data.generated_at)) / 36e5
          : 0;
        let warning = !data
          ? "Data unavailable. Please reload to retry."
          : feeds[key].fallback
            ? "Repository feed unavailable · showing the deployed backup. "
            : "";
        if (data && age > (key === "pay" ? 36 : 48))
          warning += "Source data is " + Math.floor(age) + " hours old. ";
        if (data && warning)
          warning += "Updated " + stamp(data.generated_at) + ".";
        e.setInnerContent(warning);
        if (warning && key === active) {
          e.removeAttribute("hidden");
          e.setAttribute("class", "data-status warning");
        } else e.setAttribute("hidden", "");
      },
    });
    if (data)
      rewriter = rewriter.on(
        key === "sx" ? "#sx-main-chart" : "#pay-main-chart",
        {
          element(e) {
            e.setAttribute("viewBox", "0 0 800 320");
            e.setAttribute(
              "aria-label",
              key === "sx"
                ? "StablecoinX historical market cap and token NAV"
                : "EthenaPay daily USDe card spend",
            );
            e.setInnerContent(
              chart(
                data.series.date,
                key === "sx"
                  ? data.series.ena_price.map(
                      (v, i) => v * data.series.ena_holdings[i],
                    )
                  : data.series.spend_usde,
                key === "sx"
                  ? "Historical market cap and token NAV"
                  : "Daily USDe card spend",
                true,
                key === "sx"
                  ? data.series.usde_close.map(
                      (v, i) => v * data.series.shares_outstanding[i],
                    )
                  : [],
              ),
              { html: true },
            );
          },
        },
      );
  }
  if (D) {
    const c = Ethena.current(D);
    rewriter = rewriter
      .on("#sx-cap-bar", {
        element(e) {
          e.setAttribute(
            "style",
            "width:" + (100 * c.cap) / Math.max(c.cap, c.nav) + "%",
          );
        },
      })
      .on("#unlocked-bar", {
        element(e) {
          e.setAttribute(
            "style",
            "width:" + (100 * Ethena.unlocked(D)) / D.ena_holdings + "%",
          );
        },
      });
  }
  const response = rewriter.transform(template);
  return new Response(response.body, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=60",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url),
      path = canonicalPath(url.pathname),
      local =
        env.LOCAL_DEV === "true" ||
        ["localhost", "127.0.0.1"].includes(url.hostname);
    if (!["GET", "HEAD"].includes(request.method))
      return new Response("Method not allowed", {
        status: 405,
        headers: { Allow: "GET, HEAD" },
      });
    if (
      (!local &&
        (url.hostname !== "ethenadash.com" || url.protocol !== "https:")) ||
      (path && path !== url.pathname)
    ) {
      const dest =
        (local ? url.origin : ORIGIN) + (path || url.pathname) + url.search;
      return Response.redirect(dest, 301);
    }
    let response;
    if (url.pathname === "/api/lighter/stablecoinx")
      response = await lighterResponse(ctx);
    else if (url.pathname === "/sitemap.xml")
      response = new Response(sitemap(), {
        headers: {
          "Content-Type": "application/xml; charset=utf-8",
          "Cache-Control": "public, max-age=3600",
        },
      });
    else if (url.pathname === "/robots.txt")
      response = new Response(
        "User-agent: *\nAllow: /\n\nSitemap: " + ORIGIN + "/sitemap.xml\n",
        { headers: { "Content-Type": "text/plain; charset=utf-8" } },
      );
    else if (content[path]) response = documentPage(path, content[path]);
    else if (PAGES[path]?.page) {
      const [template, sx, pay] = await Promise.all([
        env.ASSETS.fetch(new Request(url.origin + "/")),
        loadFeed("data.json", "sx", env, url.origin, ctx),
        loadFeed("ethenapay.json", "pay", env, url.origin, ctx),
      ]);
      response = renderDashboard(template, path, { sx, pay });
    } else {
      response = await env.ASSETS.fetch(request);
      if (response.status === 404)
        response = new Response(
          '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found | EthenaDash</title><body style="background:#0d1116;color:#eeeae3;font-family:system-ui;padding:10vw"><h1>Page not found.</h1><p>This address does not match a page on EthenaDash.</p><a style="color:#8aa9cf" href="/stablecoinx/">Return to the dashboard →</a></body></html>',
          {
            status: 404,
            headers: { "Content-Type": "text/html; charset=utf-8" },
          },
        );
    }
    return request.method === "HEAD"
      ? new Response(null, {
          status: response.status,
          headers: response.headers,
        })
      : response;
  },
};
