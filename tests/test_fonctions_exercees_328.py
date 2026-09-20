"""« Les fonctions exercées » — la section 1 de la fiche candidat (#328).

La section a perdu, le 03/09/2026, ce qu'une autre partie de la page portait
déjà : la frise ET le détail daté du parcours vivent dans « En bref », et les
republier ici était de la redondance pure. Ce qui reste est ce que personne
d'autre ne montre — les fonctions qu'on choisit d'exercer — et le titre le dit.

Ce que ce fichier verrouille est ce qui ne se relit pas dans le code une fois
écrit :

- **le nombre affiché est une DURÉE, jamais un compte d'enregistrements**. La
  source réécrit un même siège à chaque changement de composition : 27 entrées
  pour 5 ans 10 mois continus chez Jérôme Guedj, contre 4 entrées pour 2 jours
  à la commission des lois. Le compte ne distingue pas les deux ;
- **la durée est une UNION d'intervalles, jamais une somme** : la fusion
  additive a laissé des doublons littéraux, et la somme donnerait 9,5 ans là où
  il y en a 5,8 ;
- **ce qui ressort dépasse la moitié du temps de mandat**, et le dénominateur
  est l'union des sièges électifs — un vrai tout, on ne siège pas deux fois à la
  fois (§2 règle 7). Le total des fonctions n'en serait pas un : treize groupes
  d'amitié simultanés font 33 ans sur une carrière de 19 ;
- **la règle sait se taire** : mesurée sur les 13 blocs des deux profils de
  référence, elle parle 4 fois. Une règle qui ne peut pas se taire ne dit rien
  quand elle parle (#326, règle 5) ;
- **la marque est sans teinte**, parce qu'aucune n'était libre — le jaune est
  pris par la sélection, l'action et le badge de source, le vert et le rouge par
  les positions de vote, le bleu et le bronze par les institutions ;
- **le rôle ne s'affiche que lorsqu'il distingue** : `Membre` couvre 90,7 % des
  mandats de commission du corpus.

Les tests lisent le **code exécuté** (commentaires retirés) : une règle énoncée
en commentaire et absente du code passerait sinon au vert.

Ce qui n'est PAS couvert ici : la mise en page rendue, le responsive, le
contraste et le parcours clavier — le dépôt n'a pas de harnais JS.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "profilCandidat.js"
COMPOSANT = UI / "components" / "CandidateProfile.jsx"
FEUILLE = UI / "components" / "CandidateProfile.css"
ADAPTATEUR = UI / "data" / "pivotAdapter.js"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def sans_commentaires_css(source: str) -> str:
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


@pytest.fixture(scope="module")
def regles() -> str:
    return sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def composant() -> str:
    return sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def feuille() -> str:
    return sans_commentaires_css(FEUILLE.read_text(encoding="utf-8"))


def _corps(source: str, debut: str, fin: str) -> str:
    i = source.index(debut)
    return source[i : source.index(fin, i)]


# ── Le nombre affiché ────────────────────────────────────────────────────────


def test_la_mesure_est_une_duree_pas_un_compte(regles):
    """« 27 » à la commission des affaires sociales est un compte
    d'enregistrements ; « 5 ans 10 mois » est le siège. Le premier ne distingue
    pas un siège continu de quatre passages d'un jour, le second si."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "joursCumules" in bloc, "la ligne porte une durée, calculée"
    assert "dureeDeSiege" in bloc, "et rendue en années et en mois"
    assert "lot.length" not in bloc and ".size" not in bloc, (
        "le nombre d'enregistrements ne doit jamais devenir le nombre affiché"
    )


def test_la_duree_est_une_union_jamais_une_somme(regles):
    """La fusion additive a laissé des doublons littéraux — même début, fin
    décalée d'un jour. Les additionner donnerait 9,5 ans là où il y en a 5,8."""
    bloc = _corps(regles, "export function joursCumules", "\n}")
    assert "sort(" in bloc, "une union suppose des intervalles ordonnés"
    assert "d <= fin" in bloc, "deux intervalles qui se touchent n'en font qu'un"
    assert "reduce((" not in bloc, (
        "une somme des durées individuelles compterait deux fois les doublons"
    )


def test_un_mandat_sans_debut_ne_compte_pas_et_ne_vaut_pas_zero(regles):
    """Il n'est comptable à aucune date. Il sort du calcul ; il n'y entre pas
    comme un zéro, qui serait une mesure (§2 règle 5)."""
    bloc = _corps(regles, "export function joursCumules", "\n}")
    assert "filter((m) => m.debut)" in bloc


def test_un_mandat_ouvert_se_compte_jusqu_a_aujourd_hui(regles):
    """Un siège en cours dure jusqu'à aujourd'hui, pas jusqu'à `9999-12-31` —
    la borne ouverte du schéma ferait une durée de huit mille ans."""
    bloc = _corps(regles, "export function joursCumules", "\n}")
    assert "m.actif || !m.fin ? aujourdhui" in bloc
    assert "9999" not in bloc


# ── La règle de mise en avant ────────────────────────────────────────────────


def test_ce_qui_ressort_depasse_la_moitie_du_temps_de_mandat(regles):
    """Un fait, pas un seuil choisi : c'est le test de majorité que #328 a déjà
    retenu pour les amendements, posé sur un dénominateur qui en est un."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "lignes[0].jours * 2 > jours" in bloc, (
        "le test de majorité s'écrit sans constante : × 2 contre le tout"
    )


def test_le_denominateur_est_l_union_des_sieges_pas_le_total_des_fonctions(regles):
    """C'est LE choix qui rend le ratio publiable (§2 règle 7) : on ne siège pas
    deux fois à la fois, donc les sièges électifs forment un vrai tout. Les
    fonctions, elles, sont simultanées — treize groupes d'amitié font 33 ans sur
    une carrière de 19, et leur somme ne serait le tout de rien."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert 'm.categorie === \'mandat_electif\'' in bloc
    assert "joursCumules(\n    liste.filter" in bloc


def test_la_marque_ne_peut_aller_qu_a_la_plus_longue(regles):
    """Dépasser la moitié du tout interdit qu'une autre le fasse aussi : la
    marque est donc structurellement unique, elle n'est pas choisie."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "lignes[0].marquee = true" in bloc
    assert "forEach" not in _corps(bloc, "if (!sansMarque && lignes.length", "return {")


def test_la_regle_sait_se_taire(regles):
    """Sans mandat électif mesurable, aucune ligne n'est marquée — jamais un
    repli sur la plus longue, qui ferait parler la règle en toute circonstance."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "jours > 0 &&" in bloc


def test_toutes_les_categories_montrent_le_meme_nombre_de_lignes(regles):
    """Un bloc à une grande ligne et un autre à trois petites déséquilibraient la
    carte sans que la donnée le justifie : la marque distingue, pas le gabarit."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "montrees: lignes.slice(0, NB_FONCTIONS_MONTREES)" in bloc
    assert "reste: lignes.slice(NB_FONCTIONS_MONTREES)" in bloc


def test_aucun_total_entre_deux_natures_de_mandat(regles, composant):
    """Un groupe d'amitié et une commission d'enquête ne s'additionnent pas :
    les totaliser transformerait deux engagements en une note (§2 règle 1)."""
    bloc = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "total" not in bloc, "aucun total de catégories n'est calculé"
    rendu = _corps(composant, "function Fonctions(", "\n}")
    assert "reduce" not in rendu, "ni recomposé à l'affichage"


# ── Le rôle ──────────────────────────────────────────────────────────────────


def test_le_role_ne_s_affiche_que_lorsqu_il_distingue(regles):
    """`Membre` couvre 90,7 % des 14 128 mandats de commission du corpus, et 203
    des 225 des 13 candidats. L'écrire partout serait un mot dont le
    lecteur ne tire rien — la règle 1 de #326 le disqualifie."""
    bloc = _corps(regles, "const ROLES_PAR_DEFAUT", "\n}")
    for defaut in ("'membre'", "'membre titulaire'", "'membre de droit'"):
        assert defaut in bloc, f"{defaut} est un rôle par défaut, pas une distinction"
    assert "return null" in bloc, "un rôle par défaut ne rend rien à afficher"


def test_la_casse_est_normalisee_a_l_affichage_seulement(regles):
    """La source publie `Membre`/`membre`, `Vice-Président`/`vice-président`,
    `vice-présidente`. On uniformise ce qui s'affiche ; la donnée n'est pas
    touchée, et le défaut de collecte reste lisible pour qui l'ouvre."""
    bloc = _corps(regles, "export function roleDistinctif", "\n}")
    assert "toUpperCase" in bloc and "toLowerCase" in bloc
    # `=` seul, jamais `===` : on cherche une AFFECTATION, pas une comparaison.
    assert not re.search(r"m\.fonction\s*=(?!=)", regles), (
        "la casse s'uniformise à l'affichage ; la donnée n'est jamais réécrite"
    )


# ── La marque, à l'écran ─────────────────────────────────────────────────────


def test_la_marque_est_sans_teinte(feuille):
    """Aucune couleur n'était libre : le jaune signal est pris par la sélection,
    l'action et le badge de source ; le vert et le rouge par les positions de
    vote ; le bleu et le bronze par les institutions dans la frise. Une
    quatrième aurait dilué les trois autres — et l'encre reste lisible en
    niveaux de gris et sous daltonisme, sans pictogramme de secours."""
    regle = _corps(feuille, ".cp-fonctions-item--marquee", "}")
    assert "var(--ink)" in regle, "un filet d'encre"
    for teinte in ("var(--accent)", "#dfff00", "#007A45", "#E53420", "#3f5166", "#8a6b4c"):
        assert teinte.lower() not in regle.lower(), (
            f"{teinte} porte déjà un sens ailleurs dans la charte"
        )


def test_deux_etats_jamais_une_graduation(feuille):
    """Une ligne porte la marque ou non. Rien ne hiérarchise entre elles les deux
    autres, sans quoi la carte se lirait comme un podium."""
    assert ".cp-fonctions-item--marquee" in feuille
    for graduation in (":nth-child(2)", ":nth-child(3)", "opacity: 0."):
        assert graduation not in _corps(feuille, ".cp-fonctions-liste", ".cp-pli--fonctions")


# ── La coupe des intitulés ───────────────────────────────────────────────────


def test_la_coupe_se_fait_sur_deux_lignes(feuille):
    """Une seule perdait trop : les commissions d'enquête portent des intitulés
    de plus de 200 caractères."""
    regle = _corps(feuille, ".cp-fonctions-ligne {", "}")
    assert "max-height: 2.9em" in regle
    assert "-webkit-line-clamp" not in feuille, (
        "il peint ses propres points, et on en aurait deux avec le bouton"
    )
    assert "text-overflow" not in _corps(feuille, ".cp-fonctions-ligne {", ".cp-fonctions-role")


def test_les_trois_points_sont_un_vrai_bouton(composant):
    """Il faut pouvoir l'atteindre au clavier, et qu'un lecteur d'écran annonce
    qu'il déplie : la moitié des intitulés de commissions d'enquête dépassent
    200 caractères, et un pseudo-élément décoratif leur serait invisible."""
    bloc = _corps(composant, "function Intitule(", "\n}")
    assert 'type="button"' in bloc
    assert "aria-expanded" in bloc


def test_le_bouton_n_apparait_que_sur_ce_qui_deborde(composant):
    """Poser l'affordance partout apprendrait au lecteur à ne plus cliquer. Et
    la place disponible décide, pas le texte : la mesure se refait au
    redimensionnement."""
    bloc = _corps(composant, "function Intitule(", "\n}")
    assert "scrollHeight > el.clientHeight" in bloc, "on mesure la hauteur, pas la largeur"
    assert "deborde && (" in bloc
    assert "addEventListener('resize'" in bloc
    assert "removeEventListener('resize'" in bloc, "et l'écouteur se retire"


# ── La section ───────────────────────────────────────────────────────────────


def test_la_section_ne_republie_ni_la_frise_ni_la_liste_datee(composant):
    """Les deux vivent dans « En bref », au-dessus. La section 1 ne garde que ce
    que personne d'autre ne montre."""
    section = _corps(composant, 'titre="Les fonctions exercées"', "</Section>")
    assert "<Frise" not in section
    assert "cp-roles" not in section
    assert "Le parcours" not in composant, "le titre ne décrivait plus la section"


def test_la_section_n_a_plus_de_critere_d_en_tete(composant):
    """Il annonçait la section avant qu'on ait rien lu, et il décrivait la frise
    — qui n'y est plus. La règle de lecture est descendue en pied."""
    section = _corps(composant, 'titre="Les fonctions exercées"', "</Section>")
    assert "critere=" not in section


def test_le_pied_documente_la_regle_et_mene_a_la_methodologie(composant):
    """Le lecteur doit pouvoir savoir POURQUOI certaines fonctions sont en avant,
    et aller plus loin s'il le souhaite.

    LA RÈGLE EST LÀ, SON POURQUOI EST AILLEURS (#328). Le pied disait les trois
    règles de lecture en quarante mots — les trois plus longues, le filet à la
    moitié du mandat, le rôle précisé hors « membre ». DESIGN_SYSTEM §7 règle 2
    range cela du côté de l'explication : le pied garde les deux repères qu'on
    voit à l'écran, et le renvoi mène à `#fonctions`, où les trois sont écrites
    avec ce qu'elles ne veulent PAS dire — qu'aucune n'est un palmarès.
    """
    section = _corps(composant, 'titre="Les fonctions exercées"', "</Section>")
    assert "plus longues" in section
    # « un filet passé la moitié du mandat » nommait la FORME du repère ; le pied
    # dit maintenant ce qu'il marque — « ligne surlignée = expérience sur + de la
    # moitié du mandat ». Le repère reste documenté, en clair.
    assert "moitié du mandat" in section
    assert 'to="/methodologie#fonctions"' in section

    methodo = (
        RACINE / "web" / "UI_finale" / "src" / "pages" / "MethodologyPage.jsx"
    ).read_text(encoding="utf-8")
    ancre = methodo[methodo.index("id: 'fonctions'") :]
    ancre = ancre[: ancre.index("id: 'propose'")]
    assert "moitié du temps de mandat" in ancre
    assert "n'est pas celui de membre" in ancre


def test_le_pied_vient_apres_le_contenu(composant):
    """Une section qui s'annonce avant qu'on ait rien lu fait lire la consigne à
    la place du fait."""
    bloc = _corps(composant, "function Section(", "\n}")
    assert bloc.index("cp-section-corps") < bloc.index("cp-section-pied")


def test_le_pied_s_aligne_sur_la_carte(feuille):
    """Une largeur de texte bornée pendant que la carte prend toute la colonne
    fait se répondre deux bords gauches et partir le bord droit tout seul."""
    regle = _corps(feuille, ".cp-section-pied {", "}")
    assert "max-width" not in regle


def test_une_section_vide_dit_pourquoi(composant):
    """Un profil sans mandat collecté ne publie pas une carte vide : il publie sa
    cause, lue dans le bloc `couverture` (§2 règle 5)."""
    section = _corps(composant, 'titre="Les fonctions exercées"', "</Section>")
    assert "<ListeVide" in section
    assert "c.causes.mandats" in section


# ── Les lecteurs de la forme rendue ──────────────────────────────────────────
#
# `fonctionsExercees` a changé de forme le 03/09/2026 : elle rendait un TABLEAU
# de blocs `{cle, titre, total, items[]}`, elle rend un objet
# `{mandat, blocs[]}` dont les lignes portent une durée. La vue a suivi. Le
# second lecteur, lui, n'a pas suivi — et il n'est pas une vue : `vivierDesPoints`
# lit la même forme pour un point dormant, dont « L'essentiel » a emporté le
# rendu sans emporter le calcul. `essentiel()` est appelé sans condition par
# `buildCandidateView` : `(fonctions || []).find(...)` sur un objet lève
# `find is not a function`, et c'est TOUTE la fiche qui ne s'affiche plus, pour
# les treize candidats.
#
# Rien ne l'a vu : les tests du dépôt lisent le source, aucun n'exécute le JS.
# Ce que ces deux-ci verrouillent est donc la seule chose relisable — que les
# lecteurs de cette forme nomment les clés que cette forme porte.


def test_le_vivier_lit_la_forme_que_fonctions_exercees_rend(regles):
    """Un consommateur qui n'est pas une vue ne se voit pas en relisant la page.
    Celui-ci lit `blocs[]` et ses lignes, jamais le tableau d'avant."""
    bloc = _corps(regles, "const commissions = (fonctions?.blocs", "\n  }")
    assert "fonctions?.blocs" in bloc, "le tableau des blocs est sous `blocs`"
    assert ".items" not in bloc, "`items[]` était l'ancienne forme, elle n'existe plus"
    assert "montrees" in bloc and "nbIntitules" in bloc


def test_le_point_des_commissions_parle_en_duree_comme_la_section(regles):
    """Le point dormant portait « 27 mandats en commission sont à la commission
    des affaires sociales » : le compte d'enregistrements que #328 a écarté de
    la section publiée. Le réparer en le laissant compter aurait gardé dans le
    code la mesure que la page vient de désavouer."""
    bloc = _corps(regles, "const commissions = (fonctions?.blocs", "\n  }")
    assert "tete.jours" in bloc and "tete.duree" in bloc
    assert "mandat en commission est" not in bloc


def test_l_adaptateur_passe_la_forme_entiere_sans_la_defaire(regles):
    """Le dénominateur du point est le temps de mandat, qui vit sur `mandat` et
    non sur les blocs : passer `fonctions.blocs` seul obligerait l'adaptateur à
    refaire une mesure, ce que la fiche s'interdit."""
    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    bloc = _corps(adaptateur, "essentiel({", "}),")
    assert re.search(r"\bfonctions,", bloc), "la forme est passée entière"
    assert "fonctions.blocs" not in bloc and "fonctions.mandat" not in bloc


# ── Les fonctions exercées hors du Parlement ─────────────────────────────────
#
# La section ne montrait que les sept catégories parlementaires. Un portefeuille
# ministériel est pourtant un siège occupé — un intitulé, des dates, une durée —
# et 6 des 13 candidats en ont exercé un. Ce qui suit verrouille les
# trois natures que la catégorie `fonction_gouvernementale` mélange, et le fait
# que le discriminant soit SOURCÉ.


def test_le_portefeuille_ministeriel_est_une_fonction_exercee(regles):
    """Un ministère occupé se mesure comme une commission : même bloc, même
    durée, même forme. L'en exclure ne montrait qu'une moitié des fonctions."""
    bloc = _corps(regles, "export const CATEGORIES_FONCTIONS", "\n];")
    assert "'fonction_gouvernementale'" in bloc
    assert "Portefeuilles ministériels" in bloc


def test_les_trois_natures_se_separent_sur_la_fonction_jamais_sur_le_libelle(regles):
    """`fonction_gouvernementale` couvre l'appartenance, le portefeuille et la
    mission. Le champ `fonction` les sépare déjà pour
    `appartenancesGouvernementales` ; filtrer sur « Gouvernement (…) » aurait
    été une jointure par ressemblance de chaîne, que #639 interdit."""
    bloc = _corps(regles, "export const CATEGORIES_FONCTIONS", "\n];")
    assert "FONCTION_MEMBRE" in bloc and "FONCTION_MISSION" in bloc
    assert "Gouvernement (" not in bloc, "aucun filtre sur le libellé"
    assert "startsWith" not in bloc and "includes(" not in bloc


def test_l_appartenance_au_gouvernement_n_est_pas_un_intitule_de_fonction(regles):
    """`fonction: membre` est l'ENVELOPPE — « Gouvernement (BORNE) ». La publier
    doublerait chaque portefeuille d'une ligne qui ne dit pas ce qu'on y
    faisait. Elle reste à la frise, qui en fait une piste."""
    bloc = _corps(regles, "titre: 'Portefeuilles ministériels'", "sansMarque")
    assert "f !== FONCTION_MEMBRE" in bloc


def test_la_mission_aupres_d_un_ministere_a_son_propre_bloc(regles):
    """Un⋅e parlementaire en mission auprès d'un ministère RESTE parlementaire.
    La frise lui donne sa piste depuis le lot ; la ranger avec les ministres
    serait le contresens que la frise évite déjà."""
    bloc = _corps(regles, "Missions auprès d’un ministère", "\n  },")
    assert "f === FONCTION_MISSION" in bloc
    assert "INSTITUTION_MISSION" in bloc


def test_les_deux_blocs_gouvernementaux_ont_des_cles_distinctes(regles):
    """Ils partagent la catégorie `fonction_gouvernementale` : sans suffixe,
    React en monterait deux sous la même clé.

    Depuis le 13/09/2026 la CHAMBRE s'y ajoute, pour la même raison : les deux
    blocs « Commissions » d'une fiche mixte partageraient la leur."""
    fabrique = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "cle: [cle, suffixe, chambre].filter(Boolean).join('_')" in fabrique


def test_la_marque_ne_s_applique_pas_aux_blocs_gouvernementaux(regles):
    """Son dénominateur est le temps de mandat ÉLECTIF, et un portefeuille ne
    s'y compare pas : Édouard Philippe a été Premier ministre trois ans sans
    siéger. La marque aurait affirmé « plus de la moitié » d'un tout dont il
    était absent — un ratio sans son dénominateur (§2 règle 7)."""
    categories = _corps(regles, "export const CATEGORIES_FONCTIONS", "\n];")
    assert categories.count("sansMarque: true") == 2, (
        "les deux blocs gouvernementaux, et eux seuls"
    )
    fabrique = _corps(regles, "export function fonctionsExercees", "\n}")
    assert "if (!sansMarque && lignes.length" in fabrique


def test_la_couleur_dit_le_banc_et_non_la_categorie(regles, composant, feuille):
    """Neuf catégories auraient demandé neuf teintes, en concurrence avec la
    seule grammaire de couleurs de la fiche. Sur un profil qui a connu les deux
    bancs, c'est le banc qu'on aurait perdu — et ce qui sépare une commission
    d'un groupe d'amitié est déjà écrit dans le titre du bloc."""
    categories = _corps(regles, "export const CATEGORIES_FONCTIONS", "\n];")
    # SEPT catégories à l'origine, NEUF depuis le 13/09/2026 : deux organes que
    # la normalisation range sous `categorie: "autre"` — les délégations
    # parlementaires européennes et les groupes de liaison sénatoriaux —
    # entrent par leur `type_organe_source`. 87 mandats de candidats déclarés
    # portent cette catégorie et n'apparaissaient NULLE PART (#885).
    assert categories.count("banc: INSTITUTION_PARLEMENT") == 9
    assert categories.count("banc: INSTITUTION_GOUVERNEMENT") == 1
    assert categories.count("banc: INSTITUTION_MISSION") == 1
    assert "cp-fonctions-bloc--${b.banc}" in composant
    # Une classe par BANC, pas neuf de catégorie. Le banc compte la CHAMBRE
    # depuis le 13/09/2026 : une commission européenne se peignait de la teinte
    # de l'Assemblée (#328). Les catégories, elles, restent sans classe.
    bancs = set(re.findall(r"\.cp-fonctions-bloc--(\w+)", feuille))
    assert bancs == {"parlement", "pe", "senat", "gouvernement", "mission"}, (
        f"une classe par banc, pas par catégorie : {sorted(bancs)}"
    )


def test_la_teinte_du_banc_double_l_intitule_sans_le_remplacer(feuille):
    """La section doit se lire en niveaux de gris et sous daltonisme : le titre
    du bloc nomme la catégorie, la couleur ne fait que la doubler."""
    pastille = _corps(feuille, ".cp-fonctions-bloc--mission .cp-fonctions-titre::before", "\n}")
    assert "dashed" in pastille, (
        "la mission se distingue aussi par la FORME de sa pastille, pas par la seule teinte"
    )


def test_le_banc_ne_prend_pas_le_bord_gauche_du_bloc(feuille):
    """Le bord gauche appartient à la MARQUE, qui déborde jusqu'au bord de la
    carte pour signaler la fonction dépassant la moitié du temps de mandat. Un
    filet de banc au même endroit donnait deux traits verticaux à trois pixels
    l'un de l'autre, que la ligne marquée recouvrait. Deux faits de nature
    différente ne partagent pas un bord : celui-ci revient au seul des deux qui
    qualifie UNE ligne."""
    for banc in ["parlement", "gouvernement", "mission"]:
        regle = _corps(feuille, f".cp-fonctions-bloc--{banc} {{", "\n}")
        assert "border-left" not in regle, f"{banc} ne pose pas de filet à gauche"
        assert "padding-left" not in regle
    marque = _corps(feuille, ".cp-fonctions-item--marquee {", "\n}")
    assert "border-left: 3px solid var(--ink)" in marque, "la marque garde son filet"


def test_le_banc_se_dit_par_la_pastille_et_par_le_titre(feuille):
    """Deux porteurs, pas un : la pastille et la couleur du titre. Et le titre y
    gagne en lisibilité — `--muted` vaut 3,51:1 sur blanc, sous le seuil AA,
    quand le bleu vaut 8,14:1 et le bronze 4,90:1."""
    titres = _corps(feuille, ".cp-fonctions-bloc--parlement .cp-fonctions-titre,", "\n}")
    assert "color: var(--teinte-banc)" in titres
    pastille = _corps(feuille, ".cp-fonctions-titre::before {", "\n}")
    assert "background: var(--teinte-banc)" in pastille
