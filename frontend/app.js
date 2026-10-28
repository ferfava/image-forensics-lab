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
    results.hidden = false;
    status.textContent = "Análisis de bordes completado.";
    results.scrollIntoView({behavior:"smooth",block:"start"});
  } catch (error) {
    status.textContent = "No se pudo completar el análisis. " + error.message;
    status.classList.add("error");
  } finally { button.disabled = false; }
});