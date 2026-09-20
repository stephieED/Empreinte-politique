/*
 * LE BALISAGE SCHEMA.ORG, EN JSON-LD (#1008).
 *
 * Mesuré le 18/09/2026 : aucune des 64 pages publiées ne portait
 * `application/ld+json`. Le bloc de #1003 rend une fiche LISIBLE ; ce balisage
 * la rend INTERPRÉTABLE — au lieu d'une phrase à analyser, une machine reçoit
 * un objet typé : une personne, son nom, une fonction, ses dates, sa source.
 *
 * CE QU'IL NE PORTE JAMAIS :
 * - `ClaimReview`, écarté dès #969 : ce balisage porte une note de véracité
 *   (§2 règle 1) ;
 * - un agrégat d'activité (votes, amendements, interventions) : typé en
 *   donnée, il se lit comme un indicateur de performance ;
 * - une date qu'on n'a pas : un mandat clos sans date de fin (#922/#966) n'a
 *   pas d'`endDate`, il n'en reçoit pas une (§2 règle 5) ;
 * - une adresse qui n'est pas déjà une source citée sur la page (§2 règle 2) :
 *   `sameAs` ne renvoie qu'aux pages officielles des institutions, jamais à
 *   Wikipédia ni à un réseau social, que le dépôt ne collecte pas ;
 * - la date de naissance, la profession, la circonscription : `identite` les
 *   porte, la fiche ne les affiche pas toutes, et un balisage qui décrit autre
 *   chose que la page est du contenu caché.
 *
 * L'ÉDITEUR EST « Empreinte politique », jamais une personne : les mentions
 * légales déclarent une édition non professionnelle par une personne physique
 * qui ne se nomme pas, et ce balisage ne la nommera pas davantage.
 */

/* Les pages de personne des institutions — les seules adresses qu'un `sameAs`
 * accepte ici. Les autres `source_url` d'un mandat pointent vers un jeu de
 * données (AMO30, data.gouv.fr) : une archive n'est pas une page « à propos de
 * cette personne ». */
const PAGE_DE_PERSONNE = /^https:\/\/(www2?\.assemblee-nationale\.fr\/(deputes|dyn)\/|www\.senat\.fr\/senateur\/|www\.europarl\.europa\.eu\/meps\/)/;

const ORGANISATION_DE_CHAMBRE = {
  AN: 'Assemblée nationale',
  Senat: 'Sénat',
  PE: 'Parlement européen',
};

const CATEGORIES_PUBLIEES = ['mandat_electif', 'fonction_gouvernementale', 'mandat_local'];

function jour(date) {
  return /^\d{4}-\d{2}-\d{2}/.test(date || '') ? date.slice(0, 10) : null;
}

/* Un rôle daté, tel que schema.org l'attend dans `memberOf` : l'organisation
 * est portée par le rôle, sinon les dates ne s'y rattachent pas. */
function role(mandat) {
  const organisation = ORGANISATION_DE_CHAMBRE[mandat.chambre]
    || (mandat.categorie === 'fonction_gouvernementale' ? 'Gouvernement de la République française' : mandat.label);
  /* Un mandat local n'a pour libellé que sa collectivité — « Hénin-Beaumont » :
   * elle nomme l'organisation, pas le rôle, qui serait sinon écrit deux fois. */
  const nomDuRole = mandat.categorie === 'mandat_local' ? 'Mandat local' : mandat.label;
  const debut = jour(mandat.debut);
  const fin = jour(mandat.fin);
  return {
    '@type': 'OrganizationRole',
    roleName: nomDuRole,
    ...(debut ? { startDate: debut } : {}),
    ...(fin ? { endDate: fin } : {}),
    memberOf: { '@type': 'Organization', name: organisation },
  };
}

export function jsonldCandidat(entree, profil, url) {
  const mandats = (profil.mandats || [])
    .filter((m) => CATEGORIES_PUBLIEES.includes(m.categorie))
    .sort((a, b) => (b.debut || '').localeCompare(a.debut || ''));
  const sameAs = [...new Set(
    [profil.identite?.source_url, ...mandats.map((m) => m.source_url)]
      .filter((u) => typeof u === 'string' && PAGE_DE_PERSONNE.test(u)),
  )];
  return {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: entree.nom,
    url,
    ...(sameAs.length ? { sameAs } : {}),
    ...(entree.parti ? { affiliation: { '@type': 'Organization', name: entree.parti } } : {}),
    ...(mandats.length ? { memberOf: mandats.map(role) } : {}),
  };
}

/* Une LIGNÉE est une organisation, et ses maillons — les groupes successifs —
 * en sont les sous-organisations : la fiche publie les deux niveaux (#836). */
export function jsonldLignee(vue, url) {
  const chambre = ORGANISATION_DE_CHAMBRE[vue.chambre];
  if (!chambre) throw new Error(`${vue.id} : chambre sans organisation — ${vue.chambre}`);
  const debut = jour(vue.periode?.debut);
  const fin = jour(vue.periode?.fin);
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: vue.nom,
    url,
    parentOrganization: { '@type': 'GovernmentOrganization', name: chambre },
    ...(debut ? { foundingDate: debut } : {}),
    ...(fin ? { dissolutionDate: fin } : {}),
    ...((vue.maillons || []).length
      ? {
        subOrganization: vue.maillons.map((m) => ({
          '@type': 'Organization',
          name: m.nom,
          ...(jour(m.periode?.debut) ? { foundingDate: jour(m.periode.debut) } : {}),
          ...(jour(m.periode?.fin) ? { dissolutionDate: jour(m.periode.fin) } : {}),
        })),
      }
      : {}),
  };
}

export function jsonldGouvernement(profil, url) {
  const debut = jour(profil.periode?.debut);
  const fin = jour(profil.periode?.fin);
  const membres = (profil.membres || []).map((m) => ({
    '@type': 'OrganizationRole',
    ...(m.portefeuille ? { roleName: m.portefeuille } : {}),
    ...(jour(m.debut) ? { startDate: jour(m.debut) } : {}),
    ...(jour(m.fin) ? { endDate: jour(m.fin) } : {}),
    member: { '@type': 'Person', name: m.nom },
  }));
  return {
    '@context': 'https://schema.org',
    '@type': 'GovernmentOrganization',
    name: profil.nom,
    url,
    ...(debut ? { foundingDate: debut } : {}),
    ...(fin ? { dissolutionDate: fin } : {}),
    ...(membres.length ? { member: membres } : {}),
  };
}

export function jsonldAccueil(domaine, description) {
  const editeur = {
    '@type': 'Organization',
    name: 'Empreinte politique',
    url: `https://${domaine}/`,
    email: `contact@${domaine}`,
  };
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Empreinte politique',
    url: `https://${domaine}/`,
    inLanguage: 'fr-FR',
    description,
    publisher: editeur,
  };
}

/* `</script>` dans une donnée fermerait la balise : la seule séquence à
 * neutraliser dans un JSON-LD, et elle suffit à injecter du HTML. */
export function baliseJsonld(objet) {
  const json = JSON.stringify(objet, null, 2).replace(/<\//g, '<\\/');
  return `<script type="application/ld+json">\n${json}\n  </script>`;
}
