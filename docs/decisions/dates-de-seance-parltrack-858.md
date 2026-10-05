<a id="dates-de-seance-parltrack-858"></a>
# Une activité européenne republiée par ParlTrack se date de sa séance, ou ne se date pas (#858) (2026-10-05)

`2026-10-05`

> **En bref** — ParlTrack date du 22/11/2016 toute activité qu'il a republiée : **4 346 prises de parole et 314 textes européens de trois fiches de candidats déclarés** étaient publiés à cette date. La date de séance se lit dans la référence ou l'adresse du compte rendu ; ailleurs elle ne se lit nulle part, et la date devient `null` avec son motif. Simulé : 3 107 prises de parole retrouvent leur date, 1 211 la perdent en le déclarant, 28 gardent le 22/11/2016 parce qu'elles ont bien été tenues ce jour-là. Aucune entrée ajoutée ni perdue.

## 1. Le constat, remesuré

Sur le privé `2140244c4`, interventions de source européenne datées du
22/11/2016 : Jean-Luc Mélenchon 1 803, Florian Philippot 1 587, Marine Le Pen
956 — **4 346** ; textes portés : 4, 252, 58 — **314**. Raphaël Glucksmann, élu
en 2019, n'en a aucune.

## 2. Ce que la source porte

Le dump `ep_mep_activities` marque une activité republiée par
`date-type: "datePublished"` : 548 598 activités, toutes au 22/11/2016. Notre
index ne lisait pas ce champ.

| Type | republiées | date de séance lisible |
| --- | --- | --- |
| compte rendu de séance (`CRE`) | 354 547 | oui : dans la référence pour 347 322, dans l'adresse pour les 7 225 autres |
| tout le reste (explications de vote, questions, résolutions, rapports, avis) | 194 051 | non : la référence ne donne qu'une année |

Référence et adresse concordent sur les 347 322 comptes rendus qui portent les
deux.

## 3. La décision

1. **À l'entrée du corpus** (`parltrack_dumps.build_activities_index`) : pour une
   activité republiée, `date` est la date de séance (`date_de_seance`), ou nulle ;
   dans ce second cas `date_republication` garde la date de ParlTrack.
   `VERSION_SCHEMA_INDEX` passe à 5 — un index en cache servirait les anciennes
   dates.
2. **À la normalisation** : une date nulle pour ce motif se publie avec
   `date_non_resolue: {motif: "date_de_republication", valeur_source}`, sur
   `interventions[]` comme sur `textes_portes[]`. Même forme que la date
   impossible d'un amendement européen.
3. **Sur les entrées déjà publiées** : `merge_profile.corriger_dates_de_republication`,
   appliquée aux anciennes entrées **avant** la fusion par clé.

**Pourquoi avant, et pas un report comme les autres.** Une explication de vote
n'a pas d'identifiant, et 882 de celles des trois fiches sont dans ce cas : leur
clé de fusion pivot est leur contenu, date comprise. Corrigée après la fusion,
chacune serait publiée deux fois — mesuré : 42 doublons sans le report sur les
trois fiches, 0 avec. Le critère est sourcé : la jumelle neuve déclare la date de
republication que l'ancienne porte, ou porte la date que sa propre référence
écrit. Jamais « la nouvelle date gagne ».

Les textes portés n'ont pas besoin de report : leur clé de repli est leur
adresse, que les 314 portent, et `merge_dossier_records` laisse gagner l'entrée
neuve.

## 4. L'effet, simulé sur les quatre fiches à mandat européen

Index reconstruit depuis le dump du 12/09/2026, fusion rejouée sans rien écrire.

| Interventions européennes | Mélenchon | Philippot | Le Pen | Glucksmann |
| --- | --- | --- | --- | --- |
| publiées | 1 803 | 1 587 | 956 | 128 |
| après | 1 803 | 1 587 | 956 | 128 |
| au 22/11/2016, avant | 1 803 | 1 587 | 956 | 0 |
| au 22/11/2016, après | 10 | 10 | 8 | 0 |
| date nulle et déclarée, après | 87 | 903 | 221 | 0 |

Les 28 restantes portent le 22/11/2016 dans leur propre référence : c'était un
jour de séance plénière. Textes portés : 314 au 22/11/2016 avant, 0 après, 314 à
date nulle et déclarée.

**Simulé n'est pas mesuré** — et la simulation reprenait, pour les explications
de vote, l'adresse déjà publiée, que le run résout en ligne (#827).

## 5. Ce que cela change pour le lecteur

**1 211 prises de parole et 314 textes perdent leur date sur trois fiches.** Ils
étaient rangés à un jour faux ; ils ne sont plus rangés. L'interface, qui classe
par période, doit dire où elle met une entrée sans date : c'est à la session de
l'interface, et cela se montre avant d'être codé.

## 6. Alternative rejetée

**Dater une explication de vote de l'année de sa référence**, ou de la date du
scrutin qu'elle explique. L'année n'est pas une date ; et rattacher une
explication à un scrutin demande une jointure que le corpus ne sait pas faire —
c'est le résidu de #1011, pas un détail de ce lot (§2 règle 5).
