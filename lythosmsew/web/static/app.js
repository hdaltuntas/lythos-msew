"use strict";
/* Lythos MSEW — the browser interface.
 *
 * The forms are built from the schema the server sends: field keys, labels,
 * units and defaults are declared once, in Python. Nothing here holds a second
 * copy of a label, so changing the language means fetching the schema again and
 * redrawing the forms.
 *
 * Every input lives in one flat object (S.values). That object is what is sent
 * to the server, and what a saved project file is made of. A field can declare
 * when it applies — "only in LRFD", "only when the earthquake is on" — and the
 * form redraws itself whenever a value another field depends on changes, so
 * what is on the screen is the method that is actually running.
 */

/* --------------------------------------------------------------- state */
const S = {
  meta: null,             // /api/meta
  values: {},             // current value of every field
  module: "inputs",       // inputs | heights
  view: { inputs: "summary", heights: "heights" },
  analysis: null,         // last analysis payload
  heights: null,          // last height study payload
  figure: { inputs: "section", heights: "margins" },
  selected: { types: 0, layers: 0 },
  poll: null,
  plotVersion: 0,         // so a redrawn figure is not served from the cache
  watched: new Set(),     // keys other fields' visibility depends on
};

const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v !== null && v !== undefined && v !== false) node.setAttribute(k, v);
  }
  for (const c of children) if (c) node.append(c);
  return node;
};
const T = (key) => (S.meta && S.meta.strings[key]) || key;

/* ------------------------------------------------------------- server */
async function api(path, body) {
  const options = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const response = await fetch(path, options);
  const data = await response.json();
  if (data.error) throw new Error(data.error);
  return data;
}

function status(message, isError = false) {
  $("statusMsg").textContent = message || "";
  $("statusBar").classList.toggle("error", !!isError);
}

function busy(on, note) {
  $("progressBar").style.width = on ? "65%" : "0";
  if (note !== undefined) status(note);
  for (const id of ["btnAnalyse", "btnHeights", "btnReport", "btnGenerate"]) {
    const node = $(id);
    if (node) node.disabled = on;
  }
  $("btnCancel").disabled = !on;
}

function progress(done, total) {
  const pct = total > 0 ? Math.round((100 * done) / total) : 0;
  $("progressBar").style.width = `${pct}%`;
}

async function download(path, body, filename) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || response.statusText);
  }
  const url = URL.createObjectURL(await response.blob());
  const link = el("a", { href: url, download: filename });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

/* --------------------------------------------------- conditional fields */
/* A field or group applies when every one of its conditions holds. */
function applies(item) {
  for (const condition of item.when || []) {
    const value = S.values[condition.key];
    if (!condition.in.some((wanted) => wanted === value)) return false;
  }
  return true;
}

/* Which keys other fields watch: changing one of them redraws the forms. */
function collectWatched() {
  S.watched = new Set();
  for (const part of ["project", "wall", "layout", "options", "heights"]) {
    for (const group of S.meta.schema[part].groups) {
      for (const item of [group, ...group.fields]) {
        for (const condition of item.when || []) S.watched.add(condition.key);
      }
    }
  }
}

/* The names in the reinforcement type table, for every "type" select. */
function typeNames() {
  return (S.values.reinforcement_types || [])
    .map((row) => String(row.name || "").trim())
    .filter((name, index, all) => name && all.indexOf(name) === index);
}

function typeSelect(value, onchange) {
  const names = typeNames();
  const input = el("select", { onchange });
  for (const name of names) input.append(el("option", { value: name, text: name }));
  if (value && !names.includes(value)) {
    // keep a name the table no longer has visible, so the error is readable
    input.append(el("option", { value, text: `${value} ?` }));
  }
  input.value = value || names[0] || "";
  return input;
}

/* -------------------------------------------------------- form building */
function fieldNode(field, prefix) {
  const id = prefix + "_" + field.key;
  const value = S.values[field.key];

  if (field.kind === "check") {
    const input = el("input", {
      type: "checkbox", id,
      onchange: (e) => { setValue(field.key, e.target.checked); },
    });
    input.checked = !!value;
    return el("div", { class: "field check" }, input, el("label", { for: id, text: field.label }));
  }

  let input;
  if (field.kind === "select") {
    input = el("select", { id, onchange: (e) => setValue(field.key, e.target.value) });
    for (const option of field.options || []) {
      input.append(el("option", { value: option.value, text: option.label }));
    }
    input.value = value ?? (field.options && field.options[0] && field.options[0].value);
  } else if (field.kind === "reftype") {
    input = typeSelect(value, (e) => setValue(field.key, e.target.value));
    input.id = id;
    S.values[field.key] = input.value;
  } else if (field.kind === "text") {
    input = el("input", {
      type: "text", id,
      oninput: (e) => { S.values[field.key] = e.target.value; },
    });
    input.value = value ?? "";
  } else {
    input = el("input", {
      type: "number", id,
      step: field.step || (field.decimals === 0 ? 1 : Math.pow(10, -(field.decimals ?? 2))),
      min: field.min, max: field.max,
      oninput: (e) => {
        const raw = e.target.value.trim();
        S.values[field.key] = raw === "" ? null : parseFloat(raw);
      },
    });
    input.value = value === null || value === undefined ? "" : value;
  }

  const label = el("label", { for: id }, document.createTextNode(field.label));
  if (field.unit) label.append(el("span", { class: "unit", text: field.unit }));
  return el("div", { class: "field" }, label, input);
}

/* A value another field's visibility depends on redraws the forms. */
function setValue(key, value) {
  S.values[key] = value;
  if (S.watched.has(key)) renderForms();
  else if (key.startsWith("layout_")) renderForms();   // both copies of the layout rule
}

function groupNode(group, prefix) {
  const box = el("fieldset", {}, el("legend", { text: group.title }));
  for (const field of group.fields) {
    if (applies(field)) box.append(fieldNode(field, prefix));
  }
  if (group.note) box.append(el("div", { class: "note", text: group.note }));
  return box;
}

function renderForm(host, groups, prefix) {
  host.replaceChildren(...groups.filter(applies).map((g) => groupNode(g, prefix)));
}

function renderForms() {
  const schema = S.meta.schema;
  renderForm($("projectForm"), schema.project.groups, "p");
  renderForm($("wallForm"), schema.wall.groups, "w");
  renderForm($("layoutForm"), schema.layout.groups, "l");
  renderForm($("optionsForm"), schema.options.groups, "o");
  renderForm($("heightsForm"), schema.heights.groups, "h");
  renderForm($("layoutForm2"), schema.layout.groups, "l2");
}

/* ------------------------------------------------------------ input tables */
const TABLES = {
  types: { values: "reinforcement_types", head: "typesHead", body: "typesBody", schema: "types" },
  layers: { values: "layers", head: "layersHead", body: "layersBody", schema: "layers" },
};

/* Columns that mean nothing for a row's kind are greyed out. */
function offColumns(name, row) {
  if (name !== "types") return [];
  const schema = S.meta.schema.types;
  return row.kind === "strip" ? schema.geo_only : schema.steel_only;
}

function renderTable(name) {
  const spec = TABLES[name];
  const columns = S.meta.schema[spec.schema].columns;
  $(spec.head).replaceChildren(...columns.map((c) => el("th", { text: c.label })));

  const rows = S.values[spec.values] || (S.values[spec.values] = []);
  const body = $(spec.body);
  body.replaceChildren();
  rows.forEach((row, index) => {
    const tr = el("tr", {
      class: index === S.selected[name] ? "selected" : "",
      onclick: () => {
        if (S.selected[name] === index) return;
        S.selected[name] = index;
        for (const [i, node] of Array.from(body.children).entries()) {
          node.classList.toggle("selected", i === index);
        }
      },
    });
    const off = offColumns(name, row);
    for (const column of columns) {
      let input;
      if (column.kind === "select") {
        input = el("select", {
          onchange: (e) => {
            row[column.key] = e.target.value;
            if (name === "types" && column.key === "kind") renderTable("types");
          },
        });
        for (const option of column.options || []) {
          input.append(el("option", { value: option.value, text: option.label }));
        }
        input.value = row[column.key] ?? (column.options[0] ? column.options[0].value : "");
        row[column.key] = input.value;
      } else if (column.kind === "reftype") {
        input = typeSelect(row[column.key], (e) => { row[column.key] = e.target.value; });
        row[column.key] = input.value;
      } else {
        input = el("input", {
          type: column.kind === "number" ? "number" : "text",
          step: "any",
          oninput: (e) => {
            const raw = e.target.value;
            row[column.key] = column.kind === "number"
              ? (raw === "" ? null : parseFloat(raw))
              : raw;
          },
          onfocus: (e) => { e.target.dataset.before = e.target.value; },
          onchange: (e) => {
            // a renamed type takes its layers, and the layout rule, with it
            if (name === "types" && column.key === "name") {
              const before = (e.target.dataset.before || "").trim();
              const after = String(row.name || "").trim();
              if (before && after && before !== after) {
                for (const layer of S.values.layers || []) {
                  if (layer.type === before) layer.type = after;
                }
                if (S.values.layout_type === before) S.values.layout_type = after;
              }
              e.target.dataset.before = e.target.value;
              renderTable("layers");
              renderForms();
            }
          },
        });
        input.value = row[column.key] ?? "";
      }
      const grey = off.includes(column.key);
      input.disabled = grey;
      tr.append(el("td", { class: (grey ? "off " : "") + (column.key === "name" ? "name" : "") },
        input));
    }
    body.append(tr);
  });
}

function blankRow(name) {
  const rows = S.values[TABLES[name].values] || [];
  const last = rows.slice(-1)[0];
  if (name === "types") {
    const base = last ? { ...last } : { ...S.meta.schema.types.rows[0] };
    base.name = `${base.name || "Type"} (${rows.length + 1})`;
    return base;
  }
  if (!last) return { z: 0.3, L: S.values.H * 0.7, type: typeNames()[0] || "" };
  const previous = rows.length > 1 ? rows[rows.length - 2] : null;
  const step = previous ? last.z - previous.z : 0.6;
  return { ...last, z: Math.round((last.z + step) * 1000) / 1000 };
}

function addRow(name) {
  const key = TABLES[name].values;
  (S.values[key] = S.values[key] || []).push(blankRow(name));
  S.selected[name] = S.values[key].length - 1;
  renderTable(name);
  if (name === "types") { renderTable("layers"); renderForms(); }
}

function removeRow(name) {
  const rows = S.values[TABLES[name].values] || [];
  if (rows.length <= 1) return;
  rows.splice(S.selected[name], 1);
  S.selected[name] = Math.max(0, S.selected[name] - 1);
  renderTable(name);
  if (name === "types") { renderTable("layers"); renderForms(); }
}

/* ------------------------------------------------------------ views */
const VIEWS = {
  inputs: [["summary", "view_summary"], ["layers", "view_layers"], ["figures", "view_figures"],
           ["text", "view_text"]],
  heights: [["heights", "view_heights"], ["figures", "view_figures"], ["text", "view_text"]],
};

function renderTabs() {
  $("viewTabs").replaceChildren(...VIEWS[S.module].map(([key, label]) =>
    el("button", {
      text: T(label),
      class: S.view[S.module] === key ? "active" : "",
      onclick: () => { S.view[S.module] = key; renderTabs(); renderView(); },
    })));
}

function placeholder(text) {
  return el("div", { class: "placeholder", text });
}

function plotImage(target, kind) {
  return el("img", { src: `/api/plot?target=${target}&kind=${kind}&v=${S.plotVersion}`, alt: kind });
}

function dataTable(table) {
  const body = table.rows.map((row) => {
    const tr = el("tr", { class: row.primary ? "primary" : "" });
    (row.cells || row).forEach((cell, index) => {
      const state = row.states ? row.states[index] : "";
      tr.append(el("td", { class: state || "", text: cell }));
    });
    return tr;
  });
  return el("div", { class: "table-wrap" }, el("table", { class: "data" },
    el("thead", {}, el("tr", {}, ...table.columns.map((c) => el("th", { text: c })))),
    el("tbody", {}, ...body)));
}

function cardRow(cards) {
  return el("div", { class: "cards" }, ...cards.map((card) =>
    el("div", { class: "card " + (card.state || "") },
      el("small", { text: card.title }),
      el("b", { text: card.value }),
      el("span", { class: "sub", text: card.sub || "" }))));
}

function warningBox(warnings) {
  if (!warnings || !warnings.length) return null;
  return el("div", { class: "warnings" },
    el("h3", { text: T("warnings_title") }),
    el("ul", {}, ...warnings.map((w) => el("li", { text: w }))));
}

function updatePicker() {
  const showFigures = S.view[S.module] === "figures";
  $("picker").hidden = !showFigures;
  if (!showFigures) return;
  const figure = $("figure");
  const keys = S.module === "inputs"
    ? (S.analysis && S.analysis.figures) || []
    : (S.heights && S.heights.views) || [];
  const labels = S.module === "inputs" ? S.meta.figure_labels : S.meta.height_view_labels;
  figure.replaceChildren(...keys.map((key) => el("option", { value: key, text: labels[key] || key })));
  if (!keys.includes(S.figure[S.module])) S.figure[S.module] = keys[0] || "";
  figure.value = S.figure[S.module];
}

function renderView() {
  const view = $("view");
  const which = S.view[S.module];
  updatePicker();

  if (S.module === "inputs") {
    const a = S.analysis;
    if (!a) return view.replaceChildren(placeholder(T("no_results")));
    if (which === "summary") {
      const parts = [cardRow(a.cards)];
      const warnings = warningBox(a.warnings);
      if (warnings) parts.push(warnings);
      parts.push(el("h2", { text: T("external_title") }), dataTable(a.external));
      parts.push(plotImage("analysis", "section"));
      return view.replaceChildren(...parts);
    }
    if (which === "layers") {
      const parts = [el("h2", { text: T("internal_title") }), dataTable(a.layers)];
      if (a.seismic_layers) {
        parts.push(el("h2", { text: T("seismic_title") }), dataTable(a.seismic_layers));
      }
      parts.push(el("h2", { text: T("bearing_title") }), dataTable(a.bearing));
      parts.push(plotImage("analysis", "internal"));
      return view.replaceChildren(...parts);
    }
    if (which === "text") return view.replaceChildren(el("pre", { text: a.text }));
    return view.replaceChildren(plotImage("analysis", S.figure.inputs));
  }

  const h = S.heights;
  if (!h) return view.replaceChildren(placeholder(T("no_heights")));
  if (which === "figures") return view.replaceChildren(plotImage("heights", S.figure.heights));
  if (which === "text") return view.replaceChildren(el("pre", { text: h.text }));
  const good = h.table.rows.every((row) => row.states[row.states.length - 1] !== "bad");
  view.replaceChildren(
    el("div", { class: "verdict " + (good ? "ok" : "bad"), text: h.verdict }),
    el("h2", { text: T("heights_title") }), dataTable(h.table),
    plotImage("heights", "margins"));
}

/* ------------------------------------------------------------- actions */
async function runAnalysis() {
  busy(true, T("running_analysis"));
  try {
    const data = await api("/api/analyse", { values: S.values });
    S.analysis = data;
    S.plotVersion += 1;
    switchModule("inputs");
    renderTabs();
    renderView();
    status(`${T("analysis_complete")} ${data.headline}`);
  } catch (error) {
    S.analysis = null;
    renderView();
    status(`${T("error")}: ${error.message}`, true);
  } finally {
    busy(false);
  }
}

async function generateLayers() {
  try {
    const data = await api("/api/layout", { values: S.values });
    S.values.layers = data.layers;
    S.selected.layers = 0;
    renderTable("layers");
    status(`${T("generated")} (${data.layers.length})`);
  } catch (error) {
    status(`${T("error")}: ${error.message}`, true);
  }
}

async function runHeights() {
  busy(true, T("running_analysis"));
  try {
    const data = await api("/api/heights", { values: S.values });
    if (!data.ok) throw new Error(data.error);
    S.heights = null;
    switchModule("heights");
    startPolling();
  } catch (error) {
    busy(false);
    status(`${T("error")}: ${error.message}`, true);
  }
}

async function cancelHeights() {
  try {
    await api("/api/cancel", {});
    status(T("cancelled"));
  } catch (error) {
    status(`${T("error")}: ${error.message}`, true);
  }
}

async function loadHeights() {
  try {
    const data = await api("/api/heights");
    if (!data.ok) throw new Error(data.error);
    S.heights = data;
    S.plotVersion += 1;
    renderTabs();
    renderView();
  } catch (error) {
    status(`${T("error")}: ${error.message}`, true);
  }
}

async function downloadReport() {
  busy(true, T("report_running"));
  try {
    const format = $("reportFormat").value || "pdf";
    await download("/api/report", { format }, `lythosmsew_report.${format}`);
    status(T("report_action") + " ✓");
  } catch (error) {
    status(`${T("error")}: ${error.message}`, true);
  } finally {
    busy(false);
  }
}

async function exportHeights(format) {
  try {
    await download("/api/export-heights", { format }, `lythosmsew_heights.${format}`);
    status(T("saved"));
  } catch (error) {
    status(`${T("error")}: ${error.message}`, true);
  }
}

/* --------------------------------------------------- background polling */
function startPolling() {
  if (S.poll) return;
  S.poll = setInterval(async () => {
    let state;
    try {
      state = await api("/api/state");
    } catch {
      return;
    }
    if (state.job === "running") {
      progress(state.done, state.total);
      if (state.total) {
        status(T("hs_progress").replace("{done}", state.done).replace("{total}", state.total));
      }
      return;
    }
    clearInterval(S.poll);
    S.poll = null;
    busy(false);

    if (state.job === "error") {
      status(`${T("error")}: ${state.error}`, true);
      return;
    }
    if (state.has_heights) {
      await loadHeights();
      $("btnCsv").disabled = false;
      $("btnXlsx").disabled = false;
    }
    if (state.note) status(state.note);
  }, 300);
}

/* ------------------------------------------------------------- layout */
function switchModule(name) {
  S.module = name;
  $("paneInputs").hidden = name !== "inputs";
  $("paneHeights").hidden = name !== "heights";
  for (const button of document.querySelectorAll("nav.modules button")) {
    button.classList.toggle("active", button.dataset.module === name);
  }
  renderTabs();
  renderView();
}

function applyMeta(meta) {
  S.meta = meta;
  document.documentElement.lang = meta.language;
  collectWatched();

  $("tagline").textContent = T("tagline");
  $("lblLanguage").textContent = T("language");
  $("btnOpen").textContent = T("open");
  $("btnSave").textContent = T("save");
  $("btnTheme").title = T("theme");
  $("lblReport").textContent = T("report_format");
  $("btnReport").textContent = T("report_action");
  $("tabInputs").textContent = T("tab_inputs");
  $("tabHeights").textContent = T("tab_heights");
  $("lblTypes").textContent = T("types_group");
  $("typesNote").textContent = T("types_note");
  $("lblLayers").textContent = T("layers_group");
  $("layersNote").textContent = T("layers_note");
  $("btnGenerate").textContent = T("generate");
  $("btnAnalyse").textContent = T("run_analysis_button");
  $("btnHeights").textContent = T("hs_run");
  $("btnCancel").textContent = T("cancel");
  $("btnCsv").textContent = T("hs_export_csv");
  $("btnXlsx").textContent = T("hs_export_xlsx");
  $("lblFigure").textContent = T("figure");
  for (const button of document.querySelectorAll("button.add")) button.textContent = T("add_row");
  for (const button of document.querySelectorAll("button.del")) button.textContent = T("del_row");

  const language = $("language");
  language.replaceChildren(...meta.languages.map((code) =>
    el("option", { value: code, text: code.toUpperCase() })));
  language.value = meta.language;

  const report = $("reportFormat");
  const previous = report.value;
  report.replaceChildren(...["pdf", "html", "docx"].map((format) =>
    el("option", { value: format, text: T("report_" + format) })));
  report.value = previous || "pdf";

  renderForms();
  renderTable("types");
  renderTable("layers");
  renderTabs();
  renderView();
  status(T("ready"));
}

async function setLanguage(code) {
  applyMeta(await api("/api/language", { lang: code }));
  if (S.analysis) await runAnalysis();
  if (S.heights) await loadHeights();
}

/* ------------------------------------------------------------ save / open */
async function saveProject() {
  try {
    await download("/api/project", { values: S.values }, "project.msew");
    status(T("saved"));
  } catch (error) {
    status(`${T("error")}: ${error.message}`, true);
  }
}

function openProject(file) {
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const project = JSON.parse(reader.result);
      const data = await api("/api/load", { project });
      S.values = data.values;
      S.analysis = null;
      S.heights = null;
      renderForms();
      renderTable("types");
      renderTable("layers");
      renderView();
      status(T("loaded"));
    } catch (error) {
      status(`${T("error")}: ${error.message}`, true);
    }
  };
  reader.readAsText(file);
}

/* ------------------------------------------------------------------ theme */
async function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem("lythosmsew-theme", theme);
  } catch { /* storage can be switched off in a private window */ }
  try {
    await api("/api/theme", { theme });           // the figures follow the page
    if (S.analysis || S.heights) {
      S.plotVersion += 1;
      renderView();
    }
  } catch { /* the page is themed either way */ }
}

function storedTheme() {
  try {
    return localStorage.getItem("lythosmsew-theme");
  } catch {
    return null;
  }
}

/* ------------------------------------------------------------- start-up */
async function start() {
  const theme = storedTheme();
  if (theme) document.documentElement.setAttribute("data-theme", theme);

  const meta = await api("/api/meta");
  S.values = JSON.parse(JSON.stringify(meta.defaults));
  applyMeta(meta);
  // Always tell the server: it keeps the theme of whichever page spoke last,
  // and the figures would otherwise follow that page rather than this one.
  await applyTheme(theme === "dark" ? "dark" : "light");

  $("language").addEventListener("change", (e) => setLanguage(e.target.value));
  $("btnTheme").addEventListener("click", () => applyTheme(
    document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark"));
  $("btnSave").addEventListener("click", saveProject);
  $("btnOpen").addEventListener("click", () => $("fileInput").click());
  $("fileInput").addEventListener("change", (e) => {
    if (e.target.files[0]) openProject(e.target.files[0]);
    e.target.value = "";
  });
  $("btnReport").addEventListener("click", downloadReport);
  $("btnAnalyse").addEventListener("click", runAnalysis);
  $("btnGenerate").addEventListener("click", generateLayers);
  $("btnHeights").addEventListener("click", runHeights);
  $("btnCancel").addEventListener("click", cancelHeights);
  $("btnCsv").addEventListener("click", () => exportHeights("csv"));
  $("btnXlsx").addEventListener("click", () => exportHeights("xlsx"));
  $("figure").addEventListener("change", (e) => { S.figure[S.module] = e.target.value; renderView(); });
  for (const button of document.querySelectorAll("button.add")) {
    button.addEventListener("click", () => addRow(button.dataset.table));
  }
  for (const button of document.querySelectorAll("button.del")) {
    button.addEventListener("click", () => removeRow(button.dataset.table));
  }
  for (const button of document.querySelectorAll("nav.modules button")) {
    button.addEventListener("click", () => switchModule(button.dataset.module));
  }
  $("btnCancel").disabled = true;
  $("btnCsv").disabled = true;
  $("btnXlsx").disabled = true;
}

start().catch((error) => status("Error: " + error.message, true));
