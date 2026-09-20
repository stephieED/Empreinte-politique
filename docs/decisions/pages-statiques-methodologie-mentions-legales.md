<a id="pages-statiques-methodologie-mentions-legales"></a>
# Pages Méthodologie et Mentions légales dans web/UI_finale (#289, plan #140) (2026-08-14)

`2026-08-14`

> **En bref** — pages Méthodologie et Mentions légales portées dans `web/UI_finale`, sur un composant partagé.

**Contexte** : sous-issue 2/3 du plan #140, portant `web/old/v3/methodologie.html`
et `mentions-legales.html` dans `web/UI_finale`. Bloquée par #288 pour le
contenu Mentions légales — voir [[licences]] pour le texte validé, repris
tel quel.

**Décision — composant partagé** : `src/components/StaticPage.jsx` + `.css`
factorise bannière + sections pour les deux pages (`MethodologyPage.jsx`,
`LegalNoticePage.jsx`), avec des classes entièrement préfixées
(`static-*`) plutôt que de réutiliser les classes `.main`/`.banner` de
`CandidateProfile.css` — ce fichier ne définit ses classes qu'une fois
(`GroupProfile.jsx`/`GovernmentProfile.jsx` préfixent déjà en `gp-`/`gov-`
pour la même raison) ; s'appuyer dessus par coïncidence de bundle CSS
global aurait couplé silencieusement une page statique à l'implémentation
d'un composant candidat.

**Décision — routes hors `ExplorerLayout`** : l'issue laissait le choix
ouvert entre bandeaux visibles ou page seule. Retenu : `/methodologie` et
`/mentions-legales` sont déclarées en dehors de la route `ExplorerLayout`
dans `App.jsx`, sans les bandeaux Groupes/Gouvernements/Candidats — ces
pages n'ont pas de candidat/groupe sélectionné, et `GroupsBar`/`CandidatesBar`
n'ont de sens que dans ce contexte. *Alternative rejetée* : les nicher sous
`ExplorerLayout` pour réutiliser `Brand` déjà monté — `StaticPage` importe
directement `Brand`, le gain de réutilisation ne justifiait pas d'exposer
des bandeaux de sélection inertes sur une page sans profil.

**Contenu Méthodologie corrigé vs v3** : la section "Ordre des catégories"
de `web/old/v3/methodologie.html` décrit un clic sur les KPI
Majorité/Opposition/Non distingué qui filtre la liste détaillée, avec un
bouton "Réinitialiser". Vérifié dans `CandidateProfile.jsx` et
`src/data/pivotAdapter.js` (`buildCandidateView`, `scopeBuckets`) : ce
comportement n'existe plus — la répartition Majorité/Opposition/Non
distingué s'affiche aujourd'hui comme un graphique de comparaison en
barres (`compare-rows`), non cliquable, uniquement dans l'onglet "Textes"
du profil candidat (`GroupProfile.jsx` n'a pas d'équivalent). Le texte
repris dans `MethodologyPage.jsx` décrit ce comportement actuel plutôt que
celui de v3.

**Hors périmètre** (comme précisé par l'issue) : aucun lien de navigation
vers ces pages depuis le reste de l'app (sous-issue 3/3).

