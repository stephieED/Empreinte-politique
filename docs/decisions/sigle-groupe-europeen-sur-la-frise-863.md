# Le sigle du groupe européen entre sur la frise, parce que la source l'écrit (#863)

`2026-09-13`

> **En bref** — les segments européens de la frise du parcours étaient **muets** alors qu'ils occupent jusqu'à **70 %** de sa largeur : Raphaël Glucksmann n'affichait aucune étiquette sur ses deux mandats, quand l'Assemblée, elle, écrivait « GDR » et « FI · opposition ». La donnée manquait, puis #863 l'a livrée — `sigle_organe` et `type_organe_source` sur le mandat de groupe — et le code ne la lisait pas. **Mesuré le 13/09/2026 sur `origin/main` `87ddc9dde`** : **6 candidats déclarés**, **21 mandats de groupe politique européen, 21 avec sigle** (S&D, GUE/NGL, The Left, Verts/ALE, ENF, EFDD, ITS, NI). Deux pièges décident de la forme du code. **Le siège européen porte lui aussi `sigle_organe`, où il vaut « 10e législature »** : le discriminant est `type_organe_source`, jamais la présence du champ. Et **ces sigles ne passent pas `FORME_DE_SIGLE`** — « GUE/NGL » et « Verts/ALE » portent une barre, « The Left » une espace, le second fait 9 signes : le garde-fou existe pour ne jamais *fabriquer* une abréviation à partir d'un nom complet, pas pour refuser celle que la source publie, donc le sigle est posé directement et `avecSiglesDeSiege` ne le recalcule plus. Un siège européen croisant souvent plusieurs groupes, c'est **le plus long** qui est retenu. Le **Sénat reste muet** : aucune source ne publie son sigle. Suite complète à **4 681**, 0 échec.

## Ce qui était affiché, et ce qui l'est

Mesuré sur la page rendue, avant et après :

| Fiche | Avant | Après |
| --- | --- | --- |
| `raphael-glucksmann` | deux segments muets, 70 % et 30 % de la frise | « S&D », « S&D » |
| `emmanuel-maurel` | deux segments muets ; l'Assemblée affichait « GDR » | « S&D », « The Left », « GDR » |
| `jean-luc-melenchon` | deux segments muets ; l'Assemblée affichait « FI · opposition » | « GUE/NGL », « GUE/NGL », « FI · opposition » — **et le Sénat toujours muet** |

La liste datée suit, et elle porte le **nom complet** — « Député(e) européen(ne) · Groupe
de l'Alliance Progressiste des Socialistes et Démocrates au Parlement européen » — là où
elle écrivait « Député(e) européen(ne) ». C'est le principe posé le 11/09 : la frise donne
la silhouette et le sigle, la liste nomme. Un sigle seul ne dit rien de ce qu'est S&D à qui
ne le connaît pas déjà, et le nom complet ne tient dans aucun segment.

## Pourquoi le sigle n'est pas repassé par le garde-fou

`FORME_DE_SIGLE` (`^[\p{L}&-]{1,8}$`) sert un cas précis : l'Assemblée écrit le
sigle **dans l'intitulé**, entre parenthèses, et parfois n'y écrit que le nom
complet (« Ensemble pour la République »). Le garde-fou dit alors : sans sigle
établi, **rien** — jamais une abréviation fabriquée.

Le Parlement européen ne pose pas ce problème : il **publie** le sigle dans un
champ à lui. Le repasser par le garde-fou reviendrait à refuser trois sigles sur
huit — « GUE/NGL », « Verts/ALE », « The Left » — pour un motif qui ne les
concerne pas. D'où `sigle: r.sigle ?? sigleDuSiege(r.detail, parNom)` : ce qui
est publié passe, ce qui doit être déduit continue de l'être.

## Le groupe retenu est le plus long, jamais le premier

Emmanuel Maurel, sur la seule législature 2014-2019, passe de **S&D**
(juillet 2014) à **NI** (11 jours, octobre 2018) puis à **GUE/NGL**
(novembre 2018). Prendre la première période chevauchante donnerait un sigle
exact et arbitraire ; `groupeEuropeenDuSiege` retient celle qui recouvre le plus
de jours du siège — S&D ici, « The Left » sur 2019-2024 — et les autres restent
dans la liste datée, jamais fusionnées.

## Ce que cette décision ne traite pas

- **La position dans l'hémicycle n'existe pas au Parlement européen.** L'étiquette
  y est donc le sigle seul — « S&D », jamais « S&D · opposition » —, là où un
  siège à l'Assemblée peut porter les deux.
- **Le Sénat reste muet**, et c'est un arbitrage en attente : la seule route
  serait d'extraire le sigle de l'intitulé du mandat, c'est-à-dire de le
  fabriquer. Rien n'a changé de ce côté.
- **Les deux mandats sans sigle** que #863 signale (`sigle_organe_non_resolu`,
  le portail n'ayant rendu qu'un identifiant) ne portent aucun des 6 candidats
  déclarés : leurs 21 mandats ont tous leur sigle.
