<a id="residus-source-retiree-839"></a>
# Le nettoyage fait, la clause ODbL ne tiendrait plus que par un marqueur, sur 475 profils (#839, lot C) (2026-09-12)

`2026-09-12`

> **En bref** — `src/audit_residus_source_retiree.py` **simule** le retrait des interventions héritées et recompose la licence due avec `licences.licences_du_profil()`, la fonction de production, pour distinguer ce qu'aucun compte ne distinguait : la clause est-elle retenue par une **donnée encore publiée** ou par le **seul marqueur** `sources[]` ? Mesuré le 12/09/2026 sur `origin/main` : une fois les **492** doublons retirés, **3 profils** la retiennent par une donnée — les 19 interventions sans jumelle — et **472** par le marqueur seul (7 à provenance `candidat_declare`, 465 de roster) ; **si les 19 partent aussi, plus aucun profil du corpus ne porte une donnée de Regards Citoyens**, et la clause tient par le marqueur seul sur les **475**, ce qui rend enfin décidable la condition de retrait que §7 déclare « courir d'elle-même » ; le lot **ne décide pas** ce retrait — décision éditoriale à effet juridique — il produit la mesure qui le permet ; il corrige aussi une affirmation trop rapide des commentaires précédents : les **13** mandats publiés **actifs et sans aucune date** ne sont pas 13 intitulés de navigation mais **5** (sur `jean-luc-melenchon` : `Amendements`, `Interventions`, `Questions`, `Vidéos`, `Loi ou de résolution`) et **8 organes réels du Sénat** sur `bruno-retailleau` (commission de la culture, groupes d'études, commissions extra-parlementaires) — les 13 sont publiées comme des appartenances **en cours** ; les **47** avertissements hérités et les **75** preuves de couverture sont comptés et donnés à lire, **jamais proposés au retrait** : ce sont des textes adressés à un lecteur (#642) ; 8 tests, et la simulation travaille sur des **copies de surface** — un `deepcopy` recopiait jusqu'à 8 Mio par profil et l'audit ne rendait pas la main.

## 1. La question que les comptes ne tranchaient pas

Le lot A compte 476 entrées `sources[]` sous licence Regards Citoyens, sur 475
profils. Ce compte ne dit pas ce qui **retient** l'attribution : la donnée ou le
marqueur. Or c'est exactement la question de §7 — `meta.licence_donnees` est
dérivé, et « le jour où un profil cesse de porter quoi que ce soit de Regards
Citoyens, la clause le quitte ».

## 2. La mesure, par simulation

Le script applique `purge_interventions_heritees.purge_profil` **en mémoire**,
puis recompose la licence avec `licences.licences_du_profil()` — deux fois : sur
le profil nettoyé, et sur le même privé de son marqueur. La différence des deux
réponses donne l'état.

| État de la clause, après retrait des 492 | Profils |
| --- | --- |
| retenue par une donnée encore publiée | **3** (3 à provenance `candidat_declare`) |
| retenue par le seul marqueur `sources[]` | **472** (7 · 465) |

| Les 19 sans jumelle parties — **arbitrage rendu le 12/09/2026** | Profils |
| --- | --- |
| retenue par une donnée | **0** |
| retenue par le seul marqueur | **475** (10 · 465) |

Ce n'était une hypothèse que le temps de la mesure. **La propriétaire a tranché
le 12/09/2026 : les 19 partent**, et l'archive de l'AN dit pourquoi — sur 200
comptes rendus de la XVIe, 118 033 paragraphes, les prises de parole sous
`id_acteur="PA0"` (1 834) et sous identifiant **négatif** (11) portent toutes
`id_mandat="-1"`, et les `PA0` ont en plus un `code_parole` **vide**. L'AN ne
rattache donc ces propos à **aucun mandat** : ce sont les interruptions lancées
du banc, et — pour les 5 du Congrès de Retailleau — la parole d'un orateur sans
mandat à l'Assemblée, son mandat étant sénatorial, hors périmètre (#528). Les
publier sous le nom de la personne ajouterait un lien que la source ne fait pas.

**C'est le résultat utile** : le corpus ne devrait alors plus rien à Regards
Citoyens qu'une ligne de provenance. La condition de retrait de §7 serait
remplie le jour où cette ligne partirait.

## 3. Ce que le lot ne décide pas

**Le retrait du marqueur, et donc le passage en Licence Ouverte.** Décision
éditoriale à effet juridique : elle reste à la propriétaire, et elle entraînerait
`AGENTS.md` §7, `sources.config.js` et `LegalNoticePage.jsx`
(`docs/decisions/licence-lot-6-530.md`). Le lot produit la mesure, pas la
conclusion.

Rappel de la mesure d'août, qui ne se périme pas toute seule : `sources[]` est
**unioné par type** à la fusion. Le marqueur ne disparaîtra pas parce que les
interventions partent — il faudra le retirer explicitement, sur 475 profils,
avec son contrôle de perte.

## 4. Ce que le lot corrige

Les commentaires précédents de #839 ont présenté les **13** mandats sans date
comme les intitulés de navigation de l'ancien site. C'est faux :

| Profil | Entrées | Ce que c'est |
| --- | ---: | --- |
| `jean-luc-melenchon` | 5 | `Amendements`, `Interventions`, `Questions`, `Vidéos`, `Loi ou de résolution` — les onglets de la page, pris pour des organes |
| `bruno-retailleau` | 8 | des **organes réels du Sénat** : commission de la culture, groupes d'études, groupe Chrétiens d'Orient, commissions extra-parlementaires |

Les 13 partagent trois propriétés, vérifiées entrée par entrée : aucune date,
aucun `source_url`, et **`actif: true`**. La fiche les publie donc comme des
appartenances **en cours** — pour Mélenchon, qui a quitté l'Assemblée en 2022,
et pour Retailleau, dont le Sénat est hors périmètre depuis #528.

**Les 5 ne sont pas des faits et ne perdent rien à partir. Les 8 en sont**, et
relèvent de la réserve que la propriétaire a posée le 12/09/2026 : on ne touche
pas au résidu du Sénat tant qu'une alternative n'a pas été creusée.

## 5. Les textes publiés ne se nettoient pas par un compte

**47 avertissements hérités** (19 profils) et **75 preuves de couverture** (15
profils) citent la source retirée. Ce sont des phrases adressées à un lecteur, et
#642 a déjà tranché le principe : un avertissement publié qui nomme une source
disparue garde son destinataire. Le lot les compte et les donne à lire ; il n'en
propose aucun au retrait.

## 6. L'alternative écartée

**Compter les profils dont `sources[]` porte le marqueur, et s'arrêter là** —
ce que faisait le lot A. Le compte est juste et ne répond pas : il mélange les
profils dont une donnée retient la clause et ceux où il ne reste qu'une ligne.
Trois profils sur 475, c'est justement l'écart qui décide si le retrait du
marqueur est un geste isolé ou une décision qui emporte des données publiées.
