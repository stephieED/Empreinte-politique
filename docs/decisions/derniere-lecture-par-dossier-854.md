<a id="derniere-lecture-par-dossier-854"></a>

# La dernière lecture d'un texte se reconnaît aussi à son dossier (#854) (2026-10-08)

`2026-10-08`

> **En bref** — La dernière lecture d'un texte était reconnue à son seul intitulé (`docs/decisions/derniere-lecture-retenue-711.md`). Or un texte **change souvent de titre** entre deux lectures, ou revient sous la législature suivante : il gardait alors deux « dernières lectures », et la première s'affichait comme la position sur le texte. Arbitré par la propriétaire le 08/10/2026 (piste C) : **deux lectures sont celles d'un même texte si elles partagent l'intitulé, le dossier de l'Assemblée quand il est connu, ou l'intitulé assoupli dans une même législature**. 701 textes deviennent 661. Ce fichier **complète** la décision #711 : la règle « un texte, une position, la dernière lecture par la date » ne change pas, seule la façon de reconnaître un texte change.

## Le contexte

#854 signalait un cas : « projet de loi relatif » puis « relative » à
l'organisation des jeux Olympiques de 2030. Mesuré le 08/10/2026 sur `main`
98327b0c0, sur les 931 votes portant sur un texte entier
(`pivot_data/scrutins.json`), dont 669 ont un dossier connu
(`pivot_data/scrutins_dossiers.json`, #758) :

| Piste | Textes | Scrutins qui cessent d'être une dernière lecture | Fiches de candidats touchées, sur 35 | Positions retirées |
| --- | ---: | ---: | ---: | ---: |
| Aujourd'hui, l'intitulé | 701 | | | |
| A, l'intitulé assoupli | 698 | 3 | 12 | 14 |
| B, le dossier quand il est connu | 662 | 39 | 15 | 110 |
| C, les deux | 661 | 40 | 15 | 110 |

La fiche la plus touchée est celle d'Olivier Faure : 12 positions de première
lecture y étaient présentées comme sa position sur le texte.

Les 38 réunions que fait le dossier ont été relues une à une : un texte renommé
(« relative à la sécurité globale » → « pour une sécurité globale préservant
les libertés », « haine sur internet » → « contenus haineux sur internet »), ou
repris sous la législature suivante (formation de sage-femme, XVe puis XVIe).

## La décision

- `grouperLecturesParTexte(scrutins, dossiers)` réunit deux lectures dès
  qu'elles partagent **une** de trois clés : l'intitulé (`cleDuTexteVote`), le
  dossier, l'intitulé assoupli (`cleAssouplieDuTexteVote` : accents,
  ponctuation, pluriels simples, « relatif » et ses accords).
- **Le dossier traverse les législatures**, l'intitulé non : la clé d'intitulé
  garde sa législature, qui protège de deux textes homonymes.
- Le groupe porte le titre de sa **dernière** lecture, le nom sous lequel le
  texte a fini.
- La fiche candidat et la fiche de lignée passent toutes deux la table des
  dossiers ; sans elle, le regroupement retombe sur les deux clés d'intitulé.
- La méthodologie le dit : « par son dossier à l'Assemblée quand il est connu,
  sinon par son intitulé ».

## Ce que cela change au mode d'échec

La décision #711 notait que l'intitulé « échoue à regrouper, il ne rapproche
jamais à tort ». Le dossier, lui, rapproche — sur la foi de l'Assemblée, pas
d'une ressemblance de mots (#639). Un dossier mal rattaché à un scrutin dans
`scrutins_dossiers.json` réunirait deux textes : la garde est la relecture des
réunions, faite ici, et à refaire si la table change de méthode.

## L'alternative écartée

- **A seule** : ne voit pas un texte renommé, soit 37 des 40 cas.
- **B seule** : laisse le cas des biens culturels spoliés, dont le second vote
  n'a pas de dossier connu.

## Ce qui reste

- **262 des 931 votes n'ont pas de dossier connu** : un texte renommé y reste
  compté deux fois, et rien ne le détecte. Étendre la table est côté données.
- L'effet sur les fiches de groupe et de lignée n'a pas été mesuré.
- Non vérifié à l'écran.
