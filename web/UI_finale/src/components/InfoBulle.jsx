/* ── La bulle d'information d'un titre (revue d'ergonomie du 01/10/2026) ──────
 *
 * ELLE REMPLACE LES RENVOIS VERS LA MÉTHODOLOGIE. Chaque section portait le
 * sien, sous sa figure ou sous son titre — huit formes pour un même geste, et
 * autant de phrases que le lecteur traversait avant d'arriver au fait. La bulle
 * les range derrière un « i » posé à droite du titre : ce que la figure montre
 * en une phrase, la note qui empêche de mal la lire, et le lien vers la règle.
 *
 * AU CLIC, PAS AU SURVOL : un téléphone n'a pas de survol, et une limite qu'il
 * faut survoler n'est pas lue (DESIGN_SYSTEM §6). Le « i » est donc un vrai
 * bouton — `aria-expanded`, `aria-controls` —, qui se referme au second clic,
 * à Échap et au clic hors de la bulle.
 *
 * UNE SEULE BULLE OUVERTE À LA FOIS. Le clic hors de la bulle y suffirait à la
 * souris ; au clavier, on passe d'un « i » à l'autre sans jamais cliquer
 * ailleurs, et deux bulles ouvertes se recouvrent. Celle qui s'ouvre referme
 * donc la précédente, par le module et non par un contexte : une bulle n'a pas
 * à savoir dans quelle fiche elle est posée.
 *
 * LE BALISAGE EST EN `span`, ET CE N'EST PAS UNE COQUETTERIE : la bulle se pose
 * à côté d'un `h2` comme DANS le titre d'une carte, qui est un `span`. Des
 * paragraphes y seraient un balisage invalide ; la feuille leur rend leur
 * forme de bloc.
 *
 * L'ANCRE EST L'ANCÊTRE QUI PORTE `ib-ancre` : la bulle s'ouvre sous lui, à son
 * bord gauche. Sans cet ancêtre, elle se poserait contre la page entière.
 */
import { useEffect, useId, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import './InfoBulle.css';

/* La fermeture de la bulle actuellement ouverte, ou `null`. Une variable de
 * module, parce que l'état est celui de la PAGE : il n'y a qu'un écran. */
let fermerLaBulleOuverte = null;

/**
 * @param {string} sujet   Ce que la bulle décrit — le titre à côté duquel elle
 *                         est posée. Il nomme le bouton pour un lecteur d'écran.
 * @param {string} phrase  La première phrase, en gras : ce que la figure montre.
 * @param {string} note    La note, en corps normal — elle commence par « Note : ».
 * @param {Array}  liens   `{ libelle, vers }` pour une page du site,
 *                         `{ libelle, href }` pour une source extérieure.
 * @param {boolean} petite Le « i » de 17 px d'un titre de carte, au lieu des
 *                         20 px d'un titre de section.
 */
export default function InfoBulle({ sujet, phrase, note = null, liens = [], petite = false }) {
  const [ouverte, setOuverte] = useState(false);
  const racine = useRef(null);
  const bouton = useRef(null);
  const id = useId();

  useEffect(() => {
    if (!ouverte) return undefined;
    if (fermerLaBulleOuverte) fermerLaBulleOuverte();
    const fermer = () => setOuverte(false);
    fermerLaBulleOuverte = fermer;
    const surClic = (e) => {
      if (racine.current && !racine.current.contains(e.target)) fermer();
    };
    const surTouche = (e) => {
      if (e.key !== 'Escape') return;
      fermer();
      // Le focus revient au bouton : Échap ne doit pas renvoyer le lecteur au
      // clavier en haut de la page.
      bouton.current?.focus();
    };
    document.addEventListener('mousedown', surClic);
    document.addEventListener('keydown', surTouche);
    return () => {
      if (fermerLaBulleOuverte === fermer) fermerLaBulleOuverte = null;
      document.removeEventListener('mousedown', surClic);
      document.removeEventListener('keydown', surTouche);
    };
  }, [ouverte]);

  return (
    <span className="ib" ref={racine}>
      <button
        type="button"
        ref={bouton}
        className={`ib-bouton${petite ? ' ib-bouton--petit' : ''}`}
        aria-expanded={ouverte}
        aria-controls={id}
        aria-label={`Informations sur « ${sujet} »`}
        onClick={() => setOuverte((o) => !o)}
      >
        <span aria-hidden="true">i</span>
      </button>
      <span className="ib-bulle" id={id} hidden={!ouverte}>
        <span className="ib-phrase">{phrase}</span>
        {note && <span className="ib-note">{note}</span>}
        {liens.length > 0 && (
          <span className="ib-liens">
            {liens.map((l) => (l.href ? (
              <a href={l.href} key={l.libelle} target="_blank" rel="noreferrer">{l.libelle}</a>
            ) : (
              <Link key={l.libelle} to={l.vers}>{l.libelle}</Link>
            )))}
          </span>
        )}
      </span>
    </span>
  );
}

/* ── La bulle d'une pastille de commutateur (02/10/2026) ──────────────────────
 *
 * Quand un commutateur oppose deux versants — l'Assemblée et le Parlement
 * européen —, la règle de lecture n'est pas la même des deux côtés, et le
 * titre ne peut en porter qu'une. Chaque pastille porte donc la sienne : le
 * « i » est DANS la pastille, et le lecteur lit la règle d'un versant sans y
 * basculer.
 *
 * DEUX BOUTONS FRÈRES, PAS UN BOUTON DANS UN BOUTON — ce que HTML interdit.
 * L'enveloppe est l'ancre de la bulle ; la pastille garde sa place et réserve
 * à droite celle du « i », que la feuille pose par-dessus
 * (`ParolesParPeriode.css`, `.pp-pastille`). Cliquer le « i » n'active donc
 * jamais la pastille.
 *
 * `children` est une fonction : elle reçoit la classe à ajouter à la pastille
 * quand une bulle l'accompagne, et rend la pastille. Sans bulle, la pastille
 * est rendue seule, comme avant.
 */
export function BulleDePastille({ bulle = null, sujet, children }) {
  if (!bulle) return children('');
  return (
    <span className="pp-pastille ib-ancre">
      {children(' pp-qualite--bulle')}
      <InfoBulle petite sujet={sujet} {...bulle} />
    </span>
  );
}
