<a id="frise-segments-pleins-et-senat-885"></a>
# La frise de couverture passe aux segments pleins, et le Sénat y devient une institution (#885) (2026-09-15)

`2026-09-15`

> **En bref** — la frise de `/couverture` portait un segment par MOIS PORTEUR. Les blancs entre eux ne disaient rien de la source : ils disaient les mois où aucun candidat déclaré n'était en fonction là — **73 mois** sans texte porté à l'Assemblée, 34 sans mandat, 32 sans intervention européenne. Sur une page qui s'appelle « Ce que le dépôt porte, et depuis quand », ils se lisaient comme des lacunes de collecte. Un segment continu par rail les supprime, et rend la routine triviale : deux dates, rien à fusionner. Le Sénat y prend ses cinq listes — **133** appartenances, contre les **7** que son ancienne ligne unique comptait.

## 1. Le défaut : deux questions sur une seule figure

`tranchesMensuelles` fusionnait les mois consécutifs porteurs. Le résultat
répondait à « quand nos candidats étaient-ils en fonction », quand le titre de la
section pose « depuis quand la source est-elle lue ».

| Piste | Plus grand trou |
| --- | --- |
| Assemblée · textes portés | **73 mois** (12/2010 → 01/2017) |
| Assemblée · mandats | 34 mois |
| Parlement européen · interventions | 32 mois |
| Gouvernement · mandats | 20 mois |

Aucun n'est une lacune : ce sont des années sans mandat exercé là. La figure les
dessinait comme des absences de données.

## 2. Ce qui a été écarté, et pourquoi

**Une barre par institution** (une seule ligne par onglet). Écartée : une borne
par institution n'existe pas — il y en a **cinq**, une par liste. L'Assemblée
publie ses mandats depuis 2002, ses votes depuis 2012, ses comptes rendus depuis
2017. Une barre unique annoncerait 2002 pour des interventions lues depuis 2017.

**Une table de bornes, sans figure.** Écartée : vingt dates exactes, mais plus de
comparaison d'un coup d'œil entre institutions.

**Reculer l'axe à 1986** pour loger le premier mandat sénatorial. Écartée par la
propriétaire : les quatre institutions s'y tasseraient de 35 %. L'axe reste à
2000, et le segment est **marqué comme sectionné** — bord gauche sans arrondi,
liseré clair. Sans ce marqueur il dirait « commence en 2000 », l'erreur exacte
que #940 venait de corriger sur la borne de l'Assemblée.

## 3. Le Sénat : une institution, et la hachure plutôt que le jaune

Il portait un rail unique **en jaune** et le compte « 7 · 2 candidats ». Les sept
sont les mandats électifs ; les **126 organes** — commissions, groupes d'amitié,
groupes d'études, organismes extra-parlementaires — n'étaient comptés nulle part.

Ses quatre autres listes sortent en **hachure**, pas en jaune, et c'est la
distinction que cette frise existe pour porter :

| Encre | Ce qu'elle dit |
| --- | --- |
| jaune | un trou **de notre fait** — une action que nous n'avons pas faite |
| hachure | la **source** ne le publie pas |

`src/senat_opendata.py` lit 24 des **93** tables de l'export : aucune ne porte de
scrutin, de compte rendu, d'amendement ni de texte. Les trois tables refusées à
l'entrée — `activite_senateur`, `activite_participant`, `activite_delegation` —
sont de la présence et des procurations (§2 règle 3) : elles ne nourrissent
aucune de nos cinq listes, donc leur refus ne creuse rien ici.

Le jaune était juste **avant #885**, quand #528 tenait le Sénat hors périmètre :
le trou était alors bien de notre côté. Il a cessé de l'être le jour où les
appartenances ont été collectées.

**Le jaune disparaît donc de la page, et sa clé quitte la légende.** Une légende
décrit ce qui est à l'écran ; une clé sans occurrence se lit comme un élément
qu'on n'a pas su trouver. La règle et le style restent — le premier trou de notre
fait ramènera sa clé, ce qui est une ligne de code.

## 4. La sarcelle, retenue MALGRÉ un critère

`#169E9E` est à **67°** du bleu de l'Union, sous le seuil de 72° que
`DESIGN_SYSTEM.md` §2 pose entre institutions de même rang.

Retenue quand même, sur la mesure qui compte pour un lecteur — la séparation
sous daltonisme, plancher ΔE 8 :

| Paire | Normale | Protanopie | Deutéranopie | Tritanopie |
| --- | ---: | ---: | ---: | ---: |
| **Europe / Sénat** | 31,1 | **33,0** | **29,7** | **29,5** |
| Assemblée / Gouvernement | 15,3 | 16,0 | 13,2 | **10,4** |
| Assemblée / Europe | 21,4 | **11,2** | 17,0 | 20,7 |

Europe/Sénat est **la paire la plus séparée des six**, dans les quatre visions.
Les deux paires fragiles existaient déjà sans le Sénat : l'ajouter ne dégrade
rien. Les 67° disent « elles se lisent comme parentes » ; chaque institution
portant son titre en capitales au-dessus de ses lignes, la parenté n'induit pas
de hiérarchie.

Le gris `#9A958D` passe aux **mandats locaux**, dont il garde le sens : l'encre
de ce qui n'a aucune source.

## 5. Ce que la décision ne ferme pas

- **Le curseur à trois crans** — institutions / listes / champs — a été maquetté
  et validé dans son principe, puis mis de côté. Les trois niveaux sont réels :
  4 institutions, 20 listes, **61 champs**.
- **Les mandats locaux** (#922) restent une ligne sans activité : le job et le
  champ de schéma sont livrés, aucun run ne les a écrits. Le schéma pose qu'ils
  **ne sont pas une institution** — « les mandats locaux vivent dans `mandats[]`
  avec les autres » — donc pas une cinquième ligne comme le Sénat.

## 6. Deux tests réécrits, et pourquoi c'est le point sensible

`test_le_parlement_europeen_n_est_plus_une_ligne_non_collectee` exigeait
`cle: 'Senat'` dans `SANS_ACTIVITE`, au motif que « le Sénat garde sa ligne ».
C'était l'arbitrage de #528 ; #885 le renverse.

`test_les_origines_se_superposent_dans_un_seul_rail` comptait les occurrences de
`className="fc-rail"`. Il vérifie désormais l'**intention** — aucun rail
construit dans la boucle des origines — parce qu'une liste non publiée en ajoute
un qui n'est pas une origine.

Les deux gardent dans leur docstring la mémoire de ce qu'ils tenaient.
`tests/test_frise_segments_et_senat_885.py` tient le reste, dont
`test_le_jaune_ne_revient_pas_sans_sa_raison`.

→ voisins : [`frise-couverture-donnees-collectees-328`](frise-couverture-donnees-collectees-328.md), [`teintes-des-institutions-328`](teintes-des-institutions-328.md), [`page-couverture-commune-328`](page-couverture-commune-328.md)
