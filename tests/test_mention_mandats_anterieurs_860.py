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
- elle a sa place dans la liste de « Ce qui manque sur cette fiche » — après
  les lignes d'activité, avant ce que la collecte signale — et elle **fait
  taire « Avant juin 2002 »**. Jusqu'au 01/10/2026 elle était rangée dans une
  carte « Ce que le corpus ne dit pas de son parcours » ; la section est
  devenue une seule liste, et ce qui se garde est son rang, plus sa carte ;
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


def test_la_limite_porte_son_intitule_et_fait_taire_la_ligne_de_borne():
    """L'intitulé voyage avec la limite, et la borne ne la contredit pas.

    LA RÈGLE A CHANGÉ LE 01/10/2026. L'intitulé vivait dans une table du
    composant (`LIBELLE_LIMITE`) et la limite dans un ensemble
    (`LIMITES_DU_PARCOURS`) qui la rangeait sous la carte « Ce que le corpus ne
    dit pas de son parcours ». La section 6 est devenue UNE liste : chaque limite
    porte son `titre`, et son rang est posé par `manquesDeLaFiche`.

    Ce qui se garde de l'arbitrage de #860 : c'est une ligne de « ce qu'on n'a
    pas pu lire », sous son intitulé. Ce qui s'y ajoute : la dernière ligne de
    la liste, « Avant juin 2002 — Nos sources ne connaissent aucun mandat avant
    le 19 juin 2002 », NE PARAÎT PAS sur une fiche qui cite des mandats
    antérieurs — les deux lignes se contrediraient.
    """
    regles = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    bloc = regles[regles.index(f"cle: '{CLE}'") :]
    bloc = bloc[: bloc.index("});")]
    assert "titre: 'Mandats antérieurs'" in bloc, (
        "Sans son intitulé, la ligne sortirait sans colonne de gauche."
    )
    rangs = re.search(r"RANG_DES_AUTRES_LIMITES\s*=\s*\[(.*?)\]", regles, re.DOTALL)
    assert rangs and f"'{CLE}'" in rangs.group(1), (
        "La limite a perdu son rang dans la liste : elle se mêlerait aux "
        "signalements de collecte, qui parlent des sources rencontrées."
    )
    liste = regles[regles.index("export function manquesDeLaFiche") :]
    assert f"!limites.some((l) => l.cle === '{CLE}')" in liste, (
        "« Avant juin 2002 » reparaîtrait sous une ligne qui cite des mandats "
        "d'avant 2002."
    )
    composant = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    assert "LIBELLE_LIMITE" not in composant and "LIMITES_DU_PARCOURS" not in composant, (
        "Une seconde table d'intitulés est revenue dans le composant : elle "
        "divergera de celle que la limite porte."
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
