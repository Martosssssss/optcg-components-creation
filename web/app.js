"use strict";

const pickerSection = document.getElementById("picker");
const componentGrid = document.getElementById("component-grid");
const pickerStatus = document.getElementById("picker-status");
const generatorSection = document.getElementById("generator");
const componentName = document.getElementById("component-name");
const changeComponentBtn = document.getElementById("change-component-btn");
const fileInput = document.getElementById("file-input");
const drop = document.querySelector(".drop");
const textInput = document.getElementById("text-input");
const generateBtn = document.getElementById("generate-btn");
const zipBtn = document.getElementById("zip-btn");
const statusEl = document.getElementById("status");
const errorsSection = document.getElementById("errors");
const errorsList = document.getElementById("errors-list");
const resultsGrid = document.getElementById("results");

let currentComponent = "";

function humanize(name) {
  return name
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function hasValidInput() {
  return textInput.value.trim().length > 0;
}

function updateButtons() {
  generateBtn.disabled = !hasValidInput() || !currentComponent;
  zipBtn.disabled = !hasValidInput() || !currentComponent;
}

function setStatus(message, isError) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", Boolean(isError));
}

/* --- Selector de componentes --- */

const PREVIEW_W = 1960;

function fitPreview(iframe) {
  try {
    const doc = iframe.contentDocument;
    if (!doc) return;
    const style = doc.createElement("style");
    style.textContent =
      "html{background:#fff}body{min-height:0!important;height:auto!important;display:flex!important;align-items:center!important;justify-content:center!important}";
    doc.head.appendChild(style);
    const h = doc.documentElement.scrollHeight;
    if (!h) return;
    const tile = iframe.parentElement;
    const targetW = tile.clientWidth || 320;
    const scale = targetW / PREVIEW_W;
    iframe.style.width = `${PREVIEW_W}px`;
    iframe.style.height = `${h}px`;
    iframe.style.transform = `scale(${scale})`;
    iframe.style.transformOrigin = "top left";
    tile.style.height = `${Math.round(h * scale)}px`;
    iframe.classList.add("fitted");
  } catch (_) {
    iframe.classList.add("fitted");
  }
}

function selectComponent(name) {
  currentComponent = name;
  componentName.textContent = humanize(name);
  generatorSection.classList.remove("hidden");
  pickerSection.classList.add("hidden");
  updateButtons();
  setStatus("");
}

function renderComponents(names) {
  componentGrid.innerHTML = "";
  for (const name of names) {
    const tile = document.createElement("article");
    tile.className = "component-tile";

    const preview = document.createElement("div");
    preview.className = "tile-preview";

    const iframe = document.createElement("iframe");
    iframe.title = `Vista previa de ${name}`;
    iframe.loading = "lazy";
    iframe.setAttribute("tabindex", "-1");
    iframe.style.width = `${PREVIEW_W}px`;
    iframe.style.height = "500px";
    iframe.addEventListener("load", () => fitPreview(iframe));
    preview.appendChild(iframe);
    iframe.src = `/components/${encodeURIComponent(name)}.html`;

    const title = document.createElement("div");
    title.className = "tile-name";
    title.textContent = humanize(name);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-primary btn-small";
    btn.textContent = "Usar este";
    btn.addEventListener("click", () => selectComponent(name));

    tile.append(preview, title, btn);
    componentGrid.append(tile);
  }
}

async function loadComponents() {
  pickerStatus.textContent = "Cargando componentes…";
  try {
    const res = await fetch("/api/components");
    if (!res.ok) throw new Error(`Error ${res.status}`);
    const data = await res.json();
    const names = data.components || [];
    if (!names.length) {
      pickerStatus.textContent = "No hay componentes en la carpeta components/.";
      return;
    }
    renderComponents(names);
    pickerStatus.textContent = "";
  } catch (err) {
    pickerStatus.textContent = `Error al cargar componentes: ${err.message}`;
  }
}

changeComponentBtn.addEventListener("click", () => {
  pickerSection.classList.remove("hidden");
  generatorSection.classList.add("hidden");
  setStatus("");
});

/* --- Generación --- */

async function generate({ zip } = {}) {
  const text = textInput.value.trim();
  if (!text) return;

  const url = zip ? "/api/generate/zip" : "/api/generate";
  const body = JSON.stringify({ text, component: currentComponent });

  generateBtn.disabled = true;
  zipBtn.disabled = true;
  setStatus(zip ? "Generando y comprimiendo…" : "Generando cartas…");

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });

    if (!res.ok) {
      let detail = `Error ${res.status}`;
      try {
        const err = await res.json();
        if (err.error) detail = err.error;
      } catch (_) { /* cuerpo no JSON */ }
      throw new Error(detail);
    }

    if (zip) {
      const blob = await res.blob();
      downloadBlob(blob, "cartas.zip");
      setStatus("ZIP descargado.");
      updateButtons();
      return;
    }

    const data = await res.json();
    renderResults(data);
    renderErrors(data.errors || []);
    setStatus(
      `Generadas ${data.cards.length} carta(s)` +
        (data.errors && data.errors.length ? `, ${data.errors.length} con error` : "") +
        "."
    );
  } catch (err) {
    setStatus(`Error: ${err.message}`, true);
  } finally {
    updateButtons();
  }
}

function renderResults(data) {
  resultsGrid.innerHTML = "";
  resultsGrid.classList.remove("hidden");

  for (const card of data.cards) {
    const item = document.createElement("article");
    item.className = "card-item";

    const img = document.createElement("img");
    img.alt = card.name;
    img.src = `data:image/png;base64,${card.png_b64}`;

    const meta = document.createElement("div");
    meta.className = "card-meta";

    const title = document.createElement("div");
    title.className = "card-title";
    const strong = document.createElement("strong");
    strong.textContent = card.name;
    const span = document.createElement("span");
    span.textContent = `${card.code} · x${card.qty}`;
    title.append(strong, span);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-download";
    btn.textContent = "Descargar";
    btn.addEventListener("click", () => {
      const a = document.createElement("a");
      a.href = `data:image/png;base64,${card.png_b64}`;
      a.download = `${card.code}.png`;
      a.click();
    });

    meta.append(title, btn);
    item.append(img, meta);
    resultsGrid.append(item);
  }
}

function renderErrors(errors) {
  errorsList.innerHTML = "";
  if (!errors.length) {
    errorsSection.classList.add("hidden");
    return;
  }
  for (const err of errors) {
    const li = document.createElement("li");
    li.textContent = `${err.code}: ${err.reason}`;
    errorsList.append(li);
  }
  errorsSection.classList.remove("hidden");
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/* Subir archivo */
fileInput.addEventListener("change", () => {
  const file = fileInput.files && fileInput.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    textInput.value = reader.result;
    updateButtons();
  };
  reader.readAsText(file);
});

["dragenter", "dragover"].forEach((evt) =>
  drop.addEventListener(evt, (e) => {
    e.preventDefault();
    drop.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  drop.addEventListener(evt, (e) => {
    e.preventDefault();
    drop.classList.remove("dragover");
  })
);
drop.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) fileInput.files = e.dataTransfer.files;
  fileInput.dispatchEvent(new Event("change"));
});

textInput.addEventListener("input", updateButtons);
generateBtn.addEventListener("click", () => generate({ zip: false }));
zipBtn.addEventListener("click", () => generate({ zip: true }));

updateButtons();
loadComponents();