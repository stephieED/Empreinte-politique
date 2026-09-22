"""La recherche sur la fiche de gouvernement (#979).

Le troisième et dernier temps 1 de #979, après la fiche candidat (#993) et la
fiche de groupe (#995), et sur la même mécanique :

1. **« En bref » et « Qui le composait » se retirent** sous un mot — ni chiffres
   ni personnes ne portent d'intitulé ; **« Ce qu'on n'a pas pu lire » ne change
   pas**, comme sur la fiche de groupe.
2. **Les deux sections d'intitulés se recalculent** (`filtrerGouvernement`) :
   les débats par leur intitulé, les textes par leur titre. La figure des
   matières et des sorts est dessinée à partir de la liste des textes : filtrée,
   elle suit d'elle-même.
3. **Rien ne se recharge.** La fiche a déjà téléchargé la liste ENTIÈRE des
   débats (`paroles.tous`, 1 738 sur la fiche Borne au 20/09/2026) ; la section
   n'en affiche que les dix plus portés. C'est la différence avec la lignée,
   dont la projection ne transporte que les dix et à qui #995 a dû ajouter un
   fichier (`filtreLignee`).
4. **Le pied ne ment pas sous un mot** : « N sur M débats » deviendrait « N sur
   N », puisque M serait le nombre de débats qui portent le mot.
5. **La barre est celle du tiroir** (#1025/#1026) : la fiche de gouvernement
   rejoint les fiches qui lisent `?mot=`.

FIXTURES. Entrées copiées de `public/data/gouvernements/gouvernement-BORNE.json`
au 20/09/2026, réduites aux champs que le filtre lit.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu. Le
rendu — sections retirées, deux étiquettes, liste des textes dépliée, champ du
tiroir rempli — a été vérifié hors dépôt sur le serveur de développement, sur
la fiche Borne sans mot, avec « santé » (34 débats, 3 textes) et avec un mot
absent.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
REGLES = SRC / "utils" / "filtreGouvernement.js"
GOUVERNEMENT = SRC / "utils" / "gouvernement.js"
FICHE = SRC / "components" / "GovernmentProfile.jsx"
PAGE = SRC / "pages" / "GovernmentProfilePage.jsx"
TIROIR = SRC / "components" / "ExplorerLayout.jsx"

# Copiés de la fiche du gouvernement Borne (20/09/2026).
DEBATS = [
    {"tag": "réintégration du personnel des établissements de santé non vacciné", "nb_membres_porteurs": 3},
    {"tag": "adaptation au droit de l’union européenne dans les domaines de l’économie, de la santé, du travail, des transports et de l’agriculture", "nb_membres_porteurs": 2},
    {"tag": "motion de censure", "nb_membres_porteurs": 19},
]
TEXTES = [
    {
        "dossierId": "DLR5L16N48973",
        "titre": "Projet de loi ratifiant l’ordonnance n° 2023-285 du 19 avril 2023 portant extension et adaptation à la Polynésie française, à la Nouvelle-Calédonie et aux îles Wallis et Futuna de diverses dispositions législatives relatives à la santé",
        "statut": "promulgue",
        "commission": "Affaires sociales",
    },
    {
        "dossierId": "DLR5L16N49124",
        "titre": "Projet de loi relatif à l’organisation de la gouvernance de la sûreté nucléaire et de la radioprotection pour répondre au défi de la relance de la filière nucléaire",
        "statut": "adopte_cmp",
        "commission": None,
    },
]
COMPTAGES = {"membres_recenses": 55, "membres_distincts": 55, "membres_avec_interventions": 50}


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


CRITERES = ("dont l’intitulé contient", "dont le sujet ou le propos contient")


def _message_present(message: str, source: str) -> bool:
    """Une phrase vide s'écrit d'un seul tenant, ou en deux temps depuis #1074."""
    if message in source:
        return True
    for critere in CRITERES:
        if message.endswith(critere):
            quoi = message[: -len(critere)].strip()
            if f'{quoi}<Condition critere="{critere}"' in source:
                return True
            if f'critere="{critere}" quoi="{quoi}"' in source:
                return True
    return False


def _lire(chemin: Path) -> str:
    return _sans_commentaires(chemin.read_text(encoding="utf-8", errors="replace"))


def _executer(script: str, module: Path = REGLES, nom: str = "f") -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const {nom} = await import({json.dumps(module.as_uri())});\n"
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


def _vue(limite: int = 10) -> str:
    """La vue telle que l'adaptateur la construit, sur les fixtures."""
    return (
        f"const g = await import({json.dumps(GOUVERNEMENT.as_uri())});\n"
        f"const vue = {{ paroles: g.sujetsDeParole({json.dumps(DEBATS)}, {json.dumps(COMPTAGES)}, {limite}),"
        f" textes: {json.dumps(TEXTES)} }};\n"
    )


# ---------------------------------------------------------------------------
# 1. La vue porte la liste entière des débats, la section n'en montre que dix


def test_la_vue_porte_tous_les_debats_et_n_en_affiche_que_dix():
    rendu = _executer(
        _vue(limite=2)
        + "console.log(JSON.stringify({ liste: vue.paroles.liste.length, tous: vue.paroles.tous.length, total: vue.paroles.total }));"
    )
    assert rendu == {"liste": 2, "tous": 3, "total": 3}
    assert "limite = 10" in _lire(GOUVERNEMENT), "la section affiche dix débats"


# ---------------------------------------------------------------------------
# 2. Le filtre


def test_sans_mot_la_fiche_est_rendue_telle_quelle():
    rendu = _executer(_vue() + "console.log(JSON.stringify(f.filtrerGouvernement(vue, '  ') === vue));")
    assert rendu is True


def test_sante_retient_les_debats_et_les_textes_qui_le_portent():
    rendu = _executer(
        _vue()
        + "const r = f.filtrerGouvernement(vue, 'SANTE');"
        + "console.log(JSON.stringify({ debats: r.paroles.liste.map((s) => s.porteurs), total: r.paroles.total,"
        + " tous: r.paroles.tous.length, denominateur: r.paroles.denominateur, membres: r.paroles.membres,"
        + " textes: r.textes.map((t) => t.dossierId) }));"
    )
    assert rendu["debats"] == [3, 2]
    # Le total suit la liste retenue : « N sur N » ne se publie pas.
    assert rendu["total"] == 2 and rendu["tous"] == 2
    # Les effectifs de membres ne sont pas des intitulés : ils ne bougent pas.
    assert (rendu["denominateur"], rendu["membres"]) == (50, 55)
    assert rendu["textes"] == ["DLR5L16N48973"]


def test_un_mot_absent_vide_les_deux_sections():
    rendu = _executer(
        _vue()
        + "const r = f.filtrerGouvernement(vue, 'zzqx');"
        + "console.log(JSON.stringify([r.paroles.liste.length, r.textes.length]));"
    )
    assert rendu == [0, 0]


# ---------------------------------------------------------------------------
# 3. La fiche sous un mot


def test_deux_sections_se_retirent_la_couverture_reste():
    source = _lire(FICHE)
    # #1074 : elles se retirent sous un filtre actif — un mot OU une période.
    assert "{!actif && <EnBref" in source
    assert "{!actif && <QuiLeComposait" in source
    ligne = [l for l in source.splitlines() if "<CeQuOnNaPasPuLire" in l][0]
    assert ligne.strip() == "<CeQuOnNaPasPuLire government={government} />"


def test_chaque_figure_porte_le_mot():
    # #1074 : l'étiquette se tait d'elle-même sans mot ni période.
    assert _lire(FICHE).count("<EtiquetteFiltre mot={mot} />") == 2


@pytest.mark.parametrize(
    "message",
    [
        "Aucun débat dont l’intitulé contient",
        "Aucun texte déposé dont l’intitulé contient",
    ],
)
def test_un_mot_sans_resultat_a_son_message(message):
    # #1074 : la phrase se compose désormais en deux temps — le nom de la liste,
    # puis `Condition`, qui dit le mot, la période ou les deux. Sous une période
    # seule, « dont l'intitulé contient « » » aurait été faux.
    assert _message_present(message, _lire(FICHE)), message


def test_la_liste_des_textes_se_deplie_et_le_pied_ne_ment_pas():
    source = _lire(FICHE)
    # #1074 : sous un filtre actif, mot ou période.
    assert ": actif ? textes : [];" in source, "les textes retenus s'affichent sans clic dans la figure"
    assert "débat${liste.length > 1 ? 's' : ''} · membres qui y sont intervenus" in source


def test_la_page_lit_le_mot_et_le_tiroir_porte_le_champ():
    page = _lire(PAGE)
    assert "filtrerGouvernement(government, motDiffere, extraits, periode)" in page
    assert "useDeferredValue(params.get('mot') ?? '')" in page
    assert "const FICHES_FILTRABLES = ['/candidats', '/groupes', '/gouvernements'];" in _lire(TIROIR)
