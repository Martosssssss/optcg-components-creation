"use strict";

const fileInput = document.getElementById("file-input");
const drop = document.querySelector(".drop");
const textInput = document.getElementById("text-input");
const generateBtn = document.getElementById("generate-btn");
const zipBtn = document.getElementById("zip-btn");
const statusEl = document.getElementById("status");
const errorsSection = document.getElementById("errors");
const errorsList = document.getElementById("errors-list");
const resultsGrid = document.getElementById("results");

let lastText = "";

function hasValidInput() {
  return textInput.value.trim().length > 0;
}

function updateButtons() {
  generateBtn.disabled = !hasValidInput();
  zipBtn.disabled = !hasValidInput();
}

function setStatus(message, isError) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", Boolean(isError));
}

async function generate({ zip } = {}) {
  const text = textInput.value.trim();
  if (!text) return;

  const url = zip ? "/api/generate/zip" : "/api/generate";
  const body = JSON.stringify({ text });

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
    lastText = textInput.value;
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