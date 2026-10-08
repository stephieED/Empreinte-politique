<a id="articles-votes-par-la-seance-1264"></a>
# Sur quoi porte un article soumis au vote : rattaché par la séance, lu dans le texte officiel (#1264) (2026-10-08)

`2026-10-08`

> **En bref** — un scrutin sur un article (« l'article 5 de la proposition de loi… ») ne disait rien de l'article. Demandé par la session COM pour l'article « violences sexuelles et sexistes », arbitré par la propriétaire le 08/10/2026 (option B : titre, chapitre **et** extrait du texte). Le scrutin ne porte aucune référence exploitable, et le rattachement par le titre est interdit (`regrouper-nest-pas-joindre-639`). Mais il porte sa **séance** (`seanceRef`), que portent aussi les actes de séance des dossiers (`reunionRef`) et l'**ordre du jour** (archive Agenda). `src/articles_votes.py` publie `pivot_data/articles_votes.json` : **1 313 des 2 083 scrutins d'article des XVe-XVIIe rattachés (63 %)**, les autres avec leur motif.

## 1. Les sources, mesurées le 08/10/2026

| Source | Ce qu'elle apporte |
| --- | --- |
| Scrutin : `seanceRef` | la séance, sur tous les scrutins |
| Scrutin : `objet.dossierLegislatif.dossierRef` | le dossier, à la 17e seulement (275 des 902 scrutins d'article) |
| Dossier : actes `AN?-DEBATS-SEANCE.reunionRef` | la séance de chaque discussion, et donc la lecture en cours |
| Dossier : `AN?-COM-FOND-RAPPORT.texteAdopte`, `AN?-DEPOT.texteAssocie` | le texte discuté : celui de la commission, à défaut le texte déposé |
| Agenda : `pointsODJ[].dossiersLegislatifsRefs` | **tous** les dossiers d'une séance |
| `dyn/opendata/<uid>.html` | le texte, balisé par titre, chapitre, section, article |

Contrôle croisé : sur les 275 scrutins qui portent leur dossier, celui-ci figure à l'ordre du jour de la séance **275 fois sur 275**.

## 2. Les règles, et ce qui les a imposées

1. **Les candidats d'une séance sont l'ordre du jour, unis aux actes de séance.** Avec les seuls actes, 30 rattachements sur 1 564 désignaient le mauvais dossier : un dossier discuté dont l'acte manque disparaissait des candidats. Par exemple, l'article 6 d'une loi sur le sport était attribué à celle sur le marché de l'art.
2. **Dans une séance à plusieurs dossiers, on retient le seul texte qui porte l'article** — arbitrage de la propriétaire, 08/10 (option A). Mais seulement si **toutes** les versions de texte des autres dossiers ont été lues et qu'aucune ne porte l'article. Avec la seule version « discutée », 3 ou 4 départages sur 205 se trompaient (une version d'avant les articles ajoutés). La règle durcie en garde 30.
3. **Le dossier porté par le scrutin départage**, quand il existe.
4. **Ce qui ne se rattache pas se publie avec son motif** (§2 règle 5), dans `non_rattaches`.

Contrôle a posteriori, sur le titre du dossier comparé au libellé du scrutin (un contrôle, jamais une jointure) : 14 désaccords sur 1 259 rattachements titrés. Ceux qui ont été relus sont de fausses alertes : le titre court du dossier diffère de celui du texte (« Assurer un repas à 1 euro… » pour la PPL « visant à garantir un tarif réduit… »).

## 3. Limites déclarées

- La XIVe n'a pas de texte HTML (0/8) : non lue.
- Les lois de finances ont un autre gabarit (`assnatFPF*`, `assnatFAR*`) : 125 scrutins déclarés `texte_a_gabarit_non_lu`. Ce gabarit porte peut-être un intitulé par article, ce qui n'a pas été mesuré.
- 612 séances à plusieurs dossiers restent non départagées.
- Seuls 5 textes sur 24 de l'échantillon ont des titres ou des chapitres : pour les autres, l'extrait est le seul contenu.

## 4. Alternatives écartées

- **Le titre cité dans le libellé du scrutin** : interdit par `regrouper-nest-pas-joindre-639`.
- **Une table relue à la main** : ne passe pas à l'échelle.
- **Le Word et le PDF officiels** : serveur `docparl` injoignable depuis la machine, et sans balises de structure garanties.
