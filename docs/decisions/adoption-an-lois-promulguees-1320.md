<a id="adoption-an-lois-promulguees-1320"></a>
# Une loi se date par sa dernière adoption à l'Assemblée (#1320, 2026-10-21)

`2026-10-21`

> **En bref** — Pour rattacher une loi à une législature (#1314), ni l'ouverture du dossier ni la promulgation ne conviennent. Chaque entrée de `textes_promulgues.json` publie donc la **dernière adoption par l'Assemblée** — date, mode fermé (`scrutin_public` avec ses scrutins, `sans_scrutin_public`, `considere_adopte_49_3` sans scrutin), uid de l'acte — et si le Sénat a statué après. Une absence est `null` avec un motif ; deux décisions le même jour ne départagent rien.

## Contexte mesuré

Mesuré le 21/10/2026 sur les quatre archives de dossiers (XIVe monolithique, XV,
`repository/16`, XVIIe), **1 017** lois promulguées après dédoublonnage par uid
(l'archive de législature la plus haute fait foi, comme pour tout le fichier).

| Archive qui fait foi | Lois | Scrutin public | Sans scrutin public | 49.3 | Adoption non résolue | Sénat après | AN en dernier | Même jour | Sans décision du Sénat |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| XIVe | 412 | 25 | 385 | 2 | 0 | 179 | 214 | 18 | 1 |
| XVe | 310 | 76 | 234 | 0 | 0 | 144 | 155 | 11 | 0 |
| XVIe | 146 | 80 | 59 | 6 | 1 | 71 | 64 | 10 | 0 |
| XVIIe | 149 | 102 | 40 | 3 | 3 | 57 | 85 | 4 | 0 |

En XVIIe, une adoption datée a en plus un mode non résolu (`scrutin_non_reconnu`).
Comptée **par archive, sans dédoublonnage** (la population de l'issue), la XVe
fait 319 lois et la XVIe 147 : 9 et 1 dossiers y figurent aussi dans une archive
plus récente, qui fait foi.

## Décision

- **La dernière adoption** est le dernier acte de décision de séance de
  l'Assemblée (`AN…-DEC`, `CMP-DEBATS-AN-DEC`) dont le `fam_code` est une adoption,
  au sens de `gouvernement_textes._FAM_CODE_STATUT_MAP` (TSORTF01-06, 14, 18). Le
  `fam_code`, pas le libellé : c'est la lecture que le reste du dépôt fait déjà, et
  il écarte « considéré comme **rejeté** » (TSORTF24) qu'un préfixe de libellé
  aurait pris pour une adoption.
- **Le mode se lit sur cet acte seul.** TSORTF06 → `considere_adopte_49_3`, sans
  `scrutin_ids` même si la source en posait (§2 règle 4) ; un `voteRefs` →
  `scrutin_public`, en clé du corpus `an:<lég>:<n°>` ; rien → `sans_scrutin_public`,
  **jamais** « main levée », puisque la procédure d'examen simplifiée n'est nommée
  nulle part. Un `voteRef` qui n'est pas un scrutin de l'Assemblée laisse `mode`
  `null` avec `mode_non_resolu = scrutin_non_reconnu` et la référence recopiée.
- **Une adoption qui n'est pas la dernière n'est pas publiée.** Si une CMP s'est
  accordée après elle et avant la promulgation, l'Assemblée a forcément lu ses
  conclusions (art. 45, al. 3) et le dossier ne le porte pas :
  `lecture_cmp_an_absente`. Sans ce garde-fou, 3 lois conclues en XVIIe auraient
  été rattachées à la XVIe. Même logique pour une décision postérieure au statut
  inconnu (`fam_code_inconnu`) ou non datée (`decision_non_datee`).
- **« Le Sénat a statué après »** compte toute décision de séance du Sénat datée
  strictement après, rejet et statut absent compris : la question est qui a statué
  en dernier. Le même jour, l'indicateur est `null` (`decisions_le_meme_jour`) — la
  source date au jour, comme pour `chambre_premiere_lecture` —, sauf en lecture
  définitive, qui suit toujours la nouvelle lecture du Sénat (art. 45, al. 4).
- **Fusion inchangée** : l'entrée d'un dossier relu remplace l'ancienne, donc
  une entrée existante reçoit les nouveaux champs au prochain run ; un dossier non
  relu, ou un run sans archive, garde ce qui est publié.

## Alternatives écartées

- **La date de promulgation** : 35 des 153 lois des dossiers ouverts en XVIe ont
  été promulguées après la dissolution (mesure de l'interface). Elle date le
  gouvernement qui promulgue, pas l'Assemblée qui adopte.
- **L'ouverture du dossier** : un dossier ouvert en XVIe peut être conclu en
  XVIIe — 36 lois de dossiers de la XVIe font foi dans l'archive XVIIe.
- **« Strictement après », le même jour compté comme « l'Assemblée en dernier »**
  (la règle de la mesure de l'issue) : 43 lois en auraient reçu `false` sans que
  la source permette de le dire.

## Non vérifié

- Que la date d'une décision 49.3 soit partout celle du vote de la dernière
  motion : vrai sur 15 des 25 décisions qui portent ce vote ; pour les autres, le
  dossier ne le porte pas (détail dans `docs/sources/an-opendata.md`).
- Le compte rendu ou l'ordre du jour comme source de la procédure d'examen
  simplifiée.
- Les 4 lectures de CMP manquantes : sur `DLR5L16N46655`, elle est
  vraisemblablement l'acte codé `CMP-DEBATS-SN-DEC` du 04/02/2025, qui porte un
  scrutin de l'Assemblée. Pas corrigé : ce serait réécrire la source.
- Le tableau sur `public/main` après un run.
