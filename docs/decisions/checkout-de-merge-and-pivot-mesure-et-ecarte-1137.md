<a id="checkout-de-merge-and-pivot-mesure-et-ecarte-1137"></a>
# Le `filter: blob:none` sur le checkout de `merge-and-pivot` : mesuré, écarté (#1137) (2026-09-25)

`2026-09-25`

> **En bref** — la piste était « le checkout de `merge-and-pivot` coûte 572 s, un `filter: blob:none` serait à **mesurer** avant d'être proposé » ; mesuré : le fetch passerait de **514 Mo à 1 Mo**, ce qui a l'air décisif et ne l'est pas — le job a besoin du **worktree complet** (il committe le dépôt entier), donc les 5 065 blobs écartés du pack sont **immédiatement redemandés** à la matérialisation des **8,0 Go** de l'arbre ; `blob:none` ne retire rien, il déplace, et ajoute un aller-retour. **Piste fermée, pour que personne ne la rouvre sur la seule vue du premier chiffre.**

## 1. Ce qui a été mesuré

Sur l'arbre d'`origin/main`, 25/09/2026 :

| Grandeur | Valeur |
| --- | --- |
| Objets d'un fetch `--depth 1` complet | **5 824** — pack de **514 Mo** |
| Objets du même fetch avec `--filter=blob:none` | **759** — pack de **1 Mo** |
| Blobs de l'arbre du HEAD | **5 065** |
| Arbre matérialisé sur disque | **8,0 Go**, 5 064 fichiers |
| Step `actions/checkout` de `merge-and-pivot` | **390 s** (run `36153601970`) — 572 s au run `36040086663` |

## 2. Pourquoi le premier chiffre trompe

`actions/checkout` fait déjà un `fetch --depth 1` : il ne rapporte **aucun
historique**, seulement l'arbre du HEAD et ses blobs. Les 514 Mo ne sont donc pas
du passé qu'on traînerait, ce sont **les fichiers du dépôt**, compressés.

`--filter=blob:none` les écarte du pack initial. Mais `merge-and-pivot` ne peut
pas travailler sur un worktree partiel : il lit `raw_data/profiles`, écrit
`pivot_data/`, **committe et pousse le dépôt entier** — c'est ce qui interdit
déjà le sparse-checkout que les autres jobs utilisent. Les 5 065 blobs sont donc
tous nécessaires, et git les redemande au moment du checkout, dans un second
aller-retour.

Même volume, une requête de plus. Au mieux neutre.

## 3. Ce que la mesure dit, elle, du vrai coût

390 s pour transférer 514 Mo et écrire **8,0 Go** sur disque : l'essentiel du
temps n'est pas dans le réseau, il est dans la **décompression et l'écriture**
de l'arbre. Aucun réglage de `git` n'y touche — seule une réduction de ce que
le dépôt versionne le ferait, et c'est **#678** (le poids total du dépôt n'est
surveillé par personne), pas ce lot.

## 4. Décision

**Ne rien changer au checkout de `merge-and-pivot`.** La piste est fermée, avec
sa mesure, pour qu'elle ne se rouvre pas sur la seule vue du rapport 514 Mo → 1 Mo
— qui est réel, et qui ne mesure pas ce qu'on croit.

Ce qui la rouvrirait : que le job cesse d'avoir besoin de l'arbre complet. Il
n'en prend pas le chemin — il est le seul à committer.
