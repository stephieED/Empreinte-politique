# Un bloc structuré sans fond n'écrase plus un bloc collecté (#484) (2026-08-30)

`2026-08-30`

> **En bref** — un squelette d'identité à 8 clés dont 7 nulles n'est pas vide, donc il gagnait ; la fusion demande désormais si un bloc a du fond.

`jean-luc-melenchon` publiait `identite: null`, un avertissement « aucun mandat
français connu » et une synchronisation Assemblée nationale au 19/08 — alors que
ses 63 mandats et ses 1 016 votes étaient intacts dans le même fichier.

## Ce n'était pas un écart CI/local

L'hypothèse instruite d'abord — un cache CI portant un index d'identité périmé —
est **infirmée**. Le squelette venait d'un **autre job du même run**.

`generate-data.yml` fusionne `--dirs _artifacts/an _artifacts/ue _artifacts/roster` :
l'UE passe **après** l'AN. Le job UE écrit un profil minimal
(`build_minimal_profile`), et `merge_raw_profile` faisait :

```python
merged["identite"] = _prefer_non_empty(new.get("identite"), old.get("identite"))

def _prefer_non_empty(new_value, old_value):
    if new_value not in (None, "", [], {}):   # ne teste que la vacuité
        return new_value
    return old_value
```

Le test demande « ce bloc est-il **vide** ? », pas « a-t-il du **fond** ? ». Le
squelette du chemin minimal n'est pas `{}` : c'est un dictionnaire à 8 clés dont
`nom_complet` est rempli et les 7 autres valent `null`. Il est donc « renseigné »,
donc il gagne.

Corroboré sur le profil commité avant correctif :

| Mesure | Valeur |
| --- | --- |
| `meta.genere_le` | `2026-08-29T16:16:17+0000` — l'horodatage du job UE, à la seconde |
| `meta.warnings[0]` | le littéral exact de `build_minimal_profile` |
| `identite` pivot publiée | `null` |
| `mandats` / `votes` | intacts — la fusion des **listes** est additive |

`marine-le-pen` y échappait parce qu'elle est membre d'un groupe publié : un
troisième artifact repassait derrière. `jean-luc-melenchon` n'appartient à aucun
groupe publié — le job UE était le dernier écrivain.

**Le garde-fou et ce qui l'a déclenché étaient la même chose.** Il n'y avait rien
à chercher côté réseau, cache ou rate-limit.

## Le correctif

`_prefer_non_empty` demande désormais si le bloc **a du fond** :

- `BLOCS_PROTEGES_DU_VIDE` + `bloc_sans_fond()` + `_preferer_bloc_avec_fond()` —
  étend à `identite` la règle de
  [#465](collecte-vide-necrase-jamais.md), qui ne couvrait que des listes.
- `preserver_collectes_non_vides` étendu aux blocs.
- `_synchro_la_plus_recente()` : `synchro_sources` prend la valeur la plus
  **récente** par source, au lieu d'être recopiée en bloc.
- L'avertissement « aucun mandat français connu » s'éteint quand une identité AN
  le dément. Le littéral devient la constante `WARNING_AUCUN_MANDAT_FR` :
  **aucun texte publié ne change**.

**Aucun profil n'est supprimé ni régénéré.** Mesuré avant d'écarter cette voie :
effacer pour recollecter perdrait des mandats — dont un mandat sénatorial
2004-2010 qu'aucune source vivante ne rend. La fusion additive les conserve, et
un run normal répare le profil de lui-même.

## Vérifié en conditions réelles, pas seulement en test

12 tests ajoutés, dont la reprise bout en bout du run `33262372122` ; **8
échouent sur le code d'avant** (vérification par mutation).

Puis le run `33307905880` du 30/08/2026 a appliqué le correctif au corpus :

| Sur `jean-luc-melenchon` | Avant | Après |
| --- | --- | --- |
| `identite` brute | squelette, 2 champs sur 8 | complète (`Professeur`, `1951-08-19`, `Tanger (Maroc)`, circo 4, fiche `OMC_PA2150`) |
| `identite` pivot publiée | `null` | renseignée |
| `synchro_sources.assemblee_nationale` | `2026-08-19` (9,9 j de retard) | `2026-08-30T11:06:25+0000` |
| Avertissement du chemin minimal | présent | `warnings: []` |
| Mandats / votes | 63 / 1 016 | 63 / 1 016 |

Le job AN **résolvait bien** l'identité : c'est le squelette UE qui gagnait.

Effet de bord attendu et non régressif : le profil publie maintenant trois
avertissements qui étaient **masqués** — deux de #492/#493, un de ParlTrack. Ils
étaient invisibles parce que le `meta` venait du profil minimal UE, qui ne
portait que le sien.

## Ce que ce lot ne fait pas, et pourquoi il en appelle un autre

La forme reste **choisir un bloc gagnant**, pas **composer**. Si le job AN connaît
la `profession` et le job UE le `groupe_nom`, un seul des deux survit encore. Le
défaut n'est pas propre à `identite` : la fusion travaille à trois granularités,
et une seule compose réellement plusieurs sources.

| Granularité | Comportement | Compose ? |
| --- | --- | --- |
| Listes (`votes`, `mandats`, `interventions`, `amendements`, `textes_portes`, `tags_thematiques`) | additif par clé, dédoublonné | **oui** |
| Scalaires (`parti`, `groupe`, `chambre`) | `_prefer_non_empty` | grossièrement |
| Blocs structurés (`identite`, `meta`, `couverture`) | un bloc gagnant, entier | **non** |

C'est l'objet de l'épic **#598**, ouverte à la suite de ce lot. Ce correctif y est
un palliatif assumé : il sera **absorbé** par le lot `identite` champ par champ,
pas conservé en parallèle.

Deux points restent hors de ce lot, et le restent délibérément :

- `chambre: "senateurs"` dans le brut — c'est la sous-issue D de #486, qui
  demande de dériver `chambre` de `chambres` plutôt que de la collecte.
- `sources[0].type: "nossenateurs"` sur une URL LCP — ne s'éteint **jamais** sous
  fusion additive (`_merge_pivot_sources` unit par `type`) ; seul un run à perte
  déclarée le retirerait.
