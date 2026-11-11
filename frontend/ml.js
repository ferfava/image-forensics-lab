/* Módulo ML experimental: siempre muestra estado real del backend. */
const mlForm = document.querySelector("#ml-form");
const mlButton = document.querySelector("#ml-button");
const mlAvailability = document.querySelector("#ml-availability");
const mlStatus = document.querySelector("#ml-status");
const mlResults = document.querySelector("#ml-results");
const mlPhoto = document.querySelector("#ml-photo");
const mlBase = (window.IMAGE_FORENSICS_API_URL || "").replace(/\/$/, "");

async function checkMlAvailability() {
  mlButton.disabled = true;
  mlAvailability.textContent = "Comprobando si el modelo está instalado…";
  try {
    const response = await fetch(mlBase + "/api/ml/status");
    if (!response.ok) throw new Error("Estado ML no disponible.");
    const status = await response.json();
    if (status.available === true) {
      mlAvailability.textContent = "Modelo " + status.model +
        " instalado · Modo exclusivamente experimental, no validado.";
      mlButton.disabled = false;
    } else {
      mlAvailability.textContent = "Módulo ML no habilitado en este servidor. " +
        (status.reason || "El modelo debe instalarse de forma segura.");
    }
  } catch (error) {
    mlAvailability.textContent = "No se pudo verificar la disponibilidad del ML. " +
      "El laboratorio clásico sigue funcionando.";
  }
}

mlForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = mlPhoto.files?.[0];
  if (!file || mlButton.disabled) return;
  mlResults.hidden = true;
  mlStatus.classList.remove("error");
  if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 12 * 1024 * 1024) {
    mlStatus.textContent = "Seleccioná un JPEG o PNG de hasta 12 MB.";
    mlStatus.classList.add("error");
    return;
  }
  mlButton.disabled = true;
  mlStatus.textContent = "Extrayendo características y clasificando parches…";
  try {
    const payload = new FormData();
    payload.append("file", file);
    const response = await fetch(mlBase + "/api/ml/predict", {method:"POST", body:payload});
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ?
      data.detail : "No se pudo analizar la imagen.");
    if (data.status !== "EXPERIMENTAL_NO_VALIDADO") {
      throw new Error("Respuesta incompatible con el protocolo experimental.");
    }
    document.querySelector("#ml-overlay").src = "data:image/png;base64," + data.overlay_png_base64;
    document.querySelector("#ml-mask").src = "data:image/png;base64," + data.mask_png_base64;
    document.querySelector("#ml-percent").textContent = Number(data.suspect_percent).toFixed(2) + " %";
    document.querySelector("#ml-model").textContent = data.model;
    mlStatus.textContent = "Predicción exploratoria generada. NO determina autenticidad.";
    mlResults.hidden = false;
    mlResults.scrollIntoView({behavior:"smooth",block:"start"});
  } catch (error) {
    mlStatus.textContent = "No se pudo ejecutar el modelo: " + error.message;
    mlStatus.classList.add("error");
  } finally {
    mlButton.disabled = false;
  }
});
checkMlAvailability();
