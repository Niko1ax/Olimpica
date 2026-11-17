// Solo lee los datos de la página; no modifica reservas ni acciones de Django.
document.addEventListener("DOMContentLoaded", () => {
  const canchas = Array.from(document.querySelectorAll(".admin-complejos-nuevo .ac-cancha"));
  const total = document.getElementById("ac-total-canchas");
  const activas = document.getElementById("ac-canchas-activas");
  if (total) total.textContent = String(canchas.length);
  if (activas) activas.textContent = String(canchas.filter((cancha) => cancha.dataset.activa === "true").length);

  const formato = new Intl.NumberFormat("es-AR", {maximumFractionDigits: 2});
  for (const precio of document.querySelectorAll(".admin-complejos-nuevo [data-importe]")) {
    const valor = String(precio.dataset.importe).trim().replace(",", ".");
    if (!/^\d+(?:\.\d+)?$/.test(valor)) continue;
    const numero = Number(valor);
    if (Number.isFinite(numero)) precio.textContent = "$" + formato.format(numero);
  }
});
