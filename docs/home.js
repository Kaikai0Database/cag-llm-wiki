"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const main = document.getElementById("main");
  try {
    const data = await App.loadJSON("data.json");
    App.renderHeader();
    document.getElementById("site-title").textContent = data.site.title;
    document.getElementById("site-subtitle").textContent = data.site.subtitle || "";

    const decks = data.decks || [];
    const sources = data.sources || [];
    const chunkTotal = sources.reduce((n, s) => n + (s.chunk_count || 0), 0);
    const keptTotal = decks.reduce((n, d) => n + ((d.verification || {}).kept || 0), 0);
    document.getElementById("stats").append(tagList([
      tag(`${sources.length} 篇來源`),
      tag(`${chunkTotal} 個段落`),
      tag(`${keptTotal} 個已檢核重點`, "ok"),
    ]));

    const deckBox = document.getElementById("decks");
    if (!decks.length) {
      deckBox.append(h("div", { cls: "card", text: "還沒有簡報。執行 python -m pipeline build decks/<主題>.json" }));
    }
    for (const d of decks) {
      const v = d.verification || {};
      deckBox.append(h("article", { cls: "card feature" }, [
        h("div", { cls: "body" }, [
          h("h3", { text: d.title }),
          h("p", { cls: "lead", text: d.subtitle }),
          tagList([
            tag(`${d.slide_count} 張`),
            tag(`保留 ${v.kept ?? 0}`, "ok"),
            tag(`剔除 ${v.dropped ?? 0}`, "warn"),
          ]),
        ]),
        h("div", { cls: "actions" }, [
          h("a", { cls: "btn ghost", text: "檢核報告", attrs: { href: `reports/${encodeURIComponent(d.slug)}-verify.md` } }),
          h("a", { cls: "btn", text: "開始播放 →", attrs: { href: `slides.html?deck=${encodeURIComponent(d.slug)}` } }),
        ]),
      ]));
    }

    const list = document.getElementById("sources");
    for (const s of sources) {
      list.append(h("li", {}, [
        h("a", { cls: "row", attrs: { href: `wiki.html?src=${encodeURIComponent(s.id)}` } }, [
          h("span", { cls: "lead-in" }, [tag(s.id, "mono accent"), h("span", { cls: "title", text: s.title })]),
          h("span", { cls: "side" }, [
            h("span", { text: `${s.chunk_count} 段` }),
            h("span", { cls: "arrow", text: "→", attrs: { "aria-hidden": "true" } }),
          ]),
        ]),
      ]));
    }
  } catch (err) {
    App.showError(main, err);
  }
})();
