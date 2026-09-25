"""Ce que l'exécutif a fait entrer en vigueur (#1029 voie 1).

`pivot_data/actes_reglementaires/` porte 389 000 actes depuis 2007, et
l'interface n'en lisait aucun. `web/UI_finale/scripts/actes-gouvernement.mjs`
en tire la projection par gouvernement ; ces gardes tiennent les trois règles
qui font que la section dit vrai.

Elles ne vérifient pas le dessin : elles vérifient le classement, et ce que la
section s'interdit d'écrire.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "scripts" / "actes-gouvernement.mjs"
COMPOSANT = UI / "src" / "components" / "ActesDuGouvernement.jsx"
SYNC = UI / "scripts" / "sync-data.mjs"


def _node(corps: str) -> str:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"const M = await import({json.dumps(MODULE.as_uri())});\n{corps}"
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def test_le_module_et_le_composant_existent() -> None:
    assert MODULE.is_file(), "le module de projection des actes manque"
    assert COMPOSANT.is_file(), "la section de la fiche manque"


def test_un_acte_qui_modifie_une_creation_est_une_modification() -> None:
    """L'ordre des verbes EST le fait : l'inverse gonflait les créations."""
    sortie = _node("""
      const cas = [
        ["Décret modifiant le décret portant création du machin", "modifier"],
        ["Décret portant création d'une aide à la trésorerie", "créer"],
        ["Arrêté abrogeant l'arrêté portant création de la chose", "abroger"],
        ["Arrêté fixant la liste des personnes", "encadrer"],
      ];
      process.stdout.write(cas.map(([t, a]) => (M.verbeDe(t) === a ? "ok" : `${t} → ${M.verbeDe(t)} ≠ ${a}`)).join("\\n"));
    """)
    assert set(sortie.split("\n")) == {"ok"}, sortie


def test_le_lien_a_une_loi_se_lit_dans_le_titre() -> None:
    """La qualification structurée de Légifrance n'est plus posée : le titre est la seule source."""
    sortie = _node("""
      const cas = [
        ["Décret portant application de l'article 2 de la loi n° 2025-568", M.NOMME],
        ["Arrêté pris pour l'application de l'article 3 du décret", M.APPLIQUE],
        ["Arrêté fixant la liste des variétés de plantes", M.MUET],
      ];
      process.stdout.write(cas.map(([t, a]) => (M.lienDe(t) === a ? "ok" : `${t} → ${M.lienDe(t)}`)).join("\\n"));
    """)
    assert set(sortie.split("\n")) == {"ok"}, sortie


def test_les_actes_de_personne_sortent_du_compte() -> None:
    """Nomination, admission, naturalisation : de la vie administrative, pas une mesure."""
    sortie = _node("""
      const dedans = ["portant nomination de M. X", "portant admission à la retraite",
                      "portant naturalisation, réintégration", "portant promotion"];
      const dehors = ["portant création d'une aide", "modifiant l'arrêté du 3 mai"];
      const faux = dedans.filter((t) => !M.PERSONNE.test(t)).concat(dehors.filter((t) => M.PERSONNE.test(t)));
      process.stdout.write(faux.length ? faux.join(" | ") : "ok");
    """)
    assert sortie == "ok", sortie


def test_un_acte_est_range_dans_la_fenetre_de_son_gouvernement() -> None:
    sortie = _node("""
      const acc = M.accumulateurs([
        {id: "A", debut: "2024-01-01", fin: "2024-06-30"},
        {id: "B", debut: "2024-07-01", fin: null},
      ]);
      M.ranger(acc, {date: "2024-03-02", titre: "Décret portant création d'une aide", ministere: "Ministère de la santé", id: "1"});
      M.ranger(acc, {date: "2025-02-02", titre: "Décret portant nomination de M. X", ministere: null, id: "2"});
      const a = M.projection(acc[0]), b = M.projection(acc[1]);
      process.stdout.write(JSON.stringify({a: [a.tot, a.personnes, a.total], b: [b.tot, b.personnes, b.total]}));
    """)
    etat = json.loads(sortie)
    assert etat["a"] == [1, 0, 1], "l'acte de mars revient au gouvernement A"
    assert etat["b"] == [1, 1, 0], "une nomination est comptée puis retirée, jamais publiée comme mesure"


def test_le_delai_dit_de_quel_premier_acte_il_parle() -> None:
    """« Délai 12 ans » se lirait comme douze ans d'inaction : la fiche doit dire l'inverse."""
    texte = COMPOSANT.read_text(encoding="utf-8")
    assert "de cette période" in texte, "la note doit borner le délai à la période du gouvernement"
    assert "une loi ancienne a pu en recevoir avant" in texte


def test_la_section_ne_dit_jamais_sans_loi() -> None:
    """Un acte sans mention n'est pas un acte pris sans loi (§2 règle 5)."""
    texte = COMPOSANT.read_text(encoding="utf-8")
    assert "ne veut pas dire" in texte and "sans loi" in texte, (
        "la section doit écrire que « le titre ne le dit pas » n'est pas « sans loi »"
    )
    for interdit in ("décret sans attache", "acte sans loi", "sans base légale"):
        assert interdit not in texte.lower(), f"formule interdite : {interdit}"


def test_la_projection_est_ecrite_une_fois_pour_tous_les_gouvernements() -> None:
    """Une passe par gouvernement relirait 197 Mo dix-sept fois."""
    texte = SYNC.read_text(encoding="utf-8")
    assert "projeterLesActes" in texte, "la passe des actes n'est plus branchée sur sync-data"
    assert "actes: actesParGouvernement.has(id)" in texte, (
        "le manifeste doit déclarer le fichier des actes, sinon la fiche ne le charge pas"
    )


# ── LA RUBRIQUE DU JOURNAL OFFICIEL TRANCHE, LE TITRE EST UN REPLI (#1134) ────
#
# Les chaînes et les titres ci-dessous sont COPIÉS du corpus
# (`pivot_data/actes_reglementaires/2026-*.json`), jamais inventés : une fixture
# qui décrit le monde tel que le code l'imagine ne peut pas révéler qu'il a bougé.

NOMINATIVE = (
    "Décrets, arrêtés, circulaires > Mesures nominatives > Ministère de la santé, "
    "des familles, de l'autonomie et des personnes handicapées"
)
GENERALE = (
    "Décrets, arrêtés, circulaires > Textes généraux > Ministère de l'Europe "
    "et des affaires étrangères"
)
MEDECIN = (
    "Arrêté du 24 décembre 2025 fixant la liste des personnes autorisées à exercer "
    "en France la profession de médecin"
)


def test_la_rubrique_attrape_ce_qu_aucune_formule_du_titre_ne_voyait() -> None:
    """Le cas qui a ouvert le sujet : 308 arrêtés « médecin » que le filtre laissait passer."""
    sortie = _node(f"""
      const t = {json.dumps(MEDECIN)};
      const parLeTitre = M.PERSONNE.test(t);
      const parLaRubrique = M.acteDePersonne(t, {json.dumps(NOMINATIVE)}).personne;
      process.stdout.write(JSON.stringify({{ parLeTitre, parLaRubrique }}));
    """)
    etat = json.loads(sortie)
    assert etat["parLeTitre"] is False, "si le titre suffisait, la rubrique n'aurait pas été lue"
    assert etat["parLaRubrique"] is True, "la rubrique du JO doit sortir cet arrêté du compte"


def test_la_rubrique_prime_sur_le_titre_dans_les_deux_sens() -> None:
    """La source range ; le titre ne la contredit pas, même quand il semble plus sûr."""
    sortie = _node(f"""
      const nom = {json.dumps(NOMINATIVE)}, gen = {json.dumps(GENERALE)};
      const cas = [
        ["Arrêté portant nomination de M. X", gen, false],
        ["Arrêté portant création d'une aide", nom, true],
      ];
      const faux = cas.filter(([t, r, a]) => M.acteDePersonne(t, r).personne !== a).map(([t]) => t);
      process.stdout.write(faux.length ? faux.join(" | ") : "ok");
    """)
    assert sortie == "ok", sortie


def test_une_rubrique_absente_retombe_sur_le_titre_et_se_declare() -> None:
    """Une rubrique absente n'est pas « acte général » (§2 règle 5) : c'est le titre qui tranche, et on le dit."""
    sortie = _node("""
      const acc = M.accumulateurs([{ id: "g", debut: "2026-01-01", fin: null }]);
      M.ranger(acc, { date: "2026-02-01", titre: "Arrêté portant nomination de M. X", id: "a", rubrique: null });
      M.ranger(acc, { date: "2026-02-02", titre: "Arrêté portant création d'une aide", id: "b", rubrique: null });
      M.ranger(acc, { date: "2026-02-03", titre: "Arrêté portant création d'une aide", id: "c",
                      rubrique: %s });
      const p = M.projection(acc[0]);
      process.stdout.write(JSON.stringify({ tot: p.tot, personnes: p.personnes,
        parTitre: p.personnesParTitre, sansRubrique: p.sansRubrique, total: p.total }));
    """ % json.dumps(NOMINATIVE))
    p = json.loads(sortie)
    assert p["tot"] == 3
    assert p["personnes"] == 2, "la nomination sans rubrique et la création rangée en nominatif sortent"
    assert p["parTitre"] == 1, "un seul des deux a été tranché par le titre"
    assert p["sansRubrique"] == 2, "deux actes n'avaient pas de rubrique"
    assert p["total"] == 1


def test_la_fiche_publie_combien_d_actes_ont_ete_tranches_par_le_titre() -> None:
    """Deux absences ne se confondent jamais : le repli se lit, ou il passe pour la source."""
    texte = COMPOSANT.read_text(encoding="utf-8")
    assert "personnesParTitre" in texte, (
        "la section doit publier le nombre d'actes que le sommaire du JO n'a pas rangés"
    )
    assert "Journal officiel" in texte, "la section doit dire QUI range les actes de personne"


def test_le_rangement_du_jo_est_lu_depuis_les_fichiers_mois() -> None:
    """`rubrique_des_actes` est aligné sur `ids`, jamais une 7e colonne d'`actes`."""
    texte = SYNC.read_text(encoding="utf-8")
    assert "rubrique_des_actes" in texte and "doc.rubriques" in texte, (
        "sync-data ne lit pas le rangement du sommaire"
    )
    assert "rubriqueDesActes[i]" in texte, "la rubrique doit être prise à l'index de l'acte"
