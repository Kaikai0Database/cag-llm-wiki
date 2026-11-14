"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const main = document.getElementById("main");

  function qaCard(item) {
    return h("article", { cls: "card" }, [
      h("h3", { text: item.q }),
      h("ul", {}, item.a.map((t) => h("li", { text: t }))),
    ]);
  }

  try {
    const [site, d] = await Promise.all([App.loadJSON("data.json"), App.loadJSON("data/design.json")]);
    App.renderHeader(site.site);
    document.getElementById("design-title").textContent = d.title;
    document.getElementById("design-lead").textContent = d.lead;

    const flowTags = document.getElementById("flow-tags");
    for (const f of d.flow) flowTags.append(h("li", {}, [tag(f.step, f.repeat ? "accent" : "")]));

    const flow = document.getElementById("flow");
    for (const f of d.flow) {
      flow.append(h("article", { cls: "card" }, [
        h("h3", { text: f.step }),
        tagList([tag(f.node), f.repeat ? tag("會重複", "accent") : tag("執行一次")]),
        h("p", { text: f.does }),
        h("p", { cls: "small", text: `檢查：${f.check}` }),
      ]));
    }

    const qa = document.getElementById("qa");
    for (const item of d.qa) qa.append(qaCard(item));

    const runs = document.getElementById("runs");
    for (const r of d.runs) {
      runs.append(h("article", { cls: "card" }, [
        h("h3", { text: r.name }),
        tagList([
          tag(`保留 ${r.kept}`, "ok"),
          tag(`剔除 ${r.dropped}`, "warn"),
          tag(`迭代 ${r.iterations}`),
          tag(`空章節：${r.empty}`, r.empty === "無" ? "" : "warn"),
        ]),
        h("p", { text: r.finding }),
      ]));
    }

    const refl = document.getElementById("reflection");
    for (const item of d.reflection) refl.append(qaCard(item));
  } catch (err) {
    App.showError(main, err);
  }
})();
