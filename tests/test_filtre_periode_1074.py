"""Le filtre de période sur les fiches (#1074).

Deux cases, « 6 derniers mois » et « 12 derniers mois », arbitrées le
22/09/2026 : **des durées fixes, jamais une fenêtre libre** — deux dates libres
sont l'outil idéal pour découper la période qui fait dire ce qu'on veut aux
chiffres. De vraies cases à cocher, choisies sur maquette, mais **exclusives**.

Premier usage : le rapport « prix des carburants, ces six derniers mois » de
#1029, qui doit illustrer ce que l'outil permet avec des chiffres **que le
lecteur retrouve à l'écran**. D'où le principe : la période passe par les mêmes
adaptateurs que la fiche, comme le mot (#979). Un calcul fait à côté, dans les
données, trouvait 10 interventions de ministres là où la fiche Lecornu II en
affiche 49 sur le même débat — mesuré le 22/09/2026.

Ce que ces garde-fous protègent :

1. **Le calcul de la fenêtre**, y compris le piège du calendrier : six mois
   avant le 31 août est le 28 février, pas le 3 mars — `Date.UTC` déborde en
   silence.
2. **Le filtrage, sur des entrées copiées du corpus** : un élément sans date ne
   passe pas une fenêtre active (§2 règle 5), un texte porté y est s'il y a été
   actif.
3. **Une seule date de référence** : les cases se comptent depuis la même date
   que les fenêtres de Backend (#1077), la `date_reference` des fiches de groupe
   — sinon deux fiches diraient « depuis le » à deux dates différentes.
4. **Le compte du gouvernement est exact** : le détail de sa parole porte la date
   de chaque séance. Avec la seule première et dernière date, 26 couples membre
   × débat sur 1 427 chez Lecornu II ne disaient pas combien de tours tombaient
   dans six mois.
5. **Des cases seulement là où elles filtrent** : les fiches qui datent ce
   qu'elles montrent — la fiche de groupe depuis que #1077 lui a donné ses
   fenêtres de parole.
7. **La fiche de groupe lit les fenêtres de Backend** : un nombre de membres
   distincts par débat et par fenêtre, sur le dénominateur de la fenêtre ; ses
   amendements, comptés par dossier sur toute la législature, se retirent
   plutôt que de rester faux sous la période.
6. **Les vides disent la période** : « Aucun texte porté depuis le 21/03/2026 »,
   jamais un vide de collecte.

CE QU'ILS NE COUVRENT PAS : aucun composant React n'est rendu ici. Le rendu a été
vérifié dans l'application le 22/09/2026 — période seule, mot et période, sur
les trois types de fiche, et fiche sans filtre intacte —, sans erreur console.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
WEB = RACINE / "web" / "UI_finale"
SRC = WEB / "src"
PERIODE = SRC / "utils" / "filtrePeriode.js"
RECHERCHE = SRC / "components" / "Recherche.jsx"
TIROIR = SRC / "components" / "ExplorerLayout.jsx"
FICHE = SRC / "components" / "CandidateProfile.jsx"
FICHE_GOUV = SRC / "components" / "GovernmentProfile.jsx"
CHARGEUR = SRC / "data" / "index.js"
SYNC = WEB / "scripts" / "sync-data.mjs"
PAROLE_GOUV = WEB / "scripts" / "vue-parole-gouvernement.mjs"
VUE_LIGNEE = WEB / "scripts" / "vue-lignee.mjs"
FILTRE_LIGNEE = SRC / "utils" / "filtreLignee.js"
FICHE_LIGNEE = SRC / "components" / "LigneeProfile.jsx"

# Copiés du profil de Philippe Brun (pivot_data, 22/09/2026).
QAG_MAI = {"intervention_id": "syceron_CRSANR5L17S2026O1N220_000027", "date": "2026-05-05",
           "type_detail": "question_gouvernement"}
QAG_MARS = {"intervention_id": "syceron_CRSANR5L17S2026O1N177_000032", "date": "2026-03-24",
            "type_detail": "question_gouvernement"}
DEBAT_FEVRIER = {"intervention_id": "syceron_CRSANR5L17S2026O1N149_000316", "date": "2026-02-12",
                 "type_detail": "debat"}
PLF_2026 = {"dossier_id": "DLR5L17N52428", "titre": "Projet de loi de finances pour 2026",
            "date_min": "2025-06-03", "date_max": "2026-02-19", "stade_procedural": "promulgue"}
PLF_2025 = {"dossier_id": "DLR5L17N50198", "titre": "Projet de loi de finances pour 2025",
            "date_min": "2024-07-20", "date_max": "2025-02-14", "stade_procedural": "promulgue"}
# Le scrutin an:16:1 porte la date 2022-07-11 dans l'index des scrutins.
VOTE_2022 = {"scrutin_id": "an:16:1", "position": "pour"}


def _sans_commentaires(source: str) -> str:
    """Une règle citée en commentaire n'est pas une règle appliquée."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


def _lire(chemin: Path) -> str:
    return _sans_commentaires(chemin.read_text(encoding="utf-8"))


def _executer(script: str) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const f = await import({json.dumps(PERIODE.as_uri())});\n"
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# 1. La fenêtre


@pytest.mark.parametrize(
    ("au", "periode", "attendu"),
    [
        ("2026-09-21", "6m", "2026-03-21"),
        ("2026-09-21", "12m", "2025-09-21"),
        ("2026-08-31", "6m", "2026-02-28"),   # le piège : pas le 3 mars
        ("2028-08-31", "6m", "2028-02-29"),   # année bissextile
        ("2026-01-15", "6m", "2025-07-15"),   # l'année change
        ("2026-09-21", "3m", None),           # aucune autre durée n'existe
        ("pas-une-date", "6m", None),         # une date absente n'est pas inventée
    ],
)
def test_la_fenetre_se_compte_depuis_la_date_des_donnees(au, periode, attendu):
    assert _executer(f"console.log(JSON.stringify(f.debutDeFenetre({json.dumps(au)}, {json.dumps(periode)})));") == attendu


def test_deux_durees_et_pas_une_de_plus():
    """Durées fixes, arbitrées : ni fenêtre libre, ni troisième case."""
    cles = _executer("console.log(JSON.stringify(Object.keys(f.PERIODES)));")
    assert cles == ["6m", "12m"]


# ---------------------------------------------------------------------------
# 2. Le filtrage, sur des entrées copiées du corpus


def _profil_filtre(debut: str | None) -> dict:
    pivot = {"interventions": [QAG_MAI, QAG_MARS, DEBAT_FEVRIER, {"intervention_id": "sans-date"}],
             "textes_portes": [PLF_2026, PLF_2025], "votes": [VOTE_2022], "amendements": [{"amendement_id": "x"}]}
    script = f"""
      const pivot = {json.dumps(pivot)};
      const lecteurs = {{
        dateDuVote: (v) => (v.scrutin_id === 'an:16:1' ? '2022-07-11' : null),
        dateDeLAmendement: () => null,
      }};
      console.log(JSON.stringify(f.filtrerProfilParPeriode(pivot, {json.dumps(debut)}, lecteurs)));
    """
    return _executer(script)


def test_sans_periode_le_profil_est_inchange():
    r = _profil_filtre(None)
    assert len(r["interventions"]) == 4 and len(r["textes_portes"]) == 2


def test_six_mois_gardent_ce_qui_est_dans_la_fenetre():
    r = _profil_filtre("2026-03-21")
    assert [i["date"] for i in r["interventions"]] == ["2026-05-05", "2026-03-24"]
    assert r["votes"] == []


def test_un_element_sans_date_ne_passe_pas_une_fenetre_active():
    """On ne suppose pas (§2 règle 5) : l'intervention et l'amendement sans date sortent."""
    r = _profil_filtre("2025-09-21")
    assert "sans-date" not in [i["intervention_id"] for i in r["interventions"]]
    assert r["amendements"] == []


def test_un_texte_porte_est_dans_la_fenetre_s_il_y_a_ete_actif():
    """Le PLF 2026, déposé en juin 2025 et promulgué en février 2026, appartient
    aux douze derniers mois ; le PLF 2025, clos en février 2025, non."""
    r = _profil_filtre("2025-09-21")
    assert [t["dossier_id"] for t in r["textes_portes"]] == ["DLR5L17N52428"]


# ---------------------------------------------------------------------------
# 3. Une seule date de référence


def test_la_date_des_donnees_est_celle_des_fenetres_de_backend():
    """`sync-data` la lit sur la `date_reference` des fiches de groupe — là où
    #1077 compte ses fenêtres —, et n'écrit rien s'il n'en trouve pas."""
    sync = _lire(SYNC)
    assert "date_reference?.date" in sync
    assert "'donnees.json'" in sync
    assert "if (dates.length)" in sync, "sans date lisible, le fichier n'est pas écrit"


def test_les_votes_et_amendements_sont_dates_par_les_index():
    """Le profil ne porte que leur identifiant ; la date vit dans l'index."""
    chargeur = _lire(CHARGEUR)
    assert "scrutins[v.scrutin_id]?.date" in chargeur
    assert "?.amendements?.[a.amendement_id]?.date" in chargeur
    assert "filtrerProfilParPeriode(" in chargeur


# ---------------------------------------------------------------------------
# 4. Le gouvernement, au compte exact


def test_la_parole_du_gouvernement_porte_ses_seances_datees():
    parole = _lire(PAROLE_GOUV)
    assert "seances:" in parole
    assert "connu.seances.set(date" in parole


def test_la_fenetre_du_gouvernement_se_compte_sur_les_seances():
    fiche = _lire(FICHE_GOUV)
    assert "i.seances || []" in fiche, "les tours ne comptent que dans la fenêtre"
    assert "reduce((n, [, t]) => n + t, 0)" in fiche


# ---------------------------------------------------------------------------
# 5. Le contrôle


def test_deux_vraies_cases_exclusives_dans_le_tiroir():
    tiroir = _lire(TIROIR)
    assert 'type="checkbox"' in tiroir
    assert "if (valeur !== periode) suivant.set('periode', valeur);" in tiroir
    assert "else suivant.delete('periode');" in tiroir, "décocher la case active revient à tout"


def test_des_cases_seulement_la_ou_elles_filtrent():
    """Des cases qui ne filtrent rien seraient du mobilier : elles n'existent
    que sur les fiches qui datent ce qu'elles montrent — la fiche de groupe
    depuis que #1077 lui a donné ses fenêtres de parole."""
    tiroir = _lire(TIROIR)
    datees = re.search(r"const FICHES_DATEES = \[([^\]]*)\]", tiroir).group(1)
    assert all(f"'/{r}'" in datees for r in ("candidats", "groupes", "gouvernements"))
    assert "{periodeDisponible && (" in tiroir


# ---------------------------------------------------------------------------
# 6. Ce que la fiche dit


def test_l_etiquette_porte_la_periode_et_se_tait_sans_filtre():
    recherche = _lire(RECHERCHE)
    assert "if (!mot && !debut) return null;" in recherche
    assert "libelleDebut(debut)" in recherche


def test_les_vides_disent_la_periode_et_jamais_un_mot_vide():
    """Sous une période seule, « dont l'intitulé contient « » » serait faux :
    chaque message passe par `Condition`, qui dit le mot, la période, ou les deux."""
    for fiche in (FICHE, FICHE_GOUV):
        source = _lire(fiche)
        assert "MOT(mot)" not in source, f"{fiche.name} écrit encore sa condition à la main"
        assert "<Condition critere=" in source
    assert "useFiltreActif(mot)" in _lire(FICHE)


# ---------------------------------------------------------------------------
# 7. La fiche de groupe, dans les fenêtres de Backend (#1077)

# Copiés de la lignée AN-RN, maillon XVIIe (public/data, 22/09/2026) : les
# comptes par fenêtre sont ceux que Backend publie.
DEBATS_RN = [
    {"label": "prix des carburants", "porteurs": 7, "denominateur": 131, "parFenetre": {"6m": 7, "12m": 7}},
    {"label": "taxes sur les biocarburants", "porteurs": 1, "denominateur": 131, "parFenetre": {"6m": 0, "12m": 1}},
]
FENETRES_RN = {"6m": {"debut": "2026-03-22", "fin": "2026-09-22", "nb_membres": 127},
               "12m": {"debut": "2025-09-22", "fin": "2026-09-22", "nb_membres": 128}}


def _lignee_filtree(saisie: str, periode: str | None) -> dict:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    maillon = {"id": "AN-RN-17", "sujets": {"liste": DEBATS_RN[:1], "total": 1, "denominateur": 131},
               "scrutins": {"an:17:8419": {"date": "2026-07-20", "texte": "l'ensemble de la proposition de loi"}},
               "partageListes": {"une_seule_voix": [["an:17:8419", 121, 0, 0]]},
               "textes": [], "amendements": {"parType": {"depute": {"lignes": []}}}, "quorum": {}, "convergences": []}
    script = f"""
      const f = await import({json.dumps(FILTRE_LIGNEE.as_uri())});
      const debats = {{ 'AN-RN-17': Object.assign({json.dumps(DEBATS_RN)}, {{ fenetres: {json.dumps(FENETRES_RN)} }}) }};
      const r = f.filtrerLignee({{ maillons: [{json.dumps(maillon)}] }}, {json.dumps(saisie)}, debats,
        {json.dumps(periode)}, {json.dumps("2026-03-22" if periode == "6m" else "2025-09-22")});
      console.log(JSON.stringify(r.maillons[0]));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


def test_six_mois_comptent_les_membres_de_la_fenetre_sur_son_denominateur():
    m = _lignee_filtree("", "6m")
    assert [(s["label"], s["porteurs"], s["denominateur"]) for s in m["sujets"]["liste"]] == [
        ("prix des carburants", 7, 127)]
    assert m["sujets"]["denominateur"] == 127


def test_un_debat_sans_membre_dans_la_fenetre_sort():
    """« taxes sur les biocarburants » : un membre sur douze mois, aucun sur six."""
    six = [s["label"] for s in _lignee_filtree("", "6m")["sujets"]["liste"]]
    douze = [s["label"] for s in _lignee_filtree("", "12m")["sujets"]["liste"]]
    assert "taxes sur les biocarburants" not in six
    assert "taxes sur les biocarburants" in douze


def test_les_amendements_se_retirent_sous_une_periode():
    """Comptés par dossier sur toute la législature : les recompter dans une
    fenêtre serait inventer. Le composant dit pourquoi ils manquent."""
    m = _lignee_filtree("", "6m")
    assert m["amendements"]["parType"] == {}
    assert m["amendementsHorsPeriode"] is True
    assert "la période ne s’y applique pas" in _lire(FICHE_LIGNEE)


def test_les_scrutins_du_groupe_se_datent_eux_memes():
    assert len(_lignee_filtree("", "6m")["partageListes"]["une_seule_voix"]) == 1   # 20/07/2026 : dedans


def test_la_projection_des_debats_transporte_les_fenetres():
    vue = _lire(VUE_LIGNEE)
    assert "schema_version: 'debats-lignee-v2'" in vue
    assert "groupe.fenetres_parole" in vue
    assert "nb_membres_porteurs_par_fenetre" in vue


def test_une_fiche_close_n_a_rien_dans_la_fenetre_du_site():
    """Backend compte « 6 mois » depuis la fin d'une fiche close : 2023-12-09 →
    2024-06-09 pour le RN de la XVIe (16 des 29 fiches AN, mesuré le 22/09/2026).
    Sous la case, ces débats de 2024 s'afficheraient sous « depuis le 22/03/2026 »."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    fenetres_xvie = {"6m": {"debut": "2023-12-09", "fin": "2024-06-09", "nb_membres": 88}}
    debats = [{"label": "carburants", "porteurs": 3, "denominateur": 88, "parFenetre": {"6m": 3, "12m": 3}}]
    maillon = {"id": "AN-RN-16", "sujets": {"liste": debats, "total": 1}, "scrutins": {},
               "partageListes": {}, "textes": [], "amendements": {"parType": {}}, "quorum": {}, "convergences": []}
    script = f"""
      const f = await import({json.dumps(FILTRE_LIGNEE.as_uri())});
      const d = {{ 'AN-RN-16': Object.assign({json.dumps(debats)}, {{ fenetres: {json.dumps(fenetres_xvie)} }}) }};
      const r = f.filtrerLignee({{ maillons: [{json.dumps(maillon)}] }}, '', d, '6m', '2026-03-22');
      console.log(JSON.stringify(r.maillons[0].sujets.liste));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout.strip().splitlines()[-1]) == []
