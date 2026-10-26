# L'intitulé d'un article voté, et le gabarit des lois de finances (#1352) (2026-10-26)

`2026-10-26`

> **En bref** — demandé par la session COM pour l'article « Le parcours du budget 2027 » : les 12 scrutins d'article du PLF et du PLFSS 2027 n'étaient pas rattachés. `articles_votes.json` publie désormais l'**intitulé** que le texte donne à l'article (`intitule`) et la **partie** (`partie`). Le gabarit des lois de finances, déclaré non lu par #1264, est lu, et un chapitre cité dans un article n'est plus pris pour une division. Mesuré le 26/10/2026 sur les 2 119 scrutins d'article des XVe-XVIIe : **1 416 rattachés au lieu de 1 337 (+79, tous avec un intitulé)**, aucun rattachement perdu, et les divisions corrigées sur 264 scrutins déjà publiés.

## Contexte

#1264 (08/10/2026) publie, pour chaque scrutin d'article, le titre, le chapitre,
la section et un extrait de l'article, lus dans le texte HTML de l'Assemblée.
L'intitulé de l'article n'avait pas été retenu, pour une raison mesurée : un
texte ordinaire n'en a pas, son article n'est que son texte (« Le code pénal est
ainsi modifié : … »). La décision #1264 déclarait aussi, dans ses limites : « Les
lois de finances ont un autre gabarit […] : 125 scrutins déclarés
`texte_a_gabarit_non_lu`. Ce gabarit porte peut-être un intitulé par article, ce
qui n'a pas été mesuré. »

Mesuré le 26/10/2026 sur les deux textes du budget 2027 :

| Texte | Ce qui bloquait | Ses scrutins d'article |
| --- | --- | --- |
| PLF 2027 (`PRJLANR5L17B3210`) | le gabarit des lois de finances : aucun paragraphe `assnat9ArticleNum` ; divisions et articles sont des titres HTML (`h2` à `h6`), et chaque article a un intitulé (« ARTICLE 2 : Soutenir le travail… ») | 6, `texte_a_gabarit_non_lu` |
| PLFSS 2027 (`PRJLANR5L17B3211`) | l'intitulé est écrit dans le paragraphe du numéro (« Article 4 Aide aux cotisants… ») : l'en-tête entier devenait une désignation que le scrutin « l'article 4 » ne retrouvait pas | 6, `article_absent_du_texte` |

En les relisant, un troisième défaut est apparu, sans rapport avec la demande. Un
article qui insère un chapitre dans un code l'écrit avec la classe d'un chapitre
(« « Chapitre V ter »). La lecture le prenait pour une division du texte : elle
le donnait aux articles suivants, et coupait l'extrait de l'article qui le cite.

## Décision

1. **`en_tete_d_article`** sépare le numéro de l'intitulé. Le numéro s'arrête au
   premier blanc qui n'appartient pas à la désignation (« 4 », « 1 er », « 12
   quater A », « 1er à 3 »). Une mention de la navette entre parenthèses
   (« (nouveau) ») n'est pas un intitulé. Seul le mot « article » ignore la
   casse : « Article 6 Le régime… » rend « 6 », jamais « 6 Le ». Un en-tête qui ne
   se lit pas garde la lecture d'avant.
2. **La partie** (`assnat2Partie*` ; `h2` dans les lois de finances) est lue, et
   elle efface le titre, le chapitre et la section ouverts avant elle.
3. **Une division entre guillemets est du texte d'article**, jamais une division.
4. **`structure_loi_de_finances`** lit le gabarit des lois de finances quand
   aucun paragraphe d'article n'existe : `h2` la partie, `h3` le titre, `h4` et
   `h5` publiés sous `chapitre` et `section`, `h6` l'article. Les `h4` et `h5` sont
   des subdivisions sans nom (« I – Impôts et ressources autorisées », « B –
   Mesures fiscales ») : **`chapitre` et `section` nomment ici un niveau, pas un
   mot du texte**. Leur `numero` reste verbatim (« I », « B ») et ne contient pas
   le mot « chapitre ». Le texte de l'article est fait de ses paragraphes
   `assnatFPFprojetloiartexte`, jamais de son exposé des motifs. Un `h1` (« États
   législatifs annexés ») ferme les articles.
5. **Le fichier publie `intitule` et `partie`** à côté de `titre`, `chapitre` et
   `section`, `null` quand le texte n'en écrit pas. `SCHEMA_VERSION` passe à
   `articles-votes-v2`, et `VERSION_STRUCTURE` à `v2` : le premier run relit tous
   les textes (le workflow ne change pas).

## Mesures (26/10/2026)

Population : les 2 119 scrutins d'article des XVe-XVIIe, archives du 26/10/2026,
mêmes pages HTML lues avant et après. La passe « avant » reproduit à l'identique
le fichier publié sur `main` (`01313c5219`).

| | Avant | Après |
| --- | ---: | ---: |
| Scrutins rattachés | 1 337 | **1 416** |
| `texte_a_gabarit_non_lu` | 131 | 49 |
| `article_absent_du_texte` | 28 | 31 |
| `plusieurs_dossiers_en_seance` | 612 | 612 |
| Rattachés qui portent un intitulé | 0 | 84 (les 79 nouveaux, et 5 déjà rattachés) |
| Rattachés qui portent une partie | 0 | 188 |

- **Les 79 nouveaux** : 73 venus du gabarit des lois de finances, dont les 6 du PLF
  2027 ; 6 venus du PLFSS 2027.
- **Aucun des 1 337 n'est perdu ni déplacé** : même dossier, même texte, même
  article, même mode de rattachement.
- **264 scrutins déjà publiés voient leurs divisions corrigées.** 315 divisions
  citées retirées (« « Chapitre III », « « TITRE VII ») ; 17 autres changements :
  l'en-tête du document « projet de loi » ou le titre d'une partie précédente,
  publiés comme titre, que la partie efface désormais, et des divisions réelles
  qu'un chapitre cité avait effacées. 66 extraits changent, dont 61 qu'une
  division citée coupait.
- **Les 49 encore non lus** viennent de 16 textes : les lois de finances de la XVe
  à l'ancien format, sans titre d'article (PLF 2018 : 8 scrutins), des projets de
  loi constitutionnelle et des textes courts sans aucune balise d'article.
- **Les 9 lois de finances désormais lues dont l'article reste introuvable**, et
  les 22 « article absent » d'avant, ont d'autres causes : un article ajouté en
  commission absent du texte lu, ou un libellé de scrutin qui ne se découpe pas
  (« l'article 8 et état d… », « l'article 3, à l'exclusion de tout
  amendement »). Hors de ce lot.

## Alternatives écartées

- **Lire l'intitulé dans le libellé du scrutin** : il n'en porte pas, et un
  rattachement par le titre reste interdit (`regrouper-nest-pas-joindre-639`).
- **Nommer les `h4` et `h5` du PLF autrement que `chapitre` et `section`** (un
  champ `subdivisions`) : une forme de plus pour un seul gabarit. Le numéro reste
  verbatim, et ce sont les mots du texte qui s'affichent.
- **Lire aussi l'ancien format des lois de finances de la XVe** : sans titre
  d'article (`h6`) à lire. À mesurer à part si le besoin se présente.

## Non vérifié

- Le temps du premier run en CI, qui relit tous les textes (budget du job :
  40 min). En local, la passe complète a lu 798 pages HTML en 27 min, archives
  comprises, depuis un cache vide.
