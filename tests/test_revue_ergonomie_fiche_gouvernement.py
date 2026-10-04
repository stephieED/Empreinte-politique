"""La revue d'ergonomie de la fiche de gouvernement (04/10/2026).

Troisième volet de la revue des fiches, après la fiche candidat et la fiche de
groupe. Tout a été arbitré sur maquette par la propriétaire avant d'être codé :
`docs/decisions/revue-ux-de-la-fiche-de-gouvernement.md`.

Les textes des bulles sont recopiés ici mot pour mot : une reformulation
« pour améliorer » doit échouer.
"""
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
UI = RACINE / "web" / "UI_finale"
FICHE = UI / "src" / "components" / "GovernmentProfile.jsx"
STYLE = UI / "src" / "components" / "GovernmentProfile.css"
ACTES = UI / "src" / "components" / "ActesDuGouvernement.jsx"
REGLES = UI / "src" / "utils" / "gouvernement.js"
PROJECTION = UI / "scripts" / "vue-parole-gouvernement.mjs"
METHODO = UI / "src" / "pages" / "MethodologyPage.jsx"

BULLES = {
    "enBref": (
        "Le gouvernement en quelques faits.",
        "Note : Le nombre de membres varie au fil des remaniements.",
    ),
    "composition": (
        "Les ministres, ministres délégués et secrétaires d’État de ce gouvernement, par ministère.",
        "Note : Sont comptés tous les membres passés par ce gouvernement, même brièvement.",
    ),
    "paroles": (
        "Les prises de parole des membres du gouvernement à l’Assemblée, par débat.",
        "Note : Une prise de parole peut tenir en quelques mots.",
    ),
    "textes": (
        "Les projets de loi que ce gouvernement a présentés au Parlement, et jusqu’où chacun est allé.",
        "Note : Un texte arrêté à une étape n’est pas nécessairement rejeté. Le 49.3 est un fait de procédure, jamais un vote.",
    ),
    "actes": (
        "Les décrets, arrêtés et ordonnances parus au Journal officiel pendant ce gouvernement, par ministère.",
        "Note : Seuls les actes qui touchent au droit sont pris en compte et non ceux qui relèvent du fonctionnement interne de l’État (nominations, promotions…). Un acte peut appliquer une loi adoptée avant ce gouvernement.",
    ),
    "couverture": (
        "Les limites de cette fiche : ce que les sources ne disent pas sur ce gouvernement.",
        "Note : Une information absente de cette fiche n’a pas été trouvée dans les sources. Cela ne veut pas dire qu’il ne s’est rien passé.",
    ),
}


def _sans_commentaires(texte: str) -> str:
    texte = re.sub(r"/\*.*?\*/", "", texte, flags=re.S)
    return re.sub(r"^\s*//.*$", "", texte, flags=re.M)


def _fiche() -> str:
    return FICHE.read_text(encoding="utf-8")


# ── 1. Les bulles ────────────────────────────────────────────────────────────


def test_les_six_bulles_sont_celles_qu_elle_a_ecrites() -> None:
    fiche = _fiche()
    bloc = fiche.split("export const BULLES = {")[1].split("\n};\n")[0]
    for cle, (phrase, note) in BULLES.items():
        entree = bloc.split(f"  {cle}: {{")[1].split("\n  },")[0]
        assert f"phrase: '{phrase}'," in entree, cle
        assert f"note: '{note}'," in entree, cle
        assert "libelle: LIRE_LA_METHODE" in entree, cle


def test_en_bref_dit_pourquoi_aucun_groupe_n_est_declare_majoritaire() -> None:
    """La phrase s'ajoute à la note, au mot près, quand la fiche écrit « aucun groupe déclaré majoritaire »."""
    fiche = _fiche()
    assert "'L’Assemblée nationale ne dit quel groupe est majoritaire qu’une fois la législature achevée.'" in fiche
    assert "government.majorite.some((m) => !m.declaree)" in fiche
    assert "`${BULLES.enBref.note} ${NOTE_MAJORITE_NON_DITE}`" in fiche


def test_chaque_bulle_mene_a_une_section_de_methodologie_qui_existe() -> None:
    ancres = set(re.findall(r"/methodologie#([a-z-]+)", _fiche()))
    ids = set(re.findall(r"id: '([a-z-]+)'", METHODO.read_text(encoding="utf-8")))
    assert {"gouv-composition", "gouv-paroles", "gouv-textes", "gouv-actes"} <= ancres
    assert ancres <= ids, f"ancres absentes de la méthodologie : {ancres - ids}"


def test_plus_aucun_renvoi_en_pied_de_section() -> None:
    """Les quatre renvois d'avant vivent dans les bulles."""
    assert "gvp-methodo" not in _sans_commentaires(_fiche())


# ── 2. Qui le composait ──────────────────────────────────────────────────────


def test_une_premiere_ministre_n_a_qu_une_carte() -> None:
    """Sous Borne, la clé « premiere ministre » n'était pas reconnue : une carte
    de secours « Premier ministre » s'ajoutait, et la vraie restait parmi les
    ministères avec ses neuf rattachés."""
    regles = REGLES.read_text(encoding="utf-8")
    assert "new Set(['premier ministre', 'premiere ministre'])" in regles
    assert "CLES_PREMIER_MINISTRE.has(p.cle)" in regles


def test_le_liseré_la_fleche_et_le_lien_sont_au_neutre() -> None:
    """Une couleur qui ne distingue rien se retire (DESIGN_SYSTEM §6 bis, règle 11)."""
    style = STYLE.read_text(encoding="utf-8")

    def regle(selecteur: str) -> str:
        bloc = style[style.index(selecteur) :]
        return bloc[: bloc.index("}")]

    assert "border-top: 2px solid var(--ink);" in regle(".gvp-pole {")
    assert "var(--gouv)" not in regle(".gvp-passation {")
    assert "var(--gouv)" not in regle(".gvp-bascule {")
    assert "var(--gouv)" not in regle(".gvp-intervention-qualite {")


def test_ce_qui_s_ouvre_se_replie_au_clic_ailleurs() -> None:
    fiche = _sans_commentaires(_fiche())
    assert fiche.count("useReplieAuClicDehors(") >= 3, "pôles, sujets de parole, textes"
    assert "useReplieAuClicDehors(racine" in _sans_commentaires(ACTES.read_text(encoding="utf-8"))


# ── 3. Sur quoi ils ont pris la parole ───────────────────────────────────────


def test_le_sujet_se_lit_comme_sur_les_autres_fiches_et_rien_n_est_jete() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    assert "from '../src/utils/sujetIntervention.js'" in projection
    cle = projection.split("function cleDeSujet(intervention) {")[1].split("\n}")[0]
    assert "sujetDeIntervention(intervention)" in cle
    assert ": SUJET_NON_PUBLIE;" in cle, "une prise de parole sans intitulé est comptée"


def test_intitule_non_publie_se_compte_et_ne_s_ouvre_pas() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    extraits = projection.split("export function construireExtraitsGouvernement(")[1]
    assert "if (sujet === SUJET_NON_PUBLIE) continue;" in extraits, "ses textes ne sont pas servis"
    fiche = _sans_commentaires(_fiche())
    assert "const sansIntitule = l.label === SUJET_NON_PUBLIE;" in fiche
    assert "const ouverte = !sansIntitule && ouvert === l.label;" in fiche


def test_la_liste_est_rangee_par_prises_de_parole_un_segment_par_personne() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    fonction = projection.split("export function sujetsComptes(")[1]
    assert "parNom.set(e.membre" in fonction, "deux portefeuilles, un seul segment"
    assert ".sort((a, b) => b.tours - a.tours" in fonction


def test_le_nombre_d_un_membre_ne_s_ecrit_que_pour_celui_qu_on_designe() -> None:
    """Vingt nombres à côté de vingt noms invitaient à comparer des personnes."""
    fiche = _fiche()
    figure = fiche.split("function ParolesComptees(")[1].split("\nfunction ")[0]
    assert figure.count("de parole sur {formatNumber(l.tours)} dans") == 1
    assert "prises de parole`" not in _sans_commentaires(figure), "aucun compte dans la tête d'un membre"


# ── 4. Ce qu'il a fait déposer ───────────────────────────────────────────────


def test_les_projets_de_loi_sont_en_carres_cinq_colonnes() -> None:
    fiche = _fiche()
    assert "d3-sankey" not in _sans_commentaires(fiche)
    colonnes = fiche.split("const COLONNES_PROJETS = [")[1].split("];")[0]
    assert re.findall(r"cle: '([a-z]+)'", colonnes) == ["deposes", "navette", "adoptes", "promulgues", "rejetes"]
    assert "statuts: ['adopte', 'adopte_cmp', 'adopte_49_3']" in colonnes, "« adoptés » réunit les trois adoptions"


def test_la_pastille_49_3_allume_ses_carres_au_survol() -> None:
    fiche = _sans_commentaires(_fiche())
    assert "onMouseEnter={() => setEclaire493(true)}" in fiche
    assert "eclaire493 ? texte.statut !== STATUT_493" in fiche
    assert "cmp" not in fiche.split("function CarresDesProjets(")[1].split("\nfunction ")[0].lower().replace("adopte_cmp", ""), (
        "aucune pastille ni sigle « CMP » dans la figure"
    )


# ── 5. Ce qu'il a fait entrer en vigueur ─────────────────────────────────────


def test_les_actes_sont_en_barres_par_ministere_a_l_encre() -> None:
    actes = _sans_commentaires(ACTES.read_text(encoding="utf-8"))
    assert "PALETTE" not in actes and "<svg" not in actes, "plus de teinte au rang, plus de flux"
    assert "const LIGNES_AFFICHEES = 12;" in actes
    assert "« Le titre ne le dit pas » ne veut pas dire « sans loi »." in actes
