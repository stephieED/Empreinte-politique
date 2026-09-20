<a id="cle-index-textes-portes-997"></a>
# Un cache porte le code qui l'a écrit : le correctif de #997 n'atteignait rien (2026-09-18)

`2026-09-18`

> **En bref** — #1012 a corrigé le stade procédural : 6 808 dossiers cessaient
> d'être qualifiés `examine_commission` sans l'avoir été. Le run
> [35324142500](https://github.com/stephieED/Empreinte-politique-src/actions/runs/35324142500)
> portait ce correctif et a republié **les 21 `examine_commission` de Marine Le
> Pen à l'identique**. Le `stade` est calculé au moment de construire
> `index_acteur_textes_v3.json`, puis figé dedans ; `.cache/dossiers_an` est
> restauré d'une semaine sur l'autre. La clé passe en `_v4`.

## Contexte

Mesuré après le run du 18/09/2026, sur le commit de données `0050cfa0e` :
`marine-le-pen.pivot.json` porte toujours `{'examine_commission': 21,
'depose': 2, …}`, exactement comme avant le correctif.

Deux mécanismes se sont ajoutés, et aucun des deux n'échoue :

1. **Le stade est figé dans l'index, pas calculé à la lecture.**
   `_build_acteur_textes_portes_index` appelle `_collect_acteur_roles`, qui rend
   `(roles, stade, date_min, date_max)`, et écrit le tout dans
   `index_acteur_textes_v3.json`. `fetch_textes_portes_officiels` n'est plus
   qu'une lecture de dictionnaire.
2. **Le cache CI survit aux runs.** `.cache/dossiers_an` est restauré par une
   clé hebdomadaire dont les `restore-keys` (`public-data-cache-dossiers-`)
   acceptent la semaine précédente. L'index d'avant le correctif est donc
   revenu tel quel.

S'y ajoute une troisième condition, indépendante : `collect_dossiers_legislatifs`
vaut `false` par défaut, et le run l'a déclaré — les 205 profils de
gouvernement comme les candidats portent `meta.collecte_ecartee:
['interventions', 'textes_portes']`. Même avec la bonne clé, il faut un run qui
recollecte.

## Décision

**`index_acteur_textes_v3.json` → `index_acteur_textes_v4.json`.** Même geste
qu'en #639 et #689, pour la même raison, et c'est la troisième fois : **un
correctif qui change ce qu'un index CONTIENT change sa clé, sans quoi il ne
change rien.**

La règle générale, déjà écrite dans ce module et vérifiée une fois de plus :
*l'existence d'un cache n'est pas la preuve de sa conformité.*

## Ce que ça coûte, mesuré

| | |
| --- | ---: |
| Reconstruction de l'index, 10 764 dossiers (local) | **2,0 s** |
| Acteurs indexés | 1 643 |
| Coût par profil ensuite | une lecture de `dict` |
| Téléchargement des 3 archives | déjà fait par le run (`.cache/dossiers_an`) |

Invalider cette clé ne coûte donc que la reconstruction, négligeable devant les
42 min de `merge-and-pivot`. La crainte d'un coût réseau *par profil* était
infondée : `fetch_textes_portes_officiels` n'appelle rien.

Stades que le code actuel produit sur les trois archives, une fois l'index
reconstruit : **15 222 `depose`**, 4 335 `promulgue`, 2 154 `adopte`, **1 831
`examine_commission`**, 710 `discute_seance`, 215 sans stade.

## Ce qu'il reste à faire pour fermer #997

Un run avec **`collect_dossiers_legislatifs: true`**. Les deux conditions sont
nécessaires et aucune ne suffit : la clé sans le drapeau ne recollecte rien, le
drapeau sans la clé relit l'ancien index.

## Alternative rejetée

**Purger `.cache/dossiers_an` par un `cold_start`.** Ça marcherait une fois, et
laisserait le défaut entier : le prochain correctif du stade retomberait dans le
même trou, et rien ne le signalerait. La clé versionnée porte l'invariant ;
une purge manuelle porte la mémoire de celui qui la lance.
