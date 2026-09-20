# L'accueil dit depuis quand chaque institution est lue, et nomme les mandats hors couverture — 11/09/2026 (#328)

`2026-09-11`

> **En bref** — un candidat dont la carrière précède ce que publient les sources voit une partie de son parcours absente de sa fiche, et la propriétaire veut que le lecteur le sache **dès l'accueil**, sans ouvrir `/couverture` ; « Sources & fraîcheur des données » passe en tête de la colonne de droite et s'ouvre sur **une borne par institution**, sans le détail des listes, rendue en maquette puis annotée (artifact `a946d942`, cinq versions) ; en dessous, **« Les mandats hors couverture »** nomme les fiches concernées, calculées au build : **2** avec un mandat au Sénat collecté mais non exploitable, **11 sur 30** sans aucun mandat dans le corpus (« Mandats locaux et autres ») ; la troisième ligne, « Mandat antérieur à la publication des données de l'Assemblée nationale », **se lit dans un champ de la fiche relu à la main** (#860), car la règle calculable sur le corpus — « premier mandat lu le 19/06/2002 » — se trompait sur **3 des 5 cas** vérifiés sur Sycomore, senat.fr et Légifrance ; la hachure d'une institution n'est dessinée que si **toutes** ses listes déclarent une borne, d'où **aucune hachure pour le Gouvernement**, dont la borne était empruntée à l'AMO30 alors que le corpus ne porte aucune fonction gouvernementale avant le 18/05/2007 (#859) ; « Un fait, une source », un fait fictif relevé par l'audit du 29/08, est retiré ; l'accroche devient « … des parcours **politiques** ».

## Contexte

`/couverture` dit, liste par liste, ce que le dépôt porte et depuis quand. Personne
n'y va avant d'avoir été surpris. Un lecteur qui ouvre la fiche de Ségolène Royal,
députée depuis 1988, n'y trouve rien avant 2002 : sans l'avoir lu avant, il conclut
à une carrière qui commence là.

## Décision

**Une ligne par institution**, dans sa teinte, avec « depuis » et l'année : Assemblée
nationale 2002, Gouvernement 2007, Parlement européen 2004 ; Sénat « non collecté »
(jaune) ; mandats locaux « aucune source » (hachure). Le détail des listes reste sur
`/couverture` — c'est la relecture de la propriétaire : « juste les bornes par
institution, pour que quelqu'un ne se demande pas pourquoi le mandat d'un tel n'est
pas visible ».

**`debut` est la plus ancienne date qui ouvre une liste** — sa borne déclarée, ou sa
première donnée. **`hachureJusqua` n'existe que si toutes les listes de l'institution
déclarent une borne.** La hachure affirme « la source ne publie rien avant » ; une
liste sans borne suffit à ne plus pouvoir le dire de l'institution entière.

| Institution | Début | Hachure | Pourquoi |
| --- | --- | --- | --- |
| Assemblée nationale | 2002 | jusqu'en 2002 | les cinq listes déclarent une borne ; la plus ancienne est celle des mandats (AMO30) |
| Gouvernement | 2007 | aucune | les fonctions n'ont plus de borne : celle de l'AMO30 leur était prêtée à tort (#859) |
| Parlement européen | 2004 | aucune | les mandats européens n'ont pas de borne de source |

**Les noms sont calculés au build** (`couverture.json`, bloc `accueil`), rangés par nom
de famille, chacun menant à sa fiche. « Mandats locaux et autres » est la formulation
retenue par la propriétaire pour les fiches sans aucun mandat dans le corpus.

**La ligne des mandats antérieurs se lit sur la fiche.** Vérifié le 11/09/2026
sur les sources officielles : Ségolène Royal, Nicolas Dupont-Aignan, Bernard
Cazeneuve, Bruno Retailleau et Jean-Luc Mélenchon ont exercé un mandat national
avant ce que publient les sources. La règle « premier mandat lu le jour de la
borne » n'en retrouvait que deux. La propriétaire a tranché pour une table relue
à la main, portée par chaque fiche sous `mandats_anterieurs` (#860, PR #861) ;
l'accueil nomme les fiches dont la liste est non vide, et une fiche « non relue »
(`null`) n'y figure pas. La ligne paraît au premier run après la fusion de #861.

## Deux sources citées, pas collectées

`mandats_anterieurs` cite, ligne par ligne, **Sycomore** (la base des députés de
l'Assemblée depuis 1789) et le **Journal officiel** via Légifrance. Validé par la
propriétaire le 11/09/2026, elles entrent dans `sources.config.js`, la page des
mentions légales et `AGENTS.md` §7, qui doivent dire la même chose : le Journal
officiel sous Licence Ouverte 2.0 (page open data de Légifrance) ; Sycomore,
publiée « © Tous droits réservés », dont seuls des faits — une fonction, deux
dates — sont repris, chacun avec son lien. Aucun collecteur ne les interroge.

## Alternative écartée

**Écrire la liste des cinq en dur dans l'interface.** Elle est vraie aujourd'hui, et
elle serait fausse au premier candidat qui se déclare. La propriétaire l'a écartée :
l'information se collecte sur la fiche.

**La frise de `/couverture` en miniature, ou un tableau des bornes par liste.**
Rendues en maquette : la première fait 17 lignes pour un visiteur qui arrive, la
seconde ne montre rien.
