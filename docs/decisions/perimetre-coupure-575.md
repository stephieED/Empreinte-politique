<a id="perimetre-coupure-575"></a>
<a id="runner-bornage-576"></a>
# Un garde-fou qui bloquait sur ce que la coupure garde, et une procédure qui se saute (#575, #576) (2026-08-29)

`2026-08-29`

> **En bref** — et `--preparer` imprimait une procédure que rien n'exécutait.

Sous-issues 4 et 5 de l'épic #566, dont la prémisse est que **ce qui n'a jamais
été exécuté n'est pas connu**. Ces deux lots traitent ce que la répétition de
#569 a sorti le 28/08/2026 — sept défauts, dont aucun n'était atteignable par
relecture ou par test unitaire.

## #575 — l'outil rendait un verdict confiant sur la mauvaise chose, deux fois

`src/verifier_archivage_swh.py` est le seul outil qui autorise la coupure. Il se
trompait sur **quoi** vérifier et sur **où** le vérifier.

**Le périmètre ignorait la coupure.** Il interrogeait toute la population citée,
alors que la population à RISQUE est celle des ancêtres du point de coupure —
les seuls que l'opération perdrait. Mesuré sur le banc de #569 à `566005c`,
fenêtre 5 : **38 SHA cités, 28 perdus par la coupure et 10 conservés**, et le
script a bloqué sur `9100eb7`, l'un des 10 conservés. `9100eb7` n'est pas
ancêtre de `de23b62` : après la coupure, le dépôt en reste la copie de
référence, et que Software Heritage ne l'ait pas encore vu ne coûte rien. **Le
script a bloqué pour une raison qui n'existait pas.**

Ce n'est pas un cas limite. Software Heritage repasse tous les ~11 jours (mesuré
sur `github.com/git/git`) : tout commit fusionné depuis sa dernière visite
apparaît comme « manquant » sans rien risquer, c'est-à-dire, en régime normal,
plusieurs jours de travail à chaque lancement. Et un garde-fou qui crie à tort
finit par se contourner — le jour où il signalerait un vrai trou, on aurait pris
l'habitude de passer outre. **C'est exactement le mode de défaillance que #568
avait nommé pour les citations orphelines** — « un rouge permanent finirait par
ne plus être lu » — appliqué à un autre axe, et personne ne l'avait vu parce que
le script n'avait jamais tourné contre une coupure réelle.

`--fenetre N` (le calcul de `borner_historique_donnees.sh`, motif importé
d'`audit_volumetrie_profils` plutôt que recopié une troisième fois) ou
`--coupure <commit>` donne le point. Les SHA qui n'en sont pas ancêtres passent
dans un **quatrième cas de la nomenclature — CONSERVÉ PAR LA COUPURE** : ils ne
sont pas interrogés, et ils ne bloquent jamais.

**La nuance à ne pas perdre, et la sortie la porte** : ces SHA *tomberont sous
une coupure future*, et l'archive les couvrira d'ici là. Ce n'est pas « pas
besoin d'archive », c'est « **pas pour cette coupure-ci** ». Sans cette phrase,
on croira l'archive facultative pour eux.

**Sans point de coupure, le comportement reste celui d'avant** — tout est
vérifié — mais la sortie dit que c'est un **AUDIT D'ARCHIVE, pas un feu vert de
coupure**, et que le périmètre est plus large que le risque. Les deux usages
sont légitimes ; ils ne rendent pas le même verdict, et les confondre est ce qui
a coûté la journée.

Mesuré sur `main` à `e22de2a` le 29/08/2026 — **51 SHA cités qui résolvent en
commit**, extraits de 143 chaînes hexadécimales dans 42 fichiers `.md` suivis et
265 corps d'issues :

| fenêtre | point de coupure | à risque | conservés |
| ---: | --- | ---: | ---: |
| 0 | `68c07e0` (28/08) | 50 | 1 |
| 5 | `74c77c2` (28/08) | 40 | 11 |
| 10 | `a125e9e` (27/08) | 16 | 35 |
| 20 | `604c8d6` (18/08) | 6 | 45 |
| **30** (production) | `51d6d4c` (03/08) | **0** | **51** |

À la fenêtre de production, **aucun SHA cité n'est ancêtre de la coupure** : 0
requête au lieu de 51, contre un quota anonyme de 120/heure et une passe
complète qui avait déjà coûté 37 minutes d'attente le 28/08. Le gain de requêtes
est réel mais secondaire ; **ce qui compte est que le verdict cesse d'être
faux**.

Attention à la lecture de cette table : le nombre de conservés CROÎT avec la
fenêtre, parce qu'une fenêtre plus large recule le point de coupure. Et sa queue
tient à la forme de l'histoire de ce dépôt — 32 commits de données, dont
beaucoup groupés du 1<sup>er</sup> au 3 août : la coupure à 30 tombe donc le
03/08, avant presque toutes les citations. Ce n'est pas une propriété de la
fenêtre.

**L'origine était codée en dur.** `ORIGINE_PAR_DEFAUT` était le défaut du
paramètre `--origine`. Lancé le 28/08 sur le banc, dont le remote est
`test_procedure_bornage_issue_569`, le script a interrogé l'archive du **dépôt
réel** sans le signaler. Il n'a pas échoué — **c'est pire** : un fork, un
miroir, un dépôt renommé ou un clone de travail obtiennent un « VÉRIFIÉ » qui ne
parle pas d'eux, et c'est précisément dans ces situations qu'on lance une
vérification, avant une coupure qu'on répète ailleurs.

L'origine est maintenant dérivée de `git remote get-url origin`,
`ORIGINE_PAR_DEFAUT` n'en est plus que le **repli, annoncé dans la sortie quand
il s'applique**, et la provenance figure à côté du snapshot.

**Et elle est normalisée**, sans quoi la correction n'aurait fait que déplacer
le défaut. Software Heritage indexe une origine **par son URL** :
`git@github.com:o/r.git`, `ssh://git@github.com/o/r`, `https://github.com/o/r/`
et `https://github.com/o/r.git` sont un seul dépôt pour l'archive et quatre pour
une comparaison de chaînes. Un clone en SSH aurait interrogé une origine
inconnue de l'archive et rendu INDÉTERMINÉ en permanence — le défaut retourné,
pas corrigé. Huit écritures sont ramenées à une (schémas `ssh`/`git`/`git+ssh`,
forme *scp*, `userinfo`, casse de l'hôte, ports par défaut, `.git`, barre
finale), et un test vérifie **aussi** que deux origines différentes ne se
confondent pas — sans lui, « tout ramener à la même chaîne » passerait.

## #576 — le runner guidé

La procédure était de la prose imprimée dans un heredoc. Sept étapes, dont trois
irréversibles, **dans un ordre dont une seule inversion est irrattrapable** :
archiver après avoir coupé ne rattrape rien. Or le texte se saute, et le moment
où on le lit est celui où l'on est sous pression. La répétition l'a démontré :
les sept étapes déroulées à la main, et **une oubliée** — la suppression du tag
`amendements-figes-v1`, qui ré-épinglait 386 commits. La procédure ne parlait que
de « branches » ; l'opératrice a suivi le texte, et le texte était incomplet.

`scripts/executer_bornage_guide.sh` impose l'ordre, refuse d'avancer sur une
précondition en échec, n'oublie pas d'étape, et **tient un journal** — une trace
qui n'existait pas. Le second écart du 28/08 était précisément ça : passer outre
un verdict MANQUANTS, à bon droit, sans que rien n'en garde mémoire ailleurs que
dans une conversation. Une dérogation se tape désormais en toutes lettres et se
consigne, avec ce qui a été contourné.

**Deux scripts, deux contrats.** `borner_historique_donnees.sh` garantit par test
qu'il ne pousse jamais — c'est sa propriété centrale, actée par #551, et elle
reste vraie. Le runner est un script **distinct** : il appelle le premier pour ce
qui prépare, et porte lui-même les gestes irréversibles. Un test structurel, et
non déclaratif, tient la frontière : *toute fonction du runner qui pousse doit
demander une phrase dans la même fonction*. Un `git push` glissé dans une étape
réversible échoue le test.

**Les confirmations ne sont pas des `y`.** Pour le push forcé et la suppression
des refs, le runner fait taper une phrase, comme GitHub l'exige pour supprimer
un dépôt. Un `y` se tape par réflexe, et c'est le réflexe qu'on veut
interrompre. La comparaison est stricte — ni casse ignorée, ni espaces rognés,
ni abréviation : rendre la saisie plus facile la rendrait plus réflexe, ce qui
est l'inverse du but. Onze saisies (`y`, `oui`, la casse changée, un espace en
trop, un préfixe) sont testées et doivent toutes échouer, et une douzième — la
phrase exacte — doit passer, sans quoi « tout refuser » suffirait.

Les six corrections de procédure vivent **dans l'étape qui les concerne**, pas
seulement dans l'en-tête : c'est l'étape qu'on lit en la faisant. Les tags
(l'étape 5 énumère et supprime aussi `refs/tags/`) ; les `refs/pull/*`, nommées
comme non supprimables **avec la raison** — GitHub les gère — pour qu'on ne
cherche pas un problème de droits ; `dev` qui se repointe sur le nouveau `main`
au lieu de se supprimer (0 commit propre, mais 21 commits de données
atteignables : ancienne, pas grosse — il n'y a donc pas de contradiction avec la
politique « ne jamais supprimer `dev` ») ; le dépôt cible **résolu et affiché**
avant qu'on demande qu'aucun run n'y tourne, l'ambiguïté n'apparaissant qu'à la
première répétition ; le coût d'entrée de 4,9 Go et 45 s annoncé avant l'étape 3.

**Une décision rendue ici, et qui ne l'était nulle part : la durée de vie du tag
de sauvegarde** `archive/pre-borne-<date>`. C'est la seule reprise immédiate en
cas de regret, et elle ne fonctionne que tant que GitHub n'a pas ramassé les
objets. Règle retenue : **le garder jusqu'à ce que les deux conditions soient
remplies** — une visite Software Heritage `full` couvrant l'historique d'AVANT
la coupure (c'est le moment où l'archive prend le relais) *et* une CI verte sur
l'historique borné avec un run de données passé —, **avec un plancher de 30
jours**, la fenêtre elle-même (#551 : un mois de données), au-delà duquel un
regret ne porte plus sur cette coupure-ci. Après ce point, le tag ne fait plus
que retenir des objets, et le supprimer est le geste correct, pas un oubli. Il
ne doit **jamais** être poussé sur le dépôt borné : il y garderait tout
l'historique atteignable et le gain serait nul.

L'étape 2b passe `--fenetre` à la vérification et lit `PIPESTATUS` : `| tee`
remplace sinon le verdict par le succès de `tee`, et la précondition « le
verdict n'est pas MANQUANTS » serait verte en toutes circonstances. Un garde-fou
qui ne garde rien — la même forme que le défaut de #575, sur un troisième axe.

Le runner **ne décide pas quand**, et ne se déclenche jamais tout seul : aucun
workflow ne l'appelle, il ne porte pas de `cron`, et un test l'interdit. C'est la
ligne de la question 2 de #551 — la détection est armée, la réécriture reste
manuelle. Un runner interactif ne la franchit pas ; il rend la manualité fiable
au lieu de la laisser à la mémoire de l'opératrice.

## Ce que les tests peuvent dire, et ce qu'ils ne peuvent pas

Le runner porte des gestes irréversibles : on ne peut pas le dérouler pour le
tester. Il est donc **sourçable** — exécuté il déroule, sourcé il ne fait que
définir ses fonctions —, ce qui permet de tester pour de vrai les
confirmations, les préconditions, l'ordre et la résolution du dépôt cible, avec
une saisie au bout d'un tuyau et un faux `gh` posé dans `PATH`, sans jamais
approcher d'un `git push` ni du réseau (AGENTS.md §3). Le reste — les six
corrections de procédure — est fait de recherches de motif, qui attrapent la
disparition d'un point et non sa dénaturation. C'est la même limite que
`test_borner_historique_donnees.py`, et la même raison de les garder.

**Les tests ont été éprouvés par mutation**, comme #555, #567, #568 et #574 :
15 mutations pour #575 (l'origine recodée en dur, le remote ignoré, la
normalisation neutralisée puis rendue aplatissante, le marquage des conservés
supprimé puis généralisé, les conservés recomptés comme manquants, la coupure
décalée d'un commit, l'ascendance inversée, la mention d'audit retirée, le motif
de commit recopié…) et 19 pour #576 (le `y` accepté, la casse ignorée, la
dérogation muette, l'ordre non imposé, les tags oubliés, `dev` supprimée,
`PIPESTATUS` perdu, un `gh` muet valant feu vert, le dispatch inverti, un push
glissé dans une étape réversible…). **34 mutations, 34 tuées** — dont trois qui
ont d'abord survécu et ont fait resserrer les tests : la prose de l'étape 2b
contenait le mot `--fenetre` que le test cherchait, le commentaire expliquant
`PIPESTATUS` contenait le mot que le test cherchait, et l'en-tête nommait les
`refs/pull/*` que le test cherchait dans l'étape. Trois fois le même piège :
**chercher un mot là où il faut chercher la ligne qui agit.**

## Ce qui reste à établir, en session supervisée

Le critère de validation de #576 — dérouler le runner de bout en bout sur un
jetable et vérifier qu'il s'arrête là où il doit — **n'a pas été exécuté**. Il
exige de repasser `test_procedure_bornage_issue_569` en public (les *rulesets*
ne sont pas disponibles sur un dépôt privé en offre gratuite), d'y re-répliquer
`20260729_ruleset`, de re-synchroniser le miroir, puis d'enchaîner trois points
de non-retour sur le compte de l'utilisatrice. Rien de tout cela n'est
automatisable sans risque, et la fenêtre de confusion se rouvre pendant toute la
durée du test — le miroir reproduit le README et le `CNAME` du vrai dépôt.

Reste également non constaté, et hérité de #569 : **l'échec attendu du push
forcé pour un acteur sans dérogation de rôle**. C'est la garantie que la
réécriture ne peut pas être automatisée par accident. Elle demande un jeton
non-administrateur.

