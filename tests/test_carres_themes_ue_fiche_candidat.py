"""Les textes portés européens de la fiche candidat : une ligne par thème, un carré par texte.

Arbitré le 02/10/2026 avec la propriétaire, sur maquette (forme D) : sur la
fiche CANDIDAT, versant européen de « Les textes qu'il a portés », la cascade en
rubans laisse la place à une grille de carrés.

1. **Une ligne par thème, une colonne par étape présente.** Dans chaque case, un
   carré par texte qui touche ce thème et qui en est à cette étape.
2. **Un texte est répété sur chacun de ses thèmes** — un texte à trois thèmes a
   trois carrés —, et c'est le survol qui le dit : toutes ses occurrences
   s'entourent ensemble.
3. **L'en-tête d'une colonne compte des textes entiers**, jamais des carrés.
4. **Aucun compte par thème n'est affiché** (arbitrage du 17/09/2026) : le
   nombre de textes d'un thème classe les lignes, et s'arrête là.
5. **Les trois gestes des carrés français**, sur le même état de sélection : un
   carré, une étape, un thème.

CE QUE CES GARDE-FOUS PROTÈGENT est éditorial avant d'être graphique : une
colonne n'est pas un échelon — les stades européens ne s'ordonnent pas (#901) ;
« matière non établie » n'est pas un thème de plus (§2 règle 5) ; la teinte
suit le thème, jamais son rang ; et le lot n'écrit aucun texte publié.

LES ENTRÉES SONT COPIÉES DU CORPUS, au 02/10/2026 : les quatre textes portés
européens de Jean-Luc Mélenchon et celui de Lydie Massard, tels que leur pivot
les porte, avec les familles OEIL de leurs dossiers
(`dossiers_europeens.json`) et les matières EuroVoc de leurs documents
(`documents_europeens.json`). Une fixture inventée n'aurait pas porté le texte
à deux familles, ni celui dont le document n'a aucun concept.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu, et aucun test ne lit `pivot_data/`. Le survol, le contour des
occurrences, l'ellipse des noms, le gabarit des colonnes et le passage sous
560 px sont lus dans le code, pas à l'écran — le rendu se vérifie dans un
navigateur.
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
RANGEMENT = UI / "utils" / "carresThemesUe.js"
CARRES_FR = UI / "utils" / "carresTextes.js"
REGLES = UI / "utils" / "profilCandidat.js"
SELECTION = UI / "utils" / "cascadeTextes.js"
MATIERE = UI / "utils" / "matiere.js"
FICHE = UI / "components" / "CandidateProfile.jsx"
GRILLE = UI / "components" / "CarresThemesUe.jsx"
STYLE = UI / "components" / "CarresThemesUe.css"
LIGNEE = UI / "components" / "LigneeProfile.jsx"


def _sans_commentaires(source: str) -> str:
    """Une règle citée en commentaire n'est pas une règle appliquée."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def fiche() -> str:
    return _sans_commentaires(FICHE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def grille() -> str:
    return _sans_commentaires(GRILLE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def style() -> str:
    return _sans_commentaires(STYLE.read_text(encoding="utf-8"))


def _executer(script: str) -> dict:
    """Exécute les modules de l'application, hors navigateur."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = (
        f"const regles = await import({json.dumps(REGLES.as_uri())});\n"
        f"const rangement = await import({json.dumps(RANGEMENT.as_uri())});\n"
        f"const carresFr = await import({json.dumps(CARRES_FR.as_uri())});\n"
        f"const matiere = await import({json.dumps(MATIERE.as_uri())});\n"
    )
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


# Les quatre textes portés européens de Jean-Luc Mélenchon et celui de Lydie
# Massard, copiés de leur pivot le 02/10/2026 : seuls les champs que la fiche
# lit sont gardés, et le titre de celui de Massard est abrégé. `dossiers` et
# `documents` sont les entrées des deux index
# pour ces cinq textes, réduites à ce que `themesEuropeens` consulte.
_CORPUS = """
const base = { institution: 'parlement_europeen', nature_texte: 'proposition_de_resolution',
  role: 'auteur_proposition_de_resolution', sort: null, sort_non_resolu: { motif: 'source_sans_sort' } };
const melenchon = [
  { ...base, titre: 'PROPOSITION DE RÉSOLUTION sur la situation en Ukraine',
    reference_dossier: '2014/2717(RSP)', stade_procedural: 'ue_procedure_achevee',
    date_min: '2016-11-22', date_max: '2016-11-22',
    source_url: 'http://www.europarl.europa.eu/doceo/document/B-8-2014-0056_EN.html' },
  { ...base, titre: 'PROPOSITION DE RÉSOLUTION sur la nécessité d’une politique européenne de réindustrialisation à la lumière des récentes affaires Caterpillar et Alstom',
    reference_dossier: '2016/2891(RSP)', stade_procedural: 'ue_procedure_achevee',
    date_min: '2016-11-22', date_max: '2016-11-22',
    source_url: 'http://www.europarl.europa.eu/doceo/document/B-8-2016-1053_EN.html' },
  { ...base, titre: 'PROPOSITION DE RÉSOLUTION sur la crise provoquée par Xylella fastidiosa',
    reference_dossier: '2015/2652(RSP)', stade_procedural: 'ue_procedure_achevee',
    date_min: '2016-11-22', date_max: '2016-11-22',
    source_url: 'http://www.europarl.europa.eu/doceo/document/B-8-2015-0450_EN.html' },
  { ...base, titre: 'PROPOSITION DE RÉSOLUTION sur la conclusion de l’accord économique et commercial global (AECG) entre le Canada, d’une part, et l’Union européenne et ses États membres, d’autre part',
    reference_dossier: '2017/2525(RSP)', stade_procedural: 'ue_procedure_rejetee',
    date_min: '2016-11-22', date_max: '2016-11-22',
    source_url: 'http://www.europarl.europa.eu/doceo/document/B-8-2017-0144_EN.html' },
];
const massard = [
  { ...base, titre: 'PROPOSITION DE RÉSOLUTION sur le règlement délégué de la Commission du 12 mars 2024 modifiant le règlement délégué (UE) 2022/126 de la Commission',
    reference_dossier: null, stade_procedural: null,
    stade_procedural_non_resolu: { motif: 'activite_sans_dossier' },
    date_min: '2024-04-17', date_max: '2024-04-17',
    source_url: 'https://www.europarl.europa.eu/doceo/document/B-9-2024-0220_EN.html' },
];
const dossiers = {
  '2014/2717(RSP)': { type_procedure: 'RSP - Resolutions on topical subjects',
    familles: [{ code: '6', libelle: 'External relations of the Union' }] },
  '2016/2891(RSP)': { type_procedure: 'RSP - Resolutions on topical subjects',
    familles: [{ code: '3', libelle: 'Community policies' },
               { code: '4', libelle: 'Economic, social and territorial cohesion' }] },
  '2015/2652(RSP)': { type_procedure: 'RSP - Resolutions on topical subjects',
    familles: [{ code: '3', libelle: 'Community policies' }] },
  '2017/2525(RSP)': { type_procedure: 'RSP - Resolutions on topical subjects',
    familles: [{ code: '6', libelle: 'External relations of the Union' }] },
};
const agri = { code: '56', libelle: '56 AGRICULTURE, SYLVICULTURE ET PÊCHE' };
const documents = {
  'B-8-2014-0056': { matieres: [] }, 'B-8-2016-1053': { matieres: [] },
  'B-8-2015-0450': { matieres: [] }, 'B-8-2017-0144': { matieres: [] },
  'B-9-2024-0220': { matieres: [
    { code: '4338', domaine: agri }, { code: '4445', domaine: agri }, { code: '2965', domaine: agri },
    { code: '344', domaine: { code: '52', libelle: '52 ENVIRONNEMENT' } },
    { code: '1165', domaine: { code: '40', libelle: '40 ENTREPRISE ET CONCURRENCE' } },
    { code: '2443', domaine: agri },
  ] },
};
const cascadeDe = (textes, dos = dossiers, docs = documents) => regles.textesEuropeens(
  textes, (r) => dos[r] || null, (id) => docs[id] || null).cascade;
// `utils/cascadeTextes.js` ne se charge pas sous node (il importe d3-sankey) :
// la règle de `textesDeLaSelection` est rejouée ici, et un test plus bas
// vérifie dans la source que c'est bien celle-là.
const ouverts = (cascade, sel) => cascade.textes.filter((t, i) => {
  if (sel.texte != null) return i === sel.texte;
  const rang = cascade.stades.indexOf(t.stadeCle);
  return (!sel.matiere || t.themes.includes(sel.matiere)) && rang >= sel.lo && rang <= sel.hi;
});
const forme = (vue) => ({
  textes: vue.textes, carres: vue.carres,
  colonnes: vue.colonnes.map((c) => [c.n, c.libelle]),
  lignes: vue.lignes.map((l) => [l.theme, l.cases.map((cs) => cs.length)]),
});
"""


# ---------------------------------------------------------------------------
# 1. Une ligne par thème, une colonne par étape, un texte répété
# ---------------------------------------------------------------------------


def test_les_quatre_textes_de_melenchon_font_cinq_carres() -> None:
    """Le contrôle chiffré : 4 textes, 5 carrés — le texte sur la
    réindustrialisation relève de deux familles, il est donc sur deux lignes.
    Deux colonnes, les deux seules étapes que la fiche porte."""
    r = _executer(_CORPUS + """
console.log(JSON.stringify(forme(rangement.rangerParTheme(cascadeDe(melenchon)))));
""")
    assert r["textes"] == 4 and r["carres"] == 5
    assert r["colonnes"] == [[3, "procédure achevée"], [1, "procédure rejetée"]]
    assert r["lignes"] == [
        ["External relations of the Union", [1, 1]],
        ["Community policies", [2, 0]],
        ["Economic, social and territorial cohesion", [1, 0]],
    ]


def test_l_en_tete_compte_des_textes_entiers_pas_des_carres() -> None:
    """La colonne « procédure achevée » dessine 4 carrés pour 3 textes : c'est 3
    qu'elle affiche. Additionner les carrés compterait deux fois le texte à deux
    thèmes — et les en-têtes ne feraient plus le total de la fiche."""
    r = _executer(_CORPUS + """
const vue = rangement.rangerParTheme(cascadeDe(melenchon));
console.log(JSON.stringify({
  enTetes: vue.colonnes.map((c) => c.n),
  dessines: vue.colonnes.map((c, k) => vue.lignes.reduce((t, l) => t + l.cases[k].length, 0)),
  textes: vue.textes,
}));
""")
    assert r["enTetes"] == [3, 1] and r["dessines"] == [4, 1]
    assert sum(r["enTetes"]) == r["textes"]


def test_un_seul_texte_dessine_sa_figure() -> None:
    """La cascade renonçait sous un certain nombre de flux, et la liste parlait
    à sa place. Les carrés se dessinent toujours : le texte de Lydie Massard
    touche trois domaines EuroVoc, il fait trois carrés dans une colonne."""
    r = _executer(_CORPUS + """
console.log(JSON.stringify(forme(rangement.rangerParTheme(cascadeDe(massard)))));
""")
    assert r["textes"] == 1 and r["carres"] == 3
    assert r["colonnes"] == [[1, "sans dossier rattaché"]]
    # Trois thèmes à un texte chacun : c'est le poids au prorata qui départage
    # (quatre concepts agricoles sur six), puis l'alphabet.
    assert [ligne[0] for ligne in r["lignes"]] == [
        "Agriculture, sylviculture et pêche", "Entreprise et concurrence", "Environnement",
    ]


def test_les_stades_publies_viennent_avant_les_motifs_d_absence() -> None:
    """`cascade.stades` range les branches basses au rang 0 — c'est l'index de
    la sélection. La grille les montre en dernier, et garde pour chaque colonne
    son rang d'origine : cliquer un en-tête ouvre exactement ses textes.

    Les deux fiches sont réunies ici pour avoir un stade publié ET un motif
    d'absence dans la même figure ; aucun texte n'est modifié."""
    r = _executer(_CORPUS + """
const cascade = cascadeDe([...melenchon, ...massard]);
const vue = rangement.rangerParTheme(cascade);
console.log(JSON.stringify({
  stades: cascade.stades, basses: cascade.basses,
  colonnes: vue.colonnes.map((c) => c.cle),
  rangs: vue.colonnes.map((c) => [c.lo, c.hi]),
  ouverts: vue.colonnes.map((c) => ouverts(cascade, carresFr.selectionDeLEtape(c)).length),
  enTetes: vue.colonnes.map((c) => c.n),
  intitules: vue.colonnes.map((c) => carresFr.selectionDeLEtape(c).intitule),
}));
""")
    assert r["stades"][0] == "activite_sans_dossier" and r["basses"] == ["activite_sans_dossier"]
    assert r["colonnes"] == ["ue_procedure_achevee", "ue_procedure_rejetee", "activite_sans_dossier"]
    assert r["rangs"] == [[1, 1], [2, 2], [0, 0]]
    assert r["ouverts"] == r["enTetes"] == [3, 1, 1]
    assert r["intitules"] == ["procédure achevée", "procédure rejetée", "sans dossier rattaché"]


def test_la_largeur_d_une_colonne_suit_la_racine_du_nombre_de_textes(grille) -> None:
    """`minmax(150px, Nfr)`, N = racine du nombre de textes, comme la maquette :
    250 textes contre 1 feraient sinon une colonne de la largeur d'un carré."""
    r = _executer(_CORPUS + """
const vue = rangement.rangerParTheme(cascadeDe(melenchon));
console.log(JSON.stringify(vue.colonnes.map((c) => c.largeur.toFixed(2))));
""")
    assert r == ["1.73", "1.00"]
    assert "minmax(min(var(--cth-plancher), ${part}), ${col.largeur.toFixed(2)}fr)" in grille
    assert "--cth-plancher: 150px" in STYLE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 2. L'ordre des lignes, et ce qui n'est pas un thème
# ---------------------------------------------------------------------------


def test_matiere_non_etablie_est_la_derniere_ligne_meme_la_plus_fournie() -> None:
    """Ce n'est pas un thème de plus mais une absence de donnée (§2 règle 5).

    Les quatre textes de Mélenchon, dont on RETIRE les deux dossiers à famille
    « External relations » de l'index — le cas réel d'un dossier hors index : la
    matière de ces deux textes n'est plus établie, la ligne en compte autant que
    la première, et elle reste en bas, en gris."""
    r = _executer(_CORPUS + """
const sans = { '2016/2891(RSP)': dossiers['2016/2891(RSP)'], '2015/2652(RSP)': dossiers['2015/2652(RSP)'] };
const vue = rangement.rangerParTheme(cascadeDe(melenchon, sans));
console.log(JSON.stringify({
  lignes: vue.lignes.map((l) => [l.theme, l.cases.flat().length]),
  gris: vue.lignes.at(-1).teinte === matiere.GRIS_SANS_MATIERE,
  nom: regles.MATIERE_NON_ETABLIE,
}));
""")
    assert r["lignes"] == [
        ["Community policies", 2],
        ["Economic, social and territorial cohesion", 1],
        [r["nom"], 2],
    ]
    assert r["gris"]


def test_aucun_compte_par_theme_ne_sort_du_rangement(grille) -> None:
    """Arbitré le 17/09/2026 : le nombre de textes d'un thème classe les lignes
    et n'est rendu nulle part. Une ligne ne porte que son nom, sa teinte et ses
    cases ; le seul nombre que la figure écrit est celui d'une colonne."""
    r = _executer(_CORPUS + """
const vue = rangement.rangerParTheme(cascadeDe(melenchon));
console.log(JSON.stringify(vue.lignes.map((l) => Object.keys(l).sort())));
""")
    assert all(cles == ["cases", "teinte", "theme"] for cles in r)
    assert grille.count("formatNumber(") == 1 and "formatNumber(col.n)" in grille
    nom = grille.split('title={ligne.theme}')[1].split("</button>")[0]
    assert nom.split(">")[1].strip() == "{ligne.theme}", "le nom de la ligne, et rien d'autre"
    assert ".length}" not in grille, "aucune longueur de liste n'est écrite dans la figure"


def test_la_teinte_suit_le_theme_de_la_ligne(grille, style) -> None:
    """`teinteThemeUe(theme)` : un thème garde sa couleur d'une fiche à l'autre,
    et les carrés d'une ligne ont tous la sienne. Aucune couleur n'est écrite
    dans le rangement ni dans le composant, et la feuille n'en tient que l'encre
    et les gris de l'interface."""
    r = _executer(_CORPUS + """
const vue = rangement.rangerParTheme(cascadeDe([...melenchon, ...massard]));
console.log(JSON.stringify({
  lignes: vue.lignes.every((l) => l.teinte === matiere.teinteThemeUe(l.theme)),
  carres: vue.lignes.every((l) => l.cases.flat().every((c) => c.teinte === l.teinte && c.theme === l.theme)),
  palette: matiere.PALETTE_MATIERE,
}));
""")
    assert r["lignes"] and r["carres"]
    rangement = _sans_commentaires(RANGEMENT.read_text(encoding="utf-8"))
    for nom, source in (("carresThemesUe.js", rangement), ("CarresThemesUe.jsx", grille)):
        assert not re.search(r"#[0-9a-fA-F]{6}\b", source), f"une couleur est écrite en dur dans {nom}"
    for teinte in r["palette"]:
        assert teinte.lower() not in style.lower(), f"{teinte} est écrite dans la feuille de la grille"
    assert grille.count("background: c.teinte") == 1 and "color: c.teinte" not in grille


def test_la_figure_n_a_pas_de_legende_de_couleurs(grille) -> None:
    """Chaque ligne porte son nom : une légende redirait la colonne de gauche."""
    assert "cp-car-legende" not in grille and "cp-car-cle" not in grille
    assert "Mention493" not in grille, "le 49.3 est une procédure française"


# ---------------------------------------------------------------------------
# 3. Les trois gestes, un seul état
# ---------------------------------------------------------------------------


def test_un_texte_choisi_allume_toutes_ses_occurrences() -> None:
    """Le texte sur la réindustrialisation a deux carrés. Choisi, les deux
    restent allumés et les trois autres s'estompent ; la liste, elle, l'ouvre
    une seule fois."""
    r = _executer(_CORPUS + """
const cascade = cascadeDe(melenchon);
const vue = rangement.rangerParTheme(cascade);
const tous = vue.lignes.flatMap((l) => l.cases.flat());
const index = cascade.textes.findIndex((t) => t.titre.includes('réindustrialisation'));
const occurrences = tous.filter((c) => c.index === index);
const sel = carresFr.selectionDuCarre(occurrences[0]);
console.log(JSON.stringify({
  occurrences: occurrences.map((c) => c.theme),
  allumes: tous.filter((c) => rangement.carreThemeEclaire(sel, c, cascade)).map((c) => c.index),
  parLAutre: carresFr.memeSelection(sel, carresFr.selectionDuCarre(occurrences[1])),
  liste: ouverts(cascade, sel).map((t) => t.titre.includes('réindustrialisation')),
  index,
}));
""")
    assert r["occurrences"] == ["Community policies", "Economic, social and territorial cohesion"]
    assert r["allumes"] == [r["index"], r["index"]]
    assert r["parLAutre"], "cliquer l'autre occurrence désélectionne : c'est le même texte"
    assert r["liste"] == [True]


def test_un_theme_choisi_ouvre_les_textes_qui_le_touchent() -> None:
    """La sélection par thème lit `t.themes` (#901) : le texte à deux familles
    est dans la liste de l'une comme de l'autre. Sur la figure, seule la ligne
    choisie reste allumée."""
    r = _executer(_CORPUS + """
const cascade = cascadeDe(melenchon);
const vue = rangement.rangerParTheme(cascade);
const tous = vue.lignes.flatMap((l) => l.cases.flat());
const ouvre = (theme) => {
  const sel = rangement.selectionDuTheme(cascade, theme);
  return {
    intitule: sel.intitule,
    liste: ouverts(cascade, sel).length,
    allumes: [...new Set(tous.filter((c) => rangement.carreThemeEclaire(sel, c, cascade)).map((c) => c.theme))],
    carres: tous.filter((c) => rangement.carreThemeEclaire(sel, c, cascade)).length,
  };
};
console.log(JSON.stringify({
  rien: tous.filter((c) => rangement.carreThemeEclaire(null, c, cascade)).length,
  community: ouvre('Community policies'),
  cohesion: ouvre('Economic, social and territorial cohesion'),
  etape: tous.filter((c) => rangement.carreThemeEclaire(carresFr.selectionDeLEtape(vue.colonnes[0]), c, cascade)).length,
}));
""")
    assert r["rien"] == 5
    assert r["community"] == {
        "intitule": "Community policies", "liste": 2, "allumes": ["Community policies"], "carres": 2,
    }
    assert r["cohesion"]["liste"] == 1 and r["cohesion"]["carres"] == 1
    assert r["etape"] == 4, "les quatre carrés de « procédure achevée », sur leurs trois lignes"


def test_la_liste_lit_la_selection_comme_la_figure() -> None:
    """La liste sous la figure est `ListeCascade`, inchangée : elle lit `texte`
    pour un carré, `t.themes` pour un thème, et l'intervalle de crans pour une
    étape. Les tests ci-dessus rejouent cette règle faute de pouvoir charger le
    module sous node ; celui-ci tient la source à ce qu'ils rejouent."""
    source = _sans_commentaires(SELECTION.read_text(encoding="utf-8"))
    corps = source.split("export function textesDeLaSelection(")[1].split("\n}\n")[0]
    assert "if (selection.texte != null) {" in corps
    assert "t.themes ? t.themes.includes(selection.matiere) : t.matiere === selection.matiere" in corps
    assert "rang(t.stadeCle) >= selection.lo && rang(t.stadeCle) <= selection.hi" in corps
    rangement = _sans_commentaires(RANGEMENT.read_text(encoding="utf-8"))
    assert "matiere: theme," in rangement.split("export function selectionDuTheme(")[1].split("\n}\n")[0]


def test_le_survol_nomme_le_texte_ses_themes_son_etape_et_son_annee() -> None:
    """Thèmes · étape · année, et aucun sort : la source européenne n'en publie
    pas. Tous les thèmes y sont — c'est là qu'on lit pourquoi le carré est sur
    trois lignes —, dans l'ordre où la liste sous la figure les écrit déjà."""
    r = _executer(_CORPUS + """
const m = cascadeDe(massard).textes[0];
const c = cascadeDe(melenchon).textes.find((t) => t.titre.includes('AECG'));
console.log(JSON.stringify({ massard: rangement.faitDuTexteUe(m), aecg: rangement.faitDuTexteUe(c), themes: m.themes }));
""")
    assert r["massard"] == (
        "Agriculture, sylviculture et pêche, Environnement, Entreprise et concurrence"
        " · sans dossier rattaché · 2024"
    )
    assert r["aecg"] == "External relations of the Union · procédure rejetée · 2016"
    assert r["massard"].startswith(", ".join(r["themes"]))


def test_le_survol_entoure_toutes_les_occurrences_du_texte(grille, style) -> None:
    """La demande explicite de la propriétaire : c'est par ce contour que la
    répétition se lit. L'entourage compare le RANG DU TEXTE, pas le carré sous
    le pointeur ; il vaut au survol, au focus et tant que le texte est choisi."""
    carre = grille.split("carres.map((c) => {")[1].split("/>")[0]
    assert "choisi || survol?.index === c.index ? 'cp-cth-jumeau' : ''" in carre
    assert "const choisi = selection?.texte === c.index;" in carre
    assert "carreThemeEclaire(selection, c, cascade) ? '' : 'cp-car-voile'" in carre
    regle = re.search(r"\.cp-cth \.cp-cth-jumeau,\s*\.cp-cth \.cp-car-carre:focus-visible\s*\{(.*?)\}", style, re.DOTALL)
    assert regle, "le contour des occurrences a quitté la feuille"
    assert "outline: 2px solid var(--ink, #17141f);" in regle.group(1)
    assert "outline-offset: 1px;" in regle.group(1)


def test_les_carres_sont_des_boutons_nommes(grille) -> None:
    """Atteignables au clavier, lus par leur titre, et l'infobulle s'ouvre aussi
    au focus."""
    carre = grille.split("carres.map((c) => {")[1].split("/>")[0]
    assert "<button" in carre and 'type="button"' in carre
    assert "aria-label={c.texte.titre}" in carre
    assert "aria-pressed={choisi}" in carre
    for geste in ("onFocus=", "onBlur=", "onMouseEnter=", "onMouseLeave=", "onClick="):
        assert geste in carre
    assert 'className="cp-car-bulle"' in grille and 'role="tooltip"' in grille
    assert "{faitDuTexteUe(survole)}" in grille


def test_l_en_tete_et_le_nom_de_ligne_sont_des_boutons(grille) -> None:
    """Les deux autres gestes. L'en-tête garde la forme de celui des carrés
    français — filet d'encre, nombre, libellé — et le nom garde son intitulé
    entier dans `title`, l'ellipse pouvant le couper."""
    assert 'className="cp-car-tete cp-car-tete--cliquable"' in grille
    assert "aria-pressed={memeSelection(selection, selectionDeLEtape(col))}" in grille
    assert '<span className="cp-car-n cp-num">{formatNumber(col.n)}</span>' in grille
    assert '<span className="cp-car-lib">{col.libelle}</span>' in grille
    assert "title={ligne.theme}" in grille and "aria-pressed={choisie}" in grille
    assert "onClick={() => choisir(sel)}" in grille


# ---------------------------------------------------------------------------
# 4. La forme : un carré de 12 px, et l'écran étroit
# ---------------------------------------------------------------------------


def test_les_carres_ont_tous_la_meme_taille(grille, style) -> None:
    """12 px, rayon 2 px, écart 2 px. Une taille qui varierait se lirait comme
    une importance (§2 règle 1) — la maquette avait essayé un carré « partagé »
    plus petit, et il n'a pas été retenu."""
    regle = re.search(r"\.cp-cth \.cp-car-carre \{(.*?)\}", style, re.DOTALL).group(1)
    assert "width: 12px;" in regle and "height: 12px;" in regle and "border-radius: 2px;" in regle
    case = re.search(r"\.cp-cth-case \{(.*?)\}", style, re.DOTALL).group(1)
    assert "gap: 2px;" in case and "flex-wrap: wrap;" in case
    assert "width:" not in grille and "height:" not in grille, "aucune taille n'est posée carré par carré"


def test_le_nom_du_theme_est_gris_cale_a_droite_et_tronque(style) -> None:
    regle = re.search(r"\.cp-cth-nom \{(.*?)\}", style, re.DOTALL).group(1)
    for declaration in ("text-align: right;", "white-space: nowrap;", "overflow: hidden;", "text-overflow: ellipsis;"):
        assert declaration in regle


def test_sous_560_px_le_nom_passe_au_dessus_de_ses_cases(style) -> None:
    """210 px de noms ne laisseraient rien aux colonnes. Et la page ne défile
    jamais horizontalement : le plancher d'une colonne est borné par la part que
    la grille peut donner (`min(…)`), à toutes les largeurs."""
    etroit = style.split("@media (max-width: 560px)")[1]
    nom = re.search(r"\.cp-cth-nom \{(.*?)\}", etroit, re.DOTALL).group(1)
    assert "grid-column: 1 / -1;" in nom and "white-space: normal;" in nom
    grille_etroite = re.search(r"\.cp-cth-grille \{(.*?)\}", etroit, re.DOTALL).group(1)
    assert "grid-template-columns: var(--cth-cols);" in grille_etroite
    assert "--cth-nom: 0px;" in grille_etroite
    composant = _sans_commentaires(GRILLE.read_text(encoding="utf-8"))
    assert "max(0px, calc((100% - var(--cth-nom) - ${n} * var(--cth-ecart)) / ${n}))" in composant
    assert "overflow-x" not in style, "la figure ne défile pas non plus : l'infobulle y serait rognée"


# ---------------------------------------------------------------------------
# 5. La fiche : quelle figure pour quel versant, et aucun texte nouveau
# ---------------------------------------------------------------------------


def test_la_fiche_candidat_dessine_la_grille_sur_le_versant_europeen(fiche) -> None:
    bloc = fiche.split("function Propositions(")[1]
    choix = re.search(r"\{ue \? \(\s*<CarresThemesUe (.*?)/>\s*\) : \(\s*<CarresTextes ", bloc, re.DOTALL)
    assert choix, "le versant européen prend `<CarresThemesUe>`, le versant français `<CarresTextes>`"
    assert "cascade={cascade}" in choix.group(1), "la figure reçoit la cascade de la nature choisie"
    assert "onSelection={setSelTexte}" in choix.group(1) and "selection={selTexte}" in choix.group(1)
    assert "<Cascade" not in fiche, "les rubans ont quitté la fiche candidat"
    # Les puces de nature filtrent toujours : `cascade` reste celle de la nature.
    assert "filtreNature && nature !== 'tous' ? europe.parNature[nature].cascade : europe.cascade" in bloc


def test_la_branche_figure_non_dessinee_est_partie_avec_les_rubans(fiche) -> None:
    """Un seul texte fait un carré. Sous un mot de recherche, la liste montre
    toujours tout (#979)."""
    assert "const toutVoir = cascade && actif;" in fiche
    assert "cascadeDessinee" not in fiche and "disposerCascadeUE" not in fiche
    assert "selTexte ?? (toutVoir ? selectionDeTousLesTextes(cascade) : null)" in fiche


def test_la_fiche_de_lignee_garde_sa_cascade() -> None:
    """Ce lot ne couvre que la fiche candidat."""
    lignee = _sans_commentaires(LIGNEE.read_text(encoding="utf-8"))
    assert "<Cascade " in lignee
    assert "CarresThemesUe" not in lignee and "CarresTextes" not in lignee


def test_la_figure_n_ecrit_aucun_texte_et_la_liste_ne_parle_plus_de_rubans(fiche, grille) -> None:
    """Le composant n'écrit que ce que la donnée porte — un titre, un libellé
    d'étape, un nom de thème —, et la mention des textes en phase préparatoire
    reste telle quelle.

    UNE PHRASE, UNE SEULE, EST ENTRÉE AVEC LES CARRÉS : l'invitation de la
    liste. Sans elle, `ListeCascade` écrit son défaut — « Cliquez un ruban, une
    barre ou une étiquette… » —, faux sous une figure qui n'a plus de ruban.
    Elle reprend celle du versant français, « thème » à la place de
    « commission »."""
    assert "? 'Cliquez un carré, une étape ou un thème pour lire les textes.'" in fiche
    assert ": 'Cliquez un carré, une étape ou une commission pour lire les textes.'}" in fiche
    assert "préparatoire au Parlement, que la fiche ne publie pas." in fiche
    rendu = grille.split("  return (\n    <div className=\"cp-car cp-cth\"")[1]
    textes = [t.strip() for t in re.findall(r">([^<>{}]+)<", rendu) if re.search(r"[A-Za-zÀ-ÿ]", t)]
    assert textes == [], f"un texte est écrit en dur dans la figure : {textes}"
    for a, b in re.findall(r"'([^'\n]*)'|\"([^\"\n]*)\"", grille):
        litteral = a or b
        if " " in litteral:
            assert all(mot.startswith("cp-") for mot in litteral.split()), (
                f"une phrase est écrite dans le composant : « {litteral} »"
            )
    for attribut in ("aria-label={c.texte.titre}", "title={ligne.theme}"):
        assert attribut in grille
    assert len(re.findall(r"aria-label=|title=|placeholder=|alt=", grille)) == 2
