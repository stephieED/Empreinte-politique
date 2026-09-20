import { useState } from 'react';
import './FriseCouverture.css';

/* CE QUE LE DÉPÔT PORTE, ET DEPUIS QUAND — une frise, trois populations.
 *
 * DEUX AXES, ET UN SEUL EST UNE HIÉRARCHIE.
 * L'INSTITUTION structure la figure — Assemblée nationale, Gouvernement, Sénat,
 * Parlement européen, mandats locaux : c'est elle qui fait tenir dans une même
 * image ce que nous lisons et ce que nous ne lisons pas. Sous chaque
 * institution, ses listes ; sous chaque liste, ses champs.
 *
 * LA FICHE D'ORIGINE n'est ni un niveau ni une teinte : candidats,
 * gouvernements, groupes vivent dans le MÊME rail, une seule catégorie —
 * « données collectées » (11/09/2026). La teinte est celle de l'INSTITUTION,
 * la même que sur les fiches (`teintes-des-institutions-328`) : Assemblée
 * prune, Gouvernement ocre, Parlement européen bleu de l'Union. Le survol d'un
 * segment nomme encore la fiche d'où il vient.
 */

const AXE_DEBUT = 2000;
const GRADUATIONS = [2005, 2010, 2015, 2020, 2025];

/* Les institutions dont nous ne portons QUE le mandat. Un niveau de hiérarchie
 * pour une seule entité est un niveau de trop : elles n'ont pas de sous-partie,
 * la barre est sur leur titre.
 *
 * LES MANDATS LOCAUX SONT COLLECTÉS (#922). La ligne disait « aucune source » et
 * portait une hachure pleine ; le Répertoire national des élus les publie depuis
 * 2020, sur les candidats déclarés. Elle suit désormais la grammaire des autres :
 * hachure avant la borne de la source, un segment de la première donnée à la
 * collecte, le compte à droite. Sans donnée collectée, elle garde la hachure
 * pleine et « aucune source » — une ligne vide dirait « personne n'en a ». */
const SANS_ACTIVITE = [
  {
    cle: 'local',
    titre: 'Mandats locaux',
    quoi: 'Répertoire national des élus : les mandats locaux des candidats déclarés, publiés à partir de 2020.',
  },
];

const nb = (n) => n.toLocaleString('fr-FR').replace(/ | /g, ' ');
const jour = (d) => (d ? d.split('-').reverse().join('.') : '');
const enMois = (d) => Number(d.slice(0, 4)) * 12 + Number(d.slice(5, 7));

/* SEUIL DE LA HACHURE DE QUEUE : six mois. Un champ peut cesser d'être
 * renseigné sans que la liste s'arrête — le banc déclaré des appartenances de
 * groupe s'arrête trente-trois mois avant la fin des mandats (#770). Sans
 * hachure, ce vide se lit « plus personne n'a de groupe » au lieu de « la
 * source ne le déclare plus ». En dessous de six mois, l'écart n'est que le
 * décalage ordinaire d'un corpus arrêté à la dernière collecte : le hachurer
 * inventerait une lacune. */
const MOIS_AVANT_QUEUE = 6;

export default function FriseCouverture({ couverture }) {
  const [ouvertes, setOuvertes] = useState(() => new Set());
  const { hierarchie = [], institutions = [], bornes = {}, collecteLe } = couverture;

  const axeFin = Number(collecteLe.slice(0, 4)) + (Number(collecteLe.slice(5, 7)) - 1) / 12;
  const pos = (a) => Math.min(100, Math.max(0, ((a - AXE_DEBUT) / (axeFin - AXE_DEBUT)) * 100));
  const posDate = (d) => pos(Number(d.slice(0, 4)) + (Number(d.slice(5, 7)) - 1) / 12);

  const parInstitution = Object.fromEntries(institutions.map((i) => [i.cle, i]));
  const total = hierarchie.reduce(
    (s, i) => s + i.pistes.reduce((t, p) => t + p.couches.reduce((u, c) => u + c.total, 0), 0),
    0,
  );

  /* AVANT LA PREMIÈRE DONNÉE PUBLIABLE. À gauche de la borne, aucune source ne
   * publie : un blanc y dirait « rien fait » au lieu de « rien à lire ». La
   * borne dessinée est le PLUS TÔT des deux — la borne déclarée de la liste, et
   * la première donnée réellement portée. Une hachure ne passe jamais par-dessus
   * un fait. */
  const avantBorne = (piste) => {
    // Une piste qui déclare `borne: null` n'a pas de borne de source connue
    // (le Parlement européen) : rien n'est hachuré, plutôt qu'une hachure posée
    // sur sa première donnée, qui ne dirait rien.
    if ('borne' in piste && !piste.borne) return null;
    const b = piste.borne ?? bornes[piste.cle];
    const mini = piste.couches.reduce(
      (m, c) => (c.etendue && (!m || c.etendue[0] < m) ? c.etendue[0] : m),
      null,
    );
    const d = !b ? mini : (!mini || b < mini ? b : mini);
    if (!d) return null;
    const x = posDate(d);
    if (x <= 0) return null;
    return (
      <span
        className="fc-horssource"
        style={{ left: 0, width: `${x}%` }}
        title={`aucune donnée publiée avant le ${jour(d)}`}
      />
    );
  };

  /* La fin de la liste d'où vient un champ : c'est elle qui décide si la queue
   * mérite une hachure, pas la fin de la piste toutes origines confondues. */
  const finDe = (piste, origine) => {
    const c = piste.couches.find((x) => x.titre === origine);
    return c?.etendue ? c.etendue[1] : null;
  };

  const apresChamp = (etendue, finListe) => {
    if (!etendue || !finListe) return null;
    const f = etendue[1];
    if (!f || enMois(finListe) - enMois(f) < MOIS_AVANT_QUEUE) return null;
    return (
      <span
        className="fc-horssource"
        style={{ left: `${posDate(f)}%`, right: 0 }}
        title={`données non publiées après le ${jour(f)}`}
      />
    );
  };

  /* UN SEUL SEGMENT, DE LA PREMIÈRE À LA DERNIÈRE DONNÉE (#328, 15/09/2026).
   *
   * Il y en avait un par mois porteur. Les blancs entre eux ne parlaient pas de
   * la source mais des mois où aucun candidat déclaré n'était en fonction là —
   * jusqu'à 73 pour les textes portés de l'Assemblée —, et sur cette page ils se
   * lisaient comme des lacunes de collecte.
   *
   * `fc-seg--tronque` quand la donnée commence AVANT l'axe : le Sénat porte un
   * mandat depuis octobre 1986, quatorze ans avant `AXE_DEBUT`. Un bord arrondi
   * collé au zéro dirait « commence en 2000 », et c'est l'erreur exacte que #940
   * vient de corriger sur la borne de l'Assemblée. */
  const barres = (etendue) => {
    if (!etendue) return null;
    const [a, b] = etendue;
    const g = posDate(a);
    const h = posDate(b || collecteLe);
    const tronque = Number(a.slice(0, 4)) + (Number(a.slice(5, 7)) - 1) / 12 < AXE_DEBUT;
    return (
      <span
        className={`fc-seg${tronque ? ' fc-seg--tronque' : ''}`}
        style={{ left: `${g}%`, width: `${Math.max(0.6, h - g)}%` }}
        title={`${jour(a)} → ${jour(b || collecteLe)}${tronque ? ` — commence avant ${AXE_DEBUT}` : ''}`}
      />
    );
  };

  /* APRÈS LA DERNIÈRE PARUTION À LA SOURCE. Le Parlement européen déclare, liste
   * par liste, la date au-delà de laquelle sa source ne publie plus rien dans
   * ce corpus (`couverture_profil.bornes_europeennes`, #683) : ce qui suit n'est
   * pas absent, il n'est pas encore paru chez elle. C'est un fait sur la
   * source — la hachure pâle, pas le jaune. */
  const apresSource = (piste) => {
    if (!piste.finSource || piste.finSource >= collecteLe) return null;
    return (
      <span
        className="fc-horssource"
        style={{ left: `${posDate(piste.finSource)}%`, right: 0 }}
        title={`rien de paru à la source après le ${jour(piste.finSource)}`}
      />
    );
  };

  const rail = (piste, couches, avecQueue) => (
    <div className="fc-rail">
      {avantBorne(piste)}
      {apresSource(piste)}
      {couches.map((c) => (
        <div
          key={c.origine || c.titre}
          className="fc-couche"
          title={c.origine || c.titre}
        >
          {avecQueue ? apresChamp(c.etendue, finDe(piste, c.origine)) : null}
          {barres(c.etendue)}
        </div>
      ))}
    </div>
  );

  const bascule = (cle) =>
    setOuvertes((prev) => {
      const s = new Set(prev);
      if (s.has(cle)) s.delete(cle);
      else s.add(cle);
      return s;
    });

  return (
    <div className="fc">
      <div className="fc-tete">
        <b>Ce que le dépôt porte, institution par institution</b>
        <span>
          {nb(total)} enregistrements · de {AXE_DEBUT} à la collecte du {jour(collecteLe)}
        </span>
      </div>

      <div className="fc-corps">
        <div className="fc-lignes">
          <div className="fc-axe">
            {GRADUATIONS.map((g) => (
              <span key={g} style={{ left: `${pos(g)}%` }}>
                {g}
              </span>
            ))}
          </div>

          {hierarchie.map((inst) => (
            <div className={`fc-groupe fc-groupe--${inst.cle}`} key={inst.cle}>
              <div className="fc-groupe-titre">{inst.titre}</div>
              {inst.pistes.map((piste) => {
                const cle = `${inst.cle}-${piste.cle}`;
                const ouverte = ouvertes.has(cle);
                return (
                  <div key={cle}>
                    {/* LA SOURCE NE PORTE PAS CETTE LISTE (#885). Pas de
                        chevron : il n'y a aucun champ à ouvrir, et un chevron
                        qui n'ouvre rien se lit comme un défaut. La hachure dit
                        « la source ne le publie pas » ; le jaune aurait dit
                        « nous ne l'avons pas collecté », un fait faux sur nous. */}
                    {piste.nonPublie ? (
                      <div className="fc-piste fc-piste--liste">
                        <div className="fc-nom"><span className="fc-nom-nu">{piste.titre}</span></div>
                        <div className="fc-rail">
                          <span className="fc-horssource" style={{ left: 0, right: 0 }} title={piste.nonPublie} />
                        </div>
                        <div className="fc-n"><span className="fc-aucune">non publié</span></div>
                      </div>
                    ) : (<>
                    <div className="fc-piste fc-piste--liste">
                      <div className="fc-nom">
                        <button
                          type="button"
                          className="fc-bouton"
                          aria-expanded={ouverte}
                          aria-controls={`fc-sous-${cle}`}
                          onClick={() => bascule(cle)}
                        >
                          <span className={`fc-chevron${ouverte ? ' fc-chevron--ouvert' : ''}`} aria-hidden="true">
                            ▶
                          </span>
                          <span>{piste.titre}</span>
                        </button>
                      </div>
                      {rail(piste, piste.couches, false)}
                      <div className="fc-n">
                        {nb(piste.couches.reduce((s, c) => s + c.total, 0))}
                      </div>
                    </div>
                    <div className="fc-sous" id={`fc-sous-${cle}`} hidden={!ouverte}>
                      {piste.champs.map((ch) => (
                        <div className="fc-piste" key={ch.titre}>
                          <div className="fc-nom">{ch.titre}</div>
                          {rail(piste, ch.couches, true)}
                          <div className="fc-n">
                            {nb(ch.n)}
                            <em>sur {nb(ch.total)}</em>
                          </div>
                        </div>
                      ))}
                    </div>
                    </>)}
                  </div>
                );
              })}
            </div>
          ))}

          {SANS_ACTIVITE.map((x) => {
            const i = parInstitution[x.cle];
            const d = i?.debut ? posDate(i.debut) : 0;
            // Un mandat local en cours n'a pas de fin : le segment va jusqu'à la
            // collecte, comme sur les autres rails.
            const f = posDate(i?.fin && i.fin > (i?.debut || '') ? i.fin : collecteLe);
            return (
              <div className="fc-groupe" key={x.cle}>
                <div className="fc-piste fc-piste--seule">
                  <div className="fc-nom fc-groupe-titre">{x.titre}</div>
                  <div className="fc-rail fc-rail--nu" title={x.quoi}>
                    {!i ? (
                      <span className="fc-horssource" style={{ left: 0, width: '100%' }} />
                    ) : (
                      <>
                        {i.borne && posDate(i.borne) > 0 && (
                          <span
                            className="fc-horssource"
                            style={{ left: 0, width: `${posDate(i.borne)}%` }}
                            title={`aucune donnée publiée avant le ${jour(i.borne)}`}
                          />
                        )}
                        <span
                          className={`fc-seg fc-seg--${x.cle}`}
                          style={{ left: `${d}%`, width: `${Math.max(0.6, f - d)}%` }}
                          title={`${jour(i.debut)} → ${jour(i.fin || collecteLe)}`}
                        />
                      </>
                    )}
                  </div>
                  <div className="fc-n">
                    {i ? (
                      <>
                        {nb(i.mandats)}
                        <em>
                          {i.candidats} candidat{i.candidats > 1 ? 's' : ''}
                        </em>
                      </>
                    ) : (
                      <span className="fc-aucune">aucune source</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p className="fc-legende">
        <span><i className="fc-cle fc-cle--collecte" />Données collectées</span>
        <span><i className="fc-cle fc-cle--hors" />Données non publiées</span>
      </p>
    </div>
  );
}
