import StaticPage from '../components/StaticPage';

const SECTIONS = [
  {
    heading: 'Éditeur du site',
    body: (
      <>
        <p>
          Ce site est édité à titre non professionnel et non commercial par une personne physique.
          Conformément à l'article 6-III de la loi n° 2004-575 du 21 juin 2004 pour la confiance dans
          l'économie numérique (LCEN), l'identité complète de l'éditeur est tenue à la disposition de
          l'hébergeur du site et pourra être communiquée, sur demande, à toute autorité judiciaire
          compétente.
        </p>
        <p>
          <strong>Contact éditeur</strong> :{' '}
          <a href="mailto:contact@empreinte-politique.fr">contact@empreinte-politique.fr</a>
        </p>
        <p>
          <strong>Comptes publics</strong> :{' '}
          <a
            href="https://www.linkedin.com/company/empreinte-politique"
            target="_blank"
            rel="noopener noreferrer"
          >
            linkedin.com/company/empreinte-politique
          </a>
          {' · '}
          <a href="https://x.com/EmpreintePol" target="_blank" rel="noopener noreferrer">
            x.com/EmpreintePol
          </a>
        </p>
      </>
    ),
  },
  {
    /* L'HÉBERGEUR EST GITHUB, PAS LE REGISTRAR (#1032, 18/09/2026). Le site est
       servi par GitHub Pages — `.github/workflows/deploy-pages.yml` publie
       `web/UI_finale/dist`, et `CNAME` y attache le domaine. Gandi est le
       bureau d'enregistrement du nom de domaine, ce que la LCEN ne demande pas
       de nommer : la section le dit quand même, parce que la question s'est
       posée.

       LES DEUX ADRESSES VIENNENT DE LEUR SOURCE, pas de mémoire : celle de
       GitHub de sa déclaration de confidentialité (« Our addresses are »),
       celle de Gandi de l'enregistrement RDAP du domaine chez l'AFNIC, qui fait
       foi pour le registre `.fr`. Aucun téléphone pour GitHub : il n'en publie
       pas, et en inventer un dans une page légale serait pire que l'absence. */
    heading: 'Hébergement',
    body: (
      <>
        <p>
          Ce site est hébergé par <strong>GitHub, Inc.</strong>, 88 Colin P. Kelly Jr. Street, San
          Francisco, CA 94107, États-Unis, via le service GitHub Pages.
        </p>
        <p>
          Le nom de domaine <code>empreinte-politique.fr</code> est enregistré auprès de{' '}
          <strong>Gandi</strong>, 63-65 boulevard Masséna, 75013 Paris, France — téléphone :
          +33 1 70 37 76 61.
        </p>
      </>
    ),
  },
  {
    heading: 'Directeur de la publication',
    body: (
      <p>
        La direction de la publication est assurée par l'éditeur du site, joignable à l'adresse
        ci-dessus.
      </p>
    ),
  },
  {
    /* TROIS RÉGIMES, ET ILS NE SE CONFONDENT PAS (#1032, arbitré le 18/09/2026).
       Le paragraphe précédent disait « à préciser » pour les trois à la fois,
       pendant que /a-propos annonçait un code public : deux pages qui ne
       disaient pas la même chose sur la même question. */
    heading: 'Propriété intellectuelle — code, contenu éditorial et données',
    body: (
      <>
        <p>
          <strong>Le code source</strong> de ce site est publié sous licence{' '}
          <a
            href="https://github.com/stephieED/Empreinte-politique-src/blob/main/LICENSE"
            target="_blank"
            rel="noopener noreferrer"
          >
            GNU Affero General Public License v3.0
          </a>{' '}
          (AGPL-3.0). Il peut être utilisé, étudié, modifié et redistribué à cette condition : qui
          met en ligne un service fondé sur une version modifiée doit en publier le code source sous
          la même licence. Le dépôt est à l’adresse{' '}
          <a
            href="https://github.com/stephieED/Empreinte-politique-src"
            target="_blank"
            rel="noopener noreferrer"
          >
            github.com/stephieED/Empreinte-politique-src
          </a>
          .
        </p>
        <p>
          <strong>Les textes rédigés pour ce site et sa charte graphique</strong> — pages
          éditoriales, libellés, identité visuelle, logotype — sont protégés par le droit d’auteur
          et <strong>tous droits réservés</strong>. Une licence de logiciel ne les couvre pas : elle
          porte sur le code, pas sur la prose ni sur la marque.
        </p>
        <p>
          <strong>Les données présentées</strong> ne relèvent d’aucun de ces deux régimes : elles
          proviennent de sources publiques et restent sous leurs licences propres, détaillées dans
          « Sources et licences des données » ci-dessous.
        </p>
      </>
    ),
  },
  {
    heading: 'Sources et licences des données',
    body: (
      <>
        <p>
          Ce site s'appuie exclusivement sur des données publiques, réutilisées conformément aux
          licences suivantes. Ces licences ne sont pas les mêmes selon les sources, et le jeu de
          données publié ici <strong>n'est donc pas couvert par une licence unique</strong> :
          l'obligation de partage à l'identique s'applique à certains champs et pas à d'autres,
          comme détaillé en fin de section.
        </p>

        <h3>Open Data de l'Assemblée nationale</h3>
        <p>
          <strong>Seule source de l'activité parlementaire française.</strong> L'identité et les mandats des députés,
          la composition des groupes parlementaires, les scrutins, les amendements, les dossiers
          législatifs, les questions écrites et les débats en séance (Syceron) proviennent du portail
          Open Data officiel de l'Assemblée nationale (data.assemblee-nationale.fr et
          questions.assemblee-nationale.fr), mis à disposition sous{' '}
          <strong>Licence Ouverte / Open Licence</strong> (Etalab) :{' '}
          <a
            href="https://data.assemblee-nationale.fr/licence-ouverte-open-licence"
            target="_blank"
            rel="noopener noreferrer"
          >
            https://data.assemblee-nationale.fr/licence-ouverte-open-licence
          </a>
        </p>
        <p className="static-note">
          Contient des informations publiques issues du portail Open Data de l'Assemblée nationale, sous
          Licence Ouverte / Open Licence. Cette licence autorise la réutilisation commerciale et
          l'adaptation sans obligation de partage à l'identique, sous réserve de mention de la paternité.
        </p>

        <h3>Open Data du Sénat</h3>
        <p>
          <strong>Les appartenances, jamais l'activité.</strong> Le Sénat publie sous{' '}
          <strong>Licence Ouverte / Open Licence</strong> les mandats de ses membres, leurs groupes
          politiques, leurs commissions, délégations, groupes d'études, d'amitié et de liaison, et
          les organismes extra-parlementaires où ils siègent (data.senat.fr). Ces données
          alimentent, pour les candidats concernés, la partie sénatoriale de leur parcours.{' '}
          <strong>Ce jeu de données ne contient ni scrutins ni comptes rendus de séance</strong> :
          aucune fiche ne porte de vote ni de prise de parole au Sénat, et ce silence est une limite
          de la source, pas une absence d'activité. Les taux de présence que le Sénat publie ne sont
          pas collectés.
        </p>
        <p className="static-note">
          Contient des informations issues de data.senat.fr, mises à disposition par le Sénat sous
          Licence Ouverte / Open Licence. L'attribution est due ; il n'y a pas d'obligation de
          partage à l'identique.
        </p>

        <h3>Parltrack</h3>
        <p>
          Les données relatives aux député·es européen·nes (dossiers législatifs, votes, activités)
          proviennent des dumps JSON de Parltrack (parltrack.org), mis à disposition sous licence{' '}
          <strong>Open Database License (ODbL) v1.0</strong> :{' '}
          <a href="https://opendatacommons.org/licenses/odbl/1-0/" target="_blank" rel="noopener noreferrer">
            https://opendatacommons.org/licenses/odbl/1-0/
          </a>{' '}
          — <strong>source active</strong>, et la clause de partage à l'identique s'y applique
          pleinement.
        </p>
        <p className="static-note">
          Contient des informations issues de Parltrack (parltrack.org), mises à disposition sous licence
          ODbL.
        </p>

        <h3>Parlement européen</h3>
        <p>
          Les mandats des député·es européen·nes, ainsi que l'existence et le titre français des
          documents européens, proviennent du portail Open Data du Parlement européen
          (data.europarl.europa.eu), dont les données sont réutilisables sous licence{' '}
          <strong>Creative Commons Attribution 4.0 International (CC BY 4.0)</strong> :{' '}
          <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer">
            https://creativecommons.org/licenses/by/4.0/
          </a>
          , en application de l'article 4 de la décision du Bureau du Parlement européen du 16 décembre
          2024 :{' '}
          <a href="https://eur-lex.europa.eu/eli/C/2025/341/oj" target="_blank" rel="noopener noreferrer">
            https://eur-lex.europa.eu/eli/C/2025/341/oj
          </a>
          . Les liens vers www.europarl.europa.eu renvoient au document d'origine ; aucun contenu n'en est
          reproduit.
        </p>
        <p className="static-note">
          Contient des informations issues du portail Open Data du Parlement européen, mises à disposition
          sous licence CC BY 4.0.
        </p>

        <h3>Wikipédia et Wikidata</h3>
        <p>
          Le statut de candidature déclarée peut être recoupé via Wikipédia (fr.wikipedia.org) et Wikidata
          (query.wikidata.org). Ces deux sources ont des licences <strong>distinctes</strong> : Wikipédia
          est sous <strong>Creative Commons Attribution — Partage dans les mêmes conditions 4.0 (CC BY-SA 4.0)</strong>{' '}
          (
          <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener noreferrer">
            https://creativecommons.org/licenses/by-sa/4.0/
          </a>
          ) ; les données structurées de Wikidata sont sous <strong>CC0 1.0</strong>, domaine public (
          <a
            href="https://creativecommons.org/publicdomain/zero/1.0/"
            target="_blank"
            rel="noopener noreferrer"
          >
            https://creativecommons.org/publicdomain/zero/1.0/
          </a>
          ), sans obligation d'attribution ni de partage à l'identique.
        </p>

        <h3>Sycomore et Journal officiel</h3>
        <p>
          Les mandats nationaux exercés <strong>avant ce que publie l'open data de l'Assemblée
          nationale</strong> — des mandats de député antérieurs au 19 juin 2002, des fonctions
          gouvernementales antérieures — ne sont pas collectés : ils sont relus à la main, un par un,
          et cités avec un lien vers leur source primaire. Pour les député·es, la base Sycomore de
          l'Assemblée nationale (www2.assemblee-nationale.fr/sycomore), dont le contenu est publié
          sous « © Tous droits réservés » : seuls des faits — une fonction, deux dates — en sont
          repris, et aucun contenu n'en est reproduit. Pour les membres du Gouvernement, les décrets
          du Journal officiel publiés sur Légifrance, sous <strong>Licence Ouverte 2.0</strong>{' '}
          (Etalab) :{' '}
          <a
            href="https://www.legifrance.gouv.fr/contenu/pied-de-page/open-data-et-api"
            target="_blank"
            rel="noopener noreferrer"
          >
            https://www.legifrance.gouv.fr/contenu/pied-de-page/open-data-et-api
          </a>
        </p>

        <h3>Implication pour la réutilisation de nos propres données</h3>
        <p>
          Les jeux de données JSON produits et publiés par ce site combinent des contenus sous plusieurs
          licences. <strong>Seuls les champs dérivés de Parltrack, sous ODbL,</strong>{' '}
          sont soumis à la clause de partage à l'identique de l'ODbL : toute republication d'un jeu de
          données dérivé téléchargeable incluant ces champs doit être mise à disposition sous une licence à
          clauses équivalentes. Les champs issus de l'Open Data de l'Assemblée nationale (Licence Ouverte /
          Etalab), du Journal officiel (Licence Ouverte 2.0) et du Parlement européen n'imposent
          qu'une obligation d'attribution, sans partage à
          l'identique. Les champs issus de Wikidata (CC0) ne sont soumis à aucune restriction.
        </p>
        <p>
          L'ensemble du corpus <strong>n'est donc pas réutilisable sous simple attribution</strong> :
          Parltrack reste une source active sous ODbL. Pour savoir ce qui s'applique à un profil donné, lire son champ{' '}
          <code>meta.licence_donnees</code>, qui énumère les licences dont ce profil relève. Dans tous les
          cas, la consultation du site lui-même (page HTML, « Produced Work » au sens de l'ODbL) reste
          couverte par la simple attribution ci-dessus.
        </p>
      </>
    ),
  },
];

export default function LegalNoticePage() {
  return (
    <StaticPage
      eyebrow="Empreinte politique"
      title="Mentions légales"
      updated="Dernière mise à jour : 16 septembre 2026"
      sections={SECTIONS}
    />
  );
}
