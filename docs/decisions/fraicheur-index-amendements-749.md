# La rotation de clé hebdomadaire était toute la politique de fraîcheur, et son propre repli la désamorçait (#749)

`2026-09-07`

> **En bref** — l'index amendements de la 17e n'avait plus été reconstruit depuis **18 jours**, et le gate le criait à chaque run ; aucun module n'avait tort séparément — #249 a fait de la **clé hebdomadaire** le seul mécanisme de péremption (le seuil de 7 jours de la §3d est documenté comme « aligné » sur elle), #250/#251 ne retéléchargent que sur cache absent ou corrompu, #253 a **explicitement rejeté** le retéléchargement inconditionnel, et #424 a ajouté `restore-keys` pour éviter un cache froid ; mis bout à bout, le repli restaure la semaine précédente, **le cache n'est donc jamais absent**, et la reconstruction n'a plus jamais lieu — le seul moment où le préfixe fut vide est le jour de sa création ; **le défaut est entre deux décisions, dans aucun des deux étages**, et l'alarme prévue pour ce cas sonnait sans destinataire ; ce qui l'a rendu invisible est un **log qui décrivait l'intention et non le fait** (« Construction de l'index… 642 acteurs » pour 0,28 s sans un octet téléchargé, les 642 étant un `len()` sur des noms de fichiers) ; correctif : `outputs.cache-hit` distingue seul une correspondance **exacte** d'un `restore-keys`, donc `--reconstruire-actives` purge les législatures **non figées** à chaque changement de semaine ISO ; `restore-keys` est **gardé** — le retirer viderait le cache entier et re-matérialiserait les figées, dont [[oom-reconstruction-amendements-figees]] a mesuré le coût (OOM à 6 Gio de RSS), pour 1,22 Gio par semaine au lieu de **283 Mo** ; un seuil d'âge dans le Python est écarté aussi : la politique de fraîcheur est dans la CI **exprès**, en dédoubler la source en ferait deux à tenir d'accord ; le prédicat de cache-hit est extrait et **nommé**, pour que le log et la décision ne puissent plus diverger ; dégât mesuré **nul** à ce jour (dernier amendement au 21/07/2026, cohérent avec la suspension des travaux), le coût commençant à la reprise de session. 10 tests, suite complète à 3 871, 0 échec.

## Contexte

Le quality gate §3d signalait à chaque run : « législature 17 : index périmé —
dernière reconstruction réussie il y a 18 jour(s) (seuil 7) ». Le signal était
juste, et depuis 18 jours : **aucun run n'avait téléchargé l'archive**.

Aucun des modules concernés n'avait tort séparément.

| Décision | Ce qu'elle a posé |
| --- | --- |
| #249 ([[amendements-index-budget-ci-cache-granularite]]) | La clé **hebdomadaire** comme **seul** mécanisme de péremption. Le seuil de 7 jours de la §3d est explicitement « aligné sur la granularité de cache hebdomadaire déjà tranchée par #249 » |
| #250/#251 ([[amendements-index-job-dedie-ci]]) | On ne retélécharge l'archive (283 Mo) **que si le cache est absent ou corrompu** |
| #253 ([[amendements-index-non-regression-fraicheur]]) | Rejette **explicitement** le retéléchargement inconditionnel : « cela viderait de son sens le choix déjà tranché par #250/#251 » |
| #424 ([[cache-cle-amendements-separee]]) | Une clé propre au job, avec `restore-keys: public-data-cache-amendements-` — pour éviter un cache froid au changement de semaine |

Mis bout à bout : au changement de semaine ISO la clé exacte manque, mais
`restore-keys` restaure **la semaine précédente**. Le cache n'est donc jamais
absent, le court-circuit de `_download_and_build_amendement_index` voit toujours
un index valide, et la reconstruction n'a plus jamais lieu. Le seul moment où le
préfixe a été vide est le jour de sa **création** (#424, 18/08) — ce qui
correspond à la date que le gate rapportait.

**Le défaut n'est dans aucun des deux étages : il est entre deux décisions.**
L'une a choisi la rotation de clé comme politique de fraîcheur, l'autre a ajouté
un repli qui la désactive, et personne ne les a rapprochées. L'alarme prévue
pour ce cas sonnait depuis 18 jours sans destinataire — ce qui est le vrai
enseignement : un avertissement soft que personne ne lit ne vaut pas mieux que
pas d'avertissement.

### Le log est ce qui l'a rendu invisible

Le step imprimait « Construction de l'index amendements, législature 17 » puis
« 642 acteur(s) indexé(s) » — pour une exécution de **0,28 s** (19:03:01.61 →
19:03:01.89, run `34053322456`) sans une seule ligne de téléchargement. Les 642
étaient un `len()` sur des noms de fichiers en cache. Le log décrivait
l'**intention** de la boucle, pas ce qui s'était produit.

## Décision

**Purger la seule législature active quand la clé exacte de la semaine n'a pas
été touchée**, et garder `restore-keys`.

`actions/cache` distingue les deux cas : `outputs.cache-hit` vaut `'true'`
**uniquement** sur correspondance exacte de la clé primaire, et `'false'` quand
la restauration vient d'un `restore-keys`. C'est exactement le signal « on a
changé de semaine ISO », et c'est lui qui manquait.

1. `build_amendements_index.py --reconstruire-actives` purge le cache des
   législatures **non figées** avant de construire.
2. Le job le passe quand `steps.cache_amendements.outputs.cache-hit != 'true'`.
   Une reconstruction par semaine ISO — ce que #249 voulait.
3. Le prédicat de cache-hit est **extrait et nommé**
   (`amendements_index_en_cache_utilisable`), et le script s'en sert pour dire
   dans son log s'il a construit ou servi le cache. Le dupliquer aurait laissé
   les deux dériver, et c'est un log divergent qui a coûté 18 jours.

## Alternative rejetée

**Retirer `restore-keys`.** C'était la première proposition, et elle rendait
littéralement à #249 son mécanisme. Écartée : elle vide le cache **entier**
chaque semaine, donc re-matérialise aussi les législatures figées 14/15/16
depuis leurs archives committées — le chemin dont
[[oom-reconstruction-amendements-figees]] a mesuré le coût (OOM kill à 6 Gio de
RSS sur une machine de 7,6 Gio). Or #249 l'écrivait déjà : « Seule la 17e
législature est concernée par la mise à jour quotidienne ; les 16e et 15e sont
des législatures archivées dont les archives ne changeront plus jamais. »
Purger les actives coûte **283 Mo** par semaine ; retirer le repli en coûtait
1,22 Gio, dont les deux tiers pour rien.

**Brancher un seuil d'âge dans `_download_and_build_amendement_index`.** C'était
la recommandation portée en premier à l'arbitrage, et elle réparait au mauvais
étage : la politique de fraîcheur a été placée dans la CI **exprès** (#253), et
un second seuil dans le Python en aurait fait deux, à tenir d'accord.

## Dégât mesuré

Nul à ce jour. L'amendement le plus récent de l'index publié date du
**21/07/2026**, et rien n'a été ajouté entre le 21/07 et la dernière
construction — cohérent avec la suspension des travaux parlementaires. Le coût
commence à la reprise de session.

## Tests

`tests/test_fraicheur_index_amendements_749.py` — 10 tests : le prédicat servable
/ absent / au format hérité ; le log qui dit lequel des deux a eu lieu et
n'appelle pas la fonction lourde sur cache-hit ; la purge qui épargne les
figées ; le job CI qui arme le drapeau sur l'absence de correspondance exacte ;
et l'existence réelle du drapeau, qu'un workflow passant un nom inconnu ferait
échouer.

`tests/test_build_amendements_index.py` patche désormais aussi le nouveau
prédicat — sans quoi ses 7 tests dépendraient silencieusement de l'état du cache
disque de la machine qui les exécute, exactement le défaut relevé par
[[oom-reconstruction-amendements-figees]].

Suite complète : 3 871 tests, 0 échec.
