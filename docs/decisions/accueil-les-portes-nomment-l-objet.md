<a id="accueil-les-portes-nomment-l-objet"></a>

# L'accueil : les portes nomment l'objet, l'encart nomme son événement (2026-09-30)

`2026-09-30`

> **En bref** — Sept arbitrages de la propriétaire, rendus l'un après l'autre sur
> la maquette de l'accueil l'après-midi du 30/09/2026, et implémentés le même
> jour. Le principe de la forme B — deux portes permanentes, les candidats sous
> leur borne — ne bouge pas ; c'est son EXÉCUTION qui change.
> **Les trois portes nomment leur objet et perdent le mot « Par »**, ce qui règle
> d'un coup le singulier/pluriel et la contradiction avec « une porte est un
> objet, pas un filtre ». L'encart passe de la borne au sujet, la borne
> reparaissant en pastille sur la carte. La troisième case du concept devient
> « L'EMPREINTE ». Ce fichier ne remplace pas
> [`accueil-deux-portes-et-le-concept-en-mots-cles`](accueil-deux-portes-et-le-concept-en-mots-cles.md)
> : il dit ce que la journée a changé dedans.

## Les sept arbitrages, et ce qu'ils remplacent

| Endroit | Ce qui était écrit le matin | Ce qu'elle a arbitré |
| --- | --- | --- |
| Titre du Hero | « L'explorateur neutre et sourcé des parcours politiques. » | « Explorez l'action politique à partir des données officielles. » |
| Case 3 du concept | « Les parcours » | « L'EMPREINTE » |
| Titre de l'entrée | « Commencer à explorer » | « Commencer l'exploration » |
| Amorce | « Un groupe, un gouvernement ou une personne : … Chaque fait porte le lien vers sa source. » | « Retrouvez l'intégralité des publications institutionnelles par groupe, gouvernement ou candidat : mandats, votes, textes et interventions. » |
| Surtitre de l'encart | « Jusqu'à l'élection d'avril 2027 » | Étiquette « ÉVÉNEMENT » sur sa ligne, puis une **liste** : « Focus sur l'élection présidentielle 2027 » |
| Borne du volet | portée par ce surtitre | **pastille à cheval sur le coin** de la carte : « Jusqu'en mai 2027 » |
| Les trois portes | « Par groupes parlementaires », « Par gouvernement », « Par candidats déclarés » | « Groupes parlementaires », « Gouvernements », « Candidats déclarés » |

## Pourquoi les portes perdent « Par »

Les libellés ne suivaient **aucune règle** : deux au pluriel, un au singulier.
`accueil-deux-portes-et-le-concept-en-mots-cles` le notait comme ouvert et ne le
tranchait pas. Trois formes ont été rendues sur les vrais libellés et les vrais
volumes — 12 lignées, 17 gouvernements, 31 fiches de candidat déclaré :

| | Les libellés | Ce que ça coûte |
| --- | --- | --- |
| A | Par groupes parlementaires · Par gouvernement**s** · Par candidats déclarés | Rien à réécrire ailleurs, mais « Par » reste le mot d'un filtre |
| B | Par groupe parlementaire · Par gouvernement · Par candidat déclaré | Se lit « classé par groupe », donc un critère de tri, pas une famille de fiches |
| **C — retenue** | Groupes parlementaires · Gouvernements · Candidats déclarés | Le plus gros écart avec le rendu de la veille |

**Ce qui tranche est interne à la décision du matin** : « une porte est un OBJET,
pas un filtre » — c'est ce qui avait fait écarter les onglets. Or « Par … » est
exactement la formule d'un filtre, et le volume écrit sous chaque libellé
(« 12 fiches ») dit déjà qu'on entre dans un ensemble. La forme C règle le
singulier/pluriel **et** retire la contradiction ; A ne réglait que le premier.

## L'encart nomme son sujet, la pastille porte la borne

Le surtitre disait **quand** le volet s'arrête. Il dit maintenant **de quoi il
s'agit**, et la borne est passée sur la carte. Trois points de forme s'en
déduisent, et aucun n'est cosmétique.

**L'étiquette est sur sa ligne et le sujet est une liste**, parce qu'il pourra y
en avoir plusieurs — c'est la raison qu'elle a donnée. « Événement : … » se casse
au deuxième ; une liste s'allonge d'un élément. Le jour où un second s'y pose,
l'étiquette passe au pluriel : **pas avant**, ce serait faux.

**La pastille dit la borne, pas la fiabilité.** « Provisoire » était proposé et a
été écarté : posé au-dessus d'une liste de fiches, il se lit sur les **faits**,
qui sont sourcés exactement comme ceux des groupes (§2 règle 2). C'est le volet
qui est borné, pas la donnée.

**Elle est à cheval sur le coin supérieur droit de la carte**, et non au-dessus du
bloc : une étiquette posée sur l'objet qu'elle qualifie n'a pas à dire lequel.
Elle **déborde** — rien ne la clipe, aucun ancêtre ne porte d'`overflow` —, d'où
son fond opaque : sans lui, le filet de la carte passerait derrière son texte.
Elle ne prend **ni l'accent ni le cyan** : le jaune signal vaut 1,05:1 en bordure
sur fond clair et ne colore jamais du texte (DESIGN_SYSTEM §2), et `--notice` est
réservé aux bandeaux d'état du projet. Elle reprend donc des tokens déjà posés —
le gris `#6f6b78` des pastilles sans mandat, 5,5:1 sur blanc, sur le fond de
survol du pied de page.

Posée **dans** le bouton, elle entre dans son libellé accessible : la porte
s'annonce « Jusqu'en mai 2027, Candidats déclarés, 31 fiches ». La borne se lit
donc avant le nom de la porte — c'est exact, et informatif plutôt que décoratif.

**La borne dit mai, quand la décision du matin disait avril.** Le premier tour est
en avril ; « mai » laisse le volet en ligne quelques semaines après le scrutin.
C'est ce qu'elle a écrit, et c'est la pastille qui fait foi : ce fichier est
l'endroit où les deux cessent de se contredire.

## Ses textes sont les siens, et une réserve se signale une fois

Deux formulations ont été « corrigées » plus tôt dans la journée et elle a
répondu : « pourquoi tu as modifié mon texte ? Reprends exactement ce que je t'ai
donné ». La règle qui en sort : **signaler une réserve une fois, puis appliquer au
mot près.**

Deux réserves ont été signalées et écartées par elle, et il ne faut pas les
rouvrir :

- **« l'intégralité des publications institutionnelles »** est plus large que ce
  que `/sources` déclare couvrir — rien avant juillet 2012, le Sénat sans vote ni
  prise de parole, dossiers et interventions à partir de la XVe. La phrase reste.
- **« une fiche par élu »** était faux pour 12 des 33 candidats déclarés, qui
  n'ont aucun mandat. Cette formulation-là a disparu d'elle-même quand son
  amorce suivante a nommé les trois familles.

Un effet de bord à connaître : **« Chaque fait porte le lien vers sa source. » a
quitté l'accueil** avec l'ancienne amorce. C'était le seul endroit où la
traçabilité était écrite au lecteur. Le bandeau garde « 100 % sourcé » et la case
« Sources officielles » mène à `/sources`, donc rien n'est perdu de la page ; la
promesse n'y est simplement plus dite en toutes lettres. Signalé, non tranché.

## Deux points ouverts se ferment, un reste

**« Par gouvernement » au singulier : fermé** par la forme C.

**Le mot « parcours » : fermé sur l'accueil, par les faits.** Le recadrage
l'avait ouvert comme une question de fond — un parcours est le mot d'une
personne, il convient mal à un gouvernement et pas du tout à une lignée de
groupe. Le mot a quitté le titre avec le nouveau H1, l'amorce avec la nouvelle
phrase, puis la case 3 avec « L'EMPREINTE » : **zéro occurrence sur l'accueil**,
mesuré le 30/09/2026. Il reste à vérifier les autres pages avant de clore le
point pour de bon — le `<title>` d'`index.html` porte encore « les parcours
politiques des candidats », et il porte aussi « Présidentielle 2027 », donc
l'ancienne hiérarchie.

**« Groupes parlementaires » mène aux 12 LIGNÉES, pas aux 29 groupes : ouvert.**
C'est le mot du site, mais il ne désigne pas la même chose, et le nombre annoncé
sur la porte ne le dit pas. Ni la forme C ni le volume ne règlent ça.

## Ce qui n'est pas arbitré, et qui est en code quand même

**« Explorateur » ne paraît pas sur l'accueil, par une règle conditionnelle à la
route** (`pathname === '/'` dans `NavigationSite.jsx`). La décision du matin
laissait explicitement le choix ouvert entre retirer l'onglet partout et le
retirer sur l'accueil seul. Le conditionnel est retenu **par défaut**, parce que
`NavigationSite` est partagé et que l'onglet reste le seul raccourci vers les
fiches depuis les pages de contenu. Un test le tient
(`test_explorateur_ne_parait_pas_sur_l_accueil`), donc un retrait partout casse
la garde et ne passe pas inaperçu.

## Ce que la journée n'a pas changé

Le principe de la forme B, les onglets écartés, les listes masquées à l'arrivée,
la surbrillance qui tourne, le bloc « Le concept » en trois listes de même forme,
« agrégation » et non « traitement », la pastille jaune retirée du Hero. Aucune
règle de `AGENTS.md` §2 n'est touchée. Le grisé des fiches sans mandat survit au
changement de forme, avec son infobulle.

## Ce qui a été corrigé au passage

**Deux gardes épinglaient un libellé, pas le fait qu'elles disaient tenir.**
`test_l_accueil_ne_montre_plus_de_fait_fictif_ni_sa_frise` lisait « parcours
politiques » dans le H1 : elle aurait échoué au premier changement de titre, sans
qu'aucun fait fictif ne soit revenu. Elle vérifie maintenant l'absence des
classes de l'exemple inventé. L'autre épinglait « Commencer à explorer ».

**Le test d'ancres de méthodologie ne savait pas lire un tiret.** Ses trois motifs
étaient `[a-z]+` : il ne validait que les ancres en un mot, coupait les autres au
premier tiret, et n'aurait donc pas vu un renvoi faux vers une ancre composée.
Corrigé en `[a-z-]+`, ce qui vaut indépendamment de ce lot.

**L'amorce était bornée à 64ch** dans une carte bien plus large : la rupture se
voyait davantage que le confort de lecture ne se gagnait.
