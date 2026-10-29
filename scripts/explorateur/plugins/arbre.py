"""Extension Datasette de l'explorateur (#1389 suite, 29/10/2026).

La colonne `document` de la table `documents` s'affiche en arborescence
repliable, construite nœud par nœud au clic : un profil de 6 Mo s'ouvre en moins
d'une seconde, parce que rien n'est dessiné avant d'être déplié.
"""
import json
from datasette import hookimpl
from markupsafe import Markup

compteur = {"n": 0}


@hookimpl
def render_cell(value, column, table, database, datasette):
    if table != "documents" or column != "document" or not isinstance(value, str):
        return None
    compteur["n"] += 1
    ident = f"arbre{compteur['n']}"
    taille = len(value.encode("utf-8")) / 1e6
    charge = value.replace("</", "<\\/")
    return Markup(
        f'<div class="arbre" data-source="{ident}"><em>{taille:.1f} Mo</em></div>'
        f'<script type="application/json" id="{ident}">{charge}</script>'
    )


@hookimpl
def extra_body_script():
    return """
(function () {
  const style = document.createElement('style');
  style.textContent = `.arbre{font:13px/1.5 ui-monospace,monospace;white-space:normal}
  .arbre details{margin-left:1.2em}.arbre summary{cursor:pointer}
  .arbre .k{color:#8a3b12}.arbre .s{color:#1a6b2b}.arbre .n{color:#1d4ed8}.arbre .z{color:#888}
  .arbre .f{margin-left:1.2em}`;
  document.head.appendChild(style);
  const resume = v => Array.isArray(v) ? `[${v.length}]` : (v && typeof v === 'object') ? `{${Object.keys(v).length}}` : '';
  function feuille(v) {
    const s = document.createElement('span');
    if (v === null) { s.className = 'z'; s.textContent = 'null'; }
    else if (typeof v === 'string') { s.className = 's'; s.textContent = JSON.stringify(v); }
    else { s.className = 'n'; s.textContent = String(v); }
    return s;
  }
  function noeud(cle, v, ouvert) {
    if (v === null || typeof v !== 'object') {
      const d = document.createElement('div'); d.className = 'f';
      const k = document.createElement('span'); k.className = 'k'; k.textContent = cle + ' : ';
      d.append(k, feuille(v)); return d;
    }
    const det = document.createElement('details');
    const sum = document.createElement('summary');
    const k = document.createElement('span'); k.className = 'k'; k.textContent = cle;
    sum.append(k, ' ' + resume(v)); det.append(sum);
    let fait = false;
    const remplir = () => {
      if (fait) return; fait = true;
      const entrees = Array.isArray(v) ? v.map((x, i) => [i, x]) : Object.entries(v);
      const max = 500;
      entrees.slice(0, max).forEach(([c, x]) => det.append(noeud(c, x, false)));
      if (entrees.length > max) {
        const plus = document.createElement('div'); plus.className = 'f z';
        plus.textContent = `… ${entrees.length - max} de plus (voir la table correspondante)`;
        det.append(plus);
      }
    };
    det.addEventListener('toggle', () => det.open && remplir());
    if (ouvert) { det.open = true; remplir(); }
    return det;
  }
  document.querySelectorAll('.arbre[data-source]').forEach(div => {
    const src = document.getElementById(div.dataset.source);
    if (!src) return;
    try { div.append(noeud('document', JSON.parse(src.textContent), true)); } catch (e) { div.append(' (illisible)'); }
  });
})();
"""
