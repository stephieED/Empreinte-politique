/* ── Les nombres d'une rangée de tableau, écrits sous sa barre (#1372) ────────
 *
 * Trois tableaux de même modèle — un intitulé, une barre, deux nombres sous une
 * rangée d'en-têtes — se lisent mal à 390 px : l'en-tête se casse sur trois
 * lignes, l'intitulé est tronqué, et la barre des actes avait dû sauter. Au
 * téléphone (forme B, arbitrée le 28/10/2026), l'en-tête disparaît et chaque
 * rangée écrit ses nombres sous sa barre, suivis des mots de l'en-tête :
 * « 2 564 amendements · 2 textes distincts ». Aucun mot nouveau : ce sont ceux
 * de l'en-tête, accordés au singulier quand le nombre vaut 1.
 *
 * La ligne est toujours rendue et masquée au-delà de 720 px par la feuille de
 * style ; les cellules de colonne, elles, sont masquées en deçà. Chaque nombre
 * n'est donc présent qu'une fois à l'écran — et pour un lecteur d'écran.
 *
 * `chiffres` : [{ texte, n, pluriel, singulier }] — `texte` est ce qu'affiche
 * la colonne (« 7 / 39 », « — »), `n` le nombre qui décide de l'accord. */
import './ChiffresDeLigne.css';

export default function ChiffresDeLigne({ chiffres }) {
  return (
    <span className="chiffres-ligne">
      {chiffres.map((c, k) => (
        <span key={c.pluriel}>
          {k > 0 && ' · '}
          <b>{c.texte}</b> {c.n === 1 ? c.singulier : c.pluriel}
        </span>
      ))}
    </span>
  );
}
