<a id="controle-de-perte-avant-commit"></a>
# Le contrôle de perte était écrit, documenté, et branché sur rien (#460) (2026-08-19)

`2026-08-19`

> **En bref** — le contrôle de perte était écrit, documenté, et branché sur rien : il tourne maintenant avant le commit.

Le run `32288588518` a effacé **les 789 interventions du corpus**, et avec elles
647 `tags_thematiques` et 497 `tags_thematiques_agreges` — des champs
**publiés** (AGENTS.md §6). La section « thèmes » d'un profil de groupe s'est
vidée sur le site. Personne ne l'a vu.

## Deux comportements corrects, une donnée détruite

Ni la collecte ni l'écrasement n'étaient fautifs :

- `extract_interventions=false` saute la **collecte**. C'est le mode rapide
  documenté, et c'est voulu.
- `overwrite_profiles=true` réécrit le profil **sans** ce que ce run n'a pas
  collecté. C'est voulu aussi : c'est ce qui permet de propager une correction
  de clé, et c'est précisément ce que #445 et #451 ont rendu possible.

Chacun isolément est juste. Ensemble, ils effacent une donnée déjà acquise —
exactement ce que la fusion additive existe pour empêcher.

**Le filet qui a disparu était accidentel.** Avant #451, le bug de publication
de #450 réinjectait les copies périmées à chaque run : l'écrasement ne prenait
jamais effet, et les interventions survivaient *par accident*. En corrigeant la
publication, on a retiré un filet involontaire — et le premier run en mode
écrasement a effacé pour de bon. C'est le même run qui a fait passer les
amendements à 100 % d'`uid` : le gain était réel, le coût n'a été vu de
personne.

## Pourquoi la quality gate ne pouvait pas l'attraper

Elle a parlé. Sa §3 affichait :

```
│  Profils analysés : 209   Sous le seuil : 209
```

Un signal qui se déclenche sur **100 % du corpus** ne dit rien de ce qui a
changé — et par construction il ne le peut pas : il mesure un **niveau**, pas
une **variation**. Un profil à 0 intervention lui est indiscernable selon qu'il
n'en a jamais eu ou qu'il vient d'en perdre 789.

## Ce qui manquait n'était pas un outil, c'était un appel

`src/audit_diff_profils.py` compare une référence git au contenu courant,
profil par profil et champ par champ, et sort en erreur sur une perte. Il était
cité dans quatre documents, dont #429 qui le disait « indispensable avant tout
commit de régénération ».

Recherché dans `.github/`, `src/` et `scripts/` : **aucun appel**. Un garde-fou
écrit, testé, documenté, recommandé — et débranché. C'est le genre d'écart que
seule une recherche explicite révèle : rien dans le dépôt ne signalait qu'un
outil n'était appelé de nulle part.

## La décision

L'appel est posé dans `merge-and-pivot`, **avant** l'étape de commit. Une perte
sur un champ stable produit `::error::PERTE_PROFILS_NON_DECLAREE` et un `exit 1`
— le step suivant ne s'exécute pas, donc rien n'est committé ni déployé.

**`--ref HEAD`, pas `origin/main`.** HEAD est le commit que le job a checkouté,
donc exactement l'état d'avant ce run. C'est aussi le seul qui fonctionne avec
le `fetch-depth: 1` par défaut d'`actions/checkout`, et le seul juste sur un run
lancé hors `main` — même raison qu'au garde-fou de #413 §2.

**Une perte peut être légitime**, et la régénération de #450 en attendait une.
Elle doit alors être **déclarée** : l'input `tolerer_pertes_profils` laisse une
trace dans les paramètres du run, là où un contrôle simplement retiré n'en
laisserait aucune. Il émet un `::warning::` à l'usage.

Le rapport est joint au `$GITHUB_STEP_SUMMARY` **dans tous les cas** : c'est en
échec qu'on en a le plus besoin, et un artifact qu'il faut aller télécharger ne
serait pas lu.

## Le contrôle ne tenait pas à l'échelle — corrigé avant de le brancher

Mesuré avant de poser l'appel : `audit_diff_profils.py` culminait à **3,2 Gio de
RSS** sur les 209 profils et se faisait tuer par l'OOM killer. À 752 profils,
~11 Go : un échec certain en CI, pour un script dont tout l'intérêt est de
tourner **avant** le commit.

La cause : `git cat-file --batch` lu avec `capture_output=True`, qui bufferisait
la totalité des profils avant d'en compter la première entrée. Lu **en flux**,
blob par blob, la mémoire ne dépend plus que du plus gros blob (~26 Mo) :
**236 Mio**, soit −93 %.

C'est le troisième outil de ce dépôt à buter sur ce mode d'échec, après l'index
des amendements ([[cache-amendements-forme-dedupliquee]] #377, #392) et les
index de #431/#432. Le motif est stable : **compter n'exige jamais de tout
matérialiser**.

Le risque propre à cette réécriture est le décalage de protocole — la lecture
entrelace l'écriture des requêtes et la lecture des blobs, et un octet de
décalage décalerait tous les profils suivants en rendant des comptes faux *sans
rien signaler*. D'où un test sur 60 profils de tailles croissantes, un autre
mêlant un blob de plusieurs Mo à des petits, et un troisième sur un JSON
corrompu au milieu.
