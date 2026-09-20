<a id="baseline-du-site-1026"></a>

# La baseline du site : « 100 % automatisé • 100 % sourcé • 0 score • 0 filtre » (#1026) (2026-09-18)

`2026-09-18`

> **En bref** — la promesse du site était écrite là où elle ne se lit pas : dans le `<title>`, dans la `meta description` et dans l'introduction de /methodologie. L'accueil en disait deux traits sur trois, sous son titre — « Des faits sourcés, sans note ni classement — à consulter par candidat, par groupe ou par gouvernement » — et le pied de page deux autres, « Données publiques agrégées. Aucun score, aucun classement. » : deux textes voisins, aucun complet. Une baseline arrêtée par la propriétaire le 18/09/2026, **« 100 % automatisé • 100 % sourcé • 0 score • 0 filtre »**, les remplace tous les deux. **Deux places, et pas trois** : le bandeau sombre de l'accueil et le pied de page sous la marque, sur toutes les pages — **pas l'en-tête collé**, où une phrase répétée en haut de chaque écran devient du décor, et où la rangée est à hauteur fixe (#968). **Une seule définition**, dans `Baseline.jsx` : une promesse recopiée dans deux composants est une promesse qui divergera, et c'est exactement ce qui s'était produit entre la `meta description` et /methodologie. Les puces prennent l'accent **sur le fond sombre seulement** — 16,01:1 sur l'encre, 1,05:1 sur le fond clair (DESIGN_SYSTEM §2) —, et l'espace avant le `%` est insécable. **Écartées sur maquette rendue** : trois formulations montrées aux deux emplacements, dont « Aucune note, aucun classement — tout est collecté automatiquement », qui promettait plus que /methodologie, laquelle signale qu'un rapprochement peut être validé par un humain.

## Le contexte

Mesuré le 18/09/2026 sur `origin/main` :

| Endroit | Ce qui était écrit | Qui le voit |
| --- | --- | --- |
| `index.html` `<title>` | « Présidentielle 2027 : les parcours politiques des candidats, sourcés » | l'onglet, les moteurs |
| `index.html` `meta description` | « … Des faits sourcés, sans note ni classement. » | les moteurs, les aperçus de lien |
| /methodologie, introduction (#977) | « Tout est collecté et mis en forme automatiquement… Rien n'est noté, classé ni commenté. » | qui ouvre la page |
| Accueil, sous le titre | « Des faits sourcés, sans note ni classement — à consulter par candidat, par groupe ou par gouvernement. » | qui arrive |
| Pied de page, sous la marque | « Données publiques agrégées. Aucun score, aucun classement. » | toutes les pages |
| En-tête | rien | tout le monde |

La promesse existait donc cinq fois, jamais entière, et jamais deux fois dans
les mêmes mots.

## La décision

### 1. Les mots

> 100 % automatisé • 100 % sourcé • 0 score • 0 filtre

Quatre mentions, arrêtées par la propriétaire. Ce que chacune engage :

- **automatisé** porte sur la collecte et la mise en forme — ce que
  /methodologie détaille : aucun fait n'est écrit ni altéré à la main ;
- **sourcé** est la règle 2 : chaque fait porte le lien de sa source primaire ;
- **0 score** est la règle 1 : ni note, ni classement, ni rang ;
- **0 filtre** est la règle 8 et le pendant de la précédente : aucune sélection
  éditoriale de ce qui est publié. Le filtre par intitulé de la fiche (#979)
  est un outil de lecture du visiteur, qui ne retire rien du corpus publié.

### 2. Deux places

Le **bandeau sombre de l'accueil**, sous le titre, où elle remplace la
sous-ligne. Le **pied de page**, sous « Empreinte politique », où elle remplace
les deux lignes précédentes. Elle est donc lue une fois au premier regard, et
une fois par page, en bas.

**Pas l'en-tête collé**, arbitré le 18/09 sur maquette : la rangée suit le
lecteur sur tous les écrans, et une promesse qui suit devient du mobilier. Elle
y aurait par ailleurs occupé 300 px entre la marque et les liens, et disparu
sous 720 px — donc jamais lue sur mobile.

### 3. Une seule définition, deux échelles

`Baseline.jsx` porte les quatre mentions et rend les séparateurs ; les deux
hôtes ne donnent que la taille et la couleur (`.baseline--bandeau`,
`.baseline--pied`). Les puces sont décoratives (`aria-hidden`) : un lecteur
d'écran lit les quatre mentions, pas les points.

L'accent jaune ne porte les puces que sur le fond sombre de l'accueil. Sur le
fond clair du pied de page, il tombe à 1,05:1 et laisse la place au gris — la
même règle que partout ailleurs dans l'interface (DESIGN_SYSTEM §2).

## Les alternatives écartées

Trois formulations ont été rendues, dans les deux emplacements, avant que la
propriétaire n'arrête la sienne :

| Formulation | Pourquoi écartée |
| --- | --- |
| « Aucune note, aucun classement — tout est collecté automatiquement. » | « Tout » englobe les rapprochements qu'un humain valide, ce que la fiche signale explicitement (#977) : la baseline promettait plus que la page qui l'explique |
| « Des faits sourcés, jamais notés ni classés, collectés par un programme. » | Exacte, mais c'est une phrase : elle se lit, elle ne se retient pas |
| « Ni note, ni classement : aucun fait n'est écrit à la main. » | Reprend /methodologie mot pour mot, mais laisse « automatique » implicite |

La forme retenue n'est pas une phrase : quatre mentions scandées, qui se
retiennent et se citent. C'est ce qui l'a emportée.

## Les garde-fous

`tests/test_baseline_1026.py` : les quatre mentions sont définies une seule
fois et aucun composant ne les recopie, les deux hôtes les lisent, l'en-tête
collé ne les porte pas, l'ancienne sous-ligne de l'accueil a disparu, l'espace
avant le `%` est insécable, et l'accent ne colore les puces que sur fond
sombre.
