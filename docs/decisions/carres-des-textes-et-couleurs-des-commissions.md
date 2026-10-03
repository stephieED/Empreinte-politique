<a id="carres-des-textes-et-couleurs-des-commissions"></a>

# « Ce qu'il a proposé » : un carré par texte, une barre découpée par texte, une couleur fixe par commission (2026-10-01)

`2026-10-01`

> **En bref** — Deuxième lot de la revue d'ergonomie de la fiche candidat
> ([`retour-ux-sur-les-fiches-candidat`](retour-ux-sur-les-fiches-candidat.md)),
> arrêté sur maquette avec la propriétaire. **Trois décisions, sur la seule
> section 2 de la seule fiche candidat.** (1) Les textes portés à l'Assemblée se
> lisent en **carrés** — un par texte, rangé à l'étape la plus avancée qu'il a
> atteinte, dans quatre colonnes toujours affichées ; la cascade en rubans reste
> la figure du **versant européen** et de la **fiche de groupe**. (2) La barre
> des amendements est **découpée par texte**, et la colonne « ratio par texte »
> part avec sa seconde barre : le rapport se lit dans la barre, **aucun quotient
> n'est publié**. (3) Chacune des **huit commissions permanentes** reçoit une
> **couleur fixe**, la même dans les deux cartes et sur toutes les fiches ; elle
> suivait le rang, et « Affaires sociales » était indigo sur les textes portés de
> François Ruffin, bleu clair sur ses amendements. Les teintes sont **calculées** :
> les huit passent les cinq contrôles de `validate_palette.js` toutes paires.

Ancres : `rangerEnCarres`, `ETAPES_DES_CARRES`, `carreEclaire`, `faitDuTexte`,
`CarresTextes`, `Mention493`, `ListeCascade`, `textesDeLaSelection`,
`segmentsParTexte`, `Matieres`, `TEINTE_COMMISSION_PERMANENTE`,
`familleDeCommission`, `teinteCommission`.

## Contexte

Le retour d'ergonomie du 01/10/2026 nommait le Sankey des textes portés
« illisible pour le grand public », avec un risque précis : une barre courte en
fin de flux se lit comme un échec (§2 règle 1). La décision qui consignait ce
retour posait deux interdits — **pas de taux d'adoption** (§6), **pas de notice
sous la figure**. La réponse devait donc être une autre forme, pas un texte.

Trois défauts mesurés sur la section, le 01/10/2026 :

| Défaut | Mesure |
| --- | --- |
| Un ruban répond « combien », jamais « lesquels » | 6 textes portés publiés chez François Ruffin, et il faut cliquer pour en lire un seul |
| Le ratio écrase ce qu'il résume | « Commission spéciale retraite » : 2 553 amendements sur 2 textes, publié « 1 277 par texte » — l'un en a reçu 2 471, l'autre 82 |
| La couleur change de sens d'une carte à l'autre | Sur la fiche de François Ruffin, « Affaires sociales » est `#332288` sur les textes portés et `#88ccee` sur les amendements ; « Lois » `#88ccee` puis `#999933` |

Le troisième vient de la règle d'attribution : `teinteMatiere` donne la première
teinte à la matière la plus fréquente, et les deux cartes ne classent pas pareil
— l'une compte des textes portés, l'autre des amendements.

## Décision

### 1. Un carré par texte

Quatre colonnes dans l'ordre de la procédure — examiné en commission, discuté en
séance, adopté, promulgué — et dans chacune **un carré par texte**, à la teinte
de sa commission. Le rangement vit dans `utils/carresTextes.js`, qui ne rend
rien et se vérifie hors navigateur ; le composant est `CarresTextes.jsx`.

- **Une colonne à zéro reste affichée.** « 0 adopté » est un fait de la fiche,
  et sans la colonne, « promulgué » se lirait comme l'étape qui suit « discuté en
  séance ».
- **`inscrit_ordre_jour` se range avec « examiné en commission »** : le texte a
  passé la commission et n'a pas été discuté. Il garde son vrai stade au survol
  et dans la liste.
- **Une colonne est une étape atteinte, jamais un sort.** Le sort, quand la
  source le publie, s'écrit au survol et dans la liste, à côté de l'étape ; un
  sort absent s'écrit « Sort non résolu » (§2 règle 5).
- **Trois gestes, un état.** Un carré ouvre son texte, l'en-tête d'une colonne
  les textes de l'étape, une entrée de légende ceux de la commission. La
  sélection reste celle de la cascade — un intervalle de crans — étendue de deux
  clés : `texte` (un carré est un texte, il n'y a rien à croiser) et `famille`
  (l'entrée de légende, qui réunit les commissions spéciales).
- **La liste est toujours `ListeCascade`.** Une seule façon d'écrire un texte,
  son stade, son sort, et les deux colonnes par institution de #689. La maquette
  dessinait une liste plus simple, sur une ligne ; elle n'a pas été reprise —
  elle aurait perdu le rôle et la colonne « Au gouvernement ».
- **Le 49.3 garde sa mention et son comportement** : il filtre la liste et
  laisse la figure intacte. La mention est sortie de `Cascade` en composant
  (`Mention493`), parce que les deux figures la portent.

Contrôle, hors navigateur, par l'adaptateur de l'application sur le corpus du
dépôt : François Ruffin, 6 textes rangés 2 · 3 · 0 · 1, légende Affaires sociales
4, Lois 1, Matière non établie 1 ; Édouard Philippe, 170 textes rangés
9 · 5 · 5 · 151.

### 2. La barre découpée par texte

La barre d'une commission est découpée en segments : **un segment par texte
amendé**, large comme le nombre d'amendements déposés dessus, du plus grand au
plus petit. Les données existaient — `chute.dossiersParMatiere`. La colonne
« ratio par texte » et sa barre disparaissent ; restent le libellé, la barre,
« amendements » et « textes distincts ».

**La barre ne se découpe que si ses segments font le total.** La ligne compte
les dépôts datés, `dossiersParMatiere` ceux qui ont un dossier : quand les deux
sommes diffèrent, la barre reste d'un seul tenant plutôt que de dire une
répartition que la donnée ne porte pas (§2 règle 5). Chez François Ruffin, les
11 lignes se découpent, et « Commission spéciale retraite » montre deux segments,
2 471 et 82.

Ce n'est pas un taux d'adoption, et rien n'y ressemble (§6) : la barre ne compte
que des dépôts.

### 3. Une couleur fixe par commission permanente

`utils/commissions.js` porte la table. Huit commissions permanentes, huit
teintes ; **toutes les commissions spéciales partagent un gris** — elles naissent
et meurent avec leur texte, leur donner une couleur ouvrirait une palette sans
fin — et « Matière non établie » prend un gris plus clair, parce que ce n'est pas
une matière mais une absence (§2 règle 5).

Les teintes partent de la palette « muted » de Paul Tol, celle de
`utils/matiere.js`. Telles quelles, elles échouaient au validateur de la
compétence `dataviz` (`validate_palette.js`, fond `#ffffff`, `--pairs all` —
un carré a n'importe quelle autre commission pour voisin) : clarté hors bande
(`#332288`, `#88CCEE`), chroma sous le plancher (`#88CCEE`, `#44AA99`), paire la
plus proche en vision normale à ΔE 13,0. Chacune a été corrigée **dans sa
famille** (teinte à ±12° de l'origine), au plus près du point de départ.

| Commission | Départ | Retenue |
| --- | --- | --- |
| Affaires culturelles et éducation | `#CC6677` | `#f16675` |
| Affaires économiques | `#882255` | `#882255` |
| Affaires étrangères | `#332288` | `#463fa0` |
| Affaires sociales | `#88CCEE` | `#259ce6` |
| Défense | `#117733` | `#137731` |
| Développement durable | `#AA4499` | `#ab47aa` |
| Finances | `#44AA99` | `#09a68b` |
| Lois | `#999933` | `#9d9201` |
| Commissions spéciales | `#8d8894` | `#6e6a72` |
| Matière non établie | `#d2cec7` | `#b5b3af` |

Verdict du validateur, mesuré le 01/10/2026 :

| Jeu | Bande de clarté | Plancher de chroma | Daltonisme (toutes paires) | Vision normale | Contraste |
| --- | --- | --- | --- | --- | --- |
| Les huit teintes | PASS | PASS | PASS — pire paire ΔE 8,1 (deutéranopie) | PASS — ΔE 15,1 | PASS — toutes ≥ 3:1 |
| Les dix, gris compris | PASS | **FAIL** — les deux gris, 0,013 et 0,006 | PASS — ΔE 8,1 | PASS — ΔE 15,1 | WARN — `#b5b3af` à 2,09:1 |

Le seul échec du jeu de dix est **voulu** : un gris est sous le plancher de
chroma par définition, et c'est ce qui dit qu'il n'est pas une teinte de plus.
L'avertissement de contraste porte sur le gris clair, que la légende et le
survol nomment.

**La couleur ne porte jamais seule l'identité** : la légende nomme chaque teinte,
la ligne d'amendements écrit sa commission, le carré la dit au survol et dans la
liste. **Aucun texte ne prend la couleur d'une commission** — encre et gris
seulement.

## Ce que le validateur ne dit pas

Il ne compare pas la palette aux autres couleurs de la fiche — la vérification
reste manuelle (`DESIGN_SYSTEM.md` §2). Mesuré : **« Défense » (`#137731`) est à
ΔE 2 du vert « pour / adopté » (`#007A45`)**, et c'était déjà le cas du point de
départ `#117733`. La section 2 ne dessine aucune position de vote, mais sa liste
de dossiers écrit « N adoptés » dans ce vert. L'écart n'a pas été corrigé ici :
sortir « Défense » de la famille verte est un choix de teinte, qui revient à la
propriétaire. Les sept autres sont à ΔE 11 ou plus du rouge « contre » et à ΔE 15
ou plus du vert.

**La tritanopie n'entre dans aucun de ses seuils**, il la rapporte seulement — et
elle s'est dégradée : la pire paire des huit teintes passe de ΔE 9,3 au départ à
**3,6**, sur « Affaires sociales » / « Finances » (un bleu et un sarcelle de
clarté voisine). Imposer ΔE ≥ 6 en tritanopie a été essayé : la seule palette
trouvée poussait « Affaires sociales » vers un bleu pétrole sombre (`#025785`),
très loin du bleu clair de départ. Écarté — la forme de daltonisme est la plus
rare des trois, et les deux commissions restent nommées partout où elles sont
teintées.

## Ce que ce lot ne couvre pas

- **Le versant européen des textes portés** garde la cascade à un palier : ses
  seize stades ne s'ordonnent pas (#901), et quatre colonnes « dans l'ordre de
  la procédure » leur prêteraient une échelle. Il n'a pas été maquetté.
- **La fiche de groupe et la fiche de gouvernement** gardent `teinteMatiere`, la
  teinte au rang. Une commission n'a donc pas encore la même couleur d'un type
  de fiche à l'autre.
- **La page de méthodologie** écrit encore « un ruban, une barre ou une
  étiquette ouvre la liste » : vrai de la cascade, qui reste sur deux figures,
  faux des carrés. Le texte publié n'a pas été touché.
- **Le rendu** — survol, clic, clavier, téléphone, 151 carrés dans une colonne —
  n'a pas été regardé dans un navigateur par ce lot.

## Alternative écartée

**Garder la teinte au rang et la fixer par fiche**, en imposant aux deux cartes
l'ordre de l'une : la couleur serait devenue stable sur une fiche, pas d'une
fiche à l'autre, et un lecteur qui compare deux candidats aurait appris deux
légendes. Le référentiel étant fermé — huit commissions —, rien n'obligeait à
ce compromis.

**Publier le ratio autrement** (une médiane, un maximum) : c'était remplacer un
quotient par un autre. La barre découpée montre la répartition entière sans
ajouter un chiffre.
