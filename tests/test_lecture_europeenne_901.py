"""Le versant européen se lit comme le français : thèmes, natures, votes (#901).

CE QUE CE LOT RÈGLE, en trois points mesurés le 17/09/2026 sur le commit de
données `760f1bffe` :

1. **Les votes européens n'atteignaient pas l'écran.** Les 11 013 positions des
   six candidats déclarés à mandat européen portent `scrutin_id: null` — l'index
   de l'Assemblée ne les résout pas, par contrat — et la fiche affichait « aucune
   n'est rattachée à un scrutin identifié », ce qui décrivait notre index et non
   la source. Elles se joignent toutes par NUMÉRO + DATE à
   `pivot_data/scrutins_europeens.json`.
2. **Les amendements européens se rangeaient par commission saisie au fond**, un
   axe que le sankey des textes n'utilise pas. Arbitrage de la propriétaire :
   « les catégories doivent être en cohérence entre le sankey des textes et les
   amendements ». Les trois figures européennes partagent donc la même cascade de
   thèmes — domaines EuroVoc du dossier, sinon familles OEIL.
3. **La teinte suivait le RANG du thème dans la figure**, donc un même thème
   changeait de couleur d'une figure à l'autre et d'une fiche à l'autre.

CE QUE CES GARDE-FOUS PROTÈGENT :

- un texte voté ou un dépôt compte sous CHACUN de ses thèmes, et les effectifs
  (puces, positions) comptent des objets DISTINCTS : les deux règles vivent
  ensemble, et l'une sans l'autre publierait un faux total ;
- « pas encore interrogé » n'est pas « sans thème » : la couverture EuroVoc monte
  d'un run à l'autre (151 dossiers sur 4 642), et la famille OEIL range le
  dossier en attendant ;
- aucun découpage par période côté européen : il n'y a ni banc ni gouvernement en
  place à Strasbourg (« hors propos », 17/09/2026) ;
- aucune origine de texte côté européen : il n'y a pas de projet de loi du
  gouvernement.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu ici, et aucun test ne lit `pivot_data/`. Le rendu a été vérifié
hors dépôt sur le serveur de développement, sur Maurel, Philippot, Mélenchon et
Guedj — dont la fiche, sans mandat européen, ne doit rien voir changer.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
VOTES_UE = UI / "utils" / "votesEuropeens.js"
TEINTES = UI / "utils" / "matiere.js"
ADAPTATEUR = UI / "data" / "pivotAdapter.js"
CHARGEUR = UI / "data" / "index.js"
FICHE = UI / "components" / "CandidateProfile.jsx"
PERIODES = UI / "components" / "VotesParPeriode.jsx"
CASCADE = UI / "components" / "CascadeTextes.jsx"
SYNC = RACINE / "web" / "UI_finale" / "scripts" / "sync-data.mjs"


def _sans_commentaires(source: str) -> str:
    """Une règle citée en commentaire n'est pas une règle appliquée."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def adaptateur() -> str:
    return _sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fiche() -> str:
    return _sans_commentaires(FICHE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def periodes() -> str:
    return _sans_commentaires(PERIODES.read_text(encoding="utf-8"))


def _executer(script: str, module: Path = VOTES_UE) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const u = await import({json.dumps(module.as_uri())});\n"
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


_SCRUTINS = """
const scrutins = {
  11: { id: 'pe:11', numero_scrutin: 11, date: '2018-10-24', texte: 'A8-0299/2018 - proposition de la Commission', document: 'A8-0299/2018', source_url: 'https://parltrack.org/11' },
  12: { id: 'pe:12', numero_scrutin: 12, date: '2018-10-24', texte: 'A8-0299/2018 - résolution législative', document: 'A8-0299/2018', source_url: 'https://parltrack.org/12' },
  9: { id: 'pe:9', numero_scrutin: 9, date: '2017-06-01', texte: 'Ancienne lecture', document: 'A8-0299/2018', source_url: null },
  40: { id: 'pe:40', numero_scrutin: '2017-06-01 00:00:00-40.', date: '2019-03-12', texte: 'RC-B8-0351 - Résolution', document: 'RC-B8-0351', source_url: null },
  41: { id: 'pe:41', numero_scrutin: '2017-06-01 00:00:00-7.', date: '2019-03-12', texte: 'RC-B8-0351 - Amendement', document: 'RC-B8-0351', source_url: null },
};
const pe = (numero, date, reference, position) => ({
  position,
  scrutin_id: null,
  scrutin_non_resolu: { institution: 'parlement_europeen', numero_scrutin: numero, date, reference_dossier: reference },
});
"""


# ---------------------------------------------------------------------------
# 1. Un texte, une position : la jointure et le dernier scrutin
# ---------------------------------------------------------------------------


def test_la_jointure_demande_le_numero_ET_la_date() -> None:
    """Un numéro seul ne garantit pas le scrutin : la date en fait partie. Une
    position dont le couple ne tombe pas est COMPTÉE et déclarée, jamais rangée
    sous un scrutin voisin (§2 règle 2)."""
    out = _executer(_SCRUTINS + """
      const votes = [
        pe(11, '2018-10-24', '2018/0074(COD)', 'pour'),
        pe(11, '2011-01-01', '2018/0074(COD)', 'contre'),
        { position: 'pour', scrutin_id: 4210, scrutin_non_resolu: null },
      ];
      const r = u.votesEuropeensRetenus(votes, scrutins);
      console.log(JSON.stringify({ total: r.total, joints: r.joints, retenus: r.retenus.length }));
    """)
    assert out == {"total": 2, "joints": 1, "retenus": 1}


def test_le_vote_retenu_est_le_dernier_de_son_dossier() -> None:
    """Date la plus tardive, puis rang dans la séance : « résolution législative »
    suit « proposition de la Commission » le même jour, et c'est elle qui vaut
    position sur le texte."""
    out = _executer(_SCRUTINS + """
      const votes = [
        pe(9, '2017-06-01', '2018/0074(COD)', 'abstention'),
        pe(12, '2018-10-24', '2018/0074(COD)', 'pour'),
        pe(11, '2018-10-24', '2018/0074(COD)', 'contre'),
      ];
      const r = u.votesEuropeensRetenus(votes, scrutins);
      console.log(JSON.stringify(r.retenus.map((x) => [x.scrutin.id, x.position])));
    """)
    assert out == [["pe:12", "pour"]]


def test_un_numero_mal_forme_garde_son_rang_de_seance() -> None:
    """716 des 5 571 scrutins portent « 2017-06-01 00:00:00-13. » au lieu de 13.
    Comparés comme des chaînes, « -7. » passerait après « -40. »."""
    out = _executer("""
      console.log(JSON.stringify([13, '2017-06-01 00:00:00-13.', '2017-06-01 00:00:00-7.', null].map(u.rangDansLaSeance)));
    """)
    assert out == [13, 13, 7, -1]

    dernier = _executer(_SCRUTINS + """
      const votes = [pe(41, '2019-03-12', '2019/2000(RSP)', 'contre'), pe(40, '2019-03-12', '2019/2000(RSP)', 'pour')];
      const r = u.votesEuropeensRetenus(votes, scrutins);
      console.log(JSON.stringify(r.retenus.map((x) => x.scrutin.id)));
    """)
    assert dernier == ["pe:40"]


def test_un_vote_sans_dossier_reste_un_texte() -> None:
    """389 des positions de Raphaël Glucksmann ne portent aucune référence de
    dossier : le document voté, à défaut le scrutin, tient lieu de texte. Les
    écarter les ferait disparaître (§2 règle 5)."""
    out = _executer(_SCRUTINS + """
      const votes = [pe(40, '2019-03-12', null, 'pour'), pe(41, '2019-03-12', null, 'contre')];
      const r = u.votesEuropeensRetenus(votes, scrutins);
      console.log(JSON.stringify({ retenus: r.retenus.length, nature: u.cleNatureDuVote(null) }));
    """)
    # Même document : un seul texte, et sa nature est « sans dossier ».
    assert out == {"retenus": 1, "nature": "sans_dossier"}


# ---------------------------------------------------------------------------
# 2. Les thèmes : la cascade du sankey, et ce qu'elle ne dit pas
# ---------------------------------------------------------------------------


def test_les_themes_sont_les_domaines_puis_les_familles() -> None:
    """La cascade du sankey : les domaines EuroVoc du dossier, sinon ses familles
    OEIL. Le libellé perd son numéro de tête, comme dans la cascade."""
    out = _executer("""
      const dossiers = {
        avecDomaines: { domaines: [{ code: '08', libelle: '08 RELATIONS INTERNATIONALES' }], familles: [{ code: '6', libelle: 'External relations of the Union' }] },
        sansDomaines: { domaines: [], familles: [{ code: '3', libelle: 'Community policies' }] },
        rien: {},
      };
      console.log(JSON.stringify(['avecDomaines', 'sansDomaines', 'rien'].map((c) => u.themesDuDossier(dossiers[c]))));
    """)
    assert out == [["Relations internationales"], ["Community policies"], []]


def test_un_dossier_pas_encore_interroge_n_est_pas_un_dossier_sans_theme() -> None:
    """4 455 des 4 642 dossiers portent `question_non_posee` : la collecte ne les
    a pas encore demandés au portail. Leur famille OEIL les range ; les traiter
    comme une absence de thème publierait un vide qui n'existe pas."""
    out = _executer("""
      const dossier = {
        domaines: [],
        domaines_non_resolu: { motif: 'question_non_posee' },
        familles: [{ code: '8', libelle: 'State and evolution of the Union' }],
      };
      console.log(JSON.stringify(u.themesDuDossier(dossier)));
    """)
    assert out == ["State and evolution of the Union"]


def test_un_texte_compte_sous_chacun_de_ses_themes_mais_reste_un_texte() -> None:
    """La figure en barres duplique la LIGNE, jamais le texte : `textes` et la
    liste comptent des scrutins distincts. Sans cette séparation, un texte à
    trois thèmes serait publié comme trois votes."""
    out = _executer(_SCRUTINS + """
      const dossiers = { 'd': { domaines: [], familles: [{ libelle: 'A' }, { libelle: 'B' }] } };
      const votes = [pe(12, '2018-10-24', 'd', 'pour')];
      const { retenus } = u.votesEuropeensRetenus(votes, scrutins);
      const f = u.figureVotesEuropeens(retenus, [], (r) => dossiers[r] || null);
      console.log(JSON.stringify({
        textes: f.textes,
        lignes: f.periodes[0].votes.map((v) => v.matiere),
        distincts: new Set(f.periodes[0].votes.map((v) => v.scrutinId)).size,
      }));
    """)
    assert out == {"textes": 1, "lignes": ["A", "B"], "distincts": 1}


def test_la_figure_europeenne_n_a_qu_une_periode() -> None:
    """Le banc et le gouvernement en place découpent les votes français ; à
    Strasbourg il n'y a ni l'un ni l'autre. La période unique nomme les groupes
    traversés, et la couverture des thèmes se publie."""
    out = _executer(_SCRUTINS + """
      const votes = [pe(9, '2017-06-01', 'x', 'pour'), pe(12, '2018-10-24', 'y', 'contre')];
      const { retenus } = u.votesEuropeensRetenus(votes, scrutins);
      const mandats = [
        { categorie: 'mandat_electif', categorie_source: 'europarl', debut: '2014-07-01', fin: '2019-07-01' },
        { type_organe_source: 'groupe_politique_europeen', sigle_organe: 'S&D', debut: '2014-07-01', fin: '2019-07-01' },
      ];
      const f = u.figureVotesEuropeens(retenus, mandats, () => null);
      const p = f.periodes[0];
      console.log(JSON.stringify({ periodes: f.periodes.length, libelle: p.libelle, groupes: p.groupes, reperes: f.reperes }));
    """)
    assert out == {
        "periodes": 1,
        "libelle": "Au Parlement européen",
        "groupes": ["S&D"],
        "reperes": {"total": 2, "positions": 0, "matiere": 0},
    }


def test_le_repli_sur_le_dernier_vote_dit_ce_qu_il_retire(periodes) -> None:
    """3 598 positions donnent 3 175 textes chez Emmanuel Maurel : les 423 autres
    portent sur un scrutin antérieur du même texte. Laissé à la soustraction,
    l'écart se lirait comme une perte (§2 règles 5 et 7). Et la note ne parle
    plus de commission : l'axe européen est le thème."""
    note = periodes.split("{reperes && ue && (")[1].split("{reperes && !ue && (")[0]
    assert "ne portent aucun" in note and "thème" in note
    assert "commission" not in note
    assert "reperes.positions - reperes.total" in note
    out = _executer(_SCRUTINS + """
      const votes = [pe(9, '2017-06-01', 'd', 'abstention'), pe(12, '2018-10-24', 'd', 'pour')];
      const { retenus, joints } = u.votesEuropeensRetenus(votes, scrutins);
      const f = u.figureVotesEuropeens(retenus, [], () => null, joints);
      console.log(JSON.stringify(f.reperes));
    """)
    assert out == {"total": 1, "positions": 2, "matiere": 0}


def test_aucune_origine_de_texte_au_parlement_europeen() -> None:
    """« Origine : Parlement / Gouvernement » est une règle de l'Assemblée — il
    n'y a pas de projet de loi du gouvernement à Strasbourg."""
    out = _executer(_SCRUTINS + """
      const votes = [pe(12, '2018-10-24', 'y', 'contre')];
      const { retenus } = u.votesEuropeensRetenus(votes, scrutins);
      const f = u.figureVotesEuropeens(retenus, [], () => null);
      console.log(JSON.stringify(f.periodes[0].votes.map((v) => v.origine)));
    """)
    assert out == [None]


# ---------------------------------------------------------------------------
# 3. La teinte suit le thème
# ---------------------------------------------------------------------------


def test_un_theme_garde_sa_teinte_quel_que_soit_son_rang() -> None:
    """C'est tout l'objet du changement : « Community policies » doit être de la
    même teinte dans le sankey, dans la carte des amendements et d'une fiche à
    l'autre. Et « matière non établie » reste grise : c'est une absence, pas un
    thème de plus."""
    out = _executer("""
      console.log(JSON.stringify({
        rang0: u.teinteThemeUe('Community policies', 0),
        rang7: u.teinteThemeUe('Community policies', 7),
        autre: u.teinteThemeUe('Vie politique', 0),
        nonEtablie: u.teinteThemeUe('Matière non établie', 3),
      }));
    """, module=TEINTES)
    assert out["rang0"] == out["rang7"]
    assert out["autre"] != out["rang0"]
    assert out["nonEtablie"] == "#c4c0b9"


def test_les_trois_figures_europeennes_prennent_la_teinte_du_theme(fiche, periodes) -> None:
    """Le sankey et la carte des amendements colorient par thème ; la figure des
    votes, elle, colorie par POSITION — le thème y est nommé, pas teinté."""
    cascade = _sans_commentaires(CASCADE.read_text(encoding="utf-8"))
    assert "teinteThemeUe" in cascade and "ue ? teinteThemeUe" in cascade
    assert "ue ? teinteThemeUe" in fiche


# ---------------------------------------------------------------------------
# 4. Ce que la fiche fait de tout cela
# ---------------------------------------------------------------------------


def test_les_amendements_europeens_se_rangent_par_theme(adaptateur) -> None:
    """Et plus par commission saisie au fond : l'axe a changé le 17/09/2026, et
    la fonction qui lisait la commission n'a plus de lecteur."""
    assert "themesDuDossier" in adaptateur
    assert "commissionAuFondEuropeenne" not in adaptateur
    regles = (UI / "utils" / "profilCandidat.js").read_text(encoding="utf-8")
    assert "commissionAuFondEuropeenne" not in regles, "aucune règle sans lecteur"


def test_les_puces_de_nature_comptent_des_depots_pas_des_copies(adaptateur, fiche) -> None:
    """La duplication par thème gonflerait chaque effectif : « Législatif 3 371 »
    pour 1 552 dépôts, mesuré sur la maquette du 17/09."""
    assert "depotsParNature" in adaptateur
    bloc = adaptateur.split("depotsParNature")[1].split("};")[0]
    assert "role_signataire === 'auteur_principal'" in bloc
    assert "amendementsUe.depotsParNature[n.cle]" in fiche


def test_le_versant_europeen_des_votes_a_son_commutateur(fiche) -> None:
    """Le même que « Ce qu'il a proposé » et « Ce qu'il a dit » : la fiche ne dit
    pas la même chose de deux façons."""
    bloc = fiche.split("function Votes({")[1].split("function VotesFrancais")[0]
    assert "<CommutateurVersant" in bloc
    assert "Parlement des votes" in bloc


def test_la_fiche_ne_declare_plus_les_votes_europeens_non_rattaches(fiche) -> None:
    """La phrase était vraie quand rien ne joignait ces positions ; elle est
    fausse depuis que le numéro et la date les rattachent."""
    assert "rattachée à un scrutin identifié" not in fiche


def test_aucune_navigation_par_periode_cote_europeen(periodes) -> None:
    """Ni période, ni origine : deux repères que la source ne publie pas à
    Strasbourg."""
    assert "!periode.cumul && !ue && (" in periodes
    assert "{!ue && <span className=\"vp-sep\" />}" in periodes or "!ue && <span" in periodes


def test_l_index_des_scrutins_europeens_est_copie_puis_charge() -> None:
    """Un index que le build ne copie pas est un index que l'interface ne lit
    jamais — la panne se voit à l'écran, pas dans la CI."""
    sync = SYNC.read_text(encoding="utf-8")
    assert "scrutins_europeens.json" in sync
    chargeur = CHARGEUR.read_text(encoding="utf-8")
    assert "/data/scrutins_europeens.json" in chargeur
    assert "numero_scrutin" in chargeur, "l'index est indexé par numéro de scrutin"
    assert "scrutinsEuropeens," in _sans_commentaires(chargeur)
