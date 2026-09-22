<a id="lien-vers-la-prise-de-parole-1087"></a>
# Chaque prise de parole porte l'ancre de sa page de séance à l'AN (#1087) (2026-09-22)

`2026-09-22`

> **En bref** — `source_url` d'une intervention mène à l'archive de la législature : le lecteur ne peut rien y vérifier. La page de compte rendu de l'AN porte une ancre par prise de parole, au numéro exact de l'attribut `id_syceron` du paragraphe. Chaque entrée Syceron le publie désormais, et le lien se construit sans rien stocker d'autre.

## Constat

Relevé par la propriétaire le 22/09/2026 : l'interface pointe vers la page
qui propose de télécharger l'archive. Avec l'extrait de 280 caractères (#1029),
un lien vers le texte entier devient la condition de la vérification (§2 règle 2).

## Mesuré (22/09/2026)

| | |
| --- | --- |
| Paragraphes portant `id_syceron` | 100 % — 62 535 (120 comptes rendus, XVII), 22 237 et 21 676 (40 chacun, XV et XVI) |
| Séances citées par le corpus | 2 590 (1 385 XV, 604 XVI, 601 XVII) |
| Séances tirées au hasard | 90 / 90 répondent 200 |
| Ancre `#4166184` | mène à l'intervention de Gabriel Attal du 20/07/2026 ; une ancre vérifiée par législature |
| Échec connu | `CRSANR5L16S2021O1N144`, daté du 01/02/2021 et rangé par l'AN sous la XVI : 500 |

## Décision

1. `parse_syceron` lit `@id_syceron` ; l'entrée brute et l'entrée pivot le
   portent, **dans toutes les formes** — complète, extrait, thème : c'est le
   lien qui rend l'extrait vérifiable.
2. **Le lien n'est pas stocké.** `schema_pivot.url_seance_an` le construit :
   l'uid du compte rendu est le préfixe d'`intervention_id`. ~25 octets par
   entrée au lieu de ~110 pour une URL.
3. La clé n'est écrite **que si le parseur l'a lue**. Posée à `None` sur une
   entrée d'un vieil index, elle ferait passer cet index pour conforme :
   `_syceron_index_qualifie` prend désormais `id_syceron` pour témoin, si bien
   que tout index d'avant #1087 est reconstruit au premier run qui collecte les
   interventions.
4. `merge_profile.reporter_id_syceron` pose l'ancre sur les entrées publiées
   qui ne l'ont pas, aux deux étages — sans lui, la fusion additive ne la
   donnerait jamais aux entrées existantes.

## Ce qui suit

- **Premier run avec `collect_interventions=true`** : reconstruction de l'index
  Syceron complet dans `extract-an`, et report sur le corpus publié.
- **Poids** : ≈ 25 o par entrée, aux deux étages — de l'ordre de 60 Mo pour
  ~1,2 million d'entrées (estimé).
- **L'interface** construit le lien (même règle que `url_seance_an`) et garde
  un repli sur la séance quand l'ancre manque ; le compte rendu mal rangé de la
  XVI y sera sans lien valide.

## Alternative rejetée

**Héberger le texte dans une release GitHub** : l'archive XML y resterait
illisible pour un lecteur. La page de l'AN est la source primaire, et elle se lit.
