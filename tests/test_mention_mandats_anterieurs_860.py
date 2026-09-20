"""La fiche candidat mentionne les mandats antérieurs, et ne fait que ça (#860).

Arbitrage de la propriétaire, 12/09/2026 : **une mention dans « ce qu'on n'a pas
pu lire », et rien d'autre**. Trois formes avaient été maquettées — la frise
étendue jusqu'au premier mandat, un liseré d'amont hors échelle, une liste sous
la figure ; toutes les trois sont écartées.

La raison tient en une ligne, et c'est elle que ces tests protègent : un mandat
antérieur est un **fait cité**, relu à la main sur Sycomore ou sur un décret au
Journal officiel, et **aucune activité n'est collectée derrière** — ni vote, ni
amendement, ni intervention. Le poser sur la frise du parcours ferait lire
« couvert depuis 1988 » là où rien ne l'est (§2 règle 2).

Ce que ces tests verrouillent :

- la limite existe, sous la clé `mandats-anterieurs`, et porte son intitulé ;
- elle est rangée dans les limites **du parcours** — c'est ce que le corpus ne
  dit pas de cette personne, pas ce que la collecte a rencontré ;
- **le champ n'est lu nulle part ailleurs dans la fiche** : c'est le test le
  plus important du fichier, celui qui tient l'arbitrage. Une session suivante
  qui rebranche `mandats_anterieurs` sur la frise le fera rougir ;
- une fiche **non relue** (`null` + `non_relu`) ne produit aucune ligne : dire
  que la relecture n'a pas eu lieu parlerait de notre travail, pas de cette
  personne.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici —
le dépôt n'a pas de harnais JS. Le rendu réel a été vérifié hors dépôt le
12/09/2026, sur le serveur de développement, pour les trois cas :

  segolene-royal      « 7 mandats exercés avant le 19 juin 2002 — 3 à
                        l'Assemblée, 4 au gouvernement — sont cités depuis leur
                        source primaire. Aucune activité n'y est collectée. »
  jean-luc-melenchon  « 1 mandat exercé avant le 19 juin 2002 est cité depuis sa
                        source primaire. Aucune activité n'y est collectée. »
  marine-tondelier    aucune ligne.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "profilCandidat.js"
COMPOSANT = UI / "components" / "CandidateProfile.jsx"

CLE = "mandats-anterieurs"
CHAMP = "mandats_anterieurs"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …` (une URL est épargnée)."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_la_limite_est_declaree_avec_sa_cle():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert f"cle: '{CLE}'" in code, (
        "La limite des mandats antérieurs a disparu de `limitesDeclarees` : "
        "la fiche ne dirait plus qu'une carrière commence avant le corpus (#860)."
    )
    assert f"profil?.{CHAMP}" in code, (
        "La limite ne lit plus le champ du pivot — elle ne peut donc rien compter."
    )


def test_la_limite_porte_son_intitule_et_reste_dans_le_parcours():
    code = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    assert f"'{CLE}': 'Mandats antérieurs'" in code, (
        "Sans entrée dans LIBELLE_LIMITE, la ligne s'intitulerait « Corpus »."
    )
    bloc = re.search(r"LIMITES_DU_PARCOURS\s*=\s*new Set\(\[(.*?)\]\)", code, re.DOTALL)
    assert bloc, "LIMITES_DU_PARCOURS introuvable."
    assert f"'{CLE}'" in bloc.group(1), (
        "La limite a quitté les limites DU PARCOURS : elle se rangerait sous "
        "« ce que la collecte signale », qui parle des sources rencontrées, pas "
        "de ce que le corpus ignore de cette personne."
    )


def test_le_champ_n_est_lu_nulle_part_ailleurs_dans_la_fiche():
    """Le test qui tient l'arbitrage : une mention, et rien d'autre.

    Trois formes ont été écartées le 12/09/2026 — frise étendue, liseré d'amont,
    liste sous la figure. Les rebrancher demanderait de lire le champ ailleurs ;
    ce test le refuse, et c'est le seul endroit du dépôt où cette décision est
    écrite dans du code exécutable.
    """
    autorises = {
        MODULE_REGLES,               # la limite elle-même
        UI / "data" / "sources.config.js",  # la déclaration des sources (#860)
    }
    fautifs = {}
    for chemin in sorted(UI.rglob("*.js")) + sorted(UI.rglob("*.jsx")):
        if chemin in autorises:
            continue
        code = sans_commentaires(chemin.read_text(encoding="utf-8"))
        if CHAMP in code:
            fautifs[chemin.relative_to(UI)] = [
                l.strip() for l in code.splitlines() if CHAMP in l
            ][:3]
    assert not fautifs, (
        "`mandats_anterieurs` est lu hors de la mention : "
        f"{ {str(k): v for k, v in fautifs.items()} }. "
        "Un mandat antérieur est un fait cité — aucune activité n'est collectée "
        "derrière lui —, et l'afficher ailleurs (frise, compteur, section) ferait "
        "lire une couverture qui n'existe pas (#860, §2 règle 2)."
    )


def test_une_fiche_non_relue_ne_produit_aucune_ligne():
    """`null` + `non_relu` ne doit pas produire de limite.

    La garde `if (anterieurs.length)` s'en charge : `null || []` donne une liste
    vide, donc aucune ligne — 27 des 32 fiches de candidats déclarés au
    12/09/2026.
    """
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    bloc = re.search(
        r"const anterieurs = profil\?\.mandats_anterieurs \|\| \[\];(.*?)\n\n",
        code,
        re.DOTALL,
    )
    assert bloc, "Le bloc de la limite a changé de forme — relire le test."
    assert "if (anterieurs.length)" in bloc.group(1), (
        "Sans la garde sur la longueur, une fiche non relue afficherait une "
        "ligne qui parle de notre relecture, pas de cette personne."
    )
    assert "non_relu" not in bloc.group(1), (
        "La limite ne doit rien dire du motif `non_relu` : l'absence de "
        "relecture n'est pas un fait sur la personne affichée."
    )


def test_la_phrase_dit_qu_aucune_activite_n_est_collectee():
    """La moitié qui compte : sans elle, la ligne se lit comme une couverture."""
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "Aucune activité n’y est collectée." in code, (
        "La phrase a perdu ce qui la rend honnête : un mandat cité sans cette "
        "mention se lit comme un mandat couvert (§2 règle 5)."
    )
    assert "source primaire" in code, (
        "La ligne ne dit plus d'où vient le fait — §2 règle 2 exige la traçabilité."
    )
