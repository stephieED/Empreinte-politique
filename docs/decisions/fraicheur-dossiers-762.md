# L'archive vivante se reprend au changement de semaine, les mortes jamais (#762), 07/09/2026

`2026-09-07`

> **En bref** — `.cache/dossiers_an` porte une clé **hebdomadaire** doublée d'un `restore-keys`, et `ensure_dossiers_zip_downloaded` court-circuite sur `is_file()` sans qu'aucun appelant ne passe `force_download` : au changement de semaine le préfixe restaure le répertoire de la semaine d'avant, rien n'est repris, et il repart sous la clé neuve — **la rotation se désamorce elle-même**, exactement #749 appliqué aux dossiers, pour **cinq consommateurs** (`commissions_dossiers.json`, le statut des textes de gouvernement, `scrutins_dossiers.json`, `textes_dossiers_an`, `candidate_profile`) ; une étape reprend donc les archives **vivantes** quand `cache-hit != 'true'`, et **elles seules** — une législature dissoute ne produit plus d'acte, et reprendre les 15e et 16e coûterait **23 Mo par semaine pour un contenu identique** contre 9,8 pour la 17e ; l'option inverse de l'issue — purger les 33 Mo pour éviter « la machinerie qui distingue actives et figées » — est écartée parce que **cette machinerie existait déjà** (`ensure_dossiers_zip_downloaded` prend une législature et un `force_download`) : il n'y avait qu'un ensemble à déclarer, et il l'est **à côté des archives** plutôt qu'emprunté à `AN_SCRUTINS_LEGISLATURES_FIGEES`, les actives s'en déduisant par différence ; **défaut trouvé en relisant l'ordre des étapes** : sans la garde `!inputs.cold_start`, la reprise téléchargeait 9,8 Mo que le `rm -rf .cache` suivant effaçait ; le **dégât actuel est probablement nul** (session suspendue, comme #749) et un levier opérateur existait déjà — ce lot rend la reprise automatique. 12 tests, quatre mutations vérifiées échouantes.

Ancres : `rafraichir_dossiers_actifs`, `rafraichir_dossiers_actifs.py`,
`AN_DOSSIERS_LEGISLATURES_ACTIVES`, `AN_DOSSIERS_LEGISLATURES_FIGEES`,
`ensure_dossiers_zip_downloaded`, `AN_DOSSIERS_ARCHIVES`.

## Contexte

`.cache/dossiers_an` porte une clé **hebdomadaire** doublée d'un `restore-keys`
de préfixe, dans trois jobs. Et `ensure_dossiers_zip_downloaded` court-circuite :

```python
if not force_download and zip_path.is_file():
    return zip_path
```

**Aucun appelant ne passait `force_download=True`.** Au changement de semaine, la
clé exacte manque, le préfixe restaure le répertoire de la semaine précédente,
le test d'existence passe, et le répertoire inchangé repart sous la clé neuve :
**la rotation se désamorce elle-même**. C'est #749, appliqué aux dossiers.

Cinq consommateurs en dépendent : `commissions_dossiers.json`, le `statut` des
textes de gouvernement (#184), `scrutins_dossiers.json` (#758),
`textes_dossiers_an.py` et `candidate_profile.py`.

## Décision

Une étape reprend les archives **encore vivantes**, et seulement quand la clé
exacte de la semaine n'a pas été touchée — `cache-hit == 'true'` ne vaut que
sur correspondance exacte, `'false'` quand la restauration vient d'un
`restore-keys` : c'est exactement le signal « on a changé de semaine ».

**Et seulement les vivantes.** Une législature dissoute ne produit plus d'acte.
Reprendre `dossiers_15.zip` (14,5 Mo) et `dossiers_16.zip` (8,7 Mo) chaque
semaine, ce serait **23 Mo pour un contenu identique** ; seule la 17e est
vivante, 9,8 Mo.

L'issue laissait ouverte l'option inverse — purger le répertoire entier, 33 Mo,
pour éviter « la machinerie qui distingue actives et figées ». Elle n'a pas été
retenue : cette machinerie **existait déjà**. `ensure_dossiers_zip_downloaded`
prend une législature et un `force_download` ; il n'y avait ni drapeau ni
branche à inventer, seulement un ensemble à déclarer. Payer 23 Mo par semaine
pour éviter une complexité qui n'était pas là aurait été un mauvais échange.

**L'ensemble des figées est déclaré à côté des archives dont il parle**
(`couverture_dossiers.py`), et non emprunté à `AN_SCRUTINS_LEGISLATURES_FIGEES`.
Les deux disent aujourd'hui la même chose mais répondent à deux questions —
quelles archives de scrutins sont committées, quelles archives de dossiers ne
bougent plus — et rien ne garantit qu'ils resteront alignés. Les **actives**
s'en déduisent par différence : à l'ouverture de la 18e, la seule édition est
d'ajouter 17 aux figées.

## Un défaut trouvé en relisant l'ordre des étapes

La condition ne porte pas que sur le cache-hit : elle porte aussi sur
`!inputs.cold_start`. Dans `extract-an` et `extract-roster-groupes`, le
`rm -rf .cache` du démarrage à froid **suit** la reprise — sans cette garde,
l'étape téléchargeait 9,8 Mo que la purge effaçait aussitôt. Rien à rafraîchir
là où tout est purgé puis repris.

## Ce qui reste vrai, et qu'il faut lire avant de chercher une régression

**Le dégât actuel est probablement nul.** #749 avait mesuré le sien à zéro au
moment du correctif, les travaux parlementaires étant suspendus ; le même
caveat vaut ici. Le coût commence à la reprise de session.

**Un levier opérateur existait déjà** : relancer avec `cold_start=true` fait
`rm -rf .cache` et reprend tout. Le cache n'était pas inatteignable — il était
invisible tant que personne n'y pensait. C'est ce que ce lot change : la reprise
devient automatique et n'a plus besoin qu'on y pense.

## Alternative écartée

**Retirer le `restore-keys`.** Il viderait le cache entier chaque semaine, donc
re-téléchargerait aussi les deux archives figées — les 23 Mo qu'on veut
justement éviter — et perdrait le bénéfice du repli dans tous les autres cas où
il est légitime (une clé qui change pour une autre raison que la semaine).
