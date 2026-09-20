"""« Ce qu'il a dit » se range par qualité, et l'Europe perd ses périodes (#328).

Quatrième écart de la revue européenne du 13/09/2026 : la section rangeait
TOUTES les interventions par gouvernement français, y compris les européennes.
Mesuré — les **128 interventions** de Raphaël Glucksmann au Parlement européen
se répartissaient sur **quatre gouvernements français**, dont **une seule** sous
« gouvernement Attal ». Le cadre ne disait rien, et il le disait avec assurance
(§2 règle 2).

Forme décidée par la propriétaire le 13/09/2026, après maquette : un sélecteur
en pilules sous le titre — « En qualité de député(e) » · « … de membre du
gouvernement » · « … de député(e) européen(ne) » —, et **la sélection des
périodes disparaît dès que la qualité est européenne**.

Ce que ces tests verrouillent :

- **les trois qualités ne sont jamais devinées** : la fonction publiée par le
  compte rendu pour le gouvernement, le marqueur d'institution pour l'Europe ;
- **la qualité européenne ne se découpe pas en périodes.** C'est le cœur du
  correctif, et c'est ce qui règle le cas Glucksmann — qui n'a **qu'une** qualité,
  donc **aucun sélecteur** : un sélecteur seul n'aurait rien corrigé chez lui ;
- **le sélecteur ne s'affiche que si la fiche porte plusieurs qualités.** Mesuré
  sur les 17 fiches qui ont des interventions : 13 n'en ont qu'une, 4 en ont
  deux, **aucune n'en a trois** — les trois libellés ne coexisteront jamais ;
- **l'absence de périodes se DIT**, elle ne se contente pas de disparaître : un
  dispositif qui s'efface sans rien dire se lit comme une donnée manquante
  (§2 règle 5) ;
- **l'index de période est borné** quand on change de qualité : il vient d'une
  qualité qui pouvait avoir six périodes vers une qui n'en a qu'une.

CE QU'ILS NE COUVRENT PAS : aucun composant React n'est rendu ici. Vérifié hors
dépôt le 13/09/2026 — Glucksmann aucune pilule et aucune navigation ; Maurel
deux pilules (724 / 845), navigation présente, puis absente après le clic sur
« européen » ; Attal deux pilules (884 / 3 069) ; Guedj aucune pilule,
navigation intacte.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE = UI / "utils" / "parolesParPeriode.js"
COMPOSANT = UI / "components" / "ParolesParPeriode.jsx"
FEUILLE = UI / "components" / "ParolesParPeriode.css"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_les_trois_qualites_ne_sont_jamais_devinees():
    code = sans_commentaires(MODULE.read_text(encoding="utf-8"))
    bloc = re.search(r"export function qualiteDeParole\(intervention\) \{(.*?)\n\}", code, re.DOTALL)
    assert bloc, "qualiteDeParole a disparu ou changé de forme."
    assert "FONCTION_GOUVERNEMENTALE.test(fonction)" in bloc.group(1), (
        "La qualité gouvernementale doit venir de la fonction PUBLIÉE par le "
        "compte rendu, jamais d'une date ou d'une déduction."
    )
    assert "'parlement_europeen'" in bloc.group(1), (
        "La qualité européenne doit venir du marqueur d'institution (#328)."
    )


def test_la_qualite_europeenne_ne_se_decoupe_pas_en_periodes():
    """Le cœur du correctif : c'est lui qui règle le cas Glucksmann."""
    code = sans_commentaires(MODULE.read_text(encoding="utf-8"))
    bloc = re.search(r"export function parolesParQualite\((.*?)\n\}", code, re.DOTALL)
    assert bloc, "parolesParQualite a disparu ou changé de forme."
    assert "if (q !== QUALITE_PE)" in bloc.group(1), (
        "Sans cette branche, les interventions européennes repasseraient par "
        "`periodesDeParole` et se rangeraient sous des gouvernements français."
    )
    assert "sansDecoupage: true" in bloc.group(1), (
        "La vue reconnaît la qualité européenne à ce drapeau : sans lui, la "
        "sélection des périodes réapparaîtrait."
    )


def test_le_selecteur_ne_s_affiche_que_si_la_fiche_a_plusieurs_qualites():
    code = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    assert "qualites.length > 1 &&" in code, (
        "13 des 17 fiches n'ont qu'une qualité : leur montrer un sélecteur à "
        "une seule entrée serait un dispositif vide."
    )


def test_rien_ne_remplace_la_selection_des_periodes():
    """Arbitrage de la propriétaire, 13/09/2026 : le dispositif disparaît, et
    **rien ne prend sa place**.

    Un premier jet y mettait une phrase d'explication. Ce n'est pas une liste
    vide qu'il faudrait qualifier (§2 règle 5) : ce sont **toutes** les
    interventions, simplement sans découpage — la section ne cache rien, elle
    cesse d'annoncer un cadre qui n'existe pas.
    """
    code = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    assert "{!sansDecoupage && (" in code, (
        "Le rendu conditionnel a changé de forme : la navigation pourrait "
        "réapparaître sur une qualité européenne."
    )
    assert "pp-sans-periode" not in code, (
        "Une phrase de remplacement est revenue : la propriétaire l'a retirée."
    )
    assert "pp-sans-periode" not in FEUILLE.read_text(encoding="utf-8"), (
        "Le style survit à son usage."
    )


def test_l_index_de_periode_est_borne_quand_on_change_de_qualite():
    """Il vient d'une qualité qui pouvait avoir six périodes — Attal en a six
    comme député — vers une qui n'en a qu'une."""
    code = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    assert "Math.min(index ?? periodes.length - 1, periodes.length - 1)" in code, (
        "Sans bornage, `periodes[index]` sort du tableau au changement de "
        "qualité et la section casse."
    )
    assert "periodes[indexSur]" in code, "L'index borné n'est pas celui qui est lu."


def test_les_pilules_reprennent_le_vocabulaire_des_puces_d_institution():
    css = FEUILLE.read_text(encoding="utf-8")
    for classe in (".pp-qualite--an[aria-pressed='true']",
                   ".pp-qualite--gouv[aria-pressed='true']",
                   ".pp-qualite--pe[aria-pressed='true']"):
        assert classe in css, f"{classe} manque : une qualité n'aurait pas sa teinte."
    assert "var(--pe)" in css and "var(--parl)" in css and "var(--gouv)" in css, (
        "Les teintes doivent être celles de la frise, jamais un second jeu."
    )
