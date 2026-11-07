"""Le versant européen de la fiche candidat (#1446, première partie).

Défauts vérifiés le 06/11/2026 sur le site en ligne (#1452), et ce qui les tient :

1. un vote européen se range sous chacun de ses thèmes dans la figure ; la liste
   le montrait autant de fois (Glucksmann : « 5 972 textes » pour 1 829, colonne
   « Contre 294 » sous la pastille « Contre 96 ») — elle garde une ligne par
   texte ;
2. sous un mot, un dossier européen amendé était listé une fois par thème (la
   même résolution six fois) — la liste le garde une fois, par sa référence ;
3. une intervention européenne était marquée « Source · Assemblée nationale » —
   le libellé suit l'adresse ;
4. la carte européenne des prises de parole s'intitulait « Repère non publié »,
   ou « Toutes les périodes · 1 périodes » — elle porte le titre de la carte
   européenne des votes, « Au Parlement européen » ;
5. la ligne d'un vote européen finissait par « · » (`v.meta`, jamais fourni).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
VOTES = SRC / "components" / "VotesParPeriode.jsx"
FICHE = SRC / "components" / "CandidateProfile.jsx"
PAROLES = SRC / "components" / "ParolesParPeriode.jsx"
REGLES_PAROLES = SRC / "utils" / "parolesParPeriode.js"


def _lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def test_la_liste_des_votes_garde_une_ligne_par_texte():
    source = _lire(VOTES)
    debut = source.index("const visibles = useMemo(")
    bloc = source[debut:source.index("}, [periode, garde, matiere]);", debut)]
    assert "vus.has(v.scrutinId)" in bloc and "vus.add(v.scrutinId)" in bloc


def test_la_ligne_d_un_vote_europeen_ne_finit_pas_par_un_separateur():
    assert "v.meta" not in _lire(VOTES)


def test_un_dossier_europeen_amende_se_liste_une_fois():
    source = _lire(FICHE)
    debut = source.index("const dossiersDeLaMatiere = matiere || mot")
    assert "split('§')[0]" in source[debut:debut + 1200]


def _source_de(url: str) -> bool:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    source = _lire(PAROLES)
    debut = source.index("{/(^|\\.)europarl")
    motif = source[debut + 1:source.index(".test(", debut)]
    script = (f"const u = {json.dumps(url)};\n"
              f"console.log(JSON.stringify({motif}.test(String(u).replace(/^https?:\\/\\//, ''))));")
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_la_source_d_une_intervention_suit_son_adresse():
    assert "'Source · Parlement européen'" in _lire(PAROLES)
    # Adresses relevées sur la fiche de Raphaël Glucksmann et d'un député.
    assert _source_de("https://www.europarl.europa.eu/doceo/document/CRE-10-2024-07-17-ITM-005_FR.html") is True
    assert _source_de("https://www.assemblee-nationale.fr/dyn/17/comptes-rendus/seance/x") is False


def test_la_carte_europeenne_des_paroles_porte_le_titre_des_votes():
    regles = _lire(REGLES_PAROLES)
    debut = regles.index("cle: 'pe',")
    assert "libelle: 'Au Parlement européen'" in regles[debut:debut + 400]
    paroles = _lire(PAROLES)
    assert "laPeriode.libelle ?? titreDePeriode(laPeriode)" in paroles
    assert "tout && periodes.length > 1 ?" in paroles


def test_les_interventions_europeennes_sans_date_sont_montrees():
    """Choix de la propriétaire, 06/11/2026 : côté européen (une seule période,
    sans découpage), une intervention sans date suit les datées, avec la
    mention « date non publiée ». Philippot : 903 sur 1 587 manquaient."""
    regles = _lire(REGLES_PAROLES)
    assert "interventions: [...datees, ...sansDate]" in regles
    assert "'date non publiée'" in _lire(PAROLES)
    adaptateur = _lire(SRC / "data" / "pivotAdapter.js")
    assert "qualiteDeParole(parolesUniques[k]) !== QUALITE_PE" in adaptateur, (
        "la limite « hors du découpage » ne compte plus que l'Assemblée"
    )
