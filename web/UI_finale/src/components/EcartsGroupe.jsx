/* ── « Ses divergences », par scrutin (#328) ──────────────────────────────────
 *
 * Le composant ne calcule rien qui soit un fait : la bande, les divergences et
 * la dispersion du groupe arrivent construites par `utils/ecartsGroupe.js`. Il
 * ne décide ici que de ce qui est montré à l'écran.
 *
 * Maquette validée le 08/09/2026 (artefact « Lui, dans le vote de son groupe »).
 */
import { VOTE_STYLE, formatNumber, pageDuJeuDeDonnees } from '../utils/lecture';
import { groupeDivise, partDissidente } from '../utils/ecartsGroupe';
import { Link } from 'react-router-dom';
import './EcartsGroupe.css';

const jour = (d) => (d ? `${d.slice(8, 10)}/${d.slice(5, 7)}/${d.slice(0, 4)}` : '');
const mois = (d) => (d ? `${d.slice(0, 4)}/${d.slice(5, 7)}` : '');
const LIBELLE = { pour: 'Pour', contre: 'Contre', abstention: 'Abstention' };
const teinte = (p) => VOTE_STYLE[p]?.color ?? null;

/* La période de couverture d'une fiche, pas le nombre de scrutins qu'elle
 * partage : c'est la DURÉE sur laquelle la comparaison est possible, le seul
 * rôle de cette ligne. Une fiche encore ouverte affiche « en cours » plutôt
 * qu'une date de fin inventée. */
function couverture(f) {
  if (!f.debut) {
    return f.legislature ? `${f.legislature}ᵉ législature` : 'période non publiée';
  }
  return `${mois(f.debut)} → ${f.fin ? mois(f.fin) : 'en cours'}`;
}

/* L'infobulle d'une DIVERGENCE nomme le texte et son thème : sans eux, un point
 * cerclé n'est qu'une date, et il faut descendre dans la liste pour savoir de
 * quoi il s'agit. Les autres colonnes n'ont pas de texte à nommer — elles ne
 * portent que la composition du groupe ce jour-là. */
function infobulle(x) {
  const groupe =
    `${x.pour} pour, ${x.contre} contre, ${x.abstention} abstention, `
    + `${x.absents} absents ou non-votants sur ${x.membresEligibles} éligibles`;
  if (!x.ecart) {
    return `${jour(x.date)} · ${groupe} · sa position : ${LIBELLE[x.position]}`;
  }
  return `${jour(x.date)} · ${x.matiere || 'matière non établie'} · ${x.texte}`
    + ` — sa position : ${LIBELLE[x.position]}, celle de son groupe :`
    + ` ${LIBELLE[x.positionGroupe]} · ${groupe}`;
}

/* ── La bande ────────────────────────────────────────────────────────────────
 *
 * TROIS FAITS, TROIS ÉLÉMENTS, et jamais deux faits sur le même. Deux
 * encodages ont été essayés et portaient la même incohérence : la colonne était
 * COLORÉE par la position majoritaire du groupe alors que sa HAUTEUR comptait
 * les votes qui ne la suivaient pas — deux faits opposés sur un seul objet.
 *
 * Les étiquettes sont posées À GAUCHE, à la hauteur exacte du rang qu'elles
 * nomment : une légende sous un graphique oblige à l'aller-retour, on lit un
 * symbole, on descend, on remonte. Ce que la gouttière prend en largeur est
 * rendu par l'écart entre colonnes, ramené à 1 px — mesuré à 1 000 px de page,
 * une colonne passe de 2,97 px à 3,03 px.
 */
/* SEULE UNE DIVERGENCE EST CLIQUABLE. Une colonne ordinaire ne mène nulle part :
 * aucune ligne ne lui correspond en bas. Un objet qui a l'air interactif et ne
 * réagit pas est pire qu'un objet inerte — il fait douter de la figure entière.
 * Les colonnes ordinaires gardent leur infobulle, qui ne promet rien. */
function Bande({ bande }) {
  const versLaLigne = (scrutinId) => {
    const cible = document.getElementById(`eg-lg-${scrutinId}`);
    if (cible) cible.scrollIntoView({ block: 'center', behavior: 'smooth' });
  };

  return (
    <>
      <div className="eg-zone">
        <div className="eg-etiq">
          <span>ses positions divergentes</span>
          <span>membres qui n’ont pas suivi</span>
          <span>ce qu’a voté son groupe</span>
        </div>
        <div className="eg-bande">
          {bande.map((x) => {
            const dedans = (
              <>
                <span
                  className="eg-lui"
                  style={x.ecart ? { background: teinte(x.position) } : undefined}
                />
                <span
                  className="eg-part"
                  style={{ height: `${(partDissidente(x) * 44).toFixed(1)}px` }}
                />
                <span className="eg-socle" style={{ background: teinte(x.positionGroupe) }} />
              </>
            );
            return x.ecart ? (
              <button
                type="button"
                className="eg-col eg-col--ecart"
                key={x.scrutinId}
                title={infobulle(x)}
                onClick={() => versLaLigne(x.scrutinId)}
              >
                {dedans}
              </button>
            ) : (
              <span className="eg-col" key={x.scrutinId} title={infobulle(x)}>
                {dedans}
              </span>
            );
          })}
        </div>
      </div>
      <p className="eg-axe cp-num">
        <span>{jour(bande[0].date)}</span>
        <span>{jour(bande[bande.length - 1].date)}</span>
      </p>
      <div className="eg-cles">
        <span className="eg-cles-quoi">Position majoritaire du groupe</span>
        {['pour', 'contre', 'abstention'].map((p) => (
          <span className="eg-cle" key={p}>
            <i style={{ background: teinte(p) }} />
            {p}
          </span>
        ))}
        {/* Sous 720 px la gouttière ne tient plus : les étiquettes redeviennent
            une légende, jamais affichée en même temps que la gouttière. */}
        <span className="eg-cle eg-cle--rang">
          <i className="eg-cle-socle" /> ce qu’a voté son groupe
        </span>
        <span className="eg-cle eg-cle--rang">
          <i className="eg-cle-part" /> membres qui n’ont pas suivi
        </span>
        <span className="eg-cle eg-cle--rang">
          <i className="eg-cle-point" /> ses positions divergentes
        </span>
      </div>
    </>
  );
}

/* Télégraphique, parce que la barre à droite dit déjà la répartition. Le seul
 * fait que le dessin ne porte pas est COMBIEN ILS SONT à tenir sa position :
 * « l'un des 14 » et « le seul » ne se lisent pas dans une largeur, et ils
 * changent le sens de la divergence. Le nombre en face est celui de la position
 * MAJORITAIRE, quelle qu'elle soit — écrire « pour » systématiquement serait
 * faux dès que le groupe s'abstient. */
function lecture(x) {
  const compte = { pour: x.pour, contre: x.contre, abstention: x.abstention };
  const sien = compte[x.position];
  const majoritaires = compte[x.positionGroupe];
  return `${sien > 1 ? `l’un des ${formatNumber(sien)}` : 'le seul'} de son groupe`
    + ` · face à ${formatNumber(majoritaires)} ${LIBELLE[x.positionGroupe].toLowerCase()}`
    + ` · ${formatNumber(x.pour + x.contre + x.abstention)} exprimés sur ${formatNumber(x.membresEligibles)}`;
}

function Ligne({ x }) {
  const parts = [
    ['pour', x.pour],
    ['contre', x.contre],
    ['abstention', x.abstention],
  ];
  /* Le centre de SA part, en % de la barre entière — les absents compris, parce
     que la barre les montre : les retirer du dénominateur décalerait le repère
     de tout ce que leur segment occupe. */
  const total = parts.reduce((n, [, v]) => n + v, 0) + (x.absents || 0);
  const centre = (() => {
    if (!total) return null;
    let avant = 0;
    for (const [p, n] of parts) {
      if (p === x.position) return n ? ((avant + n / 2) / total) * 100 : null;
      avant += n;
    }
    return null;
  })();
  return (
    <div className="eg-lg" id={`eg-lg-${x.scrutinId}`}>
      <div className="eg-lg-date cp-num">{jour(x.date)}</div>
      <div>
        <p className="eg-lg-titre">
          {x.sourceUrl ? (
            <a href={pageDuJeuDeDonnees(x.sourceUrl)} target="_blank" rel="noreferrer">
              {x.texte}
            </a>
          ) : (
            x.texte
          )}
        </p>
        <p className="eg-lg-lit" style={{ color: teinte(x.position) }}>
          {LIBELLE[x.position]} <span>· {lecture(x)}</span>
        </p>
        <div className="eg-lg-puces">
          <span className="eg-puce">
            {x.groupe}
            {x.legislature ? ` · ${x.legislature}ᵉ législature` : ''}
          </span>
          {/* Le thème est TOUJOURS affiché, absent compris : une puce qui
              disparaît se lirait comme un texte sans commission saisie au fond,
              alors que c'est notre rattachement qui manque (§2 règle 5). */}
          <span className="eg-puce">{x.matiere || 'matière non établie'}</span>
          {x.sort && <span className="eg-puce">{x.sort}</span>}
          {/* « Quorum non atteint » est un mot de règlement, pas une
              information : il ne dit ni le seuil, ni sur quoi il porte. Ce que
              le lecteur doit comprendre est que la « position majoritaire »
              repose ici sur une poignée de membres (§2 règle 7). */}
          {!x.quorum && (
            <span className="eg-puce eg-puce--alerte">
              moins de la moitié du groupe s’est exprimée
            </span>
          )}
        </div>
      </div>
      <div className="eg-lg-barre">
        <span className="eg-rang">
          {parts.map(([p, n]) => (n ? (
            <span key={p} style={{ flex: n, background: teinte(p) }} />
          ) : null))}
          {x.absents ? <span className="eg-rang-absent" style={{ flex: x.absents }} /> : null}
        </span>
        {/* OÙ SA VOIX SE SITUE DANS CELLE DE SON GROUPE. Le repère se pose au
            CENTRE de la part qu'il a rejointe, et il porte la TEINTE DE SON
            VOTE — arbitré par la propriétaire le 25/09/2026, contre la lecture
            qui le voulait en encre au motif que les trois teintes sont prises
            par les positions.

            Il est donc de la même couleur que le segment sous lui : sans relief
            il y disparaîtrait. Deux choses l'en détachent, et aucune n'est
            décorative — il DÉBORDE la barre en haut et en bas, et il porte un
            anneau de la couleur du fond.

            `null` quand la part est vide : un repère posé au hasard dirait une
            position qu'il n'a pas prise (§2 règle 5). */}
        {centre === null ? null : (
          <span
            className="eg-rang-sien"
            style={{ left: `${centre}%`, background: teinte(x.position) }}
          />
        )}
      </div>
    </div>
  );
}

/* ── Les vides : trois causes, jamais confondues ─────────────────────────────
 *
 * Les deux premières sont des faits sur NOTRE couverture, la troisième un fait
 * sur la personne. Les confondre ferait lire « aucune fiche n'est publiée »
 * comme « il n'a jamais divergé » (§2 règle 5).
 */
function Vide({ ecarts, voix }) {
  if (!ecarts.fiches.length) {
    return (
      <div className="eg-vide">
        <h3>Rien n’est comparable — ce n’est pas la même chose qu’« aucune divergence »</h3>
        <p>
          Aucune fiche de groupe n’est publiée pour les groupes où {voix.pronom} a siégé. Il n’y a
          donc <b>rien à comparer</b> : la section ne dit rien de ses votes.
        </p>
      </div>
    );
  }
  return (
    <div className="eg-vide">
      <h3>Les fiches publiées ne recouvrent aucun de ses votes sur l’ensemble d’un texte</h3>
      <p>
        {ecarts.fiches.map((f, i) => (
          <span key={`${f.sigle}-${f.legislature}`}>
            {i > 0 ? ' ; ' : ''}
            <b>{f.sigle}</b> · {couverture(f)}
          </span>
        ))}
        . La comparaison est <b>vide de base</b>, pas de divergence.
      </p>
    </div>
  );
}

/* `etiquette` (#979) : le rappel du mot du filtre, en tête de la première carte. */
export default function EcartsGroupe({ ecarts, voix, etiquette = null }) {
  const { bande, fiches } = ecarts;

  return (
    <>
      <div className="cp-carte eg-carte">
        {etiquette}
        {bande.length ? (
          <>
            <div className="eg-bloc">
              <div className="eg-bloc-tete">
                <h4>Ce qui est comparable</h4>
                {fiches.length > 0 && (
                  <p className="eg-groupes">
                    <span>Ses groupes parlementaires</span>
                    {fiches.map((f, i) => (
                      <span key={`${f.sigle}-${f.legislature}`}>
                        {i > 0 ? ' · ' : ''}
                        <b>{f.sigle}</b> · {couverture(f)}
                      </span>
                    ))}
                  </p>
                )}
              </div>
              <dl className="eg-dl">
                <dt>
                  <b>Scrutins utilisés pour la comparaison</b>
                  <em>
                    scrutins sur l’ensemble d’un texte où les données sont complètes ·{' '}
                    <Link to="/methodologie#ecarts">comment ils sont retenus</Link>
                  </em>
                </dt>
                <dd className="eg-fort">{formatNumber(bande.length)}</dd>
                <dt>
                  <b>Scrutins où son groupe s’est divisé</b>
                  <em>
                    ses membres exprimés n’ont pas tous voté de la même façon ·{' '}
                    <Link to="/methodologie#ecarts">le détail</Link>
                  </em>
                </dt>
                <dd className="eg-fort">{formatNumber(bande.filter(groupeDivise).length)}</dd>
              </dl>
            </div>

            <div className="eg-bloc">
              <h4>Ses positions par rapport au groupe, scrutin après scrutin</h4>
              {/* PLUS DE PHRASE DESCRIPTIVE SOUS LE TITRE. Elle nommait les trois
                  rangs — ce que les étiquettes posées contre la figure disent
                  maintenant, à la hauteur exacte de ce qu'elles nomment. Une
                  phrase qui répète des étiquettes fait lire la consigne à la
                  place du dessin.

                  CE QUI RESTE, et seulement dans ce cas : quand la personne ne
                  diverge JAMAIS, un rang de repères sans aucun point ne se
                  distingue pas d'un rang qui n'a pas fini de charger. La carte
                  des scrutins n'existe alors pas non plus, et rien à l'écran ne
                  porterait le fait (§2 règle 5). */}
              {ecarts.ecarts.length === 0 && (
                <p className="eg-dit">
                  Sur ces scrutins, <b>sa position ne s’écarte jamais</b> de celle de la majorité
                  de son groupe.
                </p>
              )}
              <Bande bande={bande} />
            </div>
          </>
        ) : (
          <div className="eg-bloc">
            <Vide ecarts={ecarts} voix={voix} />
          </div>
        )}
      </div>

      {ecarts.ecarts.length > 0 && (
        <div className="cp-carte eg-carte">
          {/* « MAJORITAIRE » SEUL SE LIT COMME LA MAJORITÉ DE L'ASSEMBLÉE, ce qui
          serait un fait politique tout autre : la section compare sa position à
          celle de SON GROUPE. Le verbe reprend le mot de la légende juste en
          dessous — « membres qui n'ont pas suivi ». */}
      <h3 className="eg-titre">
        Les scrutins où {voix.pronom} n’a pas voté comme la majorité de son groupe
      </h3>
          <p className="eg-sous">
            Chacun avec la répartition réelle du groupe ce jour-là, et le sort du texte.
          </p>
          <div className="eg-lignes">
            {ecarts.ecarts.map((x) => (
              <Ligne x={x} key={x.scrutinId} />
            ))}
          </div>
        </div>
      )}
    </>
  );
}
