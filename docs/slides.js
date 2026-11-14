"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const stage = document.getElementById("stage");
  const counter = document.getElementById("counter");
  const progress = document.getElementById("progress");
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");

  function titleSlide(s) {
    return [
      h("h1", { text: s.title }),
      h("p", { cls: "lead", text: s.subtitle }),
      tagList((s.tags || []).map((t) => tag(t, "accent"))),
    ];
  }

  function contentSlide(s) {
    const items = (s.bullets || []).map((b) => {
      const c = b.cite || {};
      const href = `wiki.html?src=${encodeURIComponent(c.source_id || "")}#${App.chunkAnchor(c.chunk_id || "")}`;
      return h("li", {}, [document.createTextNode(b.text), tag(c.chunk_id || "無引用", "", href)]);
    });
    const srcs = [...new Set((s.bullets || []).map((b) => (b.cite || {}).source_title).filter(Boolean))];
    return [
      h("h2", { text: s.title }),
      h("ul", { cls: "points" }, items),
      h("div", { cls: "slide-foot" }, [h("p", { cls: "small", text: `來源：${srcs.join("；")}` })]),
    ];
  }

  function refSlide(s) {
    const v = s.verification || {};
    return [
      h("h2", { text: s.title }),
      h("ol", { cls: "refs" }, (s.items || []).map((r) =>
        h("li", {}, [h("strong", { text: r.title }), h("div", { cls: "citation", text: r.citation })]))),
      h("div", { cls: "slide-foot" }, [
        tagList([
          tag(`保留 ${v.kept ?? 0} 點`, "ok"),
          tag(`剔除 ${v.dropped ?? 0} 點`, "warn"),
          tag(`迭代 ${v.iterations ?? 0} 次`),
          (v.empty_sections || []).length ? tag(`空章節：${v.empty_sections.join("、")}`, "warn") : null,
        ].filter(Boolean)),
        h("p", { cls: "small", text: "本簡報由本機 LLM 依 Wiki 段落生成，僅供教學；臨床決策請以指引原文為準。" }),
      ]),
    ];
  }

  const RENDER = { title: titleSlide, content: contentSlide, references: refSlide };

  try {
    const site = await App.loadJSON("data.json");
    App.renderHeader(site.site);
    const decks = site.decks || [];
    const want = new URLSearchParams(location.search).get("deck") || (decks[0] && decks[0].slug);
    if (!want || !/^[a-z0-9-]+$/.test(want)) throw new Error("找不到簡報（deck 參數不合法或尚未產生）");
    if (!decks.some((d) => d.slug === want)) throw new Error(`data.json 中沒有簡報：${want}`);
    const deck = await App.loadJSON(`data/decks/${want}.json`);
    document.title = `${deck.title}｜教學簡報`;

    const slides = deck.slides.map((s, i) => {
      const render = RENDER[s.type];
      if (!render) throw new Error(`未知的投影片類型：${s.type}`);
      return h("section", {
        cls: `card slide${s.type === "title" ? " title-slide" : ""}`,
        attrs: { "aria-label": `第 ${i + 1} 張`, "data-type": s.type },
      }, render(s));
    });
    stage.replaceChildren(...slides);
    progress.max = slides.length;

    let idx = 0;
    function show(i) {
      idx = Math.max(0, Math.min(slides.length - 1, i));
      slides.forEach((el, j) => { el.hidden = j !== idx; });
      counter.textContent = `${idx + 1} / ${slides.length}`;
      progress.value = idx + 1;
      prev.disabled = idx === 0;
      next.disabled = idx === slides.length - 1;
      history.replaceState(null, "", `#${idx + 1}`);
    }
    prev.addEventListener("click", () => show(idx - 1));
    next.addEventListener("click", () => show(idx + 1));
    document.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "PageDown") show(idx + 1);
      else if (e.key === "ArrowLeft" || e.key === "PageUp") show(idx - 1);
      else if (e.key === "Home") show(0);
      else if (e.key === "End") show(slides.length - 1);
    });
    const start = parseInt(location.hash.slice(1), 10);
    show(Number.isFinite(start) ? start - 1 : 0);
  } catch (err) {
    App.showError(document.getElementById("main"), err);
  }
})();
