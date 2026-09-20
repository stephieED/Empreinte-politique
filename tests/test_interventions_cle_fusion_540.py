"""Garde-fou #540 : une URL de source n'est pas un identifiant d'intervention.

## Le défaut mesuré

`merge_profile._pivot_intervention_key` valait, jusqu'à ce lot :

```python
return i.get("source_url") or (i.get("date"), i.get("sujet"), (i.get("texte") or "")[:50])
```

Le `or` court-circuite : le repli discriminant — le triplet date/sujet/texte —
n'était **jamais atteint** dès que `source_url` était renseignée. La clé avait
été écrite pour une source qui publiait un permalien par intervention (l'ancre
`#inter_<hash>` de NosDéputés) ; Syceron publie l'URL de **l'archive de la
législature**, la même pour toutes les interventions de cette législature.

`merge_lists_by_key` étant purement additif, il ne peut rien perdre — mais il
n'ajoute que les clés inédites. Mesuré sur les profils bruts committés
(HEAD `74c77c2`, 27/08/2026) : **7 767 interventions collectées, 891 publiées**
sur 476 profils, dont 3 351 collectées contre 17 publiées pour gabriel-attal.

## Ce que ce fichier vérifie

Le correctif propage l'`id` du profil brut jusqu'au pivot
(`interventions[].intervention_id`) et en fait la clé. C'est **la même identité
que celle de la fusion brute** `_intervention_key`, qui repose sur `id` et n'a
jamais souffert du défaut : les deux étages disent désormais la même chose de
ce qu'est une intervention.

L'alternative — une clé composite `(source_url, date, sujet, texte[:80])` —
est éprouvée ici aussi, et elle est **lossy** : « Même avis, pour les mêmes
raisons. » est prononcé 13 fois dans la même séance du 08/11/2022, sur
13 amendements successifs. Ce ne sont pas des doublons d'archive, ce sont
13 prises de parole distinctes. Mesurée sur le corpus, cette clé rend 7 500
entrées au lieu de 7 767 : elle en absorbe 267 réelles.

Aucun test ici ne lit le corpus : le workflow de tests le sparse-checkout hors
du disque (voir `tests/conftest.py`). Les chiffres ci-dessus sont des mesures
citées, les fixtures sont des doublures.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from merge_profile import (  # noqa: E402
    _pivot_intervention_key,
    clean_stale_interventions,
    merge_lists_by_key,
    merge_pivot_profile,
)
from normalize_profil import _normalize_intervention  # noqa: E402

# L'URL que Syceron publie pour CHACUNE de ses interventions : l'archive de la
# législature, pas la prise de parole.
ARCHIVE_17 = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/"
    "vp/syceronbrut/syseron.xml.zip"
)
ARCHIVE_16 = (
    "https://data.assemblee-nationale.fr/static/openData/repository/16/"
    "vp/syceronbrut/syseron.xml.zip"
)


def _cle_avant_540(i):
    """La clé telle qu'elle était, reproduite pour montrer ce qu'elle rend."""
    return i.get("source_url") or (i.get("date"), i.get("sujet"), (i.get("texte") or "")[:50])


def _cle_composite_ecartee(i):
    """L'alternative composite proposée par #540, reproduite pour la mesurer."""
    return (i.get("source_url"), i.get("date"), i.get("sujet"), (i.get("texte") or "")[:80])


def _brut_syceron(rang, texte, date="2022-11-08", compte_rendu="CRSANR5L16S2023O1N055"):
    """Une intervention brute Syceron, telle que la produit
    `candidate_profile._parse_syceron_intervention_entry`."""
    return {
        "id": f"syceron_{compte_rendu}_{rang:06d}",
        "date": date,
        "type_detail": "loi",
        "sujet": "Projet de loi de finances pour 2023",
        "texte": texte,
        "fonction": None,
        "format": "reaction_courte",
        "mots_cles": [],
        "source": ARCHIVE_16,
        "source_url": ARCHIVE_16,
        "url": ARCHIVE_16,
        "url_detail": None,
        "source_id": compte_rendu,
        "seance_ref": "RUANR5L16S2023IDS26555",
        "session_ref": "SCR5A2023O1",
        "orateur_id_source": "PA719168",
        "orateur_nom": "M. Gabriel Attal",
        "point_ordre_du_jour": "Projet de loi de finances pour 2023 > Après l'article 9",
        "legislature": "16",
    }


def _brut_nosdeputes(id_brut, seance, ancre):
    """Une intervention héritée de NosDéputés : un permalien par entrée, et un
    `id` entier — la plateforme est sortie du pipeline (#529), ses entrées
    restent publiées et traversent la fusion additive."""
    url = f"https://2017-2022.nosdeputes.fr/15/seance/{seance}#inter_{ancre}"
    return {
        "id": id_brut,
        "date": "2017-08-09",
        "type_detail": "question",
        "sujet": "Hommage aux militaires de l'opération sentinelle",
        "texte": "Monsieur le président, mesdames et messieurs les députés...",
        "fonction": None,
        "format": "prise_de_parole_developpee",
        "mots_cles": [],
        "url": url,
        "url_detail": url,
    }


def _pivot(interventions):
    """Le squelette minimal qu'attend `merge_pivot_profile`."""
    return {
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": list(interventions),
        "amendements": [],
        "tags_thematiques": [],
        "meta": {"warnings": []},
    }


# --- 1. Le cas Syceron : N entrées, une seule source_url -------------------

def test_n_interventions_syceron_sur_une_seule_url_darchive_font_n_cles():
    """Le test discriminant de #540 : 13 « Même avis » de la même séance.

    Même `source_url` (l'archive), même date, même sujet, même texte — et
    pourtant 13 prises de parole distinctes, sur 13 amendements successifs.
    Seul l'`id` les sépare.
    """
    brutes = [
        _brut_syceron(rang, "Même avis, pour les mêmes raisons.")
        for rang in range(100, 113)
    ]
    pivot = [_normalize_intervention(i) for i in brutes]

    assert len({_pivot_intervention_key(i) for i in pivot}) == 13
    # La clé d'avant #540 les réduisait TOUTES à une seule.
    assert len({_cle_avant_540(i) for i in pivot}) == 1
    # La composite écartée aussi : elle ne discrimine pas sur du texte identique.
    assert len({_cle_composite_ecartee(i) for i in pivot}) == 1


def test_la_fusion_publie_toutes_les_interventions_syceron_collectees():
    """Bout en bout : 13 entrées collectées → 13 entrées publiées.

    Avec la clé d'avant #540, la même fusion en publiait 1 sur 13 — c'est le
    rapport 3 351 → 17 mesuré sur gabriel-attal, à l'échelle d'une séance.
    """
    brutes = [
        _brut_syceron(rang, "Même avis, pour les mêmes raisons.")
        for rang in range(100, 113)
    ]
    neuves = [_normalize_intervention(i) for i in brutes]

    merged = merge_pivot_profile(_pivot([]), _pivot(neuves))
    assert len(merged["interventions"]) == 13

    # Contrôle : la clé d'origine, sur les mêmes données.
    assert len(merge_lists_by_key([], neuves, _cle_avant_540)) == 1


def test_deux_legislatures_deux_archives_restent_distinctes():
    """Deux archives, deux `source_url` — mais c'est l'`id` qui sépare, pas
    l'URL : le compte rendu et le rang du paragraphe en font partie."""
    brutes = [
        _brut_syceron(1, "Défavorable.", compte_rendu="CRSANR5L16S2023O1N055"),
        _brut_syceron(1, "Défavorable.", compte_rendu="CRSANR5L17S2026O1N200"),
    ]
    brutes[1]["source_url"] = brutes[1]["url"] = ARCHIVE_17
    pivot = [_normalize_intervention(i) for i in brutes]
    assert len({_pivot_intervention_key(i) for i in pivot}) == 2


# --- 2. Le cas NosDéputés hérité : aucune régression ----------------------

def test_les_interventions_heritees_de_nosdeputes_ne_disparaissent_pas():
    """65 entrées héritées (Édouard Philippe, Jean-Luc Mélenchon) portent un
    permalien `#inter_<hash>` par intervention : la clé d'origine fonctionnait
    pour elles. Le correctif ne doit ni les perdre, ni les dédoubler."""
    brutes = [
        _brut_nosdeputes(29173, 131, "78eecc9dc94da665e50bfcec91180051"),
        _brut_nosdeputes(86867, 480, "6c4b8f7e673ffcb606c197ec65bbf0d1"),
        _brut_nosdeputes(94967, 525, "c902abc73ac4efc743d916032ea6a1b2"),
    ]
    neuves = [_normalize_intervention(i) for i in brutes]
    assert len({_pivot_intervention_key(i) for i in neuves}) == 3

    merged = merge_pivot_profile(_pivot([]), _pivot(neuves))
    assert len(merged["interventions"]) == 3


def test_les_entrees_nosdeputes_deja_publiees_ne_se_dedoublent_pas():
    """Le piège de la migration : l'entrée DÉJÀ publiée n'a pas
    d'`intervention_id`, sa renormalisation en a un. Sans reprise, la fusion
    additive publierait les deux."""
    brut = _brut_nosdeputes(29173, 131, "78eecc9dc94da665e50bfcec91180051")
    neuve = _normalize_intervention(brut)
    ancienne = {k: v for k, v in neuve.items() if k != "intervention_id"}

    merged = merge_pivot_profile(_pivot([ancienne]), _pivot([neuve]))

    assert len(merged["interventions"]) == 1
    assert merged["interventions"][0]["intervention_id"] == 29173


def test_lentree_syceron_ecrasee_deja_publiee_est_remplacee_pas_dedoublee():
    """Les 8 entrées publiées portant l'URL d'archive (5 profils, mesuré au
    27/08/2026) sont les rescapées de l'effondrement. Renormalisées, elles
    reviennent identifiées parmi N — l'ancienne ne doit pas rester à côté."""
    brutes = [_brut_syceron(rang, f"Intervention {rang}.") for rang in range(1, 6)]
    neuves = [_normalize_intervention(i) for i in brutes]
    # Ce que la fusion d'avant #540 avait publié : la première, sans identifiant.
    ancienne = {k: v for k, v in neuves[0].items() if k != "intervention_id"}

    merged = merge_pivot_profile(_pivot([ancienne]), _pivot(neuves))

    assert len(merged["interventions"]) == 5
    assert all(i.get("intervention_id") for i in merged["interventions"])


# --- 3. Idempotence -------------------------------------------------------

def test_refusionner_un_profil_avec_lui_meme_najoute_rien():
    """Le piège de toute clé composite sur du texte tronqué. La clé retenue est
    une fonction de l'identifiant seul : elle est stable par construction."""
    brutes = [_brut_syceron(rang, "Même avis.") for rang in range(1, 21)]
    brutes += [_brut_nosdeputes(29173, 131, "78eecc9dc94da665e50bfcec91180051")]
    neuves = [_normalize_intervention(i) for i in brutes]

    une_fois = merge_pivot_profile(_pivot([]), _pivot(neuves))
    deux_fois = merge_pivot_profile(une_fois, _pivot(neuves))
    trois_fois = merge_pivot_profile(deux_fois, _pivot(deux_fois["interventions"]))

    assert len(une_fois["interventions"]) == 21
    assert len(deux_fois["interventions"]) == 21
    assert len(trois_fois["interventions"]) == 21


def test_la_reprise_des_entrees_anciennes_est_elle_meme_idempotente():
    """Appliquée deux fois, `clean_stale_interventions` rend le même résultat :
    au second passage il ne reste plus d'entrée sans identifiant à reprendre."""
    neuve = _normalize_intervention(_brut_syceron(1, "Avis défavorable."))
    ancienne = {k: v for k, v in neuve.items() if k != "intervention_id"}
    liste = [ancienne, neuve]
    assert clean_stale_interventions(liste) == [neuve]
    assert clean_stale_interventions(clean_stale_interventions(liste)) == [neuve]


# --- 4. Non-perte des entrées déjà publiées -------------------------------

def test_une_collecte_vide_ne_retire_aucune_entree_publiee():
    """La fusion reste additive : sans entrée neuve identifiée, rien n'est
    repris. Une archive indisponible ne doit pas vider le corpus publié."""
    publiees = [
        {"source_url": f"https://2017-2022.nosdeputes.fr/15/seance/{n}#inter_x{n}",
         "date": "2017-08-09", "sujet": "Questions au gouvernement", "texte": "..."}
        for n in range(1, 51)
    ]
    merged = merge_pivot_profile(_pivot(publiees), _pivot([]))
    assert len(merged["interventions"]) == 50


def test_une_entree_ancienne_sur_une_autre_source_nest_jamais_reprise():
    """La reprise est bornée à la `source_url` effectivement recollectée : une
    entrée publiée sur une législature non recollectée reste publiée."""
    neuve = _normalize_intervention(_brut_syceron(1, "Défavorable.", compte_rendu="CR16"))
    ancienne_autre_archive = {
        "source_url": ARCHIVE_17, "date": "2026-04-10",
        "sujet": "Motion de rejet préalable", "texte": "...",
    }
    merged = merge_pivot_profile(_pivot([ancienne_autre_archive]), _pivot([neuve]))
    assert len(merged["interventions"]) == 2


def test_une_entree_ancienne_sans_source_url_nest_jamais_reprise():
    """Une donnée absente reste absente (AGENTS.md §2) : sans `source_url`, une
    entrée ancienne n'est comparable à rien, donc elle est conservée."""
    neuve = _normalize_intervention(_brut_syceron(1, "Défavorable."))
    orpheline = {"source_url": None, "date": "2022-11-08", "sujet": "X", "texte": "Y"}
    merged = merge_pivot_profile(_pivot([orpheline]), _pivot([neuve]))
    assert len(merged["interventions"]) == 2


def test_clean_stale_interventions_sans_rien_didentifie_ne_touche_a_rien():
    liste = [
        {"source_url": "https://a.fr/1", "date": "2020-01-01"},
        {"source_url": "https://a.fr/2", "date": "2020-01-02"},
    ]
    assert clean_stale_interventions(liste) == liste
    assert clean_stale_interventions(None) == []


# --- 5. La propagation de l'identifiant, verbatim -------------------------

def test_normalize_propage_lid_brut_sans_le_reconstruire():
    """L'identifiant est repris tel quel, jamais fabriqué (AGENTS.md §2)."""
    syceron = _normalize_intervention(_brut_syceron(399, "..."))
    assert syceron["intervention_id"] == "syceron_CRSANR5L16S2023O1N055_000399"

    question = _normalize_intervention({
        "id": "question_QANR5L17QG817",
        "type_detail": "question",
        "url": "https://questions.assemblee-nationale.fr/q17/QANR5L17QG817.htm",
    })
    assert question["intervention_id"] == "question_QANR5L17QG817"

    nosdeputes = _normalize_intervention(_brut_nosdeputes(29173, 131, "abc"))
    assert nosdeputes["intervention_id"] == 29173


def test_une_intervention_brute_sans_id_reste_sans_identifiant():
    """Pas de `0` par défaut, pas d'identifiant inventé : la clé retombe sur la
    `source_url`, puis sur le contenu."""
    sans_id = _normalize_intervention({
        "date": "2020-01-01", "sujet": "S", "texte": "T",
        "url": "https://a.fr/1",
    })
    assert sans_id["intervention_id"] is None
    assert _pivot_intervention_key(sans_id) == ("source_url", "https://a.fr/1")

    sans_rien = _normalize_intervention({"date": "2020-01-01", "sujet": "S", "texte": "T"})
    assert sans_rien["intervention_id"] is None
    assert _pivot_intervention_key(sans_rien) == ("contenu", "2020-01-01", "S", "T")


def test_lidentite_pivot_est_celle_de_la_fusion_brute():
    """La garantie structurelle du correctif : une entrée brute et son pivot
    sont la même chose pour les deux étages de fusion. Sans cela, le pivot peut
    de nouveau publier autre chose que ce que la collecte a rendu."""
    from merge_profile import _intervention_key

    brutes = [_brut_syceron(rang, "Même avis.") for rang in range(1, 41)]
    brutes += [_brut_nosdeputes(29173, 131, "abc"), _brut_nosdeputes(86867, 480, "def")]
    pivots = [_normalize_intervention(i) for i in brutes]

    assert len({_intervention_key(i) for i in brutes}) == len(brutes)
    assert len({_pivot_intervention_key(i) for i in pivots}) == len(brutes)
