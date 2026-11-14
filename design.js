"use strict";

(async () => {
  const { h, tag, tagList } = App;
  const main = document.getElementById("main");

  const qaBlock = (item) => h("section", {}, [
    h("h3", { text: item.q }),
    h("ul", {}, item.a.map((t) => h("li", { text: t }))),
  ]);

  try {
    const d = await App.loadJSON("data/design.json");
    App.renderHeader();
    document.getElementById("design-title").textContent = d.title;

    const flowTags = document.getElementById("flow-tags");
    for (const f of d.flow) flowTags.append(h("li", {}, [tag(f.step, f.repeat ? "accent" : "")]));

    document.getElementById("flow").append(...d.flow.map((f) =>
      h("li", { cls: f.repeat ? "loop" : "" }, [
        h("div", { cls: "head" }, [h("h3", { text: f.step }), tag(f.node, "mono")]),
        h("p", { cls: "desc", text: `${f.does}　檢查：${f.check}` }),
      ])));

    document.getElementById("qa").append(...d.qa.map(qaBlock));

    document.getElementById("runs").append(...d.runs.map((r) =>
      h("li", { cls: "row" }, [
        h("span", { cls: "title", text: r.name }),
        tagList([tag(`保留 ${r.kept}`, "ok"), tag(`剔除 ${r.dropped}`, "warn"), tag(`${r.iterations} 輪`)]),
        h("p", { cls: "sub", text: r.finding }),
      ])));

    document.getElementById("reflection").append(...d.reflection.map(qaBlock));
  } catch (err) {
    App.showError(main, err);
  }
})();
