<a id="gouvernement-textes-initiateurs"></a>
# Profils de gouvernement : le lien ministre → texte (#435) (2026-08-18)

`2026-08-18`

> **En bref** — le lien ministre → texte : le pendant manquant de `role_signataire` pour les textes de gouvernement.

**Contexte** : `textes[]` d'un profil de gouvernement portait 8 champs, dont
aucun ne désignait un membre. On savait qu'un gouvernement avait porté 725
textes, jamais **quel ministre avait déposé lequel** — le pendant manquant de
`role_signataire` pour les amendements. La donnée existait dans la source
(`initiateur.acteurs.acteur[].acteurRef` du dump AN) et était jetée par
`parse_dossier_gouvernemental`. Repéré en cadrant #429, hors de son périmètre
(un enrichissement, pas une optimisation de volume).

**Mesuré sur les trois archives (XV/XVI/XVII), 725 textes rattachés à un
gouvernement** :

| | Valeur |
| --- | --- |
| Textes avec au moins un initiateur | 723 / 725 |
| Textes sans initiateur | 2 |
| Liens initiateur → texte (après dédoublonnage) | 1213 |
| Liens résolus vers un `membre_id` | 556 |
| Acteurs initiateurs distincts | 77 |

**Décision 1 — extraction brute au niveau du parseur, résolution au niveau du
profil.** `gouvernement_textes.parse_dossier_gouvernemental` rend
`initiateurs_acteur_refs` (liste d'`acteurRef`, ordre de la source,
dédoublonnée) ; `gouvernement_profile.py` seul résout vers un `membre_id`,
parce que lui seul connaît la composition du gouvernement. Même séparation que
partout ailleurs dans ce module : le parseur reste pur et testable sans la
composition ministérielle.

**Décision 2 — résolution restreinte aux membres du gouvernement concerné.**
L'index `acteurRef -> membre_id` est construit depuis les seuls profils retenus
dans `membres[]` (l'`acteurRef` d'un profil pivot n'existe que dans
`identite.source_url`, voir `gouvernement_roster.acteur_ref_depuis_profil`).
Hors de `membres[]`, l'`acteurRef` brut est conservé avec `membre_id = null` :
un `acteurRef` peut désigner un co-signataire ou un ex-ministre — c'est
exactement la source des ~15 % de faux positifs qui avaient fait écarter cette
chaîne comme signal d'origine (voir [[gouvernement-textes-statut]]). Ici elle
ne sert qu'à dire qui a déposé, jamais de quelle origine est le texte. Deux
profils partageant un même `acteurRef` sont un conflit d'identité non tranché :
aucun `membre_id` résolu, warning explicite.

657 des 1213 liens restent sans `membre_id`, essentiellement des ministres sans
profil pivot dans le dépôt (dont les 7 Premiers ministres déjà connus pour ce
manque). C'est une couverture partielle assumée, pas un défaut à combler par
approximation : la référence AN reste vérifiable dans la source.

**Décision 3 — `initiateurs = null`, jamais `[]`, pour les 2 textes sans
initiateur.** Une liste vide affirmerait qu'aucun ministre n'a porté le texte,
alors que le fait constaté est que la source ne le dit pas (AGENTS.md §2.5).
`[]` est explicitement **refusé** par `validate_profil_gouvernement`, pour que
l'absence ne puisse pas être écrite des deux façons.

**Décision 4 — clé obligatoire, et `membre_id` vérifié contre `membres[]`.**
`initiateurs` entre dans `REQUIRED_TEXTE_KEYS` : un texte généré par une
version antérieure du pipeline est signalé, pas silencieusement accepté sans
lien. Le validateur refuse aussi un `membre_id` qui ne correspond à aucune
entrée de `membres[]` — un lien membre → texte doit pointer vers un membre du
profil (AGENTS.md §2.2). Les 10 profils de `pivot_data/gouvernements/` ont été
régénérés en conséquence ; le diff est purement additif (aucun champ existant
modifié).

**Coût réel, plus élevé que l'estimation de l'issue** : 403,7 Kio → 539,3 Kio
(+135,6 Kio, +34 %) pour les 10 profils. L'issue annonçait « quelques
kilo-octets » ; un objet `{acteur_ref, membre_id}` indenté pèse ~90 octets et
il y en a 1213. L'ordre de grandeur reste négligeable en absolu (0,53 Mo pour
l'ensemble des profils de gouvernement, à comparer aux 7,9 Go mesurés en #429
sur les profils individuels), mais l'écart est noté pour ne pas laisser croire
que le champ est gratuit.

**Alternative rejetée** : porter le `nom` du ministre dans chaque entrée
`initiateurs[]`. Redondant avec `membres[]`, qui est joignable par `membre_id`,
et sans réponse pour les initiateurs non résolus — pour ~1213 duplications de
chaîne. Le nom se lit côté présentation.

**Alternative rejetée** : une table de mapping unique à la racine du profil
plutôt qu'une liste par texte. `textes[]` est déjà l'unité de lecture du profil
(un texte, son statut, son 49.3) ; une table séparée obligerait `web/` à faire
la jointure pour afficher ce que le texte porte lui-même, sans rien économiser
(le même nombre de liens y figure).

**Non fait** : `mandatRef`, présent à côté d'`acteurRef` dans la source, n'est
pas conservé — il n'ajoute rien au lien membre → texte tant que les mandats du
profil ne sont pas indexés par cette référence.

