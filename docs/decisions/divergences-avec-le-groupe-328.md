<a id="divergences-avec-le-groupe-328"></a>

# « Ses divergences » : une bande qui montre sans compter (#328) (2026-09-08)

`2026-09-08`

> **En bref** — la section publiait la seule **liste** des scrutins où la position d'une personne diffère de celle de son groupe : juste, et **muette pour dix des treize candidats déclarés** — trois ont une base réelle et zéro divergence (Attal 108/0, Le Pen 108/0, Ruffin 56/0), six n'ont aucune fiche de groupe ; **onze faits pour treize pages** ; une **bande** — un scrutin par colonne, dans l'ordre du temps — donne désormais à voir, **sans compter**, si la personne s'écarte et dans quel groupe ; **c'est §2 règle 7 qui décide de la forme entière** — « a voté contre son groupe 47 fois » y est nommé mot pour mot comme l'indice individuel interdit —, d'où trois conséquences : la bande fait lire **d'abord ce que fait le groupe** et la divergence en second (une variante en frise, qui ne montrait qu'elles, a été dessinée puis écartée parce qu'elle met le nombre au premier plan), le compte des scrutins communs **toutes natures** n'est plus affiché — il servait de dénominateur à une division que le lecteur faisait seul, et avec le **mauvais nombre** (2 831 chez Guedj quand la base est **172**) —, et la pastille du commutateur est **binaire** ; **trois faits, trois éléments, jamais deux faits sur le même** : socle coloré = ce qu'a voté le groupe, barre en encre = les membres qui n'ont pas suivi, point cerclé = ses divergences — deux encodages successifs coloraient la colonne par la position majoritaire tout en la dimensionnant par les votes qui ne la suivaient pas, et la propriétaire a nommé l'incohérence avant nous ; le point n'est **coloré que sur une divergence** (colorer les 172 repères faisait de la teinte une texture) et garde un signal de **forme**, deux gris de la palette étant proches ; **les étiquettes passent à gauche**, à la hauteur de leur rang, la gouttière étant payée par l'écart entre colonnes ramené à 1 px — mesuré, une colonne passe de **2,97 à 3,03 px**, la densité ne bouge pas ; « quorum non atteint » devient « **moins de la moitié du groupe s'est exprimée** » (règle vérifiée dans `group_profile.py`, seuil 0,5 sur les éligibles) et le scrutin **n'est pas écarté** — choisir les faits qui arrangent serait pire ; **trois vides, trois causes**, dont une seule est un fait sur la personne ; `ecartsAvecLeGroupe` quitte `profilCandidat.js` pour `utils/ecartsGroupe.js`, `fiches[]` porte les **dates** de `periode` au lieu des comptes, et la méthodologie gagne l'ancre `#ecarts` sans laquelle le renvoi menait à un contenu absent ; **reste ouvert** : les 7 fiches de groupe déclarées par #778 (XVe : FI, NG, SOC, EDS, GDR ; XVIe : ECOLO, GDR) ne sont **pas encore produites** — le jour où un run les écrit, la section gagne des bases pour Mélenchon, Ruffin, Attal et Faure sans qu'une ligne change. 19 tests neufs, suite complète à 4 128, 0 échec.

## Le contexte

La section publiait la seule **liste** des scrutins où la position d'une
personne diffère de la position majoritaire de son groupe. Elle était juste, et
elle était muette pour **dix des treize** candidats déclarés.

Mesuré au commit de données `a48e92e3`, sur les votes sur l'ensemble d'un texte
communs à leurs positions et aux fiches de groupe publiées :

| Candidat | Base comparable | Divergences | Groupe divisé sur |
| --- | ---: | ---: | ---: |
| Jérôme Guedj | 172 | 4 | 45 |
| Philippe Brun | 165 | 5 | 41 |
| Olivier Faure | 120 | 2 | 37 |
| Gabriel Attal | 108 | **0** | 47 |
| Marine Le Pen | 108 | **0** | 16 |
| François Ruffin | 56 | **0** | **0** |
| six autres | 0 | 0 | — |

Trois personnes avaient donc une base réelle et une section vide, et six n'ont
aucune fiche de groupe publiée. **Onze faits pour treize pages.**

## La décision

La section porte une **bande** — un scrutin par colonne, dans l'ordre du temps —
qui donne à voir, sans compter, si la personne s'écarte et **dans quel groupe**.

### La règle qui décide de la forme entière

`AGENTS.md` §2 règle 7 interdit de publier le **nombre** de divergences :
« a voté contre son groupe 47 fois » y est nommé mot pour mot comme l'indice
individuel mesuré contre la moyenne d'un groupe, par un autre chemin. Ce qui est
publiable est la **juxtaposition, scrutin par scrutin**, et la **dispersion du
groupe**, qui est un fait de groupe et porte son dénominateur.

Trois conséquences, toutes tentantes à défaire :

- **La bande fait lire d'abord ce que fait le groupe**, la divergence en second.
  Une figure qui met les divergences au premier plan est le compte par un
  troisième chemin — c'est pourquoi une variante en frise, qui ne montrait
  qu'elles, a été dessinée puis écartée.
- **Le nombre de scrutins communs toutes natures confondues n'est plus
  affiché.** Posé à côté des divergences, il servait de dénominateur à une
  division que le lecteur faisait seul — et avec le mauvais nombre : **2 831**
  chez Jérôme Guedj quand la base réelle est **172**. Il reste calculé, parce
  qu'il distingue deux vides.
- **Le commutateur de la maquette porte une pastille binaire** — « il s'écarte »
  ou non —, jamais un compte.

### Trois faits, trois éléments, jamais deux faits sur le même

De bas en haut :

| Élément | Ce qu'il porte |
| --- | --- |
| **Le socle**, filet coloré | ce qu'a voté son groupe, une teinte par scrutin |
| **La barre**, en encre neutre | combien de ses membres n'ont pas suivi |
| **Le point**, coloré et cerclé | les scrutins où elle-même diverge |

**Deux encodages ont été essayés et portaient la même incohérence** : la colonne
était colorée par la position majoritaire du groupe alors que sa hauteur
comptait les votes qui ne la suivaient pas. Deux faits opposés sur un seul
objet ; on pouvait y lire que la couleur qualifiait la hauteur. La propriétaire
l'a nommée avant nous.

La barre reste **rare**, ce qui la fait ressortir : un groupe uni ne pose rien
au-dessus de son socle. C'était la qualité de la première version, perdue dès
qu'on dessinait tous les votes exprimés — la figure devenait bruitée.

**Le point n'est coloré que sur une divergence.** Colorer les 172 repères
mettait la même emphase sur ce qui se répète et sur ce qui est rare : la teinte
cessait d'être un signal pour devenir une texture. Il garde un signal de
**forme** en plus de la couleur — sur 172 repères, un point cerclé se trouve
plus vite qu'un désaccord de teinte, et deux gris de la palette sont proches.

### Les étiquettes contre la figure, pas sous elle

Les trois rangs sont nommés **à gauche**, chacun à la hauteur exacte du rang
qu'il désigne. Une légende sous un graphique oblige à l'aller-retour : on lit un
symbole, on descend, on remonte.

Ce que la gouttière prend en largeur est rendu par l'écart entre colonnes,
ramené de 2 px à 1 px. Mesuré à 1 000 px de page : une colonne faisait
**2,97 px**, elle fait **3,03 px**. La densité ne bouge pas.

Cela impose des rangs de **hauteur fixe** (20 px, le reste, 8 px) — c'est ce qui
permet l'alignement, et c'est aussi ce qui garde la figure lisible : le rang des
points ne grandit jamais, seul celui des barres respire. Sous 720 px la
gouttière ne tient plus ; les étiquettes y redeviennent une légende, et la bande
défile dans son propre conteneur.

### Ce que la ligne d'une divergence garde, et pourquoi

« Contre · **l'un des 14** de son groupe · face à **17 abstention** · 31
exprimés sur 31 ».

« L'un des 14 » ne se lit dans aucune largeur — c'est le seul fait que la barre
ne porte pas, et il change le sens de la divergence : être l'un des 14 face à
17 abstentions n'est pas être seul contre son groupe entier. Le nombre en face
est celui de la position **majoritaire, quelle qu'elle soit** : écrire « pour »
systématiquement serait faux dès que le groupe s'abstient, ce qui est le cas du
scrutin ci-dessus.

### Le quorum, dit en français

« Quorum du groupe non atteint » est un mot de règlement, pas une information :
il ne dit ni le seuil, ni sur quoi il porte, ni pourquoi c'est un
avertissement. La puce écrit désormais « **moins de la moitié du groupe s'est
exprimée** » — littéralement la règle, vérifiée dans `src/group_profile.py`
(`quorum_atteint` vaut `taux_participation >= 0,5` sur les membres éligibles).

Le scrutin n'est **pas écarté** pour autant. §2 règle 7 refuse un ratio sans
couverture suffisante ; la fiche le dit au lieu de taire le fait, parce que
choisir les scrutins qui arrangent serait pire que les publier avec leur
réserve. Un cas mesuré : Jérôme Guedj le 19/03/2024, 14 membres exprimés sur 31.

### Trois vides, trois causes

Une section sans divergence dit **trois choses différentes**, et les confondre
ferait lire « aucune fiche n'est publiée » comme « il n'a jamais divergé »
(§2 règle 5) :

1. aucune fiche de groupe n'est publiée pour les groupes où la personne a siégé ;
2. des fiches existent mais ne recouvrent aucun de ses votes sur l'ensemble ;
3. la comparaison est possible et aucune divergence n'y figure.

**Seule la troisième est un fait sur la personne.** Bruno Retailleau relève de
la deuxième — une fiche LR sans législature publiée et zéro scrutin commun —, ce
que les anciens comptes cachaient.

## L'alternative écartée

**Une frise ne montrant que les divergences, posées sur le temps.** Dessinée,
comparée, et écartée : très lisible, mais elle met le **nombre** au premier plan
— quatre points, on les compte. C'est exactement l'indice que §2 règle 7 refuse
d'affirmer. La bande, elle, fait lire d'abord ce que fait le groupe.

## Ce qui a bougé ailleurs

- **`ecartsAvecLeGroupe` quitte `utils/profilCandidat.js`** pour
  `utils/ecartsGroupe.js`, avec `groupeDivise` et `partDissidente`. Une seule
  implémentation, et un module de calcul que les tests peuvent lire — un calcul
  fait dans le JSX est un calcul qu'aucun test ne relit.
- **`fiches[]` porte désormais `debut` / `fin`**, lus dans le champ `periode` de
  chaque fiche de groupe. La ligne des groupes affiche des dates et non plus des
  comptes : elle dit sur quelle durée la comparaison est possible, ce qui est son
  seul rôle.
- **La page de méthodologie gagne l'ancre `#ecarts`** et la section qui va avec.
  Elle n'existait pas quand la maquette a été validée, et la section ne pouvait
  pas être livrée sans elle : un renvoi vers un contenu absent déplace la
  traçabilité au lieu de l'assurer (§2 règle 2).

## Ce qui reste ouvert

Les fiches de groupe de la **XVe législature** (`FI`, `NG`, `SOC`, `EDS`,
`GDR`) et deux de la XVIe (`ECOLO`, `GDR`) sont **déclarées dans
`raw_data/groupes_reels.json`** depuis #778 mais **pas encore produites sur
disque**. Le jour où un run les écrit, la section gagne mécaniquement des bases
comparables pour Jean-Luc Mélenchon, François Ruffin, Gabriel Attal et Olivier
Faure — sans qu'une ligne de code change ici.
