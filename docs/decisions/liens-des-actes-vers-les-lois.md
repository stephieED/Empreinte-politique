<a id="liens-des-actes-vers-les-lois"></a>
# Un acte publie les lois qu'il applique et celles qu'il cite, et ces liens se corrigent après coup (2026-09-23)

`2026-09-23`

> **En bref** — La jointure loi → acte n'existait qu'en mesure locale. Elle est publiée : chaque acte porte les lois qu'il **applique** et celles qu'il **cite**, deux états que la source distingue. Et parce que Légifrance pose la qualification des mois après la parution, un acte redélivré voit ses liens repris dans son fichier mensuel, déjà clos. Arbitré le 23/09/2026 (option B).

## Constat

L'interface veut montrer, par matière, la part des actes qui appliquent une loi
promulguée et celle que le gouvernement prend de lui-même. Les deux colonnes
étaient publiées — `pivot_data/actes_reglementaires/` et
`pivot_data/textes_promulgues.json` — mais **pas la jointure** : elle ne vivait
que dans des mesures locales.

Le fait qui commande tout le reste, mesuré le 23/09/2026 sur les 13 267 lois du
fonds JORF : **aucune loi promulguée depuis 2024 ne porte de lien
`APPLICATION`**, alors que 56 % d'entre elles sont déjà citées par un acte. La
qualification est un travail éditorial différé, de délai non publié.

## Décision

1. **Deux listes, pas une.** `liens_lois` donne `{id: [[lois appliquées], [lois
   citées]]}`. Un décret qui cite une loi en visa n'en est pas un décret
   d'application, et publier l'un pour l'autre affirmerait une relation que la
   source ne déclare pas (§2 règle 2).
2. **Une clé absente est « aucun lien déclaré »**, jamais « aucune loi ». Sur les
   actes récents, cette absence recouvre surtout le retard de qualification.
3. **Option B : les liens se corrigent après coup.** Un mois clos n'est jamais
   reconstruit, mais la source redélivre un acte quand ses liens changent, et
   ces redélivrances sont dans les livraisons que le run lit déjà.
   `corriger_les_liens` reprend alors **les seuls liens** de cet acte dans le
   fichier de son mois, et date la correction (`liens_revus_le`).
4. **Le reste de la ligne n'est pas repris** : les articles de l'acte ne sont pas
   relus, et son index de mots ne doit pas se retrouver en désaccord avec un
   titre corrigé.
5. **Un lien retiré par la source est retiré du corpus** : le garder ferait d'une
   qualification abandonnée la nôtre.

## Alternative rejetée

**A — figer le statut avec sa date de constat.** Sans coût de code, mais un acte
paru ce mois-ci resterait « aucun lien déclaré » pour toujours, puisque son mois
n'est jamais relu. La figure mesurerait alors la chaîne de publication de
Légifrance au lieu de l'action publique — exactement ce qu'elle cherche à éviter.

**Rattraper le lien depuis l'intitulé** (« pris pour l'application de la loi
n° 2024-42 ») : mesuré le 23/09/2026, 353 actes dans tout le fonds, 5 lois
gagnées sur nos dossiers promulgués, une seule depuis 2024.

## Ce que cette décision ne couvre pas

La lecture inverse — pour une loi, la liste de ses actes d'application — n'est
pas publiée : elle se dérive des actes, et l'interface ne l'a pas demandée.
