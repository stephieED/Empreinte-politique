"""Garde-fou #668 : une clé de fusion en `a or b` ne doit pas changer de branche.

## Le défaut mesuré

`merge_profile._pivot_texte_key` valait, jusqu'à ce lot :

```python
return t.get("source_url") or (t.get("titre"), t.get("date_min"), t.get("legislature"))
```

Le rang 2 de #639 a réparé `normalize_profil._normalize_texte_porte`, qui
publiait `source_url: null` sur **472 / 472** entrées : il lisait
`url_source`/`url_institution`, absents de 100 % des entrées brutes, alors que
la collecte AN écrit `source_url` depuis #400.

Au run suivant (`33395056902`, 31/08/2026), les entrées **déjà publiées**
étaient donc keyées sur le repli `(titre, date_min, legislature)` et leurs
jumelles renormalisées sur **`source_url`**. Deux clés incomparables pour un
même dossier : `merge_dossier_records` a conservé les deux.

Mesuré sur `origin/main` le 31/08/2026, en flux sur les 481 profils :

| | |
| --- | ---: |
| Profils publiant des textes portés | 22 |
| Entrées publiées | 940 |
| Entrées portant un `dossier_id` | 472 |
| Entrées héritées, sans `dossier_id` | 468 |
| Dossiers réellement collectés (brut `dossiers_legislatifs`) | 472 |

Ce n'est pas le défaut de #540 — une clé *collante*, qui absorbe des entrées
distinctes. C'est son symétrique : une clé **volatile**, qui dédouble une même
entrée. La donnée n'a pas changé, c'est la branche du `or` que l'objet emprunte.

## Ce que ce fichier vérifie

1. La clé repose sur `dossier_id` (`DLR…`), l'identifiant AN du dossier — la
   même identité que `dossiers_legislatifs[].id` au brut. `source_url` en est
   sorti : une URL n'est pas un identifiant (#540), et c'est la branche qui a
   basculé.
2. Une entrée **sans** `dossier_id` garde le repli `(titre, date_min,
   legislature)` — la réduire à une clé `None` serait la perte silencieuse que
   `_pivot_vote_key` décrit (#432).
3. `clean_stale_textes_portes` réconcilie l'entrée héritée avec sa jumelle
   identifiée, et **ne peut rien perdre** : sans jumelle, rien n'est écarté.
4. Deux dossiers distincts de titre voisin ne sont pas confondus.
5. `merge_pivot_profile` appelle bien la reprise — elle n'était appelée nulle
   part avant ce lot.

Aucun test ici ne lit le corpus : le workflow de tests le sparse-checkout hors
du disque (voir `tests/conftest.py`). Les chiffres ci-dessus sont des mesures
citées ; les fixtures sont des **réductions verbatim** d'entrées publiées
(`edouard-philippe`, `xavier-roseren`, `ludovic-mendes` sur `origin/main`,
31/08/2026), jamais des doublures inventées (#510).
"""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from merge_profile import (  # noqa: E402
    _pivot_texte_key,
    _repli_texte_key,
    clean_stale_textes_portes,
    merge_dossier_records,
    merge_pivot_profile,
)

# --- Réductions verbatim d'entrées publiées sur origin/main (31/08/2026) -----

# `edouard-philippe`, les deux versions du MÊME dossier : celle d'avant #639
# (pas de clé `dossier_id`, `source_url: null`) et sa renormalisation.
CETA_HERITE = {
    "titre": (
        "Accord économique et commercial global (CETA) et accord de partenariat "
        "stratégique entre l'UE et le Canada"
    ),
    "role": "auteur",
    "type_rapport": None,
    "stade_procedural": "adopte",
    "date_min": "2019-06-19",
    "date_max": "2024-03-21",
    "legislature": "15",
    "source_url": None,
}
CETA_IDENTIFIE = {
    "titre": (
        "Accord économique et commercial global (CETA) et accord de partenariat "
        "stratégique entre l'UE et le Canada"
    ),
    "dossier_id": "DLR5L15N37607",
    "role": "auteur",
    "type_rapport": None,
    "stade_procedural": "adopte",
    "date_min": "2019-06-19",
    "date_max": "2024-03-21",
    "legislature": "15",
    "source_url": (
        "https://www.assemblee-nationale.fr/dyn/15/dossiers/"
        "aecg_partenariat_strategique_ue-canada"
    ),
}

# `xavier-roseren` : une entrée identifiée dont `source_url` est resté nul —
# 4 des 472 entrées identifiées du corpus sont dans ce cas. `dossier_id` est
# donc le seul identifiant qui couvre toute la population.
MISSION_MONTAGNE = {
    "titre": "Mission d’information sur la transition des modèles des stations de montagne",
    "dossier_id": "DLR5L17N51855",
    "role": "co-rapporteur",
    "type_rapport": "rapporteur_fond",
    "stade_procedural": None,
    "date_min": "2025-04-03",
    "date_max": "2025-04-30",
    "legislature": "17",
    "source_url": None,
}

# `ludovic-mendes` : DEUX dossiers réels, de titre voisin et de même
# législature — la proposition de loi et son rapport. Les confondre serait une
# perte, exactement le piège symétrique du doublon.
CHARBON_RAPPORT = {
    "titre": (
        "Proposition de loi visant à convertir des centrales à charbon vers des "
        "combustibles moins émetteurs en dioxyde de carbone pour permettre une "
        "transition écologique plus juste socialement"
    ),
    "dossier_id": "DLR5L17N51485",
    "role": "rapporteur",
    "type_rapport": "rapporteur_fond",
    "stade_procedural": "promulgue",
    "date_min": "2025-02-11",
    "date_max": "2025-04-14",
    "legislature": "17",
    "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/DLR5L17N51485",
}
CHARBON_AUTEUR = {
    "titre": (
        "Convertir des centrales à charbon vers des combustibles moins émetteurs "
        "en dioxyde de carbone pour permettre une transition écologique plus "
        "juste socialement"
    ),
    "dossier_id": "DLR5L17N51626",
    "role": "auteur",
    "type_rapport": None,
    "stade_procedural": "examine_commission",
    "date_min": "2025-03-11",
    "date_max": "2025-03-11",
    "legislature": "17",
    "source_url": (
        "https://www.assemblee-nationale.fr/dyn/17/dossiers/"
        "convertir_centrales_charbon_combustibles_moins_emetteurs_dioxyde_carbone_17e"
    ),
}


def _profil_pivot(textes):
    return {
        "id": "slug",
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": copy.deepcopy(textes),
        "amendements": [],
        "interventions": [],
        "tags_thematiques": [],
        "meta": {"warnings": []},
    }


# --- 1. La clé repose sur l'identifiant, pas sur l'URL ----------------------


def test_la_cle_est_le_dossier_id_pas_la_source_url():
    assert _pivot_texte_key(CETA_IDENTIFIE) == ("dossier_id", "DLR5L15N37607")


def test_une_source_url_qui_se_remplit_ne_change_plus_la_cle():
    """Le cœur de #668 : `source_url` passe de `null` à une valeur, la clé non.

    Sur l'ancienne clé, la même entrée valait `(titre, date_min, legislature)`
    avant et `source_url` après — deux identités pour un dossier.
    """
    avant = dict(CETA_IDENTIFIE, source_url=None)
    assert _pivot_texte_key(avant) == _pivot_texte_key(CETA_IDENTIFIE)


def test_une_entree_identifiee_sans_source_url_est_quand_meme_identifiee():
    assert _pivot_texte_key(MISSION_MONTAGNE) == ("dossier_id", "DLR5L17N51855")


def test_une_entree_sans_dossier_id_garde_le_repli_et_non_une_cle_nulle():
    """Toutes les entrées héritées ne doivent pas s'effondrer sur une clé unique."""
    autre = dict(CETA_HERITE, titre="Un autre dossier", date_min="2020-01-01")
    assert _pivot_texte_key(CETA_HERITE) == _repli_texte_key(CETA_HERITE)
    assert _pivot_texte_key(CETA_HERITE) != _pivot_texte_key(autre)
    assert _pivot_texte_key(CETA_HERITE) is not None


def test_deux_dossiers_de_titre_voisin_ne_sont_pas_confondus():
    assert _pivot_texte_key(CHARBON_RAPPORT) != _pivot_texte_key(CHARBON_AUTEUR)
    fusion = merge_dossier_records([CHARBON_RAPPORT], [CHARBON_AUTEUR], _pivot_texte_key)
    assert len(fusion) == 2
    assert clean_stale_textes_portes(fusion) == fusion


# --- 2. La reprise des entrées d'avant #639 ---------------------------------


def test_la_reprise_ecarte_l_entree_heritee_au_profit_de_l_identifiee():
    cleaned = clean_stale_textes_portes([CETA_HERITE, CETA_IDENTIFIE])

    assert cleaned == [CETA_IDENTIFIE]
    assert cleaned[0]["dossier_id"] == "DLR5L15N37607"
    assert cleaned[0]["source_url"]


def test_la_reprise_ne_depend_pas_de_l_ordre_de_la_liste():
    assert clean_stale_textes_portes([CETA_IDENTIFIE, CETA_HERITE]) == [CETA_IDENTIFIE]


def test_la_reprise_est_idempotente():
    liste = [CETA_HERITE, CETA_IDENTIFIE]
    assert clean_stale_textes_portes(clean_stale_textes_portes(liste)) == [CETA_IDENTIFIE]


def test_la_reprise_ne_perd_rien_sans_jumelle_identifiee():
    """Collecte en échec, dossier disparu de l'open data : l'entrée reste publiée."""
    assert clean_stale_textes_portes([CETA_HERITE]) == [CETA_HERITE]
    assert clean_stale_textes_portes([CETA_HERITE, MISSION_MONTAGNE]) == [
        CETA_HERITE,
        MISSION_MONTAGNE,
    ]
    assert clean_stale_textes_portes(None) == []


def test_la_reprise_n_ecarte_que_sur_un_repli_identique():
    """Un dossier hérité dont le titre a changé n'est pas absorbé par un autre."""
    autre_date = dict(CETA_HERITE, date_min="2017-01-01")
    cleaned = clean_stale_textes_portes([autre_date, CETA_IDENTIFIE])
    assert cleaned == [autre_date, CETA_IDENTIFIE]


# --- 3. Le chemin complet : fusion additive puis reprise --------------------


def test_merge_pivot_profile_ne_republie_plus_le_dossier_en_double():
    """Le run de production : l'ancien profil porte les deux versions, le neuf
    n'a que l'identifiée. Une seule entrée doit sortir."""
    old = _profil_pivot([CETA_HERITE, CETA_IDENTIFIE])
    new = _profil_pivot([CETA_IDENTIFIE])

    merged = merge_pivot_profile(old, new)

    assert len(merged["textes_portes"]) == 1
    assert merged["textes_portes"][0]["dossier_id"] == "DLR5L15N37607"


def test_merge_pivot_profile_reconcilie_l_heritee_avec_sa_renormalisation():
    """L'état d'avant le run fautif : l'ancien profil n'a que l'entrée héritée,
    le neuf n'a que l'identifiée. La fusion additive les voyait comme deux
    dossiers — c'est ce qui a produit les 468 doublons."""
    old = _profil_pivot([CETA_HERITE])
    new = _profil_pivot([CETA_IDENTIFIE])

    merged = merge_pivot_profile(old, new)

    assert len(merged["textes_portes"]) == 1
    assert merged["textes_portes"][0]["dossier_id"] == "DLR5L15N37607"


def test_merge_pivot_profile_conserve_un_dossier_absent_de_la_collecte_neuve():
    """AGENTS.md §3a : une régénération ne retire jamais une donnée collectée."""
    old = _profil_pivot([CETA_HERITE, MISSION_MONTAGNE])
    new = _profil_pivot([CETA_IDENTIFIE])

    merged = merge_pivot_profile(old, new)

    ids = {t.get("dossier_id") for t in merged["textes_portes"]}
    assert ids == {"DLR5L15N37607", "DLR5L17N51855"}
