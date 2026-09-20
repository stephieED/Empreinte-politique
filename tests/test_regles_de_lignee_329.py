"""Les règles de la fiche de lignée (#329), EXÉCUTÉES — pas relues.

`utils/lignee.js` et les règles ajoutées à `utils/groupe.js` sont importées par
le navigateur ET par la projection de build (`scripts/vue-lignee.mjs`). Ce
fichier les fait tourner sous Node, sur des cas fabriqués, et vérifie ce
qu'elles rendent. Précédent : `tests/test_web_v3_mandate_timeline.py`, qui
lance déjà `node` en CI.

Aucun test ne lit le corpus vivant (`docs/regles/ci.md`, §3b) : les cas sont
petits, et chacun porte le défaut qu'il empêche.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UTILS = RACINE / "web" / "UI_finale" / "src" / "utils"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node absent")


def executer(corps: str):
    """Importe les trois modules de règles et rend le JSON que `corps` écrit."""
    script = f"""
    const lecture = await import({json.dumps((UTILS / 'lecture.js').as_uri())});
    const groupe = await import({json.dumps((UTILS / 'groupe.js').as_uri())});
    const lignee = await import({json.dumps((UTILS / 'lignee.js').as_uri())});
    const sortie = await (async () => {{ {corps} }})();
    process.stdout.write(JSON.stringify(sortie));
    """
    res = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


# ── L'effectif recompté jour par jour ────────────────────────────────────────

def test_une_fin_d_appartenance_compte_encore_ce_jour_la():
    """Le membre sort le LENDEMAIN de sa fin : sans quoi l'effectif à la date de
    référence, qui est souvent la dernière fin, perdrait un membre."""
    serie = executer("""
      return lignee.serieEffectif([
        { periodes: [{ debut: '2022-06-29', fin: '2024-06-09' }] },
        { periodes: [{ debut: '2022-06-29', fin: null }] },
      ]);
    """)
    assert serie == [["2022-06-29", 2], ["2024-06-10", 1]]


def test_un_membre_parti_puis_revenu_compte_deux_fois_entrer_et_sortir():
    """Ce sont les PÉRIODES réelles (#809), pas l'enveloppe, qui se tracent."""
    serie = executer("""
      return lignee.serieEffectif([
        { debut_dans_groupe: '2020-01-01', fin_dans_groupe: '2022-12-31',
          periodes: [{ debut: '2020-01-01', fin: '2020-12-31' }, { debut: '2022-01-01', fin: '2022-12-31' }] },
      ]);
    """)
    assert serie == [["2020-01-01", 1], ["2021-01-01", 0], ["2022-01-01", 1], ["2023-01-01", 0]]


def test_une_appartenance_sans_debut_ne_se_place_nulle_part():
    serie = executer("""
      return lignee.serieEffectif([{ periodes: [{ debut: null, fin: '2020-01-01' }] }]);
    """)
    assert serie == [], "une date absente ne devient jamais le premier jour (§2 règle 5)"


# ── D'où vient chaque personne d'un maillon ──────────────────────────────────

def test_trois_etats_de_passage_et_leur_somme_retombe_sur_le_maillon():
    """Un point par personne et par maillon (forme B, 11/09/2026)."""
    maillons = executer("""
      return lignee.personnesParMaillon({
        maillons: [{ groupe_id: 'A:15' }, { groupe_id: 'A:16' }, { groupe_id: 'A:17' }],
        membres: [
          { membre_id: 'toujours', nom: 'Toujours', maillons: ['A:15', 'A:16', 'A:17'] },
          { membre_id: 'revenue', nom: 'Revenue', maillons: ['A:15', 'A:17'] },
          { membre_id: 'nouvelle', nom: 'Nouvelle', maillons: ['A:17'] },
        ],
      });
    """)
    dernier = maillons[2]
    assert dernier["comptes"] == {"prec": 1, "retour": 1, "nouveau": 1}
    assert sum(dernier["comptes"].values()) == len(dernier["personnes"]) == 3
    assert [p["passage"] for p in dernier["personnes"]] == ["prec", "retour", "nouveau"], (
        "rangés par état, puis par nom"
    )
    assert maillons[0]["comptes"] == {"prec": 0, "retour": 0, "nouveau": 2}


# ── Les amendements par commission ──────────────────────────────────────────

def test_la_repartition_compte_des_amendements_distincts_par_type_et_ne_devine_aucune_matiere():
    rep = executer("""
      const amendements = {
        a1: { type_deposant: 'depute', sort: 'adopté', texte_vise: 'T1', date: '2024-01-02' },
        a2: { type_deposant: 'depute', sort: 'rejeté', texte_vise: 'T1', date: '2024-03-01' },
        a3: { type_deposant: 'depute', sort: 'rejeté', texte_vise: 'T2', date: '2023-05-01' },
        a4: { type_deposant: 'depute', sort: 'rejeté', texte_vise: null, date: '2024-01-01' },
        a5: { type_deposant: 'commission_rapporteur', sort: 'adopté', texte_vise: 'T1', date: '2024-02-01' },
      };
      const textes = { T1: { dossier_id: 'DLR5L16N1', titre: 'Premier' }, T2: { dossier_id: 'DLR5L16N2', titre: 'Second' } };
      const commissions = { DLR5L16N1: { sigle: 'Finances' } };
      return lignee.repartitionParCommission(
        new Set(['a1', 'a2', 'a3', 'a4', 'a5', 'inconnu']), amendements, textes,
        (d) => commissions[d] ?? null, (d) => (d === 'DLR5L16N1' ? 'adopte' : null),
      );
    """)
    depute = rep["types"]["depute"]
    assert depute["amendements"] == 4 and depute["adoptes"] == 1 and depute["dossiers"] == 2
    assert rep["types"]["commission_rapporteur"]["amendements"] == 1, (
        "chaque type garde son total ; les réunir est un choix du lecteur, fait par `cumulerTypes`"
    )
    assert rep["introuvables"] == 1
    finances = depute["lignes"][0]
    assert finances["commission"] == "Finances" and finances["amendements"] == 2 and finances["textes"] == 1
    assert finances["detail"][0]["statut"] == "adopte"
    assert finances["detail"][0]["sourceUrl"] == "https://www.assemblee-nationale.fr/dyn/16/dossiers/DLR5L16N1"
    # Sans dossier, ou sans commission connue : « matière non établie », jamais une déduction.
    assert depute["nonEtablie"]["amendements"] == 2 and depute["nonEtablie"]["textes"] == 1
    assert depute["nonEtablie"]["detail"][0]["statut"] is None, "un sort non publié reste `null`"


def test_les_textes_d_une_commission_se_rangent_par_date_jamais_par_volume():
    """Règle de forme 6 : le volume ne distingue pas un travail de fond d'une
    obstruction, c'est la date qui range."""
    rep = executer("""
      const amendements = {};
      for (let i = 0; i < 50; i += 1) amendements[`gros${i}`] = { type_deposant: 'depute', texte_vise: 'VIEUX', date: '2019-01-01' };
      amendements.petit = { type_deposant: 'depute', texte_vise: 'RECENT', date: '2025-01-01' };
      const textes = { VIEUX: { dossier_id: 'DLR5L15N1' }, RECENT: { dossier_id: 'DLR5L17N2' } };
      return lignee.repartitionParCommission(new Set(Object.keys(amendements)), amendements, textes, () => ({ sigle: 'Lois' }));
    """)
    detail = rep["types"]["depute"]["lignes"][0]["detail"]
    assert [d["dossier"] for d in detail] == ["DLR5L17N2", "DLR5L15N1"]


def test_deux_types_reunis_additionnent_les_amendements_et_unissent_les_textes():
    """Relecture du 11/09/2026 : les deux boutons ensemble, des comptes réunis.

    Un amendement n'a qu'un type : la somme est le compte distinct. Un dossier
    peut être amendé par les deux : la somme le compterait deux fois."""
    res = executer("""
      const d = (dossier, amendements, adoptes, dernier) => ({ dossier, titre: dossier, amendements, adoptes, dernier, statut: null });
      const parType = {
        depute: { amendements: 12, adoptes: 3, dossiers: 2,
          lignes: [{ commission: 'Finances', amendements: 10, textes: 2, detail: [d('D1', 7, 2, '2024-01-01'), d('D2', 3, 1, '2023-01-01')] }],
          nonEtablie: { amendements: 2, textes: 0, detail: [] } },
        commission_rapporteur: { amendements: 4, adoptes: 4, dossiers: 2,
          lignes: [{ commission: 'Finances', amendements: 3, textes: 1, detail: [d('D1', 3, 3, '2025-01-01')] },
                   { commission: 'Lois', amendements: 1, textes: 1, detail: [d('D3', 1, 1, '2022-01-01')] }],
          nonEtablie: null },
      };
      return { deux: lignee.cumulerTypes(parType, ['depute', 'commission_rapporteur']),
               seul: lignee.cumulerTypes(parType, ['depute']) === parType.depute };
    """)
    deux = res["deux"]
    assert (deux["amendements"], deux["adoptes"]) == (16, 7), "les amendements et les adoptés s'additionnent"
    assert deux["dossiers"] == 3, "D1 est amendé par les deux types : 3 dossiers, pas 4"
    finances = deux["lignes"][0]
    assert (finances["commission"], finances["amendements"], finances["textes"]) == ("Finances", 13, 2)
    d1 = finances["detail"][0]
    assert (d1["dossier"], d1["amendements"], d1["adoptes"], d1["dernier"]) == ("D1", 10, 5, "2025-01-01"), (
        "un texte amendé par les deux types réunit ses comptes, et garde sa date la plus récente"
    )
    assert deux["nonEtablie"] == {"amendements": 2, "textes": 0, "detail": []}
    assert res["seul"] is True, "un type seul se lit tel quel"


# ── Le partage, en trois listes ─────────────────────────────────────────────

GROUPE_PARTAGE = """
  const g = { cohesion_votes: [
    { scrutin_id: 's1', quorum_atteint: true, pour: 30, contre: 0, abstention: 0 },
    { scrutin_id: 's2', quorum_atteint: true, pour: 20, contre: 0, abstention: 5 },
    { scrutin_id: 's3', quorum_atteint: true, pour: 20, contre: 2, abstention: 0 },
    { scrutin_id: 's4', quorum_atteint: true, pour: 10, contre: 9, abstention: 0 },
    { scrutin_id: 's5', quorum_atteint: false, pour: 2, contre: 1, abstention: 0 },
    { scrutin_id: 's6', quorum_atteint: true, pour: 0, contre: 12, abstention: 0 },
  ] };
  const dates = { s1: '2024-01-01', s6: '2025-01-01' };
"""


def test_les_trois_listes_retombent_sur_les_trois_decomptes_publies():
    res = executer(GROUPE_PARTAGE + """
      const p = groupe.partageDuGroupe(g);
      const l = groupe.scrutinsParPartage(g, (id) => dates[id] ?? '');
      return { p: { une: p.uneSeuleVoix, partages: p.partages, pc: p.pourEtContre }, l };
    """)
    p, listes = res["p"], res["l"]
    assert len(listes["une_seule_voix"]) == p["une"]
    assert len(listes["pour_et_contre"]) == p["pc"]
    assert len(listes["abstention"]) == p["partages"] - p["pc"]
    assert len(listes["partages"]) == p["partages"]
    assert all("s5" not in [e[0] for e in l] for l in listes.values()), "sous le quorum, rien"


def test_les_plus_partages_d_abord_et_d_une_seule_voix_par_date():
    listes = executer(GROUPE_PARTAGE + "return groupe.scrutinsParPartage(g, (id) => dates[id] ?? '');")
    assert [e[0] for e in listes["pour_et_contre"]] == ["s4", "s3"], "9 voix minoritaires avant 2"
    assert [e[0] for e in listes["une_seule_voix"]] == ["s6", "s1"], "les plus récents d'abord"
    assert listes["pour_et_contre"][0] == ["s4", 10, 9, 0], (
        "une entrée porte les positions exprimées, jamais le nombre de voix minoritaires "
        "(§2 règle 7)"
    )


# ── Les convergences, et leurs listes ───────────────────────────────────────

def test_chaque_segment_deroule_exactement_son_compte():
    res = executer("""
      const comparaison = { groupes: [
        { sigle: 'A', effectif: 50, positions: { s1: 'pour', s2: 'contre', s3: 'abstention', s4: 'pour' } },
        { sigle: 'B', effectif: 40, positions: { s1: 'pour', s2: 'pour', s3: 'contre' } },
      ] };
      const [ligne] = groupe.convergences(comparaison, 'A');
      const listes = groupe.scrutinsParNature(comparaison, 'A').get('B');
      return { ligne, listes };
    """)
    comptes = {n["cle"]: n["valeur"] for n in res["ligne"]["natures"]}
    assert comptes == {"meme_sens": 1, "nuance": 1, "oppose": 1}
    assert {k: len(v) for k, v in res["listes"].items()} == {"meme_sens": 1, "nuance": 1, "oppose": 1, "autres": 0}
    assert res["listes"]["nuance"] == [["s3", "abstention", "contre"]], (
        "une abstention face à une position exprimée est une NUANCE, jamais un vote contraire"
    )


def test_a_base_egale_l_accord_departage_et_seulement_la():
    """Relecture du 11/09/2026 : textes communs d'abord, accord ensuite."""
    ordre = executer("""
      const comparaison = { groupes: [
        { sigle: 'A', positions: { s1: 'pour', s2: 'pour', s3: 'pour', s4: 'pour' } },
        { sigle: 'B', positions: { s1: 'contre', s2: 'contre', s3: 'pour' } },
        { sigle: 'C', positions: { s1: 'pour', s2: 'pour', s3: 'contre' } },
        { sigle: 'D', positions: { s1: 'contre', s2: 'contre', s3: 'contre', s4: 'contre' } },
      ] };
      return groupe.convergences(comparaison, 'A').map((l) => l.sigle);
    """)
    assert ordre == ["D", "C", "B"], (
        "D partage 4 textes et passe en tête malgré 0 accord ; C et B en partagent 3, et "
        "C, d'accord 2 fois, passe devant B, d'accord une fois"
    )


# ── Motifs de posture et liens ───────────────────────────────────────────────

def test_le_motif_se_lit_sur_la_posture_declaree():
    res = executer("""
      return ['majorite', 'opposition', 'minoritaire', 'non_declaree'].map((valeur) =>
        lignee.motifDePosture({ declaree: true, valeur }))
        .concat([lignee.motifDePosture({ declaree: false, valeur: null })]);
    """)
    assert res == ["plein", "diagonales", "mauve", "points", "absente"]


def test_le_lien_d_un_dossier_ne_se_construit_que_sur_un_identifiant_reconnu():
    res = executer("""
      return [lecture.urlDossierAN('DLR5L15N43849'), lecture.urlDossierAN('PRJLANR5L16B0017'), lecture.urlDossierAN(null)];
    """)
    assert res == ["https://www.assemblee-nationale.fr/dyn/15/dossiers/DLR5L15N43849", None, None]


# ── Ce qu'on n'a pas pu lire ─────────────────────────────────────────────────

def test_seuls_les_signalements_propres_a_la_fiche_sont_retenus():
    """Les avertissements identiques en nature sur toutes les fiches — source,
    date de référence, carrière écartée — partent sur `/couverture` (#328)."""
    res = executer("""
      const fiche = {
        meta: {
          couverture_roster: { roster_total: 24, profils_disponibles: 23, etat: 'dans_le_perimetre' },
          warnings: [
            "fraicheur_donnees : composition dérivée du référentiel AMO30…",
            "date_reference : tous les comptes de cette fiche se rapportent au 2024-06-09…",
            "cohesion_votes : 1570 vote(s) sans scrutin_id écarté(s) — aucun rattachement…",
            "tags_thematiques_agreges : 31980 intervention(s) tenue(s) sous une autre législature que la 15e…",
            "tags_thematiques_agreges : 1803 intervention(s) dont l'identifiant ne porte pas de législature sont CONSERVÉES — rien…",
          ],
        },
        amendements_agreges: { nb_sans_identifiant: 154 },
      };
      return lignee.signalementsDuMaillon(fiche).map((s) => [s.liste, s.n]);
    """)
    assert res == [["membres", 1], ["interventions", 1803], ["amendements", 154], ["votes", 1570]]


def test_une_fiche_sans_signalement_n_en_invente_aucun_et_le_senat_se_dit_hors_perimetre():
    res = executer("""
      const propre = { meta: { couverture_roster: { roster_total: 42, profils_disponibles: 42 }, warnings: [] } };
      const senat = { meta: { couverture_roster: { roster_total: 235, profils_disponibles: 15, etat: 'hors_perimetre' } } };
      return [lignee.signalementsDuMaillon(propre), lignee.signalementsDuMaillon(senat).map((s) => s.texte)];
    """)
    assert res[0] == []
    assert "hors du périmètre" in res[1][0] and "235" in res[1][0]


def _messages_du_pipeline():
    """Les avertissements que `group_profile.py` écrit, reconstruits depuis son
    source : un f-string rend ses valeurs sous la forme `12`."""
    arbre = ast.parse((RACINE / "src" / "group_profile.py").read_text(encoding="utf-8"))
    messages = []
    for noeud in ast.walk(arbre):
        if (isinstance(noeud, ast.Call) and isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr == "append" and noeud.args):
            arg = noeud.args[0]
            if isinstance(arg, ast.JoinedStr):
                messages.append("".join(
                    v.value if isinstance(v, ast.Constant) else "12" for v in arg.values
                ))
    return messages


def test_les_motifs_suivent_le_gabarit_du_pipeline():
    """Deux signalements ne vivent que dans `meta.warnings` : un message
    reformulé côté pipeline doit casser ce test, pas vider la section."""
    messages = _messages_du_pipeline()
    res = executer(f"""
      const messages = {json.dumps(messages, ensure_ascii=False)};
      return Object.fromEntries(Object.entries(lignee.MOTIFS_AVERTISSEMENT)
        .map(([cle, motif]) => [cle, messages.filter((m) => motif.test(m)).length]));
    """)
    assert res == {"votesSansScrutin": 1, "interventionsSansLegislature": 1, "amendementsIntrouvables": 1}


# ── Les textes portés par un groupe ──────────────────────────────────────────

def test_un_dossier_porte_par_plusieurs_membres_compte_une_fois_au_stade_le_plus_avance():
    res = executer("""
      const entrees = [
        { dossier_id: 'D1', role: 'auteur_proposition_de_loi', stade_procedural: 'depose', titre: 'T1', date_max: '2024-01-01' },
        { dossier_id: 'D1', role: 'auteur_proposition_de_loi', stade_procedural: 'adopte', sort: 'adopte', date_max: '2024-05-01' },
        { dossier_id: 'D1', role: 'rapporteur', stade_procedural: 'adopte' },
        { dossier_id: 'D2', role: 'initiateur_projet_de_loi', stade_procedural: 'promulgue' },
        { dossier_id: null, role: 'auteur', stade_procedural: 'depose' },
        { dossier_id: 'D3', role: 'co-rapporteur', stade_procedural: 'examine_commission' },
      ];
      const t = lignee.textesDuMaillon(entrees, (d) => (d === 'D1' ? { sigle: 'Lois', nom: 'Commission des lois' } : null));
      return {
        dossiers: t.map((x) => x.dossier_id),
        d1: { stade: t.find((x) => x.dossier_id === 'D1').stade_procedural, roles: t.find((x) => x.dossier_id === 'D1').roles,
              commission: t.find((x) => x.dossier_id === 'D1').commission, date: t.find((x) => x.dossier_id === 'D1').date_max },
        auteurs: lignee.textesDesQualites(t, ['auteur']).map((x) => x.dossier_id),
        rapporteurs: lignee.textesDesQualites(t, ['rapporteur']).map((x) => x.dossier_id),
        deux: lignee.textesDesQualites(t, ['auteur', 'rapporteur']).map((x) => x.dossier_id),
      };
    """)
    # Le projet de loi est signé comme ministre : il n'est pas un texte du groupe.
    assert sorted(res["dossiers"]) == ["D1", "D3"]
    assert res["d1"] == {
        "stade": "adopte",
        "roles": {"auteur": "auteur_proposition_de_loi", "rapporteur": "rapporteur"},
        "commission": {"sigle": "Lois", "nom": "Commission des lois"},
        "date": "2024-05-01",
    }
    assert res["auteurs"] == ["D1"]
    assert sorted(res["rapporteurs"]) == ["D1", "D3"]
    assert sorted(res["deux"]) == ["D1", "D3"], "deux qualités réunies : un dossier une fois"
