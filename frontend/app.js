
/* El control de contraste es visual: siempre parte del mapa sin amplificar. */
let elaRawPixels = null;
const elaSlider = document.querySelector("#ela-scale");
function renderEla() {
  if (!elaRawPixels) return;
  const canvas = document.querySelector("#ela-canvas");
  const ctx = canvas.getContext("2d");
  const pixels = new ImageData(new Uint8ClampedArray(elaRawPixels.data), elaRawPixels.width, elaRawPixels.height);
  const factor = Number(elaSlider.value);
  for (let i = 0; i < pixels.data.length; i += 4) {
    for (let channel = 0; channel < 3; channel++) {
      pixels.data[i + channel] = Math.min(255, Math.round(elaRawPixels.data[i + channel] * factor));
    }
  }
  ctx.putImageData(pixels, 0, 0);
  document.querySelector("#ela-scale-value").textContent = "×" + factor;
}
elaSlider.addEventListener("input", renderEla);
function loadElaRawMap(base64) {
  elaRawPixels = null;
  const image = new Image();
  image.onload = () => {
    const canvas = document.querySelector("#ela-canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const ctx = canvas.getContext("2d", {willReadFrequently: true});
    ctx.drawImage(image, 0, 0);
    elaRawPixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
    renderEla();
  };
  image.onerror = () => {
    document.querySelector("#status").textContent = "No se pudo mostrar el mapa ELA.";
    document.querySelector("#status").classList.add("error");
  };
  image.src = "data:image/png;base64," + base64;
}


function drawHistogram(canvasId, series) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  const left = 42, right = 12, top = 18, bottom = 35;
  const pw = w - left - right, ph = h - top - bottom;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#0d1726";
  ctx.fillRect(0, 0, w, h);
  const maxValue = Math.max(1, ...series.flatMap(s => s.data));
  ctx.strokeStyle = "#26394e"; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = top + ph * i / 4;
    ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(left + pw, y); ctx.stroke();
  }
  ctx.font = "13px system-ui"; ctx.fillStyle = "#a4b3c7"; ctx.textAlign = "center";
  for (const intensity of [0, 64, 128, 192, 255]) {
    const x = left + (intensity / 255) * pw;
    ctx.fillText(String(intensity), x, h - 12);
  }
  for (const item of series) {
    ctx.strokeStyle = item.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    item.data.forEach((value, i) => {
      const x = left + (i / 255) * pw;
      const y = top + ph - (value / maxValue) * ph;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
}

const form = document.querySelector("#analyze-form");
const photo = document.querySelector("#photo");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const original = document.querySelector("#original");
const edges = document.querySelector("#edges");
const dimensions = document.querySelector("#dimensions");
const dropzone = document.querySelector("#dropzone");
const fileTitle = document.querySelector("#file-title");
const fileSubtitle = document.querySelector("#file-subtitle");
let previousObjectUrl = null;

function showSelectedFile(file) {
  if (!file) return;
  fileTitle.textContent = file.name;
  fileSubtitle.textContent = (file.size / 1048576).toFixed(2) + " MB · Listo para analizar";
  results.hidden = true;
  status.textContent = "";
  status.classList.remove("error");
}
photo.addEventListener("change", () => showSelectedFile(photo.files?.[0]));
dropzone.addEventListener("keydown", event => {
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); photo.click(); }
});
dropzone.addEventListener("dragover", event => { event.preventDefault(); dropzone.classList.add("dragging"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
dropzone.addEventListener("drop", event => {
  event.preventDefault();
  dropzone.classList.remove("dragging");
  const file = event.dataTransfer?.files?.[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  photo.files = transfer.files;
  showSelectedFile(file);
});

form.addEventListener("submit", async event => {
  event.preventDefault();
  results.hidden = true;
  const file = photo.files?.[0];
  if (!file) return;
  status.classList.remove("error");
  if (file.size > 12 * 1024 * 1024 || !["image/jpeg", "image/png"].includes(file.type)) {
    status.textContent = "Seleccioná una fotografía JPEG o PNG de hasta 12 MB.";
    status.classList.add("error");
    return;
  }
  const button = document.querySelector("#analyze-button");
  button.disabled = true;
  status.textContent = "Analizando imagen en el servidor...";
  const formData = new FormData();
  formData.append("file", file);
  try {
    const base = (window.IMAGE_FORENSICS_API_URL || "").replace(/\/$/, "");
    const response = await fetch(base + "/api/analyze", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "No se pudo procesar la imagen.");
    if (previousObjectUrl) URL.revokeObjectURL(previousObjectUrl);
    previousObjectUrl = URL.createObjectURL(file);
    original.src = previousObjectUrl;
    edges.src = "data:image/png;base64," + data.edge_map_png_base64;
    dimensions.textContent = data.width + " × " + data.height + " px · " + data.method;
    if (data.histograms) {
      drawHistogram("rgb-hist", [
        {data:data.histograms.red, color:"#ff7070"},
        {data:data.histograms.green, color:"#64e2a5"},
        {data:data.histograms.blue, color:"#67aeff"}
      ]);
      drawHistogram("gray-hist", [{data:data.histograms.gray, color:"#d3e5f6"}]);
    }
    const filterResults = document.querySelector("#filter-results");
    if (data.filters) {
      document.querySelector("#gaussian").src = "data:image/png;base64," + data.filters.gaussian_png_base64;
      document.querySelector("#median").src = "data:image/png;base64," + data.filters.median_png_base64;
      document.querySelector("#residual").src = "data:image/png;base64," + data.filters.residual_png_base64;
      document.querySelector("#residual-metric").textContent = "Diferencia media absoluta: " + data.filters.residual_mean + " niveles de intensidad (antes de amplificar)";
      filterResults.hidden = false;
    } else { filterResults.hidden = true; }
    const elaResults = document.querySelector("#ela-results");
    if (data.ela?.raw_map_png_base64) {
      document.querySelector("#ela-original").src = previousObjectUrl;
      document.querySelector("#ela-mae").textContent = String(data.ela.mean_absolute_error);
      document.querySelector("#ela-suggested").textContent = "×" + data.ela.suggested_scale;
      const slider = document.querySelector("#ela-scale");
      slider.value = String(Math.max(1, Math.min(64, Math.round(data.ela.suggested_scale))));
      loadElaRawMap(data.ela.raw_map_png_base64);
      elaResults.hidden = false;
    } else { elaResults.hidden = true; }
    results.hidden = false;
    status.textContent = "Bordes, histogramas, filtros y ELA procesados.";
    results.scrollIntoView({behavior:"smooth",block:"start"});
  } catch (error) {
    status.textContent = "No se pudo completar el análisis. " + error.message;
    status.classList.add("error");
  } finally { button.disabled = false; }
});