<a id="liste-gouvernements-amo30-996"></a>
# La liste des gouvernements se lit dans AMO30, elle ne s'écrit plus à la main (#996) (2026-09-17)

`2026-09-17`

> **En bref** — `raw_data/gouvernements_reels.json` était une liste écrite à la
> main le 14/08/2026 (#209), jamais reprise : 10 gouvernements, alors que les
> profils en portaient 17. `src/gouvernements_amo30.py` la réécrit à chaque run
> depuis les organes `GOUVERNEMENT` du référentiel AMO30 : **17 gouvernements, de
> Fillon I (17/05/2007) à Lecornu II**. Premier lot de #996, qui étend aux
> gouvernements la logique des groupes parlementaires.

## Contexte

Constat de la session « UI gouv », transmis le 17/09/2026. Profils portant un
gouvernement absent de la liste, toutes populations confondues : Lecornu I 15,
Valls II 8, Ayrault II 6, Valls 6, Cazeneuve 6, Ayrault I 5, Fillon I 2. La
chronologie publiée sautait de Fillon III (2012) à Philippe I (2017), et de
Bayrou à Lecornu II.

Décision de la propriétaire : même logique que les groupes parlementaires — le
roster vient de la source, un profil par membre, une fiche agrégée. Ce lot en
est la première marche : la liste.

## Ce que la source publie

AMO30 (archive du 17/08/2026) décrit chaque gouvernement comme un organe
`codeType == "GOUVERNEMENT"` : `uid`, `libelleAbrege` (`FILLON 2`), `viMoDe`
(dates). **17** organes, le premier le 17/05/2007. Raffarin et Villepin n'y sont
pas : c'est la borne de disponibilité, déclarée dans l'entête du fichier produit.

## Décision

1. **Un gouvernement par organe `GOUVERNEMENT`**, lu à chaque run, avant la
   génération des fiches. `organe_ref`, `libelle_an` et `periode` sont recopiés
   **verbatim**.
2. **Les 10 fiches existantes gardent leur identifiant, leur nom et leur
   fichier** (`gouvernement:FILLON_2`, « Gouvernement Fillon II »,
   `gouvernement-FILLON_2.json`). Le `nom` met en forme le libellé de la source
   (casse, chiffre romain) ; un libellé sans numéro reçoit « I » seulement si un
   successeur numéroté existe (`PHILIPPE` → « Philippe I », `CAZENEUVE` →
   « Cazeneuve »).
3. **Les dates sont celles d'AMO30**, non plus celles que la liste manuelle
   déduisait des profils. Sur les 10 fiches existantes, elles **élargissent** les
   périodes et ne les rétrécissent jamais : Borne commence le 17/05/2022 au lieu du
   21, Barnier le 06/09/2024 au lieu du 28, Bayrou le 14/12/2024 au lieu du 24,
   Lecornu II le 11/10/2025 au lieu du 13, Fillon II le 18/06/2007 au lieu du 19.
   Le contrôle de perte ne peut donc pas bloquer sur `textes`.
4. **Sans `continue-on-error`** : une archive illisible, ou sans organe
   `GOUVERNEMENT`, lève **avant** toute écriture. La liste committée reste en
   place ; une liste vide se lirait comme « aucun gouvernement ».
5. **La composition ne change pas encore** : `membres[]` reste rattaché par le
   libellé des mandats des profils présents. La collecte d'un profil pour chaque
   membre, et le rattachement par `acteur_ref`, sont les lots suivants de #996.

## Ce que ce lot laisse ouvert, et ce qu'il risque

- **Fillon I (2 profils), Lecornu I (15)…** auront des fiches aux membres très
  partiels jusqu'aux lots de collecte.
- **Fillon I finit le 18/06/2007 et Fillon II commence ce jour-là** : AMO30 fait
  se toucher les deux périodes. Un texte déposé ce jour-là appartiendrait aux deux
  fiches.
- **Premier run** : si l'archive des dossiers de l'AN manque, la génération des
  fiches ne réécrit rien (#427). Les 7 nouvelles fiches n'existent alors pas, et
  le portail (`_report_gouvernements`) bloque sur une fiche configurée absente.

## Alternatives rejetées

- **Ajouter les 7 à la main** : la liste se serait périmée au gouvernement
  suivant, exactement comme depuis #209.
- **Reconstruire la liste depuis les libellés des profils** : elle aurait
  dépendu de qui a un profil, ce que la source n'a pas besoin de savoir.
