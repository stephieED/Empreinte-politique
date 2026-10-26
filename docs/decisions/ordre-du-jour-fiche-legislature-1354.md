<a id="ordre-du-jour-fiche-legislature-1354"></a>

# « À l'ordre du jour » : l'agenda des séances sur la fiche de législature, en Calendrier ou en Planning (#1354) (2026-10-26)

`2026-10-26`

> **En bref** — La fiche de législature gagne une section 03, « À l'ordre du jour », placée après « Qui siège » : ce qui a été discuté en séance publique, jour par jour, à la couleur de la commission saisie de chaque texte (`src/utils/commissions.js`). Un switch à deux positions choisit la forme : **Calendrier**, par défaut (douze mois, semaines numérotées en lignes, jours en colonnes), ou **Planning** (un mois par colonne, un jour par ligne). Cliquer un jour, le numéro d'une semaine ou le nom d'un mois détaille la période sous l'agenda ; la légende filtre, une catégorie à la fois. L'interface lit `ordre_du_jour/<n>.json`, que Backend publiera (#1354) : sans ce fichier, la section ne s'affiche pas. Tout a été arbitré en relecture locale avec la propriétaire, le 26/10/2026.

## Le contexte

La propriétaire a demandé « une infographie comme un agenda par an des sujets à
l'ordre du jour au cours d'une législature ». L'Assemblée publie l'ordre du jour
de chaque séance (archive `vp/reunions/Agenda`), que `src/articles_votes.py`
télécharge déjà sans rien en publier. Trois formes ont été maquettées sur
l'ordre du jour réel de la XVIIe
(https://claude.ai/artifact/Jvp4qhqXJjErdnHLbwiCWh) : un calendrier d'un carré
par jour, un agenda mural d'un mois par colonne, une frise d'une ligne par
texte. L'agenda mural a été retenu, puis la section a pris sa forme en
relecture.

## La décision

- **Deux vues, un switch.** « Pour moi, un commutateur, c'est un switch » : une
  piste et un curseur, une seule position enclenchée. **Calendrier** par
  défaut, sur le modèle d'un calendrier mural que la propriétaire a fourni en
  capture ; **Planning**, l'agenda mural de la maquette. Les noms disent la forme :
  les deux vues montrent des jours.
- **Une case ou une ligne par jour, une barre partagée** entre les textes
  discutés, au poids du nombre de points de l'ordre du jour. Un jour de
  questions ou de débats sans texte est une barre blanche cerclée. La
  législature en cours distingue un jour sans séance (rien) d'un jour dont
  l'ordre du jour n'est pas encore fixé (pointillé) : §2 règle 5.
- **Le détail sous l'agenda, au clic.** Un jour, une semaine (son numéro) ou un
  mois (son nom). Pour une période, chaque texte apparaît une fois, avec son
  nombre de jours de séance. Les jours de la période se surlignent du jaune de
  la sélection.
- **Pas d'intitulé à côté des barres.** Tronqués à une douzaine de lettres,
  « Ce n'est pas lisible » : le détail les porte en entier.
- **La légende filtre**, comme les barres des commissions : une seule catégorie
  à la fois, la recliquer l'annule, et les autres textes du jour restent en gris
  pâle pour que la part de la journée se lise.
- **Aucun classement** : les jours se suivent dans le temps, la légende est
  alphabétique (§2 règle 1). La commission est le renvoi au fond publié par
  l'Assemblée, jamais un thème déduit du titre (§2 règle 8).

## Ce que l'interface lit

`pivot_data/ordre_du_jour/<n>.json`, copié tel quel par `scripts/sync-data.mjs` :

```json
{ "legislature": "17",
  "jours": [ { "date": "2026-10-20", "seances": 2,
               "points": [ { "genre": "texte", "intitule": "<objet de la source>",
                             "dossier": "DLR5L17N…", "rattachement": "source",
                             "solennel": false, "n": 3 } ] } ] }
```

`genre` vaut `texte`, `questions_gouvernement`, `questions_orales`, `debat`,
`declaration`, `session` ou `autre` ; `dossier` est `null` quand aucun n'est
retrouvé ; `rattachement` dit d'où il vient (`source` ou `intitule`, celui
d'un autre point du même ordre du jour, `regrouper-nest-pas-joindre-639`) ;
`n` compte les points du jour sur ce dossier. Si Backend publie une autre
forme, par séance par exemple, la projection se fait dans `sync-data.mjs`,
jamais dans le composant. Les champs ne sont lus qu'à un endroit,
`web/UI_finale/src/utils/ordreDuJour.js`.

## Écarté en relecture, à ne pas reproposer

| Essai | Pourquoi |
| --- | --- |
| Détail en haut, au survol | Demandé en bas, au clic |
| Une vue Semaines qui cumule chaque semaine en une barre | « Ce n'est pas à ça que ressemblent les agendas par semaine de l'année » |
| Une vue Mois de douze barres cumulées | Refusée |
| Une vue Planning en liste chronologique | Trop haute : 680 lignes pour 2025 |
| Une vue Législature, un mois par ligne sur toute la législature | Refusée |

## Ce qui reste

- Le fichier de Backend (#1354). Sur la relecture, un fichier provisoire tiré
  de l'archive suffisait ; il n'est pas versionné.
- La section de méthodologie, dont le texte reste à valider.
- Les points « Matière non établie » : 598 des 2 565 points sur un texte de la
  XVIIe n'ont pas de dossier, et 192 renvoient à un dossier absent de
  `commissions_dossiers.json` (mesuré le 26/10/2026, hors dépôt).
