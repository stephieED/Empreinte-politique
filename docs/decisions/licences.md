<a id="licences"></a>
# Audit des sources de données et de leurs licences, pour les Mentions légales (#288) (2026-08-14)

`2026-08-14`

> **En bref** — audit des sources et de leurs licences : ce que le partage à l'identique impose au corpus publié.

**Contexte** : sous-issue 1/3 du plan #140. L'ancien `web/old/v3/mentions-legales.html`
ne couvre que NosDéputés/NosSénateurs, Parltrack et Wikipédia, alors que le pipeline
actuel interroge aussi l'Open Data de l'Assemblée nationale, l'Open Data du Parlement
européen et Wikidata. Audit exhaustif via `grep -rn https:// src/*.py` (tous les
domaines listés en AGENTS.md §7), puis vérification en direct de chaque page de
licence officielle (accessible dans le sandbox réseau de cet agent pour tous les
domaines listés, sauf `data.europarl.europa.eu`, portail Angular non rendu par un
simple `curl`, et `www.wikidata.org`, hors liste des hôtes autorisés — `query.wikidata.org`
seul y figure).

**Constat par domaine** :

| Domaine(s) | Donnée réutilisée | Licence | Texte officiel | Attribution requise |
|---|---|---|---|---|
| `www.nosdeputes.fr`, `2007-2012\|2012-2017\|2017-2022.nosdeputes.fr`, `archive.nossenateurs.fr` | Mandats, votes, amendements, fiches parlementaires (législatures 13 à 17) | **ODbL v1.0** | https://opendatacommons.org/licenses/odbl/1-0/ (référencée par https://www.nosdeputes.fr/a-propos : « les données sous licence ODbL ») | Oui — « NosDéputés.fr (ou NosSénateurs.fr) par Regards Citoyens à partir de l'Assemblée nationale (ou du Sénat) et du Journal Officiel » |
| `data.assemblee-nationale.fr`, `questions.assemblee-nationale.fr`, `www.assemblee-nationale.fr`, `schemas.assemblee-nationale.fr` | Scrutins, amendements, dossiers législatifs, questions écrites, débats Syceron | **Licence Ouverte / Open Licence (Etalab)** | https://data.assemblee-nationale.fr/licence-ouverte-open-licence (PDF/RTF téléchargeables sur cette page — la page ne précise pas explicitement 1.0 vs 2.0 ; utiliser le PDF de l'AN comme texte de référence plutôt que de présumer une version) | Oui, mention de la paternité obligatoire — **pas** de partage à l'identique |
| `parltrack.org` (dumps JSON) | Dossiers législatifs, votes, activités des député·es européen·nes | **ODbL v1.0** | https://opendatacommons.org/licenses/odbl/1-0/, référencée en direct par https://parltrack.org/ (section Copyright : « data … ODBLv1.0 ») | Oui — partage à l'identique si republication d'un jeu de données dérivé |
| `data.europarl.europa.eu`, `www.europarl.europa.eu` | Fiches et photos des député·es européen·nes (API v2 + pages MEP) | Politique de réutilisation du **Legal Notice** du Parlement européen (reproduction/adaptation/diffusion commerciale ou non commerciale autorisée si l'élément est reproduit intégralement et la source indiquée) | https://www.europarl.europa.eu/legal-notice/fr/ (confirmée en direct) | Oui — « © Union européenne, [année] – Source : Parlement européen » |
| `fr.wikipedia.org` | Statut de candidature déclarée (pas de citation de texte actuellement) | **CC BY-SA 4.0** | https://creativecommons.org/licenses/by-sa/4.0/ (confirmée en direct via le pied de page Wikipédia) | Oui, + partage à l'identique si citation de texte |
| `query.wikidata.org` | Identifiants/métadonnées structurées liées aux candidatures | **CC0 1.0** | https://creativecommons.org/publicdomain/zero/1.0/ (politique de licence Wikidata bien établie — non re-vérifiée en direct dans ce sandbox, `www.wikidata.org` n'étant pas dans la liste des hôtes réseau autorisés) | Non — aucune obligation |

**Correction apportée à AGENTS.md §7** : la ligne Parltrack indiquait « CC0 / ODbL
(mixed) », ce que ne confirme pas la page Copyright de parltrack.org (uniquement
ODbL v1.0 pour les dumps JSON que consomme ce pipeline — le CC BY-SA 3.0 mentionné
sur ce site concerne le contenu HTML des pages, jamais téléchargé ici). Corrigée en
« ODbL v1.0 ». *Point non corrigé dans ce ticket* (hors périmètre, aucun fichier de
code) : `src/mep_profile.py:419` inscrit `"Open Data — Parltrack (CC0 / Open Database
License)"` dans `meta.licence_donnees`, la même approximation — à corriger dans la
sous-issue d'implémentation ou un ticket dédié. De même, `candidate_profile.py:2829`
et `generate_all_profiles.py:287` étiquettent tout `meta.licence_donnees` d'un profil
`"ODbL (Regards Citoyens…)"` alors que le même profil peut aussi contenir des champs
issus de l'Open Data AN (Etalab) via Syceron/scrutins/amendements — la métadonnée
interne ne distingue donc pas aujourd'hui les deux licences au sein d'un même profil ;
sans incidence sur le texte public des Mentions légales ci-dessous (qui couvre les deux
sources séparément), mais à garder en tête si `licence_donnees` est un jour affiché
tel quel côté `web/`.

**Hébergement de `web/UI_finale`** : aucun pipeline de déploiement du site trouvé —
`.github/workflows/` ne contient que `claude.yml`, `claude-code-review.yml`,
`generate-data.yml` et `retry-generate-data.yml` (génération de données, pas de build/
déploiement front), et `web/UI_finale` n'a ni config Vercel/Netlify ni workflow
GitHub Pages. **Statué : à préciser** — ne pas reprendre la mention « GitHub, Inc. »
de `web/old/v3/mentions-legales.html` tant qu'un hébergeur réel n'est pas choisi.

**Clause de partage à l'identique révisée** : dans `web/old/v3/mentions-legales.html`,
la clause « Implication pour la réutilisation de nos propres données » applique le
partage à l'identique ODbL à l'ensemble du jeu de données combiné. C'est inexact
depuis l'ajout des sources Etalab (AN) et CC0 (Wikidata), qui n'ont pas de clause de
réciprocité. Le partage à l'identique ne s'applique qu'aux **champs dérivés de
sources ODbL** (NosDéputés/NosSénateurs, Parltrack) en cas de republication d'un jeu
de données téléchargeable — voir le texte ci-dessous.

**Texte "Mentions légales" prêt à intégrer (sous-issue 2/3)** :

> # Mentions légales
>
> *Dernière mise à jour : 14 août 2026*
>
> ## Éditeur du site
>
> Ce site est édité à titre non professionnel et non commercial par une personne
> physique. Conformément à l'article 6-III de la loi n° 2004-575 du 21 juin 2004 pour
> la confiance dans l'économie numérique (LCEN), l'identité complète de l'éditeur est
> tenue à la disposition de l'hébergeur du site et pourra être communiquée, sur
> demande, à toute autorité judiciaire compétente.
>
> **Contact éditeur** : empreinte.politique@gmail.com

*Cette citation est datée du 14/08/2026 et n'est pas réécrite : c'est le texte
tel qu'il était au moment de la décision. L'adresse publiée est depuis
`contact@empreinte-politique.fr`, et le seul endroit qui fasse foi est
`web/UI_finale/src/pages/LegalNoticePage.jsx` (#328).*
>
> ## Hébergement
>
> *À préciser.* L'hébergement définitif de ce site n'est pas encore déterminé à la
> date de rédaction de cette page ; cette section sera complétée dès qu'un hébergeur
> sera choisi.
>
> ## Directeur de la publication
>
> La direction de la publication est assurée par l'éditeur du site, joignable à
> l'adresse ci-dessus.
>
> ## Propriété intellectuelle — code et contenu éditorial
>
> Le code source, la charte graphique et les textes rédigés pour ce site sont à
> préciser, sauf mention contraire pour les données présentées (voir « Sources et
> licences des données » ci-dessous).
>
> ## Sources et licences des données
>
> Ce site s'appuie exclusivement sur des données publiques, réutilisées conformément
> aux licences suivantes.
>
> ### NosDéputés.fr et NosSénateurs.fr (Regards Citoyens)
>
> Les données relatives aux député·es et sénateur·rices français·es (mandats, votes,
> amendements) proviennent de NosDéputés.fr et NosSénateurs.fr, projets de
> l'association Regards Citoyens, mises à disposition sous licence **Open Database
> License (ODbL) v1.0** : https://opendatacommons.org/licenses/odbl/1-0/
>
> *Contient des informations issues de NosDéputés.fr et NosSénateurs.fr, par Regards
> Citoyens à partir de l'Assemblée nationale (ou du Sénat) et du Journal Officiel,
> mises à disposition sous licence ODbL.*
>
> ### Open Data de l'Assemblée nationale
>
> Les scrutins, amendements, dossiers législatifs, questions écrites et débats en
> séance (Syceron) proviennent du portail Open Data officiel de l'Assemblée nationale
> (data.assemblee-nationale.fr), mis à disposition sous **Licence Ouverte / Open
> Licence** (Etalab) : https://data.assemblee-nationale.fr/licence-ouverte-open-licence
>
> *Contient des informations publiques issues du portail Open Data de l'Assemblée
> nationale, sous Licence Ouverte / Open Licence.* Cette licence autorise la
> réutilisation commerciale et l'adaptation sans obligation de partage à l'identique,
> sous réserve de mention de la paternité.
>
> ### Parltrack
>
> Les données relatives aux député·es européen·nes (dossiers législatifs, votes,
> activités) proviennent des dumps JSON de Parltrack (parltrack.org), mis à
> disposition sous licence **Open Database License (ODbL) v1.0** :
> https://opendatacommons.org/licenses/odbl/1-0/
>
> *Contient des informations issues de Parltrack (parltrack.org), mises à disposition
> sous licence ODbL.*
>
> ### Parlement européen
>
> Les fiches et photos des député·es européen·nes proviennent du portail Open Data du
> Parlement européen (data.europarl.europa.eu) et du site institutionnel
> (www.europarl.europa.eu), réutilisées conformément au Legal Notice du Parlement
> européen : https://www.europarl.europa.eu/legal-notice/fr/ — reproduction, diffusion
> commerciale ou non commerciale autorisées sous réserve de reproduire l'élément dans
> son intégralité et d'en indiquer la source (« © Union européenne, [année] – Source :
> Parlement européen »).
>
> ### Wikipédia et Wikidata
>
> Le statut de candidature déclarée peut être recoupé via Wikipédia (fr.wikipedia.org)
> et Wikidata (query.wikidata.org). Ces deux sources ont des licences **distinctes** :
> Wikipédia est sous **Creative Commons Attribution — Partage dans les mêmes
> conditions 4.0 (CC BY-SA 4.0)** (https://creativecommons.org/licenses/by-sa/4.0/) ;
> les données structurées de Wikidata sont sous **CC0 1.0**, domaine public
> (https://creativecommons.org/publicdomain/zero/1.0/), sans obligation d'attribution
> ni de partage à l'identique.
>
> ### Implication pour la réutilisation de nos propres données
>
> Les jeux de données JSON produits et publiés par ce site combinent des contenus sous
> plusieurs licences. **Seuls les champs dérivés de sources sous ODbL (NosDéputés.fr,
> NosSénateurs.fr, Parltrack)** sont soumis à la clause de partage à l'identique de
> l'ODbL : toute republication d'un jeu de données dérivé téléchargeable incluant ces
> champs doit être mise à disposition sous une licence à clauses équivalentes.
> Les champs issus de l'Open Data de l'Assemblée nationale (Licence Ouverte / Etalab)
> et du Parlement européen n'imposent qu'une obligation d'attribution, sans partage à
> l'identique. Les champs issus de Wikidata (CC0) ne sont soumis à aucune restriction.
> Dans tous les cas, la consultation du site lui-même (page HTML, « Produced Work » au
> sens de l'ODbL) reste couverte par la simple attribution ci-dessus.

