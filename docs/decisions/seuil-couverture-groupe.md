<a id="seuil-couverture-groupe"></a>
# Seuil de couverture de groupe (`--groupe-min-members`) : conservé faute de chiffres réels à pleine échelle (2026-08-12)

`2026-08-12`

> **En bref** — `--groupe-min-members` conservé, faute de chiffres réels à pleine échelle.

**Contexte** : #193 demande de recalibrer `--groupe-min-members` (`check_quality_gate.py`,
défaut 1, cf. `generate-data.yml:413`) maintenant que la couverture roster est censée
approcher 100 % (post #188/#190/#191), ce seuil absolu ayant été pensé à l'origine
pour une couverture quasi nulle. L'issue #193 demande explicitement de trancher
« en fonction des résultats réels [...] (ne pas fixer de nouveau seuil dans le vide
avant d'avoir des chiffres réels) ».

**Constat** : au moment de cette recalibration, aucun run à pleine échelle
(~750 membres roster, #188) n'a encore été exécuté en CI. Les fichiers
`pivot_data/groupes/*.json` présents dans le dépôt proviennent de runs à échelle
réduite (`--limit`/`--sample`, voir [[limit-sample]]) et affichent des taux de
couverture réels très faibles et hétérogènes (ex. `AN:REN` 1/193 ≈ 0,5 %,
`AN:SOC` 1/31 ≈ 3,2 %, `AN:LFI` 0/76 = 0 %) — non représentatifs de la couverture
quasi complète visée. Fixer un seuil relatif strict dès maintenant reviendrait à
choisir un nombre dans le vide, exactement ce que #193 demande d'éviter.

**Décision** : conserver `--groupe-min-members 1` comme seuil par défaut (soft
fail uniquement, jamais bloquant), et ajouter en parallèle un seuil relatif
optionnel `--groupe-min-coverage-pct` (défaut `0`, désactivé) dans `_report_groupes`
(`check_quality_gate.py`), pour permettre d'activer un contrôle basé sur le taux de
couverture (`profils_disponibles / roster_total`) dès que des chiffres réels à
pleine échelle seront disponibles (issues de suivi #188/#190/#191), sans nouveau
changement de signature. `audit_groupe_dataset.py` expose désormais
`taux_couverture_pct` dans `coherence.ecart_couverture_roster` (voir
[[provenance-pivot]] pour le contexte de la recalibration roster), pour suivre
cette progression dans le temps avant de choisir une valeur définitive. Le
fichier `.github/workflows/generate-data.yml` (permissions de modification hors
périmètre agent) n'est pas mis à jour par ce changement : la valeur par défaut de
`--groupe-min-members` y reste `1`, cohérente avec le choix ci-dessus.

*Alternative rejetée* : remplacer directement `--groupe-min-members` par un seuil
relatif avec une valeur par défaut choisie a priori (ex. 80 %) — rejeté car aucune
donnée réelle à pleine échelle ne permet de justifier ce chiffre à ce stade, et un
seuil trop haut ferait immédiatement échouer le gate qualité (en soft fail) sur les
runs actuels à échelle réduite, sans valeur informative.

