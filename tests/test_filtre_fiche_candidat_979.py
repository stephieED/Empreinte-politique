"""Le filtre par intitulé de la fiche candidat (#979).

CE QUE LE LOT PUBLIE. Une barre en tête de la fiche candidat : un mot tapé, et
la fiche se recalcule sur les seuls textes, votes, amendements et interventions
dont l'intitulé le contient. Arbitré sur maquette le 17/09/2026, sur la fiche
d'Emmanuel Maurel :

1. **Les figures suivent les listes.** Le filtre réduit le PROFIL avant que la
   fiche ne soit calculée ; il ne masque pas des lignes sous une figure qui
   resterait celle de toute la carrière.
2. **« En bref », « Les fonctions exercées » et « Ce qu'on n'a pas pu lire » se
   retirent** tant qu'un mot est tapé. Recalculé sur « finances », « En bref »
   publiait « 259 amendements sur 4 dossiers ».
3. **Le mot est rappelé en tête de chaque figure**, pour qu'une capture de la
   figure seule ne circule pas sans lui.
4. **Les listes se déplient sans clic**, et « Ce qu'il a voté » cumule ses
   périodes — exception assumée à la règle qui refuse le cumul hors filtre.
5. **Un mot qui ne trouve rien laisse la section en place, avec un message du
   filtre** — jamais « Non collecté », que la fiche affichait sans lui : faux,
   puisque la collecte n'est pas vide (§2 règle 5).
6. **Les interventions se cherchent aussi dans leur verbatim**, et le mot y est
   surligné : la barre dit « Rechercher sur cette page ». Sur le sujet seul,
   « nucléaire » ne trouvait aucune des 5 interventions de Maurel qui en parlent.
7. **Sans casse, sans accents, sans traduction.** « énergie » ne trouve pas
   « energy » : les intitulés des dossiers amendés européens sont en anglais, et
   le message le dit.

Et un défaut corrigé en chemin : sous trois flux, la cascade des textes portés
n'est pas dessinée et annonce « la liste ci-dessous les porte tous » — mais la
liste n'apparaissait qu'après un clic dans le diagramme absent.

FIXTURES. Les entrées de profil sont copiées de
`pivot_data/profiles/emmanuel-maurel.pivot.json` au 17/09/2026, réduites aux
champs que le filtre lit ; aucune valeur n'est inventée.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu, et
`data/index.js` ne se charge pas sous `node` (imports sans extension). Le rendu
— les sections retirées, les cinq étiquettes, les listes dépliées, les cinq
messages — a été vérifié hors dépôt sur le serveur de développement, sur Maurel
avec « finances », « énergie » et « numérique », et sans mot. Le temps de
recalcul, mesuré en développement le 17/09/2026 : 109 à 307 ms (verbatims compris) par mot sur
Ruffin, Mélenchon, Faure et Maurel.
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
REGLES = SRC / "utils" / "filtreIntitule.js"
FICHE = SRC / "components" / "CandidateProfile.jsx"
CHARGEUR = SRC / "data" / "index.js"
PAGE = SRC / "pages" / "CandidateProfilePage.jsx"
CASCADE = SRC / "utils" / "cascadeTextes.js"
LISTE_CASCADE = SRC / "components" / "CascadeTextes.jsx"
VOTES = SRC / "components" / "VotesParPeriode.jsx"
PAROLES = SRC / "components" / "ParolesParPeriode.jsx"
ECARTS = SRC / "components" / "EcartsGroupe.jsx"

# Copiés du profil d'Emmanuel Maurel (17/09/2026).
TEXTE_PLF = {
    "titre": "Projet de loi de finances pour 2026",
    "dossier_id": "DLR5L17N52428",
    "stade_procedural": "promulgue",
}
VOTE_EUROPEEN = {
    "scrutin_id": None,
    "position": "abstention",
    "scrutin_non_resolu": {
        "institution": "parlement_europeen",
        "titre": "Avenir numérique de l’Europe: marché unique numérique et utilisation de l’IA "
        "pour les consommateurs européens - Digital future of Europe: digital single market "
        "and use of AI for European consumers - Digitale Zukunft Europas: digitaler "
        "Binnenmarkt und Einsatz von KI für europäische Verbraucher - A9-0149/2021 - "
        "Deirdre Clune - Proposition de résolution",
    },
}
VOTE_FRANCAIS = {"scrutin_id": "an:17:518", "position": "contre"}
INTERVENTION = {
    "intervention_id": "syceron_CRSANR5L17S2026E1N024_000394",
    "theme_officiel": "Modernisation de la gestion du patrimoine immobilier de l’État",
    "dossier": {
        "point_ordre_du_jour": "Modernisation de la gestion du patrimoine immobilier de l’État "
        "> Discussion générale"
    },
}
MANDAT = {"label": "Commission des affaires européennes", "categorie": "commission"}


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
    entete = f"const f = await import({json.dumps(REGLES.as_uri())});\n"
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# 1. La comparaison : sans casse, sans accents, sans traduction


@pytest.mark.parametrize(
    ("intitule", "saisie", "attendu"),
    [
        ("Projet de loi de finances pour 2026", "FINANCES", True),
        ("Projet de loi de finances pour 2026", "loi finances", True),
        ("Projet de loi de finances pour 2026", "finances  loi", True),
        ("Projet de loi de finances pour 2026", "finances retraite", False),
        ("Modernisation de la gestion du patrimoine immobilier de l’État", "l'etat", True),
        ("PROPOSITION DE RÉSOLUTION sur le résultat de la modernisation du traité sur la Charte de l’énergie", "energie", True),
        # Pas de traduction : le mot français ne trouve pas le mot anglais.
        ("European Digital Identity framework", "numérique", False),
    ],
)
def test_la_comparaison_ignore_casse_et_accents_sans_traduire(intitule, saisie, attendu):
    rendu = _executer(
        f"console.log(JSON.stringify(f.contientLesMots({json.dumps(intitule)}, "
        f"f.motsDuFiltre({json.dumps(saisie)}))));"
    )
    assert rendu is attendu


def test_un_intitule_absent_ne_passe_pas_un_filtre_actif():
    """Sans intitulé, on ne suppose pas qu'il contiendrait le mot (§2 règle 5)."""
    rendu = _executer(
        "console.log(JSON.stringify([f.contientLesMots(null, ['x']), "
        "f.contientLesMots('', ['x']), f.contientLesMots(null, [])]));"
    )
    assert rendu == [False, False, True]


# ---------------------------------------------------------------------------
# 2. Le profil réduit : quatre listes filtrées, les mandats intacts


def _profil_filtre(saisie: str) -> dict:
    profil = {
        "nom": "Emmanuel Maurel",
        "mandats": [MANDAT],
        "textes_portes": [TEXTE_PLF],
        "votes": [VOTE_EUROPEEN, VOTE_FRANCAIS],
        "amendements": [{"amendement_id": "an:AMANR5L17PO838901B2247P0D1N003564"}],
        "interventions": [INTERVENTION],
    }
    return _executer(
        f"""
        const profil = {json.dumps(profil)};
        const lecteurs = {{
          intituleDuVote: (v) => v.scrutin_non_resolu?.titre
            ?? (v.scrutin_id === 'an:17:518' ? 'Projet de loi de finances de fin de gestion pour 2024' : null),
          intituleDeLAmendement: () => 'Projet de loi de finances pour 2026',
          intituleDeLIntervention: (i) => i.dossier?.point_ordre_du_jour ?? i.theme_officiel,
        }};
        const r = f.filtrerProfil(profil, {json.dumps(saisie)}, lecteurs);
        console.log(JSON.stringify({{
          meme: r === profil,
          mandats: r.mandats.length,
          textes: r.textes_portes.length,
          votes: r.votes.map((v) => v.scrutin_id ?? 'pe'),
          amendements: r.amendements.length,
          interventions: r.interventions.length,
        }}));
        """
    )


def test_sans_mot_le_profil_est_rendu_tel_quel():
    assert _profil_filtre("   ")["meme"] is True


def test_finances_garde_ce_qui_le_porte_et_laisse_les_mandats():
    r = _profil_filtre("finances")
    assert r == {
        "meme": False,
        "mandats": 1,
        "textes": 1,
        "votes": ["an:17:518"],
        "amendements": 1,
        "interventions": 0,
    }


def test_un_vote_europeen_non_rattache_est_filtre_sur_son_intitule_de_source():
    """Le filtre le trouve ; la fiche ne l'affiche pas davantage — le message le dit."""
    r = _profil_filtre("numérique")
    assert r["votes"] == ["pe"]
    assert r["textes"] == 0 and r["interventions"] == 0


# ---------------------------------------------------------------------------
# 3. Sous un mot, les votes cumulent leurs périodes


def test_la_periode_cumulee_borne_et_reunit_sans_rien_perdre():
    rendu = _executer(
        """
        const p = [
          { cle: '|BARNIER', debut: '2024-10-31', fin: '2024-12-04', votes: [{ scrutinId: 'an:17:217' }, { scrutinId: 'an:17:518' }], groupes: ['GDR'] },
          { cle: '|BAYROU', debut: '2025-01-23', fin: '2025-07-10', votes: [{ scrutinId: 'an:17:900' }], groupes: ['GDR'] },
        ];
        const c = f.periodeCumulee(p);
        console.log(JSON.stringify({ c, vide: f.periodeCumulee([]) }));
        """
    )
    c = rendu["c"]
    assert c["cumul"] is True
    assert (c["debut"], c["fin"]) == ("2024-10-31", "2025-07-10")
    assert [v["scrutinId"] for v in c["votes"]] == ["an:17:217", "an:17:518", "an:17:900"]
    assert c["groupes"] == ["GDR"]
    assert c["banc"] is None and c["gouvernement"] is None
    assert rendu["vide"] is None


# ---------------------------------------------------------------------------
# 4. Le branchement : le filtre agit AVANT le calcul de la fiche


def test_la_fiche_est_calculee_sur_le_profil_filtre():
    source = _lire(CHARGEUR)
    corps = source[source.index("export function vueCandidat"):]
    assert corps.index("filtrerProfil(") < corps.index("buildCandidateView(")
    assert "periodeCumulee(view.votes.periodes)" in corps
    # Le chargement ne se refait pas à chaque mot.
    assert "useMemo(() => vueCandidat(sources, motDiffere)" in _lire(PAGE)


def test_les_intitules_compares_sont_ceux_que_la_fiche_affiche():
    source = _lire(CHARGEUR)
    assert "titreDuTexteVote(brut)" in source
    assert "dossiersEuropeens?.[europeen.texte_vise]?.titre" in source
    assert "intituleDeLIntervention: (i) => [cheminDuPoint(i), i.texte]" in source


# ---------------------------------------------------------------------------
# 5. La fiche sous un mot


def test_trois_sections_se_retirent_sous_un_mot():
    source = _lire(FICHE)
    assert "{!filtre && <GrandsChiffres" in source
    for numero in ("1", "6"):
        assert re.search(r"\{!filtre && \(\s*<Section\s+numero=\"%s\"" % numero, source), numero
    for numero in ("2", "3", "4", "5"):
        assert not re.search(r"\{!filtre && \(\s*<Section\s+numero=\"%s\"" % numero, source), numero


def test_chaque_figure_porte_le_mot():
    source = _lire(FICHE)
    assert source.count("{mot && <EtiquetteFiltre mot={mot} />}") == 3  # textes, amendements, amendements vides
    assert source.count("etiquette={mot ? <EtiquetteFiltre mot={mot} /> : null}") == 3  # votes, écarts, dit
    for composant in (VOTES, PAROLES, ECARTS):
        assert "{etiquette}" in _lire(composant)


@pytest.mark.parametrize(
    "message",
    [
        "Aucun texte porté dont l’intitulé contient",
        "Aucun dossier amendé dont l’intitulé contient",
        " Au Parlement européen, ces intitulés sont publiés en anglais.",
        "Aucun vote affiché dont l’intitulé contient",
        # La phrase qui déclarait les positions européennes non rattachées est
        # partie avec #901 : elles le sont, par numéro et date, et la fiche les
        # affiche. Le message du filtre n'a plus à les excepter.
        "Aucun scrutin comparable avec son groupe dont l’intitulé contient",
        "Aucune intervention dont le sujet ou le propos contient",
    ],
)
def test_un_mot_sans_resultat_a_son_message(message):
    assert message in _lire(FICHE)


def test_un_vide_du_filtre_passe_avant_le_vide_de_collecte():
    """« Non collecté » sous un mot serait faux : la branche du filtre vient d'abord."""
    source = _lire(FICHE)
    assert source.index("textes.total === 0 && europe.total === 0 && mot") < source.index(
        'source="Textes portés comme auteur ou rapporteur"'
    )
    amdt = source[source.index("amdt.totalAuteur === 0 ? ("):]
    assert amdt.index("{mot ? (") < amdt.index("source={`Amendements déposés comme auteur principal")
    paroles = source[source.index("function Paroles("):]
    assert paroles.index("!interventions.total && mot") < paroles.index("<ListeVide")
    votes = source[source.index("function Votes("):]
    assert votes.index("if (mot &&") < votes.index("<ListeVide")


def test_les_listes_se_deplient_sous_un_mot():
    fiche = _lire(FICHE)
    # `figureAmdt` depuis #901 : la population affichée est celle du versant et
    # de la nature retenus, le dépliage sous un mot ne change pas.
    assert "Object.values(figureAmdt.chute?.dossiersParMatiere || {}).flat()" in fiche
    assert "'Toutes les commissions'" in fiche
    assert "deplie={Boolean(mot)}" in fiche
    paroles = _lire(PAROLES)
    assert "useState(deplie && !sansDecoupage ? null : periodes.length - 1)" in paroles
    assert "{!sujet && !deplie ? (" in paroles
    votes = _lire(VOTES)
    # `&& !ue` depuis #901 : le versant européen n'a pas de période du tout.
    assert "{!periode.cumul && !ue && (" in votes


# ---------------------------------------------------------------------------
# 6. Le défaut corrigé : une cascade non dessinée laisse voir sa liste


def test_une_cascade_non_dessinee_montre_tous_ses_textes():
    assert "export function cascadeDessinee" in _lire(CASCADE)
    fiche = _lire(FICHE)
    assert "!cascadeDessinee(cascade, disposer)" in fiche
    assert "selTexte ?? (toutVoir ? selectionDeTousLesTextes(cascade) : null)" in fiche
    # « Tout afficher » ne s'affiche que s'il retire une sélection.
    assert "{onRaz && <button" in _lire(LISTE_CASCADE)


# ---------------------------------------------------------------------------
# 7. Le mot surligné dans un verbatim


def test_le_surlignage_rend_le_texte_du_compte_rendu_a_l_identique():
    """Repéré sans casse ni accents, mais découpé dans l'original : rien n'est
    réécrit, et la concaténation redonne le verbatim caractère pour caractère."""
    verbatim = (
        "consommait une quantité d’électricité équivalente à la production annuelle "
        "d’un réacteur nucléaire. Les plateformes mobilisent"
    )
    rendu = _executer(
        f"const s = f.segmentsSurlignes({json.dumps(verbatim)}, 'NUCLEAIRE');"
        f"console.log(JSON.stringify({{ s, meme: s.map((x) => x.texte).join('') === {json.dumps(verbatim)} }}));"
    )
    assert rendu["meme"] is True
    assert [x["texte"] for x in rendu["s"] if x["marque"]] == ["nucléaire"]


def test_sans_mot_rien_n_est_surligne():
    rendu = _executer("console.log(JSON.stringify(f.segmentsSurlignes('Très bien !', '  ')));")
    assert rendu == [{"texte": "Très bien !", "marque": False}]


def test_le_verbatim_porte_le_surlignage_sous_un_mot():
    paroles = _lire(PAROLES)
    assert "segmentsSurlignes(i.verbatim, mot)" in paroles
    assert 'className="pp-mot"' in paroles
    assert "mot={mot}" in _lire(FICHE)
