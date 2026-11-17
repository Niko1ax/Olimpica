(function () {
  'use strict';
  const metodo = document.getElementById('id_metodo');
  const panel = document.getElementById('rp-mercadopago');
  const qr = document.getElementById('rp-codigo-qr');
  const aviso = document.getElementById('rp-qr-faltante');
  if (!metodo || !panel || !qr || !aviso) return;

  const rutaQR = panel.dataset.qrSrc;
  let qrCargado = false;
  qr.addEventListener('load', function () {
    qrCargado = true;
    qr.hidden = false;
    aviso.hidden = true;
  });
  qr.addEventListener('error', function () {
    qrCargado = false;
    qr.hidden = true;
    aviso.hidden = false;
  });

  function actualizarMetodo() {
    const esMP = metodo.value === 'MERCADO_PAGO';
    panel.hidden = !esMP;
    if (esMP && !qr.getAttribute('src')) {
      aviso.hidden = false;
      qr.src = rutaQR;
    } else if (esMP) {
      qr.hidden = !qrCargado;
      aviso.hidden = qrCargado;
    }
  }
  metodo.addEventListener('change', actualizarMetodo);
  actualizarMetodo();

  // Muestra cifras en formato de Argentina sin alterar valores del formulario/Django.
  document.querySelectorAll('.rp-monto[data-monto]').forEach(function (elemento) {
    const valor = elemento.dataset.monto;
    if (!/^\d+(?:[.,]\d{1,2})?$/.test(valor)) return;
    const numero = Number(valor.replace(',', '.'));
    if (!Number.isFinite(numero)) return;
    elemento.textContent = new Intl.NumberFormat('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(numero);
  });
})();
