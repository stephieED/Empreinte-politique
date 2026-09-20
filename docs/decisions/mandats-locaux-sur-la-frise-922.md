<a id="mandats-locaux-sur-la-frise-922"></a>
# Les mandats locaux entrent sur la frise du parcours, et le Sénat y prend sa sarcelle (#922) (2026-09-16)

`2026-09-16`

> **En bref** — les **29 mandats locaux** versés au pivot par #922, portés par **14 des 30 fiches publiées**, n'apparaissaient nulle part : la frise ne connaissait que les sièges électifs et les fonctions gouvernementales. Quatre fiches — Lisnard, Bouamrane, Verdier, Tondelier — n'affichaient **rien** dans « En bref ». Les mandats locaux prennent une piste grise sur la frise et une ligne dans le détail daté, avec un astérisque en légende qui renvoie à « données parcellaires, publiées seulement à partir de 2020 ». Le Sénat quitte ce gris pour la sarcelle `#169E9E`, et « Chef du gouvernement » devient un brun quadrillé de jaune. Arbitré par la propriétaire le 16/09/2026, sur maquettes puis sur le rendu local.

## 1. Le parcours, et pas « En bref » ni « Les fonctions exercées »

Trois emplacements ont été maquettés : un rang d'« En bref », un bloc des fonctions exercées, la frise. La propriétaire a retenu **la frise et son détail daté** — le parcours —, puis écarté une variante où les mandats locaux restaient dans le détail seul. Le bloc des fonctions exercées aurait de toute façon buté sur la mesure : il range **par durée**, et la source ne publie **aucune date de fin**. La seule autre date disponible, le constat du 27/02/2026, vient du fichier des sortants et **précède** les mandats de mars 2026 — une durée calculée y valait −22 jours sur la mairie de Cannes.

## 2. Une piste, sans être une institution

Le schéma pose que les mandats locaux ne sont pas une institution. Ils prennent pourtant une **piste à eux** (`INSTITUTION_LOCAL`), parce que le lecteur doit distinguer une mairie d'un siège de député. Aucun consommateur du parcours ne la lit par erreur : la comparaison au groupe, les périodes politiques et les colonnes d'« En bref » filtrent tous explicitement sur `parlement` ou `gouvernement`.

« En bref » se rend désormais dès qu'il a une frise, même sans aucun chiffre : seul le tableau reste absent.

## 3. Ce que la source publie, et comment la frise le dessine

| Mesuré sur les 29 mandats | Nombre | Sur la frise |
| --- | ---: | --- |
| début en mars-avril 2026 (municipales, agglomérations) | 19 | environ six mois |
| début en juillet 2021 (régions, départements) | 7 | environ cinq ans |
| mandat clos, fichier des sortants | 4 | de 2020 à la date de constat |

- **La date est celle du mandat en cours.** Le répertoire ne publie que la mandature commencée ; un maire de longue date apparaît « depuis le 21 mars 2026 ». Le pied de section le dit.
- **La fonction d'abord** : « Maire » commence le jour où le conseil l'élit, pas le jour du scrutin.
- **Un mandat en cours finit sur `FIN_OUVERTE`**, comme tous les rôles ouverts. Le premier branchement laissait `null` : `positionSurAxe(null)` vaut 0, et chaque mandat en cours se dessinait à la largeur minimale — la présidence de région de Bruno Retailleau, commencée en 2021, tenait comme trois mois. C'est la propriétaire qui l'a vu sur la page ; un test le garde.
- **Un mandat clos n'est pas rouvert.** `actif` se lit sur la source, jamais sur l'absence de fin : le segment s'arrête à la date où la source l'atteste, et la liste écrit « fin non publiée ».

Les libellés de collectivité restent ceux de la source — « Ca Cannes Pays De Lerins », « 4eme Vice-président du conseil communautaire » — : les recaser serait réécrire une source.

## 4. Les teintes

**Le Sénat prend la sarcelle `#169E9E`**, déclarée une fois sur `.cp-main` et lue par la frise, les colonnes et les blocs de fonctions. Elle lui était réservée « pour le jour où sa collecte serait rebranchée » ; ce jour est #885, et la sarcelle a été retenue le 15/09 malgré ses 67° d'écart au bleu de l'Union ([`frise-segments-pleins-et-senat-885`](frise-segments-pleins-et-senat-885.md) §4). Texte en encre : 5,55:1, contre 3,27:1 en blanc.

**Les mandats locaux prennent le gris `#9A958D`**, par `--local: var(--neutre)` — le gris pointe, il n'est pas recopié.

**« Chef du gouvernement » devient un brun quadrillé de jaune** (maille de 9 px, traits de 1,5 px). L'aplat jaune en faisait une institution de plus ; c'est une déclinaison du gouvernement, et la teinte le dit. Un contour jaune de 2 px a été essayé d'abord et ne se voyait pas : `--accent` est presque aussi clair que le fond blanc. Sur le brun, c'est le fond sombre qui donne son contraste au jaune ; la maille large a été préférée à la fine parce qu'elle se lit sur un segment court et gêne moins un libellé posé dessus.

## 5. Un défaut de légende corrigé au passage

La légende filtrait ses entrées sur la **piste** des rôles. « Membre du gouvernement » et « Chef du gouvernement » partageant la piste `gouvernement`, toute fiche de ministre affichait « Chef du gouvernement ». Elle lit désormais les **classes dessinées** : une entrée n'apparaît que si sa teinte est à l'écran. Le défaut précédait ce lot (#328).

## 6. Un test réécrit, et ce qu'il tenait

`test_la_teinte_d_un_banc_est_declaree_une_seule_fois` exigeait `--senat: var(--neutre)` — l'arbitrage où le Sénat n'avait pas de teinte propre. Il vérifie désormais la sarcelle, et que `--local` pointe sur `--neutre` sans recopier la valeur. La règle qu'il protège ne change pas : chaque teinte déclarée une fois, et lue par tous.

## 7. Ce que ce lot ne fait pas

- **Les mandats 2020-2026 perdus à la collecte.** La décision [`collecte-mandats-locaux-rne-922`](collecte-mandats-locaux-rne-922.md) mesurait quatre mandats pour David Lisnard, dont Cannes 2020 clos ; le corpus et le fichier brut n'en portent que trois. Sa mairie apparaît donc comme six mois. Signalé au pipeline le 16/09/2026.
- **Une hachure avant 2020** sur la piste locale a été maquettée et n'a pas été retenue : l'astérisque et la mention de pied la remplacent.

→ voisins : [`borne-mandats-locaux-2020-922`](borne-mandats-locaux-2020-922.md), [`frise-segments-pleins-et-senat-885`](frise-segments-pleins-et-senat-885.md)
