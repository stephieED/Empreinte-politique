"""« Les fonctions exercées » portent la teinte de leur chambre (#328).

Défaut repéré par la propriétaire le 13/09/2026, sur la fiche de Raphaël
Glucksmann : le titre du bloc « Commissions » s'affichait en mauve — la teinte
de l'Assemblée — alors que toutes ses commissions sont européennes.

La cause : `CATEGORIES_FONCTIONS` écrivait `banc: INSTITUTION_PARLEMENT` **en
dur** pour les sept catégories parlementaires, sans jamais consulter la chambre,
et le CSS ne connaissait que trois blocs — ni `--pe`, ni `--senat`. C'est
exactement le défaut que #328 avait corrigé sur la frise, « l'institution dit le
banc, la chambre voyage à côté », et que cette section n'avait pas suivi.

Mesuré sur les 21 fiches qui ont des fonctions : **4** les ont toutes
européennes (Glucksmann, Philippot, Bardella, Massard) et **3** mélangent les
deux chambres dans leur bloc « Commissions » (Maurel, Mélenchon, Le Pen).

Ce que ces tests verrouillent :

- **la chambre fait la teinte**, et les deux classes manquantes existent ;
- **un bloc parlementaire se scinde par chambre**, parce qu'une seule teinte ne
  peut pas dire les deux — et parce que le titre annonçait « 13 intitulés » sans
  dire combien étaient européens, un dénominateur qui agrège deux institutions
  (§2 règle 7) ;
- **la chambre n'est nommée que si la fiche en a plusieurs** : sur une fiche qui
  n'a connu qu'un banc, la teinte suffit et le préciser ferait un refrain ;
- **une fonction gouvernementale ne se scinde pas** : un portefeuille n'a pas de
  chambre, et lui en inventer une serait faux.

UN DÉFAUT CORRIGÉ AU PASSAGE, et c'est le plus intéressant : « Commission des
affaires étrangères » existe **à l'Assemblée et au Parlement européen**. Les deux
étaient regroupées sous un seul intitulé, avec leurs durées cumulées comme s'il
s'agissait du même organe — sur `emmanuel-maurel` et `jean-luc-melenchon`, les
deux seules fiches concernées. Scinder par chambre les sépare.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Vérifié hors dépôt le 13/09/2026 — Glucksmann « Commissions · 19 intitulés » en
`rgb(0, 51, 153)` ; Maurel scindé en « Commissions · Assemblée nationale ·
5 intitulés » (mauve) et « Commissions · Parlement européen · 9 intitulés »
(bleu) ; Guedj et Philippe inchangés.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "profilCandidat.js"
FEUILLE = UI / "components" / "CandidateProfile.css"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_les_deux_teintes_manquantes_existent():
    css = FEUILLE.read_text(encoding="utf-8")
    assert ".cp-fonctions-bloc--pe {" in css, (
        "Sans cette classe, une commission européenne retombe sur la teinte de "
        "l'Assemblée — le défaut d'origine."
    )
    assert "--teinte-banc: var(--pe);" in css, (
        "La teinte doit être celle de la frise, jamais un second jeu de valeurs."
    )
    assert ".cp-fonctions-bloc--pe .cp-fonctions-titre" in css, (
        "Le titre ne prendrait pas la teinte : seule la pastille changerait."
    )


def test_un_bloc_parlementaire_se_scinde_par_chambre():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "const chambreDOrgane = (m) => {" in code, (
        "La chambre d'un organe n'est plus dérivée : le banc redeviendrait "
        "écrit en dur."
    )
    assert "m.categorie_source === 'europarl'" in code and "m.categorie_source === 'senat'" in code, (
        "`categorie_source` est le discriminant — les organes ne portent pas "
        "tous une `chambre` —, et il y a TROIS chambres depuis que le Sénat "
        "est collecté (#885). La première version n'en connaissait que deux : "
        "les 26 commissions sénatoriales de Bruno Retailleau retombaient sur "
        "l'Assemblée, teinte et compte compris."
    )
    assert "return INSTITUTION_SENAT" in code, (
        "Le Sénat n'a plus de banc à lui : ses organes seraient comptés avec "
        "ceux de l'Assemblée."
    )
    assert "CATEGORIES_FONCTIONS.flatMap(" in code, (
        "Sans `flatMap`, une catégorie ne peut plus produire deux blocs."
    )


def test_une_fonction_gouvernementale_ne_se_scinde_pas():
    """Un portefeuille ministériel n'a pas de chambre."""
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "banc === INSTITUTION_PARLEMENT" in code, (
        "La scission doit être bornée aux fonctions parlementaires : inventer "
        "une chambre à un portefeuille serait faux."
    )


def test_la_chambre_n_est_nommee_que_si_la_fiche_en_a_plusieurs():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "const nommerLaChambre = chambres.length > 1;" in code, (
        "Sur une fiche qui n'a connu qu'un banc, préciser la chambre à chaque "
        "bloc ferait un refrain — la teinte suffit, et elle est juste."
    )
    assert "nommerLaChambre && chambre ? `${titre} · ${NOM_DE_CHAMBRE[chambre]}`" in code, (
        "Le titre ne porte plus la chambre : les deux blocs « Commissions » "
        "d'une fiche mixte seraient indistinguables autrement que par leur teinte."
    )


def test_la_cle_du_bloc_porte_la_chambre():
    """Sans elle, React monterait deux blocs sous la même clé."""
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "cle: [cle, suffixe, chambre].filter(Boolean).join('_')" in code, (
        "Deux blocs « Commissions » d'une même fiche partageraient leur clé."
    )
