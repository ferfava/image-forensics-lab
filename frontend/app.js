const form = document.querySelector("#analyze-form");
const photo = document.querySelector("#photo");
const status = document.querySelector("#status");
const results = document.querySelector("#results");
const original = document.querySelector("#original");
const edges = document.querySelector("#edges");
const dimensions = document.querySelector("#dimensions");
let previousObjectUrl = null;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  results.hidden = true;
  const file = photo.files?.[0];
  if (!file) return;
  if (file.size > 12 * 1024 * 1024 || !["image/jpeg", "image/png"].includes(file.type)) {
    status.textContent = "Seleccioná un archivo JPEG o PNG de hasta 12 MB.";
    return;
  }
  const button = form.querySelector("button");
  button.disabled = true;
  status.textContent = "Procesando imagen...";
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
    dimensions.textContent = data.width + " × " + data.height + " píxeles · " + data.method;
    results.hidden = false;
    status.textContent = "Análisis exploratorio completado.";
  } catch (error) {
    status.textContent = "Error: " + error.message + " Revisá que el backend esté activo y la URL configurada.";
  } finally {
    button.disabled = false;
  }
});
