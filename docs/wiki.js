"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const main = document.getElementById("main");
  try {
    const [data, chunks] = await Promise.all([App.loadJSON("data.json"), App.loadJSON("wiki/chunks.json")]);
    App.renderHeader(data.site);
    const sources = data.sources || [];
    const want = new URLSearchParams(location.search).get("src");
    const current = sources.find((s) => s.id === want) || sources[0];
    if (!current) throw new Error("Wiki 尚無來源，請先執行 python -m pipeline ingest");

    document.getElementById("source-tabs").append(tagList(sources.map((s) =>
      tag(s.id, s.id === current.id ? "accent" : "", `wiki.html?src=${encodeURIComponent(s.id)}`))));

    const body = document.getElementById("wiki-body");
    const mine = chunks.filter((c) => c.source_id === current.id);
    body.append(h("h2", { cls: "section-title", text: current.title }));
    body.append(h("div", { cls: "card" }, [
      h("p", { cls: "citation", text: current.citation }),
      current.note ? h("p", { cls: "small", text: current.note }) : null,
      tagList([tag(`${mine.length} 段`, "accent"),
        tag("Wiki 原始 Markdown", "", current.wiki_page)]),
    ]));
    const grid = h("div", { cls: "grid section-title" });
    for (const c of mine) {
      grid.append(h("article", { cls: "card chunk", attrs: { id: App.chunkAnchor(c.id) } }, [
        tagList([tag(c.id, "accent")]),
        h("h3", { text: c.heading }),
        h("p", { text: c.text }),
      ]));
    }
    body.append(grid);
    if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
  } catch (err) {
    App.showError(main, err);
  }
})();
