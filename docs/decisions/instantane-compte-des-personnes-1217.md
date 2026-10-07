<a id="instantane-compte-des-personnes-1217"></a>

# Un instantané compte des personnes, et lit un périmètre de mots relu à la main (#1217) (2026-10-06)

`2026-10-06`

> **En bref** — Le troisième article de type instantané, « Les conditions d'enseignement, de l'école au lycée » (#1217, PR #1226), n'a pas de mot unique comme « carburant » : son sujet est un **périmètre de mots**. Quatre règles en sont sorties, arbitrées par la propriétaire les 05 et 06/10/2026 sur maquette. **Le périmètre est étroit** — les moyens de l'école — et sa liste de mots est **relue titre par titre**, parce que les mots seuls ramènent des faux amis. **On compte des personnes intervenues, jamais des tours de parole, et sans les rapporteurs** : en tours de parole, un groupe passait de 35 à 3 selon qu'on comptait son rapporteur ou non. **Une comparaison entre groupes ne se montre ni triée ni chiffrée par rang** : ordre alphabétique ou place dans l'hémicycle, sans compteur. **Au Journal officiel, seuls les actes qui posent une règle sont gardés**, et ce tri n'est pas dans la source. Ce fichier **complète** `docs/decisions/instantanes-publies-1029.md` sur un point : il admet un compte de personnes sans doublon **par sujet**, que l'article des carburants refusait par débat.

## Le contexte

Mesuré le 06/10/2026 sur `main` 446cf1b65, période du 04/10/2025 au 04/10/2026,
dans les intitulés des débats portés par les 1 402 profils publiés.

| Mesure | Valeur | Population |
| --- | --- | --- |
| Intitulés retenus | 44, dont 43 questions | intitulés de débat de l'Assemblée nationale |
| Prises de parole | 418, sur 26 jours de séance | hors présidence de séance |
| Députés intervenus | 100 sur 567 | membres des onze groupes au 30/06/2026, hors rapporteurs et présidents de commission |
| Textes déposés | 15, dont 2 adoptés | textes portés par un membre des profils collectés |
| Actes du ministère de l'éducation nationale sous ces mots | 47, dont 41 sur les postes offerts aux concours | Journal officiel, arrêté au 01/10/2026 |

Deux périmètres ont été mesurés avant d'en retenir un : l'étroit (45 intitulés,
638 prises de parole présidence comprise) et le large (65 intitulés, 1 880
prises de parole, dont 812 sur un seul débat consacré aux violences en milieu
scolaire).

## La décision

- **Le périmètre est étroit, sur douze mois.** Les moyens : postes, fermetures
  de classes, carte scolaire, accompagnants d'élèves, effectifs, remplacement,
  éducation prioritaire, établissements scolaires, périscolaire. L'enseignement
  supérieur, les violences, la laïcité, les programmes et les examens en
  sortent, et la page l'écrit. Douze mois et non six, parce que le sujet suit
  l'année scolaire.
- **La liste de mots se relit titre par titre.** Les mots seuls avaient retenu
  19 textes ; la relecture en a retiré 4 et un intitulé — « code des postes et
  des communications électroniques », le « remplacement » de conseillers
  départementaux et de parlementaires, le « CDD multi-remplacement ». Les
  chiffres annoncés avant cette relecture (45 intitulés, 19 textes) étaient
  faux.
- **On compte des personnes, sans les rapporteurs ni les présidents de
  commission.** Sur les fermetures de classes, un groupe comptait 35 tours de
  parole, tous dans le débat de son propre texte, dont 25 de son rapporteur :
  3 personnes. Un autre, 25 tours de parole dont 20 d'un seul orateur :
  4 personnes. 28 prises de parole sont écartées à ce titre.
- **Une personne est comptée une fois par sujet**, même si elle intervient sous
  plusieurs intitulés du même sujet. Pour la figure en hémicycle, elle est
  rangée sous son **sujet principal**, celui où elle a le plus de prises de
  parole : 24 des 100 députés sont sur plusieurs sujets, dont 7 à égalité, où
  l'ordre de la liste des sujets tranche — ce qui est arbitraire, et la page le
  dit.
- **Entre groupes : ni tri par nombre, ni compteur dans un titre.** La liste des
  textes rangée du groupe qui en a déposé le plus au moins a été refusée
  (« cette mise en forme ressemble à un classement ») ; elle est par ordre
  alphabétique, en un seul bloc. Un ratio de groupe garde son numérateur et son
  dénominateur (`AGENTS.md` §2 règle 7), dans la légende quand ils chargent la
  figure.
- **Au Journal officiel, les actes « liés au droit » seulement.** Les 41 arrêtés
  qui fixent ou répartissent les postes offerts aux concours relèvent du
  fonctionnement interne de l'État et sortent ; il reste 6 actes. **Ce tri
  n'est pas dans la source** : `rubrique_des_actes` range les 47 sous « Textes
  généraux ». Aucun de ces actes n'est déclaré par `liens_lois` comme
  appliquant une loi ; 5 en citaient une, tous parmi les 41 écartés.

## Les alternatives écartées

- **Compter les tours de parole par groupe**, en disques ou en barres à 100 % :
  elle compare des volumes entre groupes d'effectifs inégaux, et un rapporteur
  ou un orateur de groupe en produit vingt dans une séance.
- **Rapporter les prises de parole à l'effectif du groupe** : sur des totaux de
  8 à 63, le ratio grossit des écarts d'une ou deux interventions, et il
  ressemble à l'indice de participation que §2 règle 7 réserve au contrôle
  interne. Non construite.
- **Un bloc par groupe rempli à la part de ses membres intervenus**, et sa
  variante à angle égal et rayon selon l'effectif : la première se lit comme un
  classement et réduit les petits groupes à des filets, la seconde perd l'image
  de l'hémicycle.
- **Un hémicycle par sujet** : avec 11 ou 13 députés allumés sur 567, l'image
  est presque vide.
- **Garder les 41 arrêtés sur les postes** : recommandé par l'agent, parce que
  ce sont les seuls actes qui répondent au sujet le plus débattu ; écarté par la
  propriétaire.

## Ce qui n'a pas été vérifié

- **L'ordre des groupes de gauche à droite** dans l'hémicycle est placé de
  mémoire : la page de l'Assemblée répondait en erreur 503, et le dépôt ne porte
  aucun numéro de place. Il vaut aussi pour l'article du budget 2026 (#1166).
- **Les cas limites** : des intitulés et des textes ne sont retenus que parce
  qu'ils portent « établissements scolaires » ou « périscolaire » — port de
  l'uniforme, cérémonie des couleurs, mixité sociale et scolaire, violences dans
  le périscolaire. La question a été posée, la page a été fusionnée avec eux.
- **La répartition du temps de parole entre groupes par le règlement** n'a pas
  été mesurée : un écart entre groupes peut en venir autant que du sujet.
- Les familles de sujets reposent sur des expressions régulières écrites pour
  cet article, hors du dépôt (`~/Documents/github/Media/enseignement-sources/`).
