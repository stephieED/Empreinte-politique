"""La recherche sur la fiche de groupe (lignée) (#979).

Le même geste que sur la fiche candidat (#993), arbitré sur maquette le
17/09/2026 (Socialistes, « retraite ») :

1. **« En bref » et « Qui sont-ils » se retirent** sous un mot ; **« Ce qu'on
   n'a pas pu lire » ne change pas** — contrairement à la fiche candidat.
2. **Les sections 2 à 5 sont recalculées** sur la PROJECTION de la lignée
   (`filtrerLignee`) : chaque figure recompte à partir des listes qu'elle
   transporte déjà.
3. **Tous les groupes de la lignée à la suite** (forme B) : chaque section
   empile les groupes où le mot trouve quelque chose, sans flèches.
4. **Les débats complets vivent à part.** La projection n'en porte que dix par
   groupe (10 sur 284 pour NG-15) ; `vue-lignee.mjs` écrit un fichier de débats
   par lignée (1,0 Mo pour les douze, 115 Ko pour les Socialistes, mesuré le
   17/09/2026), que la page ne charge qu'au premier mot tapé.
5. **Une barre, une étiquette, une note** : `components/Recherche.jsx`, partagé
   avec la fiche candidat.

FIXTURES. Entrées copiées de la projection `AN-SOC` (maillon `AN-SOC-17`)
construite le 17/09/2026, réduites aux champs que le filtre lit.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu. Le
rendu — sections retirées, groupes empilés, étiquettes, cinq messages, débats
chargés au premier mot seulement — a été vérifié hors dépôt sur le serveur de
développement, sur les Socialistes avec « retraite », « zzqx » et sans mot,
et la fiche d'Emmanuel Maurel avec « nucléaire ».
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"
REGLES = SRC / "utils" / "filtreLignee.js"
FICHE = SRC / "components" / "LigneeProfile.jsx"
PAGE = SRC / "pages" / "GroupProfilePage.jsx"
RECHERCHE = SRC / "components" / "Recherche.jsx"
CANDIDAT = SRC / "components" / "CandidateProfile.jsx"
CHARGEUR = SRC / "data" / "index.js"
VUE = UI / "scripts" / "vue-lignee.mjs"
SYNC = UI / "scripts" / "sync-data.mjs"

MAILLON = {
    "id": "AN-SOC-17",
    "sujets": {
        "liste": [
            {"label": "projet de loi de financement de la sécurité sociale pour 2026", "porteurs": 50, "denominateur": 70},
            {"label": "droit à l’aide à mourir", "porteurs": 35, "denominateur": 70},
        ],
        "total": 721,
        "denominateur": 70,
    },
    "textes": [
        {"dossier_id": "DLR5L17N52530", "titre": "Reconnaître et valoriser l’engagement associatif dans le calcul des droits à la retraite", "stade_procedural": "examine_commission"},
        {"dossier_id": "DLR5L17N53053", "titre": "Protéger la santé mentale des agricultrices et des agriculteurs", "stade_procedural": "adopte"},
    ],
    "amendements": {
        "distincts": 14278,
        "sansType": 3991,
        "parType": {
            "depute": {
                "amendements": 502,
                "adoptes": 44,
                "dossiers": 2,
                "lignes": [
                    {
                        "commission": "Affaires sociales",
                        "amendements": 502,
                        "textes": 2,
                        "detail": [
                            {"dossier": "DLR5L17N52517", "titre": "Garantir un revenu mensuel à tout nouveau retraité dès l’entrée en jouissance de la pension de retraite", "amendements": 3, "adoptes": 2},
                            {"dossier": "DLR5L17N51670", "titre": "Fin de vie", "amendements": 499, "adoptes": 42},
                        ],
                    }
                ],
                "nonEtablie": None,
            }
        },
    },
    "quorum": {"agreges": 8369, "mesurables": 3},
    "partage": {"mesurables": 3, "uneSeuleVoix": 2, "partages": 1, "pourEtContre": 1},
    "partageListes": {
        "une_seule_voix": [["an:17:2257", 44, 0, 0], ["an:17:8430", 0, 0, 63]],
        "abstention": [],
        "pour_et_contre": [["an:17:217", 1, 52, 0]],
        "partages": [["an:17:217", 1, 52, 0]],
    },
    "scrutins": {
        "an:17:2257": {"texte": "la proposition de résolution visant à abroger la loi n° 2023-270 du 14 avril 2023 de financement rectificative de la sécurité sociale pour 2023 dite réforme des retraites."},
        "an:17:8430": {"texte": "l'ensemble du projet de loi relatif à la protection des enfants (première lecture)."},
        "an:17:217": {"texte": "l'ensemble de la proposition de loi visant à restaurer un système de retraite plus juste en annulant les dernières réformes portant sur l’âge de départ et le nombre d’annuités (première lecture)."},
    },
    "convergences": [
        {
            "sigle": "ECOS",
            "communs": 2,
            "natures": [{"cle": "meme_sens", "valeur": 2}, {"cle": "nuance", "valeur": 0}, {"cle": "oppose", "valeur": 0}],
            "autres": 0,
            "scrutins": {"meme_sens": [["an:17:217", "contre", "contre"], ["an:17:8430", "abstention", "abstention"]], "nuance": [], "oppose": [], "autres": []},
        }
    ],
}


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


def _lire(chemin: Path) -> str:
    return _sans_commentaires(chemin.read_text(encoding="utf-8"))


def _executer(script: str) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const f = await import({json.dumps(REGLES.as_uri())});\n"
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


def _filtre(saisie: str, debats: object = None) -> dict:
    lignee = {"id": "AN-SOC", "maillons": [MAILLON]}
    return _executer(
        f"const l = {json.dumps(lignee)};"
        f"const r = f.filtrerLignee(l, {json.dumps(saisie)}, {json.dumps(debats)});"
        "const m = r.maillons[0];"
        "console.log(JSON.stringify({ meme: r === l, m, resultats: Object.fromEntries("
        "Object.entries(f.MAILLON_A_DES_RESULTATS).map(([k, g]) => [k, g(m)])) }));"
    )


# ---------------------------------------------------------------------------
# 1. La projection réduite, recomptée


def test_sans_mot_la_lignee_est_rendue_telle_quelle():
    assert _filtre("  ")["meme"] is True


def test_retraite_recompte_chaque_figure_sur_ses_listes():
    m = _filtre("retraite")["m"]
    assert [t["dossier_id"] for t in m["textes"]] == ["DLR5L17N52530"]
    depute = m["amendements"]["parType"]["depute"]
    assert (depute["amendements"], depute["adoptes"], depute["dossiers"]) == (3, 2, 1)
    assert depute["lignes"][0]["textes"] == 1
    assert m["amendements"]["distincts"] == 3
    assert m["partage"] == {"mesurables": 2, "uneSeuleVoix": 1, "partages": 1, "pourEtContre": 1}
    assert m["quorum"]["mesurables"] == 2
    # Le total agrégé n'est porté par aucune liste : il n'est pas recalculé,
    # et c'est le composant qui le tait sous un mot.
    assert m["quorum"]["agreges"] == 8369
    ecos = m["convergences"][0]
    assert ecos["communs"] == 1 and ecos["natures"][0]["valeur"] == 1


def test_les_debats_complets_remplacent_les_dix_de_la_projection():
    complets = {
        "AN-SOC-17": [
            {"label": "abrogation de la retraite à 64 ans", "porteurs": 11, "denominateur": 70},
            {"label": "droit à l’aide à mourir", "porteurs": 35, "denominateur": 70},
        ]
    }
    sans = _filtre("retraite")["m"]["sujets"]["liste"]
    avec = _filtre("retraite", complets)["m"]["sujets"]
    assert sans == []
    assert [s["label"] for s in avec["liste"]] == ["abrogation de la retraite à 64 ans"]
    assert avec["total"] == 1


def test_un_mot_absent_vide_chaque_section():
    assert _filtre("zzqx")["resultats"] == {"parole": False, "propose": False, "vote": False, "avec": False}


# ---------------------------------------------------------------------------
# 2. La fiche sous un mot


def test_en_bref_et_qui_sont_ils_se_retirent_la_couverture_reste():
    source = _lire(FICHE)
    assert "{!mot && (\n      <section className=\"lp-section lp-section--bref\"" in source
    assert "{!mot && <QuiSontIls lignee={lignee} />}" in source
    corps = source[source.index("export default function LigneeProfile"):]
    # « Ce qu'on n'a pas pu lire » est rendue hors de toute condition sur le mot.
    ligne = [l for l in corps.splitlines() if "<CeQuOnNaPasPuLire" in l][0]
    assert ligne.strip() == "<CeQuOnNaPasPuLire lignee={lignee} />"


def test_les_groupes_s_empilent_sans_fleches():
    source = _lire(FICHE)
    for cle, composant in (("parole", "SurQuoiIlsParlent"), ("propose", "CeQuIlsOntPropose"), ("vote", "CeQuIlsOntVote"), ("avec", "AvecQuiIlsVotent")):
        assert f'<EnPile Composant={{{composant}}} cle="{cle}" lignee={{lignee}} />' in source
    assert "if (periodes.length < 2 || force != null) return null;" in source


@pytest.mark.parametrize(
    "message",
    [
        "Aucun débat dont l’intitulé contient",
        "Aucun texte porté dont l’intitulé contient",
        "Aucun dossier amendé dont l’intitulé contient",
        "Aucun scrutin dont l’intitulé contient",
        "Aucun texte comparé dont l’intitulé contient",
    ],
)
def test_un_mot_sans_resultat_a_son_message(message):
    assert message in _lire(FICHE)


def test_ce_qui_ne_se_recompte_pas_se_tait_sous_un_mot():
    source = _lire(FICHE)
    assert "{mot ? '' : `, sur ${formatNumber(q.agreges)}`}" in source
    assert "if (m.amendements.sansType && !mot)" in source


def test_les_listes_se_deplient_sous_un_mot():
    source = _lire(FICHE)
    assert "const ouvert = ouverte === l.commission || Boolean(mot);" in source
    assert '<details className="lp-tous" open={Boolean(mot)}>' in source
    assert "...(m.partageListes?.une_seule_voix || [])" in source


# ---------------------------------------------------------------------------
# 3. Les débats : écrits à part, chargés au premier mot


def test_les_debats_complets_sont_ecrits_a_part():
    vue = _lire(VUE)
    assert "export function construireDebatsLignee" in vue
    assert "etiquettesThematiques(groupe, Infinity)" in vue
    assert "liste: etiquettesThematiques(groupe, 10)," in vue, "la projection garde ses dix débats"
    sync = _lire(SYNC)
    assert "debats: `${id}.debats.json`," in sync
    assert "writeFileSync(path.join(outDir, 'lignees', entree.debats)" in sync


def test_la_page_ne_charge_les_debats_qu_au_premier_mot():
    page = _lire(PAGE)
    assert "cherche && data?.lignee ? getDebatsLignee(data.lignee.id) : null" in page
    assert "filtrerLignee(data?.lignee, motDiffere, debats)" in page
    assert "etiquettesThematiques({" in _lire(CHARGEUR)


# ---------------------------------------------------------------------------
# 4. Une barre pour les deux fiches


def test_la_barre_est_partagee_par_les_deux_fiches():
    recherche = _lire(RECHERCHE)
    assert 'placeholder="Rechercher sur cette page"' in recherche
    assert "Contenant <mark>« {mot} »</mark>" in recherche
    for fiche in (CANDIDAT, FICHE):
        assert "from './Recherche'" in _lire(fiche)
    assert "function BarreFiltre" not in _lire(CANDIDAT)
