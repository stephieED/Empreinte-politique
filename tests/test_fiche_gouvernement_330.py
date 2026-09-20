"""Ce que la fiche de gouvernement ne doit pas reperdre (#330).

Les arbitrages de la maquette des 17 et 18/09/2026 tiennent à des détails qu'une
session suivante défait sans le savoir : le 49.3 qui prendrait une couleur
d'issue, « le groupe le plus nombreux » qui remplacerait « le groupe déclaré
majoritaire », un seuil de remaniement qui disparaîtrait dans une comparaison.

CE QUE CES GARDES NE COUVRENT PAS, et il faut le dire (§2 règle 5) : elles ne
rendent aucun composant React et n'exécutent pas d3-sankey. La géométrie du flux
et le comportement du dépliage ont été vérifiés en navigateur sur quatre
gouvernements — Philippe II (282 textes, 50 membres), Attal, Lecornu II et
Fillon I (0 texte) —, pas ici.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"

REGLES = UI / "src" / "utils" / "gouvernement.js"
COMPOSANT = UI / "src" / "components" / "GovernmentProfile.jsx"
ADAPTATEUR = UI / "src" / "data" / "pivotAdapter.js"
SYNC = UI / "scripts" / "sync-data.mjs"
DECISION = RACINE / "docs" / "decisions" / "fiche-de-gouvernement-330.md"


def test_les_regles_de_la_fiche_vivent_dans_utils():
    """Une règle testable vit dans `utils/*.js`, pas dans le composant."""
    source = REGLES.read_text(encoding="utf-8")
    for symbole in (
        "export function organigramme",
        "export function vaguesDeNomination",
        "export function fourchetteEffectif",
        "export function majoriteDuGouvernement",
        "export function chiffresDesTextes",
        "export function fluxMatiereSort",
    ):
        assert symbole in source, f"{symbole} a disparu de utils/gouvernement.js"


def test_le_49_3_ne_prend_aucune_teinte():
    """§2 règle 4 : un fait de procédure ne porte pas la couleur d'une issue."""
    source = COMPOSANT.read_text(encoding="utf-8")
    table = re.search(r"const TEINTE_SORT = \{(.+?)\};", source, re.S)
    assert table, "la table des teintes d'issue a disparu"
    for cle in ("adopte_49_3", "rejete_49_3"):
        assert re.search(rf"{cle}:\s*null", table.group(1)), (
            f"{cle} doit rester sans teinte : une couleur le rangerait parmi les issues de vote"
        )


def test_la_majorite_est_declaree_par_l_assemblee_jamais_deduite():
    """On lit `position === 'majorite'` ; on ne classe jamais par effectif."""
    source = REGLES.read_text(encoding="utf-8")
    assert "position === 'majorite'" in source
    assert "aucun groupe déclaré majoritaire" in source, (
        "l'absence de déclaration depuis 2024 se dit ; elle ne se comble pas"
    )
    # Aucun tri par nombre de membres dans la fonction : ce serait notre jugement.
    fonction = re.search(r"export function majoriteDuGouvernement\(.+?\n\}", source, re.S)
    assert fonction, "majoriteDuGouvernement a disparu"
    assert "effectif" not in fonction.group(0), (
        "le groupe le plus nombreux n'est pas le groupe majoritaire (§2 règle 1)"
    )


def test_le_seuil_d_une_vague_de_nominations_est_declare():
    """Le seuil décide du nombre de remaniements : il se nomme, il ne se cache pas."""
    source = REGLES.read_text(encoding="utf-8")
    assert "export const JOURS_MEME_VAGUE" in source


def test_l_effectif_compte_des_personnes_pas_des_portefeuilles():
    source = REGLES.read_text(encoding="utf-8")
    fonction = re.search(r"export function effectifAu\(.+?\n\}", source, re.S)
    assert fonction and "new Set()" in fonction.group(0), (
        "quelqu'un qui tient deux portefeuilles le même jour ne compte qu'une fois"
    )


def test_le_rattachement_se_lit_dans_le_libelle_officiel():
    """La source écrit « après » pour « auprès », et des espaces insécables."""
    source = REGLES.read_text(encoding="utf-8")
    assert "aupr[èe]s|apr[èe]s" in source, (
        "la faute de la source se lit, elle ne se corrige pas : sinon un ministère fantôme apparaît"
    )
    assert "\\u00a0" in source, "les espaces insécables des libellés se normalisent à l'entrée"


def test_la_matiere_d_un_texte_est_la_commission_saisie_au_fond():
    source = ADAPTATEUR.read_text(encoding="utf-8")
    assert "commission_saisie_au_fond" in source, (
        "la matière est sourcée sur la commission, jamais lue dans le titre du texte"
    )


def test_le_manifest_porte_la_position_des_groupes():
    """Sans elle, la fiche téléchargerait des fiches de groupe de 500 Ko."""
    source = SYNC.read_text(encoding="utf-8")
    assert "position: groupe.position_politique?.position" in source


def test_les_criteres_de_section_tiennent_en_une_limite():
    """DESIGN_SYSTEM §7 règle 2 : au-delà de 22 mots, ce n'est plus une limite,
    c'est une explication — et une explication va dans la méthodologie."""
    source = COMPOSANT.read_text(encoding="utf-8")
    # Une section peut n'en porter aucun : son titre suffit, et la limite
    # tient dans le renvoi. La garde porte sur la LONGUEUR, pas sur la présence.
    criteres = re.findall(r'<p className="gvp-section-critere">(.*?)</p>', source, re.S)
    trop_longs = [
        (len(" ".join(c.split()).split()), " ".join(c.split()))
        for c in criteres
        if len(" ".join(c.split()).split()) > 22
    ]
    assert not trop_longs, f"critères qui expliquent au lieu de limiter : {trop_longs}"


def test_les_renvois_remplacent_l_explication_et_atteignent_une_ancre():
    """La fiche garde le renvoi ; le paragraphe part en méthodologie.

    Un pied de section ne subsiste que là où AUCUNE forme ne porte le fait —
    le 49.3, que §2 règle 4 veut nommé à côté de la figure. Décrire ce que la
    figure montre déjà est l'aveu d'échec que DESIGN_SYSTEM §7 règle 2 refuse.
    """
    source = COMPOSANT.read_text(encoding="utf-8")
    assert '49.3 est un fait de procédure' in source, (
        "le 49.3 se nomme à côté de la figure : aucune forme ne le porte seule"
    )
    ancres = set(re.findall(r"/methodologie#([a-z]+)", source))
    assert ancres, "aucun renvoi vers la méthodologie"
    methodo = (UI / "src" / "pages" / "MethodologyPage.jsx").read_text(encoding="utf-8")
    ids = set(re.findall(r"id: '([a-z]+)'", methodo))
    assert ancres <= ids, f"renvois vers des ancres inexistantes : {ancres - ids}"


def test_la_fiche_dit_ce_qu_elle_n_a_pas_pu_lire():
    """Trois absences, trois causes, jamais confondues (DESIGN_SYSTEM §7 règle 7)."""
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "function limitesDeLaFiche" in source
    # Hors commentaires : la mention de la borne d'hier y explique le piège.
    sans_commentaires = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    assert "21 juin 2017" not in sans_commentaires, (
        "la borne de couverture se lit sur `textesCouverture.borne` : écrite en dur, "
        "elle a menti le jour où l'archive de la XIVe a reculé la borne à 2012 (#1019)"
    )
    for cause in (
        "commencent au ${jour(couverture.borne)}",  # une archive que la source ne publie pas
        "ne déclare plus la position de ses groupes",  # une position qu'elle ne déclare plus
        "Un gouvernement ne vote pas",         # une activité qui n'existe pas à ce niveau
    ):
        assert cause in source, f"limite disparue : {cause}"


def test_une_entree_sans_portefeuille_ne_dedouble_pas_une_personne():
    """La source publie deux mandats pour Abad et Braun-Pivet sous Borne, dont
    un sans portefeuille : le muet n'ajoute rien et ne fait pas un second bloc."""
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "!nommes.has(m.nom)" in source


def test_le_nom_du_premier_ministre_ne_mene_pas_a_une_page_absente():
    """Seules les fiches de candidats déclarés sont publiées : 4 des 17 Premiers
    ministres en ont une. Les 13 autres nommaient une adresse qui rend « Aucun
    candidat trouvé » — un lien mène là où le texte le dit, ou n'existe pas."""
    index = (UI / "src" / "data" / "index.js").read_text(encoding="utf-8")
    assert "manifest.candidates || []).find((c) => c.nom === pm)" in index, (
        "le slug du Premier ministre se résout sur les fiches publiées"
    )
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "government.premierMinistreId ? (" in source, (
        "sans fiche publiée, le nom s'affiche sans lien"
    )


def test_la_parole_compte_des_membres_et_publie_son_denominateur():
    """Gabarit de la fiche de groupe (#329) : des sujets, jamais des positions ;
    des membres, jamais des occurrences ; et le dénominateur à côté du
    numérateur (§2 règles 1, 7 et 8)."""
    regles = REGLES.read_text(encoding="utf-8")
    fonction = re.search(r"export function sujetsDeParole\(.+?\n\}", regles, re.S)
    assert fonction, "sujetsDeParole a disparu"
    assert "nb_membres_porteurs" in fonction.group(0), "le compte est un nombre de MEMBRES"
    assert "membres_avec_interventions" in fonction.group(0), (
        "le dénominateur publié est la population dont la parole est collectée"
    )
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "membres dont la parole est collectée" in source, (
        "le pied de section nomme la population du dénominateur"
    )
    assert "/methodologie#paroles" in source, "le renvoi dit d'où viennent les intitulés"


def test_l_etiquetage_des_debats_declare_sa_limite():
    """Sur Philippe II, 329 interventions sur 48 370 portent un intitulé : sans
    cette ligne, 61 sujets contre 1 738 se lisent comme un gouvernement
    silencieux."""
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "quoi: 'Prises de parole'" in source
    assert "n’apparaît que si la source publie son intitulé" in source


def test_le_detail_d_un_sujet_est_une_ligne_par_membre():
    """Une intervention de la source est un TOUR DE PAROLE : la première version
    rendait 857 lignes pour la motion de censure de décembre 2023, dont
    trente-quatre fois la même personne au même jour. Une ligne par membre et
    par portefeuille, du plus parlant au moins parlant."""
    projection = (UI / "scripts" / "vue-parole-gouvernement.mjs").read_text(encoding="utf-8")
    # L'ordre est le NOMBRE DE TOURS, décroissant (arbitrage du 20/09/2026), le
    # nom ne servant qu'à départager. Aucun total ni rang n'est publié.
    # Deux niveaux (arbitrage du 20/09/2026) : la dernière prise de parole,
    # décroissante, puis le nombre de tours, décroissant. Aucun total ni rang.
    assert "b.derniere.localeCompare(a.derniere)" in projection
    assert "b.tours - a.tours" in projection
    assert "tours" in projection and "premiere" in projection and "derniere" in projection
    assert "verbatim" not in projection.split("*/", 1)[1], (
        "la projection ne porte pas de texte : les membres de gouvernement sont "
        "collectés en mode réduit au thème"
    )


def test_la_cle_du_detail_est_celle_de_l_agregat():
    """`deriver_tags_thematiques` range un thème en `strip().lower()` : keyer la
    projection sur le libellé brut donnait zéro correspondance sur les 1 738
    sujets de Borne."""
    projection = (UI / "scripts" / "vue-parole-gouvernement.mjs").read_text(encoding="utf-8")
    assert "theme.trim().toLowerCase()" in projection


def test_aucun_lien_ne_mene_a_une_archive():
    """La source publie le compte rendu en zip de 100 Mo : un badge « Source »
    qui y mène n'atteste rien pour un lecteur."""
    projection = (UI / "scripts" / "vue-parole-gouvernement.mjs").read_text(encoding="utf-8")
    assert "syceronbrut|syseron" in projection


def test_la_projection_se_charge_au_clic_et_pas_avec_la_fiche():
    """4,1 Mo sur Borne quand la fiche entière en pèse 1."""
    index = (UI / "src" / "data" / "index.js").read_text(encoding="utf-8")
    assert "export async function getParolesDuGouvernement" in index
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "if (ouvert === null || detail !== null) return undefined;" in source, (
        "la projection ne se télécharge qu'au premier sujet ouvert"
    )


def test_la_qualite_se_lit_sur_la_fenetre_du_portefeuille():
    """En qualité de quoi la personne a parlé : la source ne le dit PAS sur
    l'intervention — `fonction` est vide sur les 4 213 entrées d'Élisabeth
    Borne — mais le portefeuille exercé ce jour-là est publié. Il se lit dans
    la fenêtre qui contient la date, il ne se devine pas. Onze membres du
    gouvernement Borne en ont tenu deux : ils portent deux lignes."""
    projection = (UI / "scripts" / "vue-parole-gouvernement.mjs").read_text(encoding="utf-8")
    assert "function fenetreDe" in projection
    assert "portefeuille: fenetre.portefeuille" in projection
    source = COMPOSANT.read_text(encoding="utf-8")
    assert "gvp-intervention-qualite" in source


def test_la_decision_existe_et_porte_sa_date():
    contenu = DECISION.read_text(encoding="utf-8")
    assert contenu.startswith("# "), "un titre de niveau 1 ouvre la décision"
    assert "`2026-09-18`" in contenu
    assert "> **En bref**" in contenu
