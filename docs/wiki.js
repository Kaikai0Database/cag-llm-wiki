"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const main = document.getElementById("main");
  try {
    const [data, chunks] = await Promise.all([App.loadJSON("data.json"), App.loadJSON("wiki/chunks.json")]);
    App.renderHeader();
    const sources = data.sources || [];
    const want = new URLSearchParams(location.search).get("src");
    const current = sources.find((s) => s.id === want) || sources[0];
    if (!current) throw new Error("Wiki 還沒有來源，請先執行 python -m pipeline ingest");

    document.getElementById("source-tabs").append(tagList(sources.map((s) => {
      const t = tag(s.id, s.id === current.id ? "mono accent" : "mono", `wiki.html?src=${encodeURIComponent(s.id)}`);
      if (s.id === current.id) t.setAttribute("aria-current", "page");
      return t;
    })));

    const mine = chunks.filter((c) => c.source_id === current.id);
    const isDraft = /整理稿/.test(current.note || "");
    const body = document.getElementById("wiki-body");
    body.append(h("header", { cls: "source-head" }, [
      h("h2", { text: current.title }),
      tagList([tag(`${mine.length} 段`), isDraft ? tag("整理稿，非原文全文", "warn") : null].filter(Boolean)),
      h("details", {}, [
        h("summary", { text: "引用與說明" }),
        h("p", { cls: "citation", text: current.citation }),
        current.note ? h("p", { cls: "citation", text: current.note }) : null,
        h("p", { cls: "citation" }, [h("a", { text: "原始 Markdown", attrs: { href: current.wiki_page } })]),
      ]),
    ]));
    body.append(h("ol", { cls: "chunks" }, mine.map((c) =>
      h("li", { cls: "chunk", attrs: { id: App.chunkAnchor(c.id) } }, [
        h("div", { cls: "head" }, [tag(c.id, "mono"), h("h3", { text: c.heading })]),
        h("p", { text: c.text }),
      ]))));
    const target = location.hash && document.getElementById(location.hash.slice(1));
    if (target) {
      target.classList.add("is-target");
      target.scrollIntoView();
    }
  } catch (err) {
    App.showError(main, err);
  }
})();
