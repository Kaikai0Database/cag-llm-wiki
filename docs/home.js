"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const main = document.getElementById("main");
  try {
    const data = await App.loadJSON("data.json");
    App.renderHeader(data.site);
    document.getElementById("site-title").textContent = data.site.title;
    document.getElementById("site-subtitle").textContent = data.site.subtitle || "";

    const decks = data.decks || [];
    const sources = data.sources || [];
    const chunkTotal = sources.reduce((n, s) => n + (s.chunk_count || 0), 0);
    document.getElementById("stats").append(tagList([
      tag(`${sources.length} 篇來源`, "accent"),
      tag(`${chunkTotal} 個 Wiki 段落`),
      tag(`${decks.length} 份簡報`),
      tag(`Wiki 更新：${data.wiki_updated_at || "—"}`),
    ]));

    const deckBox = document.getElementById("decks");
    if (!decks.length) deckBox.append(h("div", { cls: "card", text: "尚未產生簡報。請執行 python -m pipeline build decks/<主題>.json" }));
    for (const d of decks) {
      const v = d.verification || {};
      deckBox.append(h("article", { cls: "card" }, [
        h("h3", { text: d.title }),
        h("p", { cls: "small", text: d.subtitle }),
        tagList((d.tags || []).map((t) => tag(t))),
        tagList([
          tag(`${d.slide_count} 張投影片`),
          tag(`保留 ${v.kept ?? 0} 點`, "ok"),
          tag(`剔除 ${v.dropped ?? 0} 點`, "warn"),
          tag(`模型 ${d.model}`),
        ]),
        h("p", { cls: "small", text: `產生時間：${d.generated_at}` }),
        h("div", { cls: "card-actions" }, [
          h("a", { cls: "btn", text: "開始播放", attrs: { href: `slides.html?deck=${encodeURIComponent(d.slug)}` } }),
          h("a", { cls: "btn ghost", text: "檢核報告", attrs: { href: `reports/${encodeURIComponent(d.slug)}-verify.md` } }),
        ]),
      ]));
    }

    const srcBox = document.getElementById("sources");
    for (const s of sources) {
      srcBox.append(h("article", { cls: "card" }, [
        h("h3", { text: s.title }),
        tagList([tag(s.id, "accent"), tag(`${s.chunk_count} 段`)]),
        s.summary ? h("p", { text: s.summary }) : null,
        s.key_terms && s.key_terms.length ? tagList(s.key_terms.map((t) => tag(t))) : null,
        h("p", { cls: "citation", text: s.citation }),
        h("div", { cls: "card-actions" }, [
          h("a", { cls: "btn ghost", text: "閱讀 Wiki 段落", attrs: { href: `wiki.html?src=${encodeURIComponent(s.id)}` } }),
        ]),
      ]));
    }
  } catch (err) {
    App.showError(main, err);
  }
})();
