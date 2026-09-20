<a id="mise-en-oeuvre-des-grands-chiffres-328"></a>

# « Les grands chiffres » : la mise en œuvre, et les trois constats qu'elle corrige (#328) (2026-09-02)

`2026-09-02`

> **En bref** — le bloc de tête est écrit : `grandsChiffres()` et `pistesDuParcours()` dans `profilCandidat.js`, `GrandsChiffres` dans `CandidateProfile.jsx`, les sélecteurs `.cp-gc*` dans sa feuille. La vue de « L'essentiel » est retirée — section, `Point`, 25 sélecteurs CSS, 5 tests — mais **le vivier reste calculé et testé**, parce que la décision de la veille prévoit qu'un vrai résumé prenne la place libérée ; son retrait est à la charge de ce lot-là. Trois constats de la maquette sont corrigés par la mesure : le cas « ni l'un ni l'autre » vaut **3 des 13** et non 4 (`jordan-bardella` a un siège européen, donc une colonne), l'empreinte par commission saisie est **inerte** faute de `pivot_data/commissions_dossiers.json`, jamais produit, et la barre des textes ne publie **que ce qui est parvenu au moins en commission** (§6), en disant ce qu'elle écarte. Le rôle range le texte, jamais l'institution seule : replier `rapporteur` sur le Parlement afficherait « 3 propositions de loi » pour 2 propositions et 1 rapport. **20 tests, 9 mutations vérifiées échouantes** ; aucun runner JS dans le dépôt, donc ni mise en page, ni responsive, ni contraste, ni clavier.

[`les-grands-chiffres-fiche-candidat-328`](les-grands-chiffres-fiche-candidat-328.md)
a figé les arbitrages en maquette, sans une ligne de code. Ce fichier consigne ce
que l'écriture a appris — **la maquette avait raison sur la forme et tort sur
trois chiffres**, et un fichier de décision qui garde ses chiffres faux oriente
la décision suivante.

## 1. Ce qui est écrit, et où

| Couche | Ce qu'elle porte |
| --- | --- |
| `profilCandidat.grandsChiffres()` | les cinq lignes appariées, le cas, les colonnes |
| `profilCandidat.pistesDuParcours()` | la frise : une piste par rôle, la posture en motif |
| `CandidateProfile.jsx` — `GrandsChiffres` | la vue, dans un `<details>` |
| `CandidateProfile.css` — `.cp-gc*` | le bleu, le bronze, les cinq motifs, les deux thèmes |

**Aucune mesure n'est refaite dans l'adaptateur** : le bloc reçoit `roles`,
`bornes`, `mandats`, `amendements`, `textes`, `interventions`, `appartenances`
déjà calculés. Recalculer ici ferait porter à la fiche deux comptes du même
fait, qui divergeraient au premier ajustement — la duplication que #672 a fermée
sur `isWholeTextVote`.

**Une seule mesure est neuve, et elle est datée** : le partage des interventions
entre les deux colonnes. `depuisLeBancDuGouvernement` rend une qualité pour
**tout le profil** ; il faut ici savoir, prise de parole par prise de parole, de
quel banc elle vient, et c'est la date d'appartenance qui le dit. Une
intervention sans date n'est attribuée à aucun banc (§2 règle 5).

## 2. « L'essentiel » perd sa vue, garde son vivier

La section, la fonction `Point` et ses trois rendus, les 25 sélecteurs CSS et
**cinq tests** qui les décrivaient sont retirés. Du CSS mort se maintient tout
seul pendant des mois avant qu'on ose y toucher.

**`essentiel()` et `vivierDesPoints()` restent** — calculés, exportés, testés
(18 tests). Ce n'est pas de l'indécision : la décision de la veille écrit que
nommer le bloc honnêtement « libère la place pour un vrai résumé ailleurs ».
Supprimer le calcul avant de savoir ce qui le remplace détruirait ce que
`tests/test_essentiel_328.py` documente — et le remettre coûterait plus que de
le laisser.

**Retrait à la charge du lot qui écrira ce résumé**, ou de sa renonciation. Sans
cette phrase, le vivier devient permanent par omission, comme les replis de
lecture de #431 et #432.

## 3. Trois constats de la maquette que la mesure corrige

Mesuré le 02/09/2026 sur les **13 profils `candidat_declare`** de `657bad12`.

| Ce que la décision du 02/09 écrit | Ce que la mesure rend |
| --- | --- |
| « Ni l'un ni l'autre : **4 sur 13** — Lisnard, Bardella, Tondelier, Arthaud » | **3** — `jordan-bardella` a un **siège électif européen**, donc une colonne parlementaire et une ligne (2 mandats en commission sur 6, au Parlement européen) |
| « L'empreinte thématique vient de la commission saisie » | **inerte** : `pivot_data/commissions_dossiers.json` n'a **jamais été produit**. Le constructeur existe (`src/build_commissions_dossiers.py`), sa sortie n'est ni versionnée ni générée par un run. `AGENTS.md` en fait pourtant l'un des « sept outputs de `pivot_data/` » |
| « 4 propositions de loi, dont 2 au dépôt » (maquette Guedj) | **2** — `AGENTS.md` §6 ne publie par défaut qu'un texte parvenu **au moins en commission**. La maquette publiait sous le seuil ; le code ne le fait pas, et **dit** ce qu'il écarte |

## 4. Le rôle range le texte, jamais l'institution seule

Replier les rôles sur `institutionDuTexte` afficherait, pour `gabriel-attal`,
**« 3 propositions de loi »** là où il y a 2 propositions et **1 rapport** : être
rapporteur d'une proposition n'est pas en être l'auteur. Les rôles sont donc
nommés un par un — `auteur_proposition_de_loi` et
`auteur_proposition_de_resolution` d'un côté, `initiateur_projet_de_loi` de
l'autre — et **tout autre rôle est compté à part et nommé**, jamais rangé
d'office. Sur les 13, cela couvre 4 `auteur` et 1 `rapporteur`.

## 5. Ce que le code refuse, et qui n'est pas décoratif

- **Additionner ou comparer les deux colonnes.** Chaque cellule compte contre le
  total de **son** côté ; le total du profil n'apparaît nulle part. Deux métiers,
  pas deux notes (§2 règle 1). Verrouillé par test.
- **Un seuil pour la concentration.** La ligne « N d'entre eux sur X » n'apparaît
  que si ce dossier porte **plus que tous les autres réunis** — un fait, pas une
  constante. Un P90 avait été essayé : il sélectionne toujours 10 % des dossiers,
  donc il ne peut **jamais** se taire.
- **Confondre les deux absences.** Un **tiret** est un fait sur le métier (« un
  ministre ne dépose pas d'amendement ») ; une **liste vide** est un fait sur la
  collecte. Et sur la frise, « non déclarée par l'Assemblée » est une **valeur
  publiée** — les cinq groupes de la XVIIe — quand le contour tireté dit qu'on ne
  l'a pas.

## 6. Ce qui n'est pas vérifié

- **Aucun runner JS dans le dépôt.** Les 20 tests lisent le **code exécuté**
  (commentaires retirés) ; **neuf mutations** ont été vérifiées échouantes. Ce
  qu'ils ne couvrent pas : la mise en page rendue, le responsive, le contraste,
  le parcours clavier.
- **Le rendu a été fait hors dépôt**, `react-dom/server` sur les données
  publiées : les deux fiches rendent sans erreur (64 921 et 172 212 caractères).
  Ce n'est pas une relecture à l'écran.
- **Les sujets d'intervention sont encore pollués** : #710 est livré et non
  fusionné, et **aucun run n'a passé**. La ligne « Interventions » nomme donc
  aujourd'hui un intitulé de séance sur plusieurs profils — le code est juste,
  la donnée ne l'est pas encore.
- **12 % des mandats de catégorie `commission` n'en sont pas** : 27 sur 225,
  dont « Amendements », « Interventions », « Vidéos », « Questions ». Le
  dénominateur de la ligne « Mandats en commission » les porte. Défaut de
  collecte, hors périmètre de ce lot.

## Alternative écartée

**Filtrer les libellés de commission sur leur premier mot.** Écartée : ce serait
une classification construite par ce dépôt sur un libellé, exactement ce que
#639 interdit et ce que §4 qualifie d'acte éditorial. Le défaut se corrige à la
collecte, où la catégorie est écrite — pas dans la vue qui la lit.
