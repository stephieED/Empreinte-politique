<a id="budgets-extract-an-remesures-546"></a>
# La décomposition d'un shard `extract-an`, et les deux budgets recalés dessus (#546) (2026-08-27)

`2026-08-27`

> **En bref** — décomposition mesurée d'un shard `extract-an`, et les deux budgets recalés dessus.

Suite de [#budgets-extract-an-perimes-546](budgets-extract-an-perimes-546.md), qui
constatait que les deux budgets ne valaient plus sans dire par quoi les
remplacer. Voici la mesure, puis l'arbitrage.

## Ce qui est mesuré, et sur quelle population

**Population : les 8 shards du run `33110395663` (27/08, 19:53-20:45 UTC), en
mode `collect_interventions`.** C'est le SEUL run connu où les trois archives
Syceron ont répondu. Le run `33100214165`, deux heures plus tôt et cité à côté
de lui dans #546, n'en est pas un second : ses journaux portent

```
[!] Index des débats Syceron (législature 16) NON mis en cache : aucun compte
    rendu lisible (archive indisponible ?).
[!] Index des débats Syceron (législature 15) NON mis en cache : ...
```

— seule la 17e a été indexée, `jean-luc-melenchon` en est sorti avec **15**
interventions contre 3 933 au run suivant, et ses shards ont duré 2,3 à 6,7 min.
**Ses durées ne caractérisent pas ce mode** et ne sont utilisées nulle part
ci-dessous. C'est aussi ce qui explique le « identiques à la seconde près entre
les deux runs » de #546 : les deux tableaux de durées n'étaient pas comparables.

Décomposition par shard, en secondes, reconstruite depuis les horodatages des
journaux (`gh run view --log`) et les durées de step de l'API
(`/actions/runs/33110395663/jobs`) :

| Shard | Préambule job | Préambule script | Syceron 16 | Syceron 15 | Questions | Écriture | Extraction | Horloge budget | Job |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| jean-luc-melenchon | 187 | 6 | 55 | 147 | 104 | 4 | 342 | **332\*** | 531 |
| jerome-guedj | 197 | 5 | 39 | 166 | 19 | 3 | 256 | **247\*** | 456 |
| marine-le-pen | 146 | 6 | 34 | 123 | 63 | 3 | 253 | 244 | 402 |
| bruno-retailleau | 181 | 5 | 50 | 79 | 54 | 3 | 217 | 208 | 400 |
| edouard-philippe | 153 | 5 | 42 | 100 | 43 | 3 | 216 | 208 | 371 |
| gabriel-attal | 163 | 5 | 45 | 103 | 29 | 3 | 208 | 200 | 374 |
| laurent-wauquiez | 162 | 5 | 34 | 93 | 14 | 3 | 175 | 166 | 339 |
| jordan-bardella | 192 | — | — | — | — | — | 1 | — | 195 |

`*` = collecte tronquée par le budget de 240 s alors en place. « Horloge budget »
est le temps que le budget interne compte réellement : il démarre au premier
téléchargement Syceron, ce que les valeurs déclarées par le programme confirment
à la seconde (247 s pour `jerome-guedj`, 332 s pour `jean-luc-melenchon`).
`jordan-bardella` n'a aucun mandat AN : son shard ne collecte rien, il n'entre
dans aucune borne.

**Deux profils tronqués, pas un.** #546 n'avait relevé que `jerome-guedj`. La
troncature de `jean-luc-melenchon` est dans le journal du run — `##[warning]` et
`[!]` — mais **elle n'est pas dans son profil publié** : `meta.warnings[]` y
porte « aucun mandat français connu », l'avertissement du profil minimal écrit
par `extract-ue-officiel` à 19:53:29, et `meta.genere_le` vaut cette heure-là,
pas les 20:02:34 d'`extract-an`. La fusion a gardé les 3 933 interventions du
second et le `meta` du premier. **`meta.warnings[]` n'est donc pas un détecteur
fiable de troncature pour un candidat qui porte aussi un profil UE** — le
`::warning::` du run, lui, l'est. Ce n'est pas corrigé ici ; à traiter à part.

## Pourquoi l'ancien calibrage ne vaut plus

Il posait « 240 s de préambule provisionné + 240 s de budget + ~60 s de marge »
sur deux hypothèses tombées depuis : 90 s de recherche NosDéputés, retirée par
#529 ; et des archives Syceron facturées 22-55 s par législature **alors
qu'elles rendaient zéro intervention** (défaut #510). La mesure ci-dessus donne
34-55 s pour la 16e et **79-166 s pour la 15e** — le poste réel n'était pas celui
qui était facturé.

**Et la paire était incohérente, pas seulement juste.** Le budget est vérifié
ENTRE deux unités de collecte, jamais au milieu de l'une : quand il expire,
l'unité en vol va à son terme. Le `timeout-minutes` doit donc couvrir le budget
PLUS cette unité. Avec 240 s de budget, la somme provisionnée valait 575 s pour
540 s disponibles : **un shard pouvait être tué avant d'écrire son profil**,
c'est-à-dire publier « 0 profil(s) » — le défaut même que #498 corrige. Que
`jean-luc-melenchon` soit sorti à 8,9 min tenait à l'unité qui a dépassé ce
jour-là (une législature de questions, 104 s), pas à un dimensionnement. Les
~6 s de marge lues dans #546 sont une marge observée, pas une marge garantie.

Quelle unité peut dépasser ? Pas une législature Syceron : elles sont engagées à
l'horloge 41-63 s (mesuré sur les 7 shards porteurs), très en deçà de tout budget
de cet ordre. C'est une législature de questions officielles, mesurée **5-104 s**.

## L'arbitrage retenu

Les deux valeurs tirent en sens contraires : agrandir le budget rapproche du
timeout, agrandir le timeout allonge un gel éventuel — et c'est ce que le passage
de 5 à 9 min bornait, après le run du 16/08 où `jerome-guedj` a bloqué 20+ min et
immobilisé le matrix séquentiel (`max-parallel: 1`) derrière lui.

Contrat posé, entièrement mesuré :

```
timeout >= préambule de job provisionné      200 s   (mesuré 146-197)
        +  préambule de script + écriture     15 s   (mesuré 8-10)
        +  budget d'interventions            250 s
        +  unité en vol provisionnée         120 s   (mesuré 5-104)
        =                                    585 s
```

**`timeout-minutes: 10` (était 9) et `--budget-interventions-secondes 250`
(était 240).** 585 s pour 600 s disponibles, 15 s de marge. La provision de
préambule descend de 240 s à 200 s : le maximum mesuré n'a pas bougé (193 s hier,
197 s aujourd'hui), et les 40 s de confort valaient mieux là où la marge manquait.

Ce que ça achète, sur la population mesurée : six des sept profils porteurs
sortent complets au lieu de cinq. `jerome-guedj` (247 s) passe — **à 3 s près.
Ce n'est pas une garantie, c'est un profil de plus ce jour-là.**

Ce que ça n'achète pas : `jean-luc-melenchon` reste tronqué. Le compléter demande
au moins 340 s d'horloge, donc un timeout d'au moins 11,3 min, au-delà du plafond
de 10 min que le gel du 16/08 a posé. **La perte reste déclarée**, dans le
`::warning::` du run — et, pour ce profil-là seulement, pas dans `meta.warnings[]`
(voir plus haut).

## Ce que ce recalage ne règle pas, et qui est le vrai coût

**113 à 219 s par shard partent à réindexer les législatures Syceron 15 et 16 —
le MÊME travail, refait par chacun des 7 shards porteurs**, soit 40 à 60 % de
l'horloge de collecte. La cause est dans le journal : la clé
`public-data-cache-an-2026-W35-interv` a fait un *exact key hit* sur l'entrée
écrite par le run `33100214165`, celui où ces deux archives étaient
injoignables ; `actions/cache` saute alors sa sauvegarde
(« Cache hit occurred on the primary key ..., not saving cache »), et l'index
reconstruit à chaque shard est jeté à la fin de chaque shard.

C'est [#cache-mode-interventions-505](cache-mode-interventions-505.md) sous une
troisième forme : la clé porte le **mode**, jamais la **complétude** du contenu.
Le refus de mettre en cache une législature illisible est juste pris isolément —
mais il produit une entrée partielle que la clé déclare complète.

Tant que ça tient, **aucune paire (budget, timeout) sous le plafond de 10 min ne
peut à la fois tout collecter et garantir l'écriture** : c'est arithmétique, pas
une opinion. Réparer le cache retirerait 113-219 s de l'horloge de chaque shard
et ferait rentrer les sept profils dans le budget actuel. C'est là qu'est le
gain, pas dans un chiffre plus grand. À ouvrir en issue propre.

> **Ouvert en #550 et corrigé** (2026-08-28) : la clé porte désormais la
> complétude et la sauvegarde est explicite. Voir
> [#cache-completude-interventions-550](cache-completude-interventions-550.md).
> Une nuance de cette section y est corrigée sur mesure : « ferait rentrer les
> sept profils dans le budget actuel » vaut pour les runs qui **restaurent** un
> index complet, pas pour celui qui le **construit**. La construction à froid
> des trois législatures Syceron coûte 244 s (42 + 55 + 147, les deux derniers
> mesurés ici, le premier sur le run `33100214165`) : le shard constructeur
> consomme la quasi-totalité du budget et reste tronqué. Le gain porte donc sur
> **six** shards par run — 908 s, ~15 min — et sur les sept dès le run suivant.

---

