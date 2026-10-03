"""La revue d'ergonomie de la fiche candidat, arrêtée le 01/10/2026 — premier lot.

La propriétaire a relu la fiche section par section, sur maquette, et arrêté ce
qui change. Ce premier lot porte ce qui ne touche à aucune figure :

- **les bulles d'information** remplacent les renvois vers la méthodologie et
  les critères de section — huit emplacements, textes arrêtés AU MOT PRÈS ;
- **la légende** de « Les fonctions exercées » entre dans la carte ;
- **les modes d'emploi** quittent « Ce qu'il a voté » ;
- **la section 4** change de titre et ne compare plus que la dernière lecture ;
- **les deux encadrés** « Ce que cette figure ne sait pas » quittent leur figure.

Les gardes de chaque section vivent dans les fichiers de test de ces sections
(`test_fonctions_exercees_328`, `test_votes_par_periode_328`,
`test_ecarts_groupe_328`, `test_paroles_par_periode_328`). Ce fichier garde ce
qui n'appartient à aucune : le composant de bulle, ses huit textes, et les
phrases que la revue a retirées — parce qu'une phrase explicative retirée
revient toute seule, une par une, chacune paraissant utile isolément.

CE QUE CES GARDES NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est
rendu ici. La position de la bulle sous son titre, son recouvrement des figures
et sa tenue à 390 px se vérifient à l'écran.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
COMPOSANTS = SRC / "components"

BULLE = COMPOSANTS / "InfoBulle.jsx"
BULLE_CSS = COMPOSANTS / "InfoBulle.css"
FICHE = COMPOSANTS / "CandidateProfile.jsx"
VOTES = COMPOSANTS / "VotesParPeriode.jsx"
PAROLES = COMPOSANTS / "ParolesParPeriode.jsx"
ECARTS = COMPOSANTS / "EcartsGroupe.jsx"
ECARTS_CSS = COMPOSANTS / "EcartsGroupe.css"
NAVIGATION = COMPOSANTS / "NavigationPeriodes.jsx"
LIGNEE = COMPOSANTS / "LigneeProfile.jsx"
PROFIL = SRC / "utils" / "profilCandidat.js"
METHODO = SRC / "pages" / "MethodologyPage.jsx"

#: Les huit textes, tels que la propriétaire les a arrêtés. Les recopier ici est
#: voulu : c'est la seule façon qu'une reformulation « pour améliorer » échoue.
#: La bulle des amendements accorde son pronom comme le titre de sa carte — le
#: test la lit donc de part et d'autre du pronom.
TEXTES = {
    "enBref": (
        "Le parcours d’élu, et l’activité en quelques chiffres bruts.",
        "Note : « Majorité » et « opposition » sont les qualifications déclarées par l’Assemblée nationale. Quand elle n’en déclare aucune, la fiche l’indique.",
    ),
    "fonctions": (
        "Les responsabilités tenues pendant les mandats, classées par durée dans chaque catégorie.",
        "Note : Une ligne sans rôle indiqué signifie simple membre. Une fonction longue n’est pas une fonction plus importante.",
    ),
    "textes": (
        "Les textes de loi dont la personne est l’auteur ou le rapporteur, rangés à l’étape qu’ils ont atteinte.",
        "Note : Seuls les textes examinés en commission sont affichés. Un texte arrêté à une étape n’est pas nécessairement rejeté.",
    ),
    "amendements": (
        "est l’auteur, répartis par thème de la commission.",
        "Note : Chaque segment d’une barre est un texte amendé. Sa largeur est le nombre d’amendements déposés sur ce texte.",
    ),
    "votes": (
        "Les votes sur les textes de loi en dernière lecture, par période de gouvernement.",
        "Note : Dernière lecture : le vote le plus récent sur le texte entier. Les votes sont regroupés par gouvernement pour distinguer ceux émis dans la majorité, la minorité ou l’opposition.",
    ),
    "ecarts": (
        "Les votes où sa position diffère de celle de la majorité de son groupe parlementaire.",
        "Note : Seuls les votes en dernière lecture sont comparés, et uniquement sur les scrutins où une majorité se dégage dans le groupe.",
    ),
    "dit": (
        "Les prises de parole à l’Assemblée, par période de gouvernement, par type et par sujet.",
        "Note : Les sujets sont les titres de l’ordre du jour de l’Assemblée.",
    ),
    # Réécrite le 02/10/2026 : la section est devenue une liste de manques.
    "couverture": (
        "Les limites de cette fiche : les mandats non couverts, et ce que les sources ne disent pas.",
        "Note : Quand un mandat n’est pas couvert, la fiche ne sait rien de cette période. Cela ne veut pas dire qu’il ne s’est rien passé.",
    ),
    # Les quatre textes du versant européen, arrêtés le 02/10/2026 sur la fiche
    # rendue d'Emmanuel Maurel.
    "textesUe": (
        "Les textes dont la personne est l’auteur ou le rapporteur au Parlement européen, par thème et par étape de la procédure.",
        "Note : Un texte qui traite de plusieurs thèmes apparaît sur chaque ligne concernée. « Sans dossier rattaché » : la source ne dit pas où en est le texte.",
    ),
    "amendementsUe": (
        "est l’auteur au Parlement européen, répartis par thème.",
        "Note : Chaque segment d’une barre est un texte amendé. Un amendement qui traite de plusieurs thèmes est compté sur chaque ligne concernée.",
    ),
    "votesUe": (
        "Les votes au Parlement européen, classés par thème.",
        "Note : Pour chaque texte, seul le vote le plus récent est retenu. Un texte qui traite de plusieurs thèmes apparaît sur chaque ligne concernée.",
    ),
    "ditUe": (
        "Les prises de parole au Parlement européen, par type et par sujet.",
        "Note : La source publie les sujets le plus souvent en anglais.",
    ),
    # La bulle unique d'une section 2 entièrement vide : une phrase, pas de note.
    "proposeVide": (
        "Les textes de loi dont la personne est l’auteur ou le rapporteur, et les amendements dont elle est l’auteur.",
        None,
    ),
}

#: Les tournures que la propriétaire a jugées « bancales » le 02/10/2026 : une
#: règle de comptage, une conséquence dite en négatif. Une note de bulle dit ce
#: que le lecteur a sous les yeux ; elle ne lui fait pas la soustraction.
TOURNURES_REFUSEES = (
    "les lignes ne s’additionnent pas",
    "compte une fois, à son dernier vote",
    "paraît sur la ligne de chacun de ses thèmes",
    "Le Parlement européen ne publie pas le sort",
)

#: L'ancre de méthodologie de chaque bulle. `couverture` et `dit` portent un
#: second lien, vérifié à part.
ANCRES = {
    "enBref": "fonctions",
    "fonctions": "fonctions",
    "textes": "propose",
    "amendements": "propose",
    "votes": "votes",
    "ecarts": "ecarts",
    "dit": "interventions",
    "couverture": "couverture",
    "textesUe": "propose",
    "amendementsUe": "propose",
    "votesUe": "votes",
    "ditUe": "interventions",
    "proposeVide": "propose",
}


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : les commentaires CITENT les phrases retirées."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def lire(chemin: Path) -> str:
    return sans_commentaires(chemin.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fiche() -> str:
    return lire(FICHE)


@pytest.fixture(scope="module")
def bulles(fiche: str) -> str:
    """Le tableau `BULLES`, de son ouverture à la fonction qui le suit."""
    debut = fiche.index("const BULLES = {")
    return fiche[debut : fiche.index("function Section(", debut)]


def _entree(bulles: str, cle: str) -> str:
    debut = bulles.index(f"  {cle}: ")
    suivante = re.search(r"\n  [a-zA-Z]+: ", bulles[debut + 1 :])
    return bulles[debut : debut + 1 + suivante.start()] if suivante else bulles[debut:]


# ── Le composant ─────────────────────────────────────────────────────────────


def test_la_bulle_s_ouvre_au_clic_et_jamais_au_survol() -> None:
    """Un téléphone n'a pas de survol, et une limite qu'il faut survoler n'est
    pas lue (DESIGN_SYSTEM §6). Le « i » est un vrai bouton."""
    bulle = lire(BULLE)
    assert '<button' in bulle and 'type="button"' in bulle
    assert "onClick={() => setOuverte((o) => !o)}" in bulle, "second clic : elle se referme"
    for survol in ("onMouseEnter", "onMouseOver", "onPointerEnter", ":hover"):
        assert survol not in bulle, f"{survol} : la bulle ne s'ouvre pas au survol"
    assert ":hover" not in BULLE_CSS.read_text(encoding="utf-8")


def test_le_bouton_dit_son_etat_et_ce_qu_il_commande() -> None:
    bulle = lire(BULLE)
    assert "aria-expanded={ouverte}" in bulle
    assert "aria-controls={id}" in bulle
    assert "id={id} hidden={!ouverte}" in bulle, "la bulle commandée porte l'identifiant annoncé"
    # `display: block` l'emporterait sur l'attribut `hidden` : sans cette règle,
    # une bulle fermée resterait à l'écran.
    feuille = BULLE_CSS.read_text(encoding="utf-8")
    assert ".ib-bulle[hidden] {" in feuille


def test_la_bulle_se_ferme_a_echap_et_au_clic_dehors() -> None:
    bulle = lire(BULLE)
    assert "e.key !== 'Escape'" in bulle
    assert "document.addEventListener('mousedown', surClic)" in bulle
    assert "!racine.current.contains(e.target)" in bulle
    assert "document.removeEventListener('mousedown', surClic)" in bulle, "l'écouteur ne survit pas à la bulle"


def test_une_seule_bulle_ouverte_a_la_fois() -> None:
    """Au clavier on passe d'un « i » à l'autre sans cliquer ailleurs : le clic
    dehors n'y suffit pas, celle qui s'ouvre referme la précédente."""
    bulle = lire(BULLE)
    assert "let fermerLaBulleOuverte = null;" in bulle
    assert "if (fermerLaBulleOuverte) fermerLaBulleOuverte();" in bulle
    assert "if (fermerLaBulleOuverte === fermer) fermerLaBulleOuverte = null;" in bulle


def test_il_n_y_a_qu_un_composant_de_bulle(fiche: str) -> None:
    """Huit emplacements, une implémentation : la fiche l'importe et ne la
    redéfinit pas."""
    assert "import InfoBulle, { BulleDePastille } from './InfoBulle';" in fiche
    assert "function InfoBulle" not in fiche
    assert "function BulleDePastille" not in fiche
    assert fiche.count("<InfoBulle") == 5, (
        "deux titres composés à la main (« En bref », `Section`) et trois titres de carte — "
        "les textes, les amendements, et la carte des amendements quand elle est vide"
    )


# ── Les huit textes ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("cle", sorted(TEXTES))
def test_le_texte_de_la_bulle_est_celui_qui_a_ete_arrete(bulles: str, cle: str) -> None:
    entree = _entree(bulles, cle)
    phrase, note = TEXTES[cle]
    assert phrase in entree, f"la phrase de la bulle « {cle} » a été reformulée"
    if note is None:
        assert "note:" not in entree, f"la bulle « {cle} » n'a pas de note : aucune figure à lire"
    else:
        assert note in entree, f"la note de la bulle « {cle} » a été reformulée"
    assert f"vers: '/methodologie#{ANCRES[cle]}'" in entree


def test_la_bulle_des_amendements_accorde_son_pronom(bulles: str) -> None:
    """« dont il est l'auteur », « dont elle est l'auteur » : comme le titre de
    la carte, et par le même mot de `voix`."""
    assert "`Les amendements dont ${voix.sujet} est l’auteur, répartis" in _entree(bulles, "amendements")


def test_les_bulles_menent_a_des_ancres_qui_existent(bulles: str) -> None:
    methodo = METHODO.read_text(encoding="utf-8")
    ancres = set(re.findall(r"vers: '/methodologie#([a-z-]+)'", bulles))
    assert ancres == set(ANCRES.values())
    for ancre in ancres:
        assert f"id: '{ancre}'" in methodo, f"#{ancre} n'existe pas en méthodologie"


def test_la_source_des_paroles_est_le_premier_lien_de_sa_bulle(bulles: str, fiche: str) -> None:
    """La phrase « Les comptes rendus de séance sont publiés… sous forme
    d'archive » est retirée : la source est un lien de la bulle, vers la page du
    jeu de données — jamais vers l'archive de 100 Mo."""
    entree = _entree(bulles, "dit")
    source = entree.index("La source : les comptes rendus de l’Assemblée →")
    assert source < entree.index("LIRE_LA_METHODE")
    assert "href: PAGE_JEU_DE_DONNEES_DEBATS" in entree
    assert "sous forme d’archive" not in lire(PAROLES)
    assert "PAGE_JEU_DE_DONNEES_DEBATS" not in lire(PAROLES)


def test_la_bulle_de_couverture_porte_ses_deux_liens(bulles: str) -> None:
    entree = _entree(bulles, "couverture")
    assert "{ libelle: 'Nos sources, et depuis quand →', vers: '/sources#frise' }" in entree


# ── Les emplacements ─────────────────────────────────────────────────────────


def test_la_section_deux_porte_une_bulle_par_carte_et_aucune_a_son_titre(fiche: str) -> None:
    """Ses deux figures ne se lisent pas de la même façon. Une exception : la
    section entièrement vide, qui n'a plus de carte et porte une bulle unique."""
    section = fiche[fiche.index('<Section numero="2"') :]
    section = section[: section.index(">")]
    assert "bulle={proposeVide ? BULLES.proposeVide : null}" in section
    assert "{...(ue ? BULLES.textesUe : BULLES.textes)}" in fiche
    assert fiche.count("{...(ue ? BULLES.amendementsUe(voix) : BULLES.amendements(voix))}") == 2, (
        "la carte des amendements, pleine et vide"
    )


# ── Le versant européen (02/10/2026) ─────────────────────────────────────────


def test_aucune_bulle_ne_porte_une_tournure_refusee(bulles: str) -> None:
    for tournure in TOURNURES_REFUSEES:
        assert tournure not in bulles, f"« {tournure} » est revenue dans une bulle"


def test_la_bulle_des_amendements_europeens_accorde_son_pronom(bulles: str) -> None:
    assert "`Les amendements dont ${voix.sujet} est l’auteur au Parlement européen, répartis" in _entree(
        bulles, "amendementsUe"
    )


def test_avec_un_commutateur_la_bulle_est_dans_la_pastille_et_plus_au_titre(fiche: str) -> None:
    """La règle de lecture n'est pas la même à Paris et à Strasbourg, et un
    titre ne peut en porter qu'une : chaque pastille du commutateur porte la
    sienne. Le titre n'en porte alors plus — deux « i » pour un même objet
    feraient chercher lequel dit vrai."""
    # Section 2 : au titre seulement SANS commutateur.
    assert fiche.count("{!commutateur && (\n                <InfoBulle") == 3
    assert "bulleFr={BULLES.textes}" in fiche and "bulleUe={BULLES.textesUe}" in fiche
    assert fiche.count("bulleFr={BULLES.amendements(voix)}") == 2
    assert fiche.count("bulleUe={BULLES.amendementsUe(voix)}") == 2
    # Sections 3 et 5 : le titre se tait dès que les deux versants sont là.
    assert "bulles={votesDesDeuxCotes ? { fr: BULLES.votes, ue: BULLES.votesUe } : null}" in fiche
    assert "bulles={parolesDesDeuxCotes ? BULLES_DES_QUALITES : null}" in fiche


def test_la_regle_ne_vaut_que_si_un_versant_europeen_est_present(fiche: str) -> None:
    """Le commutateur « député / membre du gouvernement » des prises de parole
    garde sa bulle au titre : la propriétaire l'a tranché le 02/10/2026."""
    assert "qualites.some((q) => q.qualite === QUALITE_PE)" in fiche
    assert "const parolesDesDeuxCotes = parolesUe && qualites.length > 1;" in fiche


def test_le_i_n_est_pas_un_bouton_dans_un_bouton() -> None:
    """HTML l'interdit, et un clic sur le « i » basculerait de versant. La
    pastille et le « i » sont deux boutons frères, posés l'un sur l'autre par
    la feuille."""
    bulle = lire(BULLE)
    assert "export function BulleDePastille({ bulle = null, sujet, children }) {" in bulle
    assert "if (!bulle) return children('');" in bulle
    assert '<span className="pp-pastille ib-ancre">' in bulle
    paroles = lire(PAROLES)
    assert "<BulleDePastille bulle={bulles?.[q.qualite]} key={q.qualite} sujet={q.libelle}>" in paroles
    feuille = (COMPOSANTS / "ParolesParPeriode.css").read_text(encoding="utf-8")
    assert ".pp-pastille .ib-bouton::after" in feuille, "la cible du doigt ne déborde plus le dessin"


def test_le_versant_europeen_n_a_plus_de_renvoi_hors_de_ses_bulles(fiche: str) -> None:
    assert "Quels textes et quels amendements sont retenus" not in fiche
    assert 'className="cp-methodo"' not in fiche


def test_la_derniere_lecture_est_la_cinquieme_condition_de_la_methodologie() -> None:
    """Une phrase avait été ajoutée en fin de paragraphe, après « quatre
    conditions ». Arrêté le 02/10/2026 : la dernière lecture est une condition
    comme les autres."""
    methodo = METHODO.read_text(encoding="utf-8")
    assert "Cinq conditions, toutes nécessaires" in methodo
    assert "Quatre conditions" not in methodo
    assert "la{' '}\n          <strong>dernière lecture</strong> du texte, c'est-à-dire le vote le plus récent sur ce" in methodo
    assert "même règle que pour ses votes" not in methodo


def test_en_bref_porte_sa_bulle_et_plus_son_renvoi(fiche: str) -> None:
    assert '<InfoBulle sujet="En bref" {...BULLES.enBref} />' in fiche
    assert "selon l’Assemblée →" not in fiche, "le pied d'« En bref » est revenu"


# ── Ce que la revue a retiré, et qui ne revient pas ──────────────────────────


@pytest.mark.parametrize(
    ("chemin", "phrase"),
    [
        (FICHE, "Jamais totalisée"),
        (FICHE, "Le verbatim est celui du compte rendu"),
        (FICHE, "Pourquoi ce n’est pas un palmarès"),
        (FICHE, "Pourquoi ces limites se déclarent"),
        (VOTES, "Cliquez une barre"),
        (VOTES, "Comment ces votes sont retenus"),
        (PAROLES, "Comment ces interventions sont collectées"),
        (ECARTS, "comment ils sont retenus"),
        (ECARTS, "ses membres exprimés n’ont pas tous voté de la même façon"),
        (ECARTS, "Chacun avec la répartition réelle du groupe"),
    ],
)
def test_une_phrase_retiree_ne_revient_pas(chemin: Path, phrase: str) -> None:
    assert phrase not in lire(chemin), f"« {phrase} » est revenue dans {chemin.name}"


def test_la_ligne_de_position_se_tait_sur_la_fiche_candidat() -> None:
    """« Période 7 sur 7 · 31 textes · les flèches ← → du clavier naviguent
    aussi » : retirée des deux sections de la fiche candidat. En section 5, le
    lien « Voir toutes les périodes » qu'elle portait reste, seul.

    La fiche de groupe partage le composant et n'a pas été relue : elle ne passe
    pas la prop, et garde sa ligne.
    """
    navigation = lire(NAVIGATION)
    assert "sansPosition = false," in navigation
    assert "{!sansPosition && (tout" in navigation, "le texte de position ne dépend plus de la prop"
    assert "const ligne = !sansPosition || avecTout;" in navigation
    for composant in (VOTES, PAROLES):
        appel = lire(composant).split("<NavigationPeriodes")[1].split("/>")[0]
        assert "sansPosition" in appel, f"{composant.name} affiche encore la ligne de position"
    assert "avecTout" in lire(PAROLES).split("<NavigationPeriodes")[1].split("/>")[0]
    assert "sansPosition" not in lire(LIGNEE)


def test_la_regle_des_votes_dit_ce_qu_elle_compte(fiche: str) -> None:
    assert "regle={`Sur ${formatNumber(votes.textes)} scrutins de textes en dernière lecture`}" in fiche


# ── La section 4 ─────────────────────────────────────────────────────────────


def test_le_titre_de_la_section_quatre_s_accorde_par_la_voix() -> None:
    """« Où il a voté autrement que son groupe » : le titre dit ce que la
    section compare — un vote —, là où « écarté des siens » le qualifiait."""
    profil = lire(PROFIL)
    for sujet in ("il", "elle", "cette personne"):
        assert f"ecarts: 'Où {sujet} a voté autrement que son groupe'," in profil
    assert "écarté" not in profil.split("const VOIX_MASCULINE")[1].split("export function voixDuProfil")[0]


def test_les_points_d_ecart_passent_au_premier_plan() -> None:
    """Le point fait 10 px dans une colonne de trois : les repères des colonnes
    voisines, peints après lui, passaient par-dessus."""
    feuille = sans_commentaires(ECARTS_CSS.read_text(encoding="utf-8"))
    regle = feuille.split(".eg-col--ecart {")[1].split("}")[0]
    assert "position: relative;" in regle
    assert "z-index: 1;" in regle


# ── Ce qui s'ouvre au clic se replie au clic ailleurs (02/10/2026) ───────────

HOOK = SRC / "hooks" / "useReplieAuClicDehors.js"


def test_le_repli_attend_le_clic_et_garde_la_cible_en_place() -> None:
    """Replier un bloc retire de la hauteur au-dessus de ce que le lecteur vise.
    Le repli se fait donc au `click`, jamais au `mousedown`, et rend au
    défilement ce que la page a perdu : mesuré à l'écran, la cible ne bouge pas.
    """
    hook = lire(HOOK)
    assert "document.addEventListener('click', surClic);" in hook
    assert "mousedown" not in hook
    assert "const avant = cible.getBoundingClientRect().top;" in hook
    assert "if (ecart) window.scrollBy(0, ecart);" in hook


def test_la_barre_de_defilement_n_est_pas_un_clic_ailleurs() -> None:
    assert "if (cible === document.documentElement) return;" in lire(HOOK)


def test_tout_ce_qui_s_ouvre_sur_la_fiche_se_replie(fiche: str) -> None:
    """Les listes sous les figures des sections 2, 3 et 5, et les trois plis."""
    assert "useReplieAuClicDehors(carteTextes, selTexte != null, () => setSelTexte(null));" in fiche
    assert "useReplieAuClicDehors(carteAmendements, matiere != null, () => setMatiere(null));" in fiche
    assert "useReplieAuClicDehors(racine, matiere != null, () => setMatiere(null));" in lire(VOTES)
    assert "useReplieAuClicDehors(racine, sujet != null, () => { setSujet(null); setLimite(PAS_DE_FIL); });" in lire(PAROLES)
    # Un seul `details` dans la fiche : celui de `Pli`, qui tient son état.
    assert fiche.count("<details") == 1 and fiche.count("<Pli") == 3
    assert "useReplieAuClicDehors(ref, ouvert, () => setOuvert(false));" in fiche
