<a id="matieres-eurovoc-documents-901"></a>
# 628 textes européens sans dossier, et le portail les classait déjà (#901) (2026-09-16)

`2026-09-16`

> **En bref** — `dossiers_europeens.json` porte la matière d'un **dossier**. Or
> 628 des 694 textes portés européens n'en citent aucun : des résolutions
> déposées en séance, qui n'ouvrent pas de procédure. L'axe thématique plafonnait
> à **66 textes sur 694**. Le portail du Parlement les classe pourtant —
> `is_about` rend 2 à 9 concepts **EuroVoc** par document — et ces concepts
> arrivaient déjà dans la réponse que `ResolveurDocuments` télécharge. Un index
> partagé, `documents_europeens.json`, les publie avec leurs libellés français.

## Contexte

La question de départ était : « peut-on afficher la commission d'un texte
européen ? ». Trois mesures ont déplacé la réponse.

| Mesure | Résultat |
| --- | --- |
| Textes portés européens (32 candidats déclarés) | **694** |
| …qui citent une `reference_dossier` | **66** |
| …dont le dossier porte une commission au fond | **16 dossiers sur 43** |

Une résolution d'actualité n'est **jamais renvoyée en commission** : la source
n'a rien à publier pour elle, et aucun lot ne comblera ce fait. L'axe commission
est structurellement plafonné.

`is_about`, lui, ne dépend pas de la procédure. Vérifié une à une sur 20
documents tirés au hasard parmi les 628 : **20 sur 20** portent des concepts.

## Un index, et pas un champ sur chaque texte porté

Les 628 occurrences ne recouvrent que **335 documents distincts** : un même
texte est porté par plusieurs candidats. L'écrire sur chaque fiche le répéterait,
et c'est la raison même de #431 pour les amendements. L'index suit la forme de
`scrutins.json` : la fiche cite une clé, l'index porte le fait. Arbitré le
16/09/2026.

## Deux sources, et une seule coûte

Les **concepts** viennent du portail du Parlement, dans la réponse que le
résolveur télécharge déjà pour l'existence et le titre. Le cache passe en
`documents-doceo-v3` (`{existe, titre_fr, concepts}`) : cet index ne coûte
**aucune requête de plus** au Parlement, qui nous avait justement coupés le
matin même.

Les **libellés** viennent d'EuroVoc, sous **CC BY 4.0**, résolus par SPARQL et
par **lots de 100** — mesuré, 4 libellés en 0,22 s. Interroger concept par
concept aurait multiplié les appels par cent pour le même résultat.

C'est aussi ce qui distingue cet index de celui des dossiers : **les libellés
sont en français**. EuroVoc est multilingue là où les intitulés de dossier ne le
sont pas.

## Trois absences, qui ne se confondent pas

| Motif | Ce qu'il dit |
| --- | --- |
| `portail_non_interroge` | la question n'a pas pu être posée |
| `source_sans_concept` | le portail répond, et ne classe pas ce document |
| `libelle_eurovoc_introuvable` | le concept existe, son libellé manque — **les codes sont nommés** |

Aucune entrée n'est sans matière **ni** motif. Le troisième cas garde les
libellés trouvés et ne jette pas les autres : une matière perdue en silence
serait indétectable. Et si EuroVoc ne répond pas du tout, la construction
**lève** plutôt que de publier des codes nus — un index de matières illisibles
vaut moins que pas d'index.

## Le piège, et il ne s'annonçait par aucune erreur

Mon premier filtre lisait les `source_url` commençant par `DOCEO_BASE`, en
`https://`. Le périmètre est tombé à **56 documents**. Mesure faite :
**625 des `source_url`** de textes portés européens sont en `http://`, contre
**56** en `https://` — la collecte a changé de forme en cours de route, et les
deux cohabitent.

Un filtre sur la seule forme moderne rendait donc un index qui **avait l'air de
fonctionner**, avec 83 % du corpus manquant. Le schéma est désormais retiré avant
comparaison, et un test le tient.

## Ce que ce lot ne fait pas

**Il ne classe rien.** La matière d'un document est un fait du Parlement, pas
une lecture que nous ferions de son titre — condition pour qu'elle soit
publiable (§2 règles 2 et 8), et raison pour laquelle l'autre voie envisagée,
déduire la matière des intitulés (« on Azerbaijan… »), a été écartée sans être
essayée.

**Il ne mesure pas sa propre couverture.** Le portail avait cessé de répondre
depuis cette machine au moment de l'écriture — limitation ciblée, diagnostiquée
le jour même. Le nombre de documents réellement classés se lira au premier run
où il répond, et `disjoncte` dira si la passe s'est arrêtée en route.
