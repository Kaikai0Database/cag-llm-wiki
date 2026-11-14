/* 共用工具：所有資料一律用 textContent 寫入，不解析任何 HTML 字串。 */
"use strict";

const App = (() => {
  function safeUrl(u) {
    try {
      return new URL(String(u), location.href).origin === location.origin;
    } catch (_) {
      return false;
    }
  }

  /** 建立元素：h("p", {cls, text, attrs}, [children]) */
  function h(tag, opts = {}, children = []) {
    const el = document.createElement(tag);
    if (opts.cls) el.className = opts.cls;
    if (opts.text !== undefined && opts.text !== null) el.textContent = String(opts.text);
    for (const [k, v] of Object.entries(opts.attrs || {})) {
      if (/^on/i.test(k)) continue;                       // 不允許 inline 事件
      if ((k === "href" || k === "src") && !safeUrl(v)) continue; // 只允許同源連結
      el.setAttribute(k, String(v));
    }
    for (const c of children) if (c) el.append(c);
    return el;
  }

  function tag(text, kind = "", href = "") {
    return href
      ? h("a", { cls: `tag ${kind}`.trim(), text, attrs: { href } })
      : h("span", { cls: `tag ${kind}`.trim(), text });
  }

  function tagList(items) {
    return h("ul", { cls: "tags" }, items.map((t) => h("li", {}, [t])));
  }

  async function loadJSON(path) {
    const r = await fetch(path, { cache: "no-cache" });
    if (!r.ok) throw new Error(`${path} 讀取失敗（HTTP ${r.status}）`);
    return r.json();
  }

  /** 頁首結構寫在 HTML，這裡只標示目前頁面 */
  function renderHeader() {
    const page = document.body.dataset.page;
    for (const a of document.querySelectorAll("#nav a")) {
      if (a.dataset.page === page) a.setAttribute("aria-current", "page");
    }
  }

  function showError(container, err) {
    container.replaceChildren(
      h("div", { cls: "card status" }, [
        h("h2", { text: "資料載入失敗" }),
        h("p", { text: String(err && err.message ? err.message : err) }),
      ])
    );
  }

  function chunkAnchor(chunkId) {
    return "c-" + String(chunkId).replace(/[^a-z0-9-]/gi, "-");
  }

  return { h, tag, tagList, loadJSON, renderHeader, showError, chunkAnchor };
})();
