<a id="fiches-de-groupe-xive-1328"></a>
# Les fiches de groupe s'ouvrent à la XIVe : sept groupes, quatre rattachés à leur lignée (#1328, 2026-10-22)

`2026-10-22`

> **En bref** — « On ne remonte pas avant 2017 » (03/10/2026, `borne-noms-et-sigles-des-groupes-ajoutes-1168`) tenait sur deux raisons : la règle de filiation n'avait pas été mesurée avant, et une fiche XIVe aurait été « un squelette ». La première est réglée par la règle de #1328 (`filiation-par-les-reelus-1328`), la seconde ne tient plus depuis #1019 (dossiers de la XIVe lus). La borne descend à la XIVe (`PREMIERE_LEGISLATURE = 14`) : sept groupes entrent dans la table écrite à la main, `SRC`, `UMP`, `UDI` et `GDR` rattachés aux lignées SOC, LR, UDI et GDR, `ECOLO`, `RRDP` et `R-UMP` ouvrant chacun la leur. Coût accepté : ≈ + 80 Mo de profils pivot, ≈ + 1,0 Go de profils bruts.

## Contexte mesuré

La fiche d'une législature (#1314) n'avait, pour la XIVe, ni groupe à relier ni
position à afficher. Mesuré le 22/10/2026 :

| Raison de la borne de 2017 | Où | Tient-elle ? |
| --- | --- | --- |
| La règle de filiation n'a été éprouvée que de la XVe à la XVIIe | `borne-noms-et-sigles-des-groupes-ajoutes-1168` | non — mesurée sur XIV → XV, elle n'y tenait pas, d'où la règle de #1328 |
| Une fiche XIVe serait un squelette : votes et amendements, ni dossiers ni interventions | `ROADMAP.md`, plancher du corpus (01/09/2026) ; #777 | en partie — les dossiers sont lus depuis #1019 ; restent absentes les interventions (Syceron commence à la XVe) |

Les sept groupes de la XIVe (organes `GP` d'AMO30, non-inscrits exclus, renommages
réunis par la règle de la moitié) :

| Groupe (sigles AN) | Effectif | Lignée | Pourquoi |
| --- | ---: | --- | --- |
| `SRC` → `SER` | 350 | SOC | lien vers `SOC`-15 : 28 communs, 55 réélus, 28 anciens (67 %) |
| `UMP` → `LES-REP` | 210 | LR | lien vers `LR`-15 : 56, 65, 56 (93 %) |
| `UDI` | 35 | UDI | lien vers `UDI`-15 : 14, 15, 23 (74 %) |
| `GDR` | 15 | GDR | lien vers `GDR`-15 : 6, 6, 6 (100 %) |
| `ECOLO` (jusqu'au 19/05/2016) | 18 | nouvelle, `AN:LIGNEE:ECOLO-14` | aucun groupe de la XVe ne passe la règle ; `AN:LIGNEE:ECOLO` est déjà pris par ECOLO-16 → ECOS-17 |
| `RRDP` | 21 | nouvelle, `AN:LIGNEE:RRDP` | aucun lien |
| `R-UMP` (27/11/2012 – 15/01/2013) | 73 | nouvelle, `AN:LIGNEE:R-UMP` | aucun lien (vers `LR`-15 : 47 %) |

## Décision

**Les quatre arbitrages du 22/10/2026**, dans #1328 : la règle F (« on va partir sur
F »), le seuil de 60 %, le plancher de 5, et pour `R-UMP` une fiche, lignée d'un seul
maillon — « oui, A » : la règle commune, sans exception par la durée. Ses sept semaines
couvrent 10 scrutins du corpus, dont 2 solennels.

**Les groupes et leurs liens sont écrits dans la table écrite à la main**
(`config/groupes_reels.json`), pas laissés au run. La mise à jour automatique
(`groupes_amo30.mettre_a_jour_table`) calcule un lien **à l'entrée du successeur**
et ne réécrit jamais une entrée existante. Or les groupes de la XIVe sont les
prédécesseurs de groupes déjà dans la table. Laissée seule, avec la borne abaissée,
elle aurait ouvert quatre lignées neuves (dont une `AN:LIGNEE:UMP` nommée « Les
Républicains », distincte de la lignée LR) et laissé trois groupes non tranchés
(identifiant de lignée déjà pris). Mesuré à blanc le 22/10/2026. Les quatre liens sont
donc écrits sur les entrées de la XVe (`succede_a`), comme les seize liens déjà publiés
l'étaient, et **mesurés** à chaque run comme eux : les quatre passent la règle, et se
publient `comparaison_des_membres`.

Identifiants : le premier sigle de l'Assemblée à l'entrée, comme pour un groupe ajouté
par le run (arbitrage du 03/10/2026, « on garde tel quel ») — `AN:SRC:14`,
`AN:UMP:14`, `AN:UDI:14`, `AN:ECOLO:14`, `AN:GDR:14`, `AN:RRDP:14`, `AN:R-UMP:14` ; le
nom, le dernier de l'Assemblée. Après écriture, la dérivation et la table disent la même
chose : 18 lignées, 38 groupes, 20 liens identiques (`groupes_amo30.py --comparer`).

**La collecte.** 638 membres de groupes XIVe, dont 228 ont déjà un profil et **410
n'en ont aucun**. Ils reçoivent un slug fabriqué au roster puis leur entrée de
correspondance, comme les membres des groupes de la XVe ajoutés par #777.

## Le coût, mesuré et accepté

« oui j'accepte ce coût. Il faudra documenter tout ça » (22/10/2026).

| Ajout pour les 410 nouveaux | Estimation |
| --- | --- |
| Profils pivot | ≈ + 80 Mo (1,93 Go → 2,0 Go) |
| Profils bruts | ≈ + 1,0 Go (6,0 Go → 7,0 Go) |
| Shards `extract-roster-groupes` | ≈ + 30 % (9-11 min le 21/10, `timeout-minutes: 60`) |

Dix députés de la seule XIVe tirés au sort en proportion des groupes, collectés en local
hors dépôt : 13 à 54 Ko de profil pivot, 24 à 159 Ko de brut, aucune intervention. Les
amendements n'en sont pas sortis (la XIVe passe par les tranches figées en CI) ; ils sont
estimés depuis l'index par acteur de la XIVe — 756 500 signatures et cosignatures pour
408 des 410 — au poids par ligne mesuré sur `abdelkader-lahmar` (1 271 octets en brut,
94 en pivot). **Le chiffre exact viendra du premier run.**

## Alternative écartée

**Abaisser la borne seule et laisser le run tout ajouter** : quatre lignées neuves et
trois groupes non tranchés, mesuré ci-dessus. **Généraliser la mise à jour pour qu'un
prédécesseur nouveau s'accroche à un successeur existant** : le lien serait écrit sur
une entrée de la table écrite, que la composition refait à chaque run depuis le fichier
— il disparaîtrait au run suivant. Une extension vers le passé arrive une fois ; elle se
relit et s'écrit.

## Ce qui n'a pas été vérifié

- Les fiches XIVe elles-mêmes : elles paraissent au premier run. Ce que l'interface fait
  d'une fiche sans prise de parole, et d'une lignée qui commence en 2012, est à voir avec
  elle.
- Les 410 slugs fabriqués : une homonymie avec un profil existant est résolue par le
  roster (`an_roster.resoudre_slugs`), non relue une à une.
- `R-UMP` : ses 73 membres sont presque tous aussi membres de `UMP` ; la fiche de lignée
  LR et celle de R-UMP comptent donc les mêmes personnes pour des périodes distinctes.
