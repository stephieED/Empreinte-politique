import { useEffect } from 'react';

// Permet de faire défiler un conteneur horizontal à la souris (drag),
// en plus du scroll natif (molette+shift, trackpad, swipe tactile).
// La capture du pointeur n'est déclenchée qu'une fois un vrai glissement
// détecté (seuil de mouvement), pour ne jamais perturber un simple clic
// sur les chips à l'intérieur du conteneur.
export function useDragScroll(ref) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let tracking = false;
    let dragging = false;
    let pointerId = null;
    let startX = 0;
    let startScrollLeft = 0;

    const onPointerDown = (e) => {
      if (e.pointerType !== 'mouse') return;
      tracking = true;
      dragging = false;
      pointerId = e.pointerId;
      startX = e.clientX;
      startScrollLeft = el.scrollLeft;
    };

    const onPointerMove = (e) => {
      if (!tracking) return;
      const delta = e.clientX - startX;
      if (!dragging && Math.abs(delta) > 4) {
        dragging = true;
        el.setPointerCapture(pointerId);
        el.classList.add('is-dragging');
      }
      if (dragging) el.scrollLeft = startScrollLeft - delta;
    };

    const onClickCapture = (e) => {
      if (dragging) {
        e.preventDefault();
        e.stopPropagation();
      }
    };

    const endDrag = () => {
      tracking = false;
      dragging = false;
      el.classList.remove('is-dragging');
    };

    el.addEventListener('pointerdown', onPointerDown);
    el.addEventListener('pointermove', onPointerMove);
    el.addEventListener('pointerup', endDrag);
    el.addEventListener('pointerleave', endDrag);
    el.addEventListener('click', onClickCapture, true);

    return () => {
      el.removeEventListener('pointerdown', onPointerDown);
      el.removeEventListener('pointermove', onPointerMove);
      el.removeEventListener('pointerup', endDrag);
      el.removeEventListener('pointerleave', endDrag);
      el.removeEventListener('click', onClickCapture, true);
      if (dragging && pointerId !== null) {
        try { el.releasePointerCapture(pointerId); } catch (_) { /* element peut être détaché */ }
      }
    };
  }, [ref]);
}
