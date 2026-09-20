"""Le sigle du groupe européen se lit sur la source, il ne se fabrique pas (#863).

Les segments européens de la frise du parcours étaient muets, alors qu'ils
occupent jusqu'à 70 % de sa largeur : mesuré le 13/09/2026, Raphaël Glucksmann
n'avait aucune étiquette sur ses deux mandats, quand l'Assemblée, elle,
affichait « GDR » et « FI · opposition ». La donnée manquait, puis elle est
arrivée (#863 : `sigle_organe` + `type_organe_source` sur le mandat de groupe),
et le code ne la lisait pas.

Mesuré sur `origin/main` `87ddc9dde` : **6 candidats déclarés** portent un
mandat de groupe politique européen, **21 mandats, 21 avec sigle** — S&D,
GUE/NGL, The Left, Verts/ALE, ENF, EFDD, ITS, NI.

Ce que ces tests verrouillent, et pourquoi chacun a failli être faux :

- **le discriminant est `type_organe_source`, jamais la présence du champ.**
  Le SIÈGE européen porte lui aussi `sigle_organe`, où il vaut
  « 10e législature » : lire le sigle sur le siège écrirait « 10e législature »
  en travers du segment ;
- **le sigle publié n'est pas repassé par `FORME_DE_SIGLE`.** Ce garde-fou
  refuse la barre, l'espace, et plus de 8 signes : « GUE/NGL », « Verts/ALE » et
  « The Left » y échouent tous les trois. Il existe pour ne jamais FABRIQUER une
  abréviation à partir d'un nom complet, pas pour refuser celle que la source
  écrit — d'où `r.sigle ?? sigleDuSiege(...)` dans `avecSiglesDeSiege` ;
- **un siège européen croise souvent plusieurs groupes** — Emmanuel Maurel passe
  de S&D à NI puis à GUE/NGL sur la seule législature 2014-2019 —, et c'est
  celui où il a passé le plus de temps qui est retenu, jamais le premier venu ;
- **le Sénat reste muet** : aucune source ne publie son sigle, et l'arbitrage du
  11/09/2026 dit qu'un segment sans sigle se tait plutôt que de répéter la
  légende.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Le rendu a été vérifié hors dépôt le 13/09/2026 sur le serveur de développement —
Glucksmann « S&D » deux fois, Maurel « S&D » puis « The Left », Mélenchon
« GUE/NGL » deux fois et son segment Sénat muet, l'Assemblée inchangée.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "profilCandidat.js"
ADAPTATEUR = UI / "data" / "index.js"

TYPE = "groupe_politique_europeen"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_le_groupe_europeen_est_reconnu_par_son_type_d_organe():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert f"TYPE_GROUPE_EUROPEEN = '{TYPE}'" in code, (
        "Le type d'organe est le seul discriminant fiable : le siège européen "
        "porte lui aussi `sigle_organe`, où il vaut « 10e législature »."
    )
    assert "m.type_organe_source === TYPE_GROUPE_EUROPEEN" in code, (
        "Le filtre ne teste plus le type d'organe — un sigle de législature "
        "pourrait s'écrire en travers d'un segment (#863)."
    )


def test_le_sigle_vient_du_champ_publie_et_n_est_pas_derive_de_l_intitule():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    bloc = re.search(r"function periodesDeGroupeEuropeen\(mandats\) \{(.*?)\n\}", code, re.DOTALL)
    assert bloc, "periodesDeGroupeEuropeen a disparu ou changé de forme."
    assert "sigle: m.sigle_organe" in bloc.group(1), (
        "Le sigle doit venir de `sigle_organe`, que la source publie. "
        "Le dériver de l'intitulé serait le fabriquer."
    )
    assert "sigleDeGroupePolitique" not in bloc.group(1), (
        "L'extraction entre parenthèses est la règle de l'Assemblée ; le "
        "Parlement européen publie son sigle et n'en a pas besoin."
    )


def test_un_sigle_deja_pose_n_est_pas_repasse_par_la_forme_de_sigle():
    """Le test le plus important : sans lui, trois sigles sur huit disparaissent.

    « GUE/NGL » et « Verts/ALE » portent une barre, « The Left » une espace, et
    `FORME_DE_SIGLE` (`^[\\p{L}&-]{1,8}$`) les refuse tous les trois.
    """
    code = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    assert "sigle: r.sigle ?? sigleDuSiege(" in code, (
        "`avecSiglesDeSiege` recalcule le sigle sans regarder s'il est déjà "
        "posé : les sigles européens que la source publie seraient perdus, et "
        "les segments redeviendraient muets (#863)."
    )


def test_le_groupe_retenu_est_le_plus_long_du_siege():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    bloc = re.search(r"function groupeEuropeenDuSiege\(siege, periodes\) \{(.*?)\n\}", code, re.DOTALL)
    assert bloc, "groupeEuropeenDuSiege a disparu ou changé de forme."
    assert "reduce" in bloc.group(1) and "jours(p) > jours(meilleure)" in bloc.group(1), (
        "Le groupe retenu n'est plus le plus long : sur la législature "
        "2014-2019, Emmanuel Maurel passe de S&D à NI puis à GUE/NGL, et "
        "prendre le premier venu donnerait un sigle exact mais arbitraire."
    )


def test_le_segment_porte_le_sigle_et_la_liste_datee_le_nom_complet():
    """« La frise donne la silhouette, la liste la nomme » — demandé le 13/09/2026.

    Un sigle seul ne dit rien de ce qu'est S&D à qui ne le connaît pas déjà ;
    le nom complet ne tient pas dans un segment. Les deux coexistent donc, et
    `detail` — que la liste datée rend — porte le nom.
    """
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    bloc = re.search(r"function periodesDeGroupeEuropeen\(mandats\) \{(.*?)\n\}", code, re.DOTALL)
    assert "nom: m.label" in bloc.group(1), (
        "Le nom complet du groupe n'est plus repris de la source : la liste "
        "datée retomberait sur le sigle, qu'elle répéterait après la frise."
    )
    assert "detail: groupePE?.nom ?? groupePE?.sigle" in code, (
        "La liste datée doit recevoir le NOM, le segment le SIGLE. Inverser "
        "les deux ferait déborder le segment et rendrait la liste muette."
    )


def test_seul_un_siege_europeen_lit_un_groupe_europeen():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "siege.chambre === 'PE' ? groupeEuropeenDuSiege(" in code, (
        "La lecture doit être bornée à la chambre PE : un siège de l'Assemblée "
        "ou du Sénat n'a pas de groupe européen, et le Sénat doit rester muet."
    )
