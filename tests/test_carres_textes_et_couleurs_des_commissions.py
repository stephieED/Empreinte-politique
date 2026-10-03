"""« Ce qu'il a proposé » : un carré par texte, une barre découpée, une couleur fixe.

Arrêté le 01/10/2026 avec la propriétaire, sur maquette, pour la fiche candidat :

1. **Les textes portés à l'Assemblée se lisent en carrés** — un par texte, rangé à
   l'étape la plus avancée qu'il a atteinte, dans quatre colonnes qui restent
   toutes affichées. La cascade en rubans reste la figure de la fiche de groupe.
   Le versant européen l'a gardée jusqu'au 02/10/2026, puis a pris sa propre
   grille — une ligne par thème, sans ordre entre ses colonnes, ses seize stades
   ne s'ordonnant pas (#901) : `tests/test_carres_themes_ue_fiche_candidat.py`.
2. **La barre des amendements est découpée par texte**, et la colonne « ratio
   par texte » disparaît avec sa seconde barre : le rapport se lit dans la
   barre, aucun quotient n'est publié.
3. **Une couleur fixe par commission permanente**, la même dans les deux cartes
   et sur toutes les fiches. Elle suivait le rang : « Affaires sociales » était
   indigo sur les textes portés de François Ruffin et bleu clair sur ses
   amendements.

CE QUE CES GARDE-FOUS PROTÈGENT est éditorial avant d'être graphique : une
colonne est une étape ATTEINTE, jamais un sort ; un sort absent reste absent
(§2 règle 5) ; aucun taux n'entre dans la section (§6) ; la couleur ne porte
jamais seule l'identité d'une commission.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu, et aucun test ne lit `pivot_data/` — les six textes ci-dessous
sont COPIÉS de la fiche de François Ruffin au 01/10/2026, avec la commission que
`commissions_dossiers.json` donnait à chacun ce jour-là. La séparation des
teintes sous daltonisme n'est pas rejouée non plus : elle a été calculée par
`validate_palette.js` (compétence `dataviz`), et le verdict est consigné dans
`docs/decisions/carres-des-textes-et-couleurs-des-commissions.md`. Le rendu —
survol, clic, clavier, téléphone — se vérifie à l'écran.
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
RANGEMENT = UI / "utils" / "carresTextes.js"
COMMISSIONS = UI / "utils" / "commissions.js"
REGLES = UI / "utils" / "profilCandidat.js"
SELECTION = UI / "utils" / "cascadeTextes.js"
FICHE = UI / "components" / "CandidateProfile.jsx"
CARRES = UI / "components" / "CarresTextes.jsx"
STYLE_CARRES = UI / "components" / "CarresTextes.css"
CASCADE = UI / "components" / "CascadeTextes.jsx"
LIGNEE = UI / "components" / "LigneeProfile.jsx"

PERMANENTES = {
    "Affaires culturelles et éducation",
    "Affaires économiques",
    "Affaires étrangères",
    "Affaires sociales",
    "Défense",
    "Développement durable",
    "Finances",
    "Lois",
}


def _sans_commentaires(source: str) -> str:
    """Une règle citée en commentaire n'est pas une règle appliquée."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def fiche() -> str:
    return _sans_commentaires(FICHE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def carres() -> str:
    return _sans_commentaires(CARRES.read_text(encoding="utf-8"))


def _executer(script: str) -> dict:
    """Exécute les modules de l'application, hors navigateur."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = (
        f"const regles = await import({json.dumps(REGLES.as_uri())});\n"
        f"const rangement = await import({json.dumps(RANGEMENT.as_uri())});\n"
        f"const commissions = await import({json.dumps(COMMISSIONS.as_uri())});\n"
    )
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


# Les six textes portés publiés de François Ruffin, copiés du pivot le
# 01/10/2026 (titres abrégés), et la commission saisie au fond de leur dossier.
_SIX_TEXTES = """
const textes = [
  { titre: 'Accord UE-Mercosur : saisine de la Cour de justice', dossier_id: 'DLR5L17N52728',
    role: 'auteur_proposition_de_resolution', nature_texte: 'proposition_de_resolution',
    stade_procedural: 'discute_seance', sort: null, sort_non_resolu: { motif: 'fam_code_inconnu' },
    date_min: '2025-09-15', date_max: '2026-01-05', legislature: '17' },
  { titre: 'Projet de loi de financement de la sécurité sociale pour 2024', dossier_id: 'DLR5L16N48683',
    role: 'co-rapporteur', nature_texte: 'projet_de_loi', stade_procedural: 'promulgue',
    sort: 'adopte_49_3', sort_non_resolu: null, date_min: '2023-07-05', date_max: '2023-12-26', legislature: '16' },
  { titre: 'Revenu de solidarité active pour les jeunes de 18 à 25 ans', dossier_id: 'DLR5L15N42028',
    role: 'auteur_proposition_de_loi', nature_texte: 'proposition_de_loi', stade_procedural: 'discute_seance',
    sort: 'rejete', sort_non_resolu: null, date_min: '2021-03-23', date_max: '2021-05-06', legislature: '15' },
  { titre: 'Femmes de ménage : encadrer la sous-traitance', dossier_id: 'DLR5L15N39668',
    role: 'auteur_proposition_de_loi', nature_texte: 'proposition_de_loi', stade_procedural: 'examine_commission',
    sort: 'navette_en_cours', sort_non_resolu: null, date_min: '2020-05-12', date_max: '2020-05-27', legislature: '15' },
  { titre: 'Interdiction des techniques d’immobilisation létales', dossier_id: 'DLR5L15N38487',
    role: 'auteur_proposition_de_loi', nature_texte: 'proposition_de_loi', stade_procedural: 'examine_commission',
    sort: 'navette_en_cours', sort_non_resolu: null, date_min: '2020-01-21', date_max: '2020-03-04', legislature: '15' },
  { titre: 'Reconnaissance de l’épuisement professionnel comme maladie', dossier_id: 'DLR5L15N36227',
    role: 'auteur_proposition_de_loi', nature_texte: 'proposition_de_loi', stade_procedural: 'discute_seance',
    sort: 'navette_en_cours', sort_non_resolu: null, date_min: '2017-12-20', date_max: '2018-02-01', legislature: '15' },
];
const table = {
  DLR5L16N48683: { sigle: 'Affaires sociales', nom: 'Commission des affaires sociales' },
  DLR5L15N42028: { sigle: 'Affaires sociales', nom: 'Commission des affaires sociales' },
  DLR5L15N39668: { sigle: 'Affaires sociales', nom: 'Commission des affaires sociales' },
  DLR5L15N36227: { sigle: 'Affaires sociales', nom: 'Commission des affaires sociales' },
  DLR5L15N38487: { sigle: 'Lois', nom: 'Commission des lois' },
};
const cascade = regles.textesPortes(textes, (id) => table[id] || null).cascade;
const vue = rangement.rangerEnCarres(cascade);
"""


# ---------------------------------------------------------------------------
# 1. Un carré par texte, quatre colonnes, et l'étape atteinte
# ---------------------------------------------------------------------------


def test_les_six_textes_de_ruffin_se_rangent_2_3_0_1() -> None:
    """Le contrôle chiffré de la maquette validée : 2 examinés en commission,
    3 discutés en séance, 0 adopté, 1 promulgué — et une colonne à zéro reste
    affichée, sans quoi « promulgué » se lirait comme l'étape qui suit « discuté
    en séance »."""
    r = _executer(_SIX_TEXTES + """
console.log(JSON.stringify({
  colonnes: vue.colonnes.map((c) => [c.n, c.libelle]),
  total: vue.total,
  carres: vue.colonnes.reduce((s, c) => s + c.carres.length, 0),
}));
""")
    assert r["colonnes"] == [
        [2, "examinés en commission"],
        [3, "discutés en séance"],
        [0, "adopté"],
        [1, "promulgué"],
    ]
    assert r["total"] == 6 and r["carres"] == 6, "un carré par texte, ni plus ni moins"


def test_la_legende_ne_porte_que_les_commissions_presentes() -> None:
    """Affaires sociales 4, Lois 1, Matière non établie 1 — dans l'ordre de la
    légende, les deux gris en dernier. Dix entrées pour trois teintes dessinées
    feraient chercher sept couleurs qui ne sont pas là."""
    r = _executer(_SIX_TEXTES + """
console.log(JSON.stringify(vue.legende.map((l) => [l.famille, l.n])));
""")
    assert r == [["Affaires sociales", 4], ["Lois", 1], ["Matière non établie", 1]]


def test_un_texte_inscrit_a_l_ordre_du_jour_se_range_avec_la_commission() -> None:
    """Il a passé la commission et n'a pas été discuté : une cinquième colonne
    resterait vide sur presque toutes les fiches. Le texte, lui, garde son vrai
    stade au survol et dans la liste.

    L'entrée est le premier texte de la fixture, dont SEUL le stade est changé :
    aucun texte du corpus ne s'arrêtait à ce cran le 01/10/2026."""
    r = _executer(_SIX_TEXTES + """
const avec = textes.map((t, i) => (i === 3 ? { ...t, stade_procedural: 'inscrit_ordre_jour' } : t));
const c2 = regles.textesPortes(avec, (id) => table[id] || null).cascade;
const v2 = rangement.rangerEnCarres(c2);
const col = v2.colonnes[0];
const inscrit = col.carres.find((q) => q.texte.stadeCle === 'inscrit_ordre_jour');
console.log(JSON.stringify({
  n: col.n, crans: [col.lo, col.hi], stades: c2.stades,
  fait: rangement.faitDuTexte(inscrit.texte),
}));
""")
    assert r["n"] == 2
    assert r["stades"][r["crans"][0]] == "examine_commission"
    assert r["stades"][r["crans"][1]] == "inscrit_ordre_jour"
    assert "inscrit à l'ordre du jour" in r["fait"]


def test_chaque_geste_eclaire_ce_qu_il_ouvre() -> None:
    """Un carré, une étape, une commission : ce qui reste allumé est exactement
    ce que la sélection désigne. Et le 49.3 laisse la figure intacte — il filtre
    la liste, comme sur la cascade."""
    r = _executer(_SIX_TEXTES + """
const tous = vue.colonnes.flatMap((c) => c.carres);
const allumes = (sel) => tous.filter((q) => rangement.carreEclaire(sel, q, cascade)).length;
console.log(JSON.stringify({
  rien: allumes(null),
  carre: allumes(rangement.selectionDuCarre(tous[0])),
  seance: allumes(rangement.selectionDeLEtape(vue.colonnes[1])),
  sociales: allumes(rangement.selectionDeLaFamille(cascade, 'Affaires sociales')),
  article493: allumes({ procedure493: true }),
  bascule: rangement.memeSelection(
    rangement.selectionDuCarre(tous[0]), rangement.selectionDuCarre(tous[0])),
  autre: rangement.memeSelection(
    rangement.selectionDuCarre(tous[0]), rangement.selectionDuCarre(tous[1])),
}));
""")
    assert r == {
        "rien": 6, "carre": 1, "seance": 3, "sociales": 4, "article493": 6,
        "bascule": True, "autre": False,
    }


def test_un_sort_absent_se_dit_absent_au_survol() -> None:
    """Le texte sur le Mercosur n'a pas de sort résolu : l'infobulle l'écrit, et
    n'en invente aucun (§2 règle 5). Sa matière non plus ne se déduit pas de
    l'intitulé."""
    r = _executer(_SIX_TEXTES + """
const t = cascade.textes.find((x) => x.titre.startsWith('Accord UE-Mercosur'));
const plfss = cascade.textes.find((x) => x.titre.startsWith('Projet de loi de financement'));
console.log(JSON.stringify({ sans: rangement.faitDuTexte(t), avec: rangement.faitDuTexte(plfss) }));
""")
    assert r["sans"] == "Matière non établie · discuté en séance · Sort non résolu · 2026"
    assert r["avec"] == "Affaires sociales · promulgué · Adopté via 49.3 · 2023"


def test_la_figure_ne_nomme_aucun_sort_d_elle_meme() -> None:
    """Une colonne est une étape atteinte. « Rejeté » ou « abandonné » en
    libellé de colonne publierait un sort que le stade n'établit pas — le sort
    vient de `LIBELLE_SORT_TEXTE`, texte par texte, ou pas du tout."""
    for source in (RANGEMENT, CARRES):
        code = _sans_commentaires(source.read_text(encoding="utf-8")).lower()
        for mot in ("rejeté", "rejete", "abandonn", "échec", "echec"):
            assert mot not in code, f"« {mot} » est écrit en dur dans {source.name}"


# ---------------------------------------------------------------------------
# 2. Les deux figures de la section, et qui garde la cascade
# ---------------------------------------------------------------------------


def test_les_carres_sont_la_figure_francaise_le_versant_europeen_a_la_sienne(fiche) -> None:
    """Les seize stades européens ne s'ordonnent pas (#901) : quatre colonnes
    « dans l'ordre de la procédure » leur prêteraient une échelle. Le
    commutateur de versant choisit donc la figure.

    Le versant européen gardait la cascade en rubans ; depuis le 02/10/2026 il a
    sa grille par thème (`CarresThemesUe`), et `CarresTextes` reste la figure
    française, elle seule."""
    bloc = fiche.split("function Propositions(")[1]
    choix = re.search(r"\{ue \? \(\s*<CarresThemesUe (.*?)\) : \(\s*<CarresTextes ", bloc, re.DOTALL)
    assert choix, "le versant européen prend `<CarresThemesUe>`, le versant français `<CarresTextes>`"
    assert "<Cascade" not in bloc, "les rubans ont quitté la fiche candidat"


def test_la_fiche_de_groupe_garde_la_cascade() -> None:
    """Ce lot ne couvre que la fiche candidat."""
    lignee = _sans_commentaires(LIGNEE.read_text(encoding="utf-8"))
    assert "<Cascade " in lignee and "CarresTextes" not in lignee


def test_l_invitation_est_celle_qui_a_ete_validee(fiche) -> None:
    """Le texte est arrêté au mot près, et il nomme les trois gestes."""
    assert "Cliquez un carré, une étape ou une commission pour lire les textes." in fiche
    cascade = CASCADE.read_text(encoding="utf-8")
    assert "Cliquez un ruban, une barre ou une étiquette pour lire ce qui la compose." in cascade, (
        "la cascade, elle, parle toujours de rubans : sa phrase reste la sienne"
    )


def test_la_mention_49_3_est_la_meme_sous_les_deux_figures(carres) -> None:
    """Recopiée, elle aurait divergé au premier correctif : un seul composant."""
    cascade = _sans_commentaires(CASCADE.read_text(encoding="utf-8"))
    assert "export function Mention493(" in cascade
    assert cascade.count('className="cp-ter-493-bouton"') == 1
    assert "<Mention493 " in carres
    corps = cascade.split("export function Cascade(")[1].split("export function Mention493(")[0]
    assert "<Mention493 " in corps


def test_les_carres_sont_des_boutons_nommes(carres) -> None:
    """Atteignables au clavier, et lus par leur titre : un carré sans nom serait
    six fois « bouton » à la suite."""
    carre = carres.split("col.carres.map(")[1].split("/>")[0]
    assert "<button" in carre and 'type="button"' in carre
    assert "aria-label={c.texte.titre}" in carre
    assert "aria-pressed={choisi}" in carre
    assert "onFocus=" in carre and "onBlur=" in carre, "l'infobulle s'ouvre aussi au clavier"


def test_la_selection_d_un_carre_ouvre_ce_texte_seul() -> None:
    """La liste est celle de la cascade : elle apprend deux clés, pas une
    seconde façon d'écrire un texte."""
    selection = _sans_commentaires(SELECTION.read_text(encoding="utf-8"))
    corps = selection.split("export function textesDeLaSelection(")[1].split("\n}\n")[0]
    assert "selection.texte != null" in corps
    assert "familleDeCommission(t.matiere) === selection.famille" in corps


# ---------------------------------------------------------------------------
# 3. Les amendements : la barre découpée, et plus aucun quotient
# ---------------------------------------------------------------------------


def test_le_ratio_par_texte_a_quitte_la_carte(fiche) -> None:
    """La colonne et sa seconde barre sont parties : 2 553 amendements sur 2
    textes y faisaient « 1 277 par texte », quand l'un en a reçu 2 471 et
    l'autre 82. Aucun quotient ne les remplace."""
    bloc = fiche.split("function Matieres(")[1].split("\n}\n")[0]
    assert "ratio par texte" not in fiche
    assert not re.search(r"\.amdt\s*/\s*\w+\.textes", bloc), (
        "un rapport amendements / textes est revenu dans la carte"
    )
    entetes = re.findall(r'<span className="cp-mr-n">([^<{]+)</span>', bloc)
    assert entetes == ["amendements", "textes distincts"]


def test_la_barre_ne_se_decoupe_que_si_les_segments_font_le_total(fiche) -> None:
    """La ligne compte les dépôts datés, `dossiersParMatiere` ceux qui ont un
    dossier. Quand les deux sommes diffèrent, découper la barre lui ferait dire
    une répartition que la donnée ne porte pas (§2 règle 5)."""
    bloc = fiche.split("function segmentsParTexte(")[1].split("\n}\n")[0]
    assert "dossiersParMatiere" in bloc
    assert "=== total ? parTexte : null" in bloc
    assert ".sort((a, b) => b - a)" in bloc, "du plus grand segment au plus petit"


def test_aucun_taux_n_entre_dans_la_section(fiche, carres) -> None:
    """§6 : jamais de taux d'adoption. Les comptes bruts restent."""
    bloc = fiche.split("function segmentsParTexte(")[1].split("function Propositions(")[0]
    for source in (bloc, carres, _sans_commentaires(RANGEMENT.read_text(encoding="utf-8"))):
        # Le mot entier : `totauxDepots` est un total, pas un taux.
        assert not re.search(r"\btaux\b", source.lower())
        assert not re.search(r"adoptes\s*/|/\s*\w*\.?adoptes", source)


# ---------------------------------------------------------------------------
# 4. Une couleur fixe par commission permanente
# ---------------------------------------------------------------------------


def _teintes() -> dict:
    return _executer("""
console.log(JSON.stringify({
  permanentes: commissions.TEINTE_COMMISSION_PERMANENTE,
  speciales: commissions.GRIS_COMMISSIONS_SPECIALES,
  nonEtablie: commissions.GRIS_MATIERE_NON_ETABLIE,
  ordre: commissions.ORDRE_DES_FAMILLES,
  retraite: [commissions.familleDeCommission('Commission spéciale retraite'),
             commissions.teinteCommission('Commission spéciale retraite')],
  finDeVie: commissions.teinteCommission('CS Fin de vie'),
  absente: [commissions.familleDeCommission(null), commissions.teinteCommission(null)],
  nd: [commissions.familleDeCommission(regles.MATIERE_NON_ETABLIE),
       commissions.teinteCommission(regles.MATIERE_NON_ETABLIE)],
  lois: commissions.teinteCommission('Lois'),
}));
""")


def test_les_huit_commissions_permanentes_ont_chacune_leur_teinte() -> None:
    t = _teintes()
    assert set(t["permanentes"]) == PERMANENTES
    valeurs = [v.lower() for v in t["permanentes"].values()]
    assert len(set(valeurs)) == 8, "deux commissions partagent une teinte"
    assert all(re.fullmatch(r"#[0-9a-f]{6}", v) for v in valeurs)
    assert t["lois"] == t["permanentes"]["Lois"]


def test_les_commissions_speciales_partagent_un_gris_et_l_absence_un_autre() -> None:
    """Une commission spéciale naît et meurt avec son texte : lui donner une
    couleur ouvrirait une palette sans fin. « Matière non établie » n'est pas
    une matière de plus mais une absence de donnée (§2 règle 5)."""
    t = _teintes()
    assert t["retraite"] == ["Commissions spéciales", t["speciales"]]
    assert t["finDeVie"] == t["speciales"]
    assert t["nd"] == ["Matière non établie", t["nonEtablie"]]
    assert t["absente"] == ["Matière non établie", t["nonEtablie"]]
    assert t["speciales"] != t["nonEtablie"]
    # L'ordre de la légende : alphabétique, puis les deux gris. Jamais le volume,
    # qui changerait d'une fiche à l'autre.
    assert t["ordre"] == [
        "Affaires culturelles et éducation", "Affaires économiques", "Affaires étrangères",
        "Affaires sociales", "Défense", "Développement durable", "Finances", "Lois",
        "Commissions spéciales", "Matière non établie",
    ]
    for gris in (t["speciales"], t["nonEtablie"]):
        r, v, b = (int(gris[i:i + 2], 16) for i in (1, 3, 5))
        assert max(r, v, b) - min(r, v, b) <= 12, f"{gris} n'est pas un gris"


def _luminance(couleur: str) -> float:
    def canal(c: int) -> float:
        x = c / 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, v, b = (canal(int(couleur[i:i + 2], 16)) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * v + 0.0722 * b


def test_chaque_teinte_se_detache_du_blanc_de_la_carte() -> None:
    """3:1 contre `#ffffff`, le seuil d'un élément graphique (WCAG 1.4.11). Les
    huit le passent ; le gris clair de « Matière non établie » ne le peut pas
    sans cesser d'être clair — il est nommé dans la légende et au survol."""
    t = _teintes()
    for nom, teinte in t["permanentes"].items():
        contraste = 1.05 / (_luminance(teinte) + 0.05)
        assert contraste >= 3, f"{nom} ({teinte}) : {contraste:.2f}:1 contre le blanc"
    assert 1.05 / (_luminance(t["speciales"]) + 0.05) >= 3


def test_les_deux_cartes_lisent_la_meme_table(fiche) -> None:
    """C'est tout l'objet : une commission, une couleur, dans les deux cartes."""
    rangement = _sans_commentaires(RANGEMENT.read_text(encoding="utf-8"))
    assert "from './commissions.js'" in rangement and "teinteDeLaFamille(" in rangement
    matieres = fiche.split("function Matieres(")[1].split("\n}\n")[0]
    assert "teinteCommission(x.m)" in matieres
    carres = _sans_commentaires(CARRES.read_text(encoding="utf-8"))
    for nom, source in (("carresTextes.js", rangement), ("CarresTextes.jsx", carres), ("Matieres", matieres)):
        assert not re.search(r"#[0-9a-fA-F]{6}\b", source), (
            f"une couleur est écrite en dur dans {nom} : elles vivent dans `utils/commissions.js`"
        )


def test_aucun_texte_ne_prend_la_couleur_d_une_commission() -> None:
    """Encre et gris seulement : la teinte est portée par le carré et par la
    pastille de légende, jamais par un mot."""
    t = _teintes()
    palette = {v.lower() for v in t["permanentes"].values()}
    style = STYLE_CARRES.read_text(encoding="utf-8").lower()
    for teinte in palette:
        assert teinte not in style, f"{teinte} est écrite dans la feuille de style des carrés"
    carres = _sans_commentaires(CARRES.read_text(encoding="utf-8"))
    assert "color: c.teinte" not in carres and "color: l.teinte" not in carres
    assert carres.count("background: c.teinte") == 1 and carres.count("background: l.teinte") == 1
