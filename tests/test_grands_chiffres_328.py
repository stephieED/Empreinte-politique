"""« Les grands chiffres » — le bloc de tête de la fiche candidat (#328).

Ce que ce fichier verrouille est ce qui a coûté quinze allers-retours de
maquette, et que rien dans le code ne rappelle une fois écrit :

- le bloc est un **tableau de bord**, pas un résumé, et il est nommé pour ce
  qu'il est — « Coup d'œil » et « L'essentiel » ont été essayés et écartés ;
- **chaque colonne compte contre son propre total** : les additionner ou les
  comparer transformerait deux métiers en deux notes (§2 règle 1) ;
- **le texte explicatif est un aveu d'échec** : la ligne d'introduction a été
  réduite trois fois, jusqu'à cinq mots ;
- deux absences ne se confondent jamais — un **tiret** est un fait sur le
  métier (« un ministre ne dépose pas d'amendement »), une **liste vide** est
  un fait sur la collecte (§2 règle 5).

Les tests lisent le **code exécuté** (commentaires retirés) : une règle
énoncée en commentaire et absente du code passerait sinon au vert.

Ce qui n'est PAS couvert ici : la mise en page rendue, le responsive, le
contraste et le parcours clavier. Le rendu `react-dom/server` des 13 profils
publiés a été fait hors dépôt, et il ne remplace pas une relecture à l'écran.
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


@pytest.fixture(scope="module")
def adaptateur() -> str:
    return sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))


def _corps(source: str, debut: str, fin: str) -> str:
    i = source.index(debut)
    return source[i : source.index(fin, i)]


def _media_etroit(feuille: str) -> str:
    """Le bloc `@media (max-width: 720px)` qui règle « Les grands chiffres ».

    La feuille en porte trois, et le bloc visé n'est pas le premier : viser par
    `index` lisait celui de la mise en page générale, et le test passait au vert
    sur la mauvaise règle. On retient donc le bloc **par son contenu**.
    """
    morceaux = feuille.split("@media (max-width: 720px)")
    vises = [m for m in morceaux[1:] if "overflow-x: auto" in m and ".cp-gc-duo--deux" in m]
    assert len(vises) == 1, (
        "un seul bloc étroit règle le tableau des grands chiffres ; "
        f"{len(vises)} trouvé(s)"
    )
    # Jusqu'à la règle qui ferme le bloc, la dernière que la media query porte.
    fin = vises[0].index(".cp-gc-barre")
    return vises[0][: vises[0].index("\n}", vises[0].index("}", fin))]



# ── Le nom, et la ligne qui l'accompagne ────────────────────────────────────


def test_le_bloc_s_appelle_en_bref(composant):
    """Quatre noms ont été essayés. « Coup d'œil » promettait de la rapidité et
    non du contenu ; « L'essentiel » promettait une synthèse que le bloc ne
    délivre pas ; « Les grands chiffres » nommait honnêtement un tableau de bord,
    mais le bloc a changé de contenu — la frise et le détail daté y sont
    descendus, et « chiffres » ne les couvre plus. « En bref » les couvre tous.

    Le nom porte le format d'un titre de SECTION, pas d'une étiquette : c'est ce
    qui le met au même rang que « Les fonctions exercées » juste dessous."""
    assert "En bref" in composant
    assert "Les grands chiffres" not in composant
    assert "Coup d’œil" not in composant and "Coup d'œil" not in composant
    assert "L’essentiel" not in composant
    # Le `span` interne porte le surlignage jaune commun à tous les titres de
    # section : le dégradé posé sur le `h2`, bloc de la largeur de la colonne,
    # courrait jusqu'au bord et se lirait comme un fond de section.
    assert '<h2 className="cp-section-titre"><span>En bref</span></h2>' in composant, (
        "même bande, même filet, même h2 que les titres de section"
    )
    assert "cp-gc-label" not in composant, (
        "l'étiquette propre au bloc part avec le format qu'elle portait"
    )


def test_la_these_tient_en_une_ligne(composant):
    """Réduite trois fois. Le motif de chaque coupe est le même : si une phrase
    doit expliquer un chiffre, c'est la forme qui n'a pas fait son travail."""
    assert "Ce que cette personne a engagé, en chiffres." in composant
    bloc = _corps(composant, "Ce que cette personne a engagé", "</summary>")
    assert bloc.count(".") <= 2, (
        "la thèse est une phrase, pas un paragraphe : le texte explicatif est "
        "un aveu d'échec"
    )


def test_ce_qui_se_replie_est_la_partie_dense_pas_la_frise(composant):
    """La frise est l'ossature : elle donne aux colonnes leur couleur et leur
    raison d'être. Replier le bloc entier cachait ce qui explique le reste —
    relevé en relecture d'écran le 02/09/2026. Le `<details>` n'enveloppe donc
    que les colonnes, et la frise reste dehors."""
    bloc = _corps(composant, "function GrandsChiffres(", "export default function")
    assert bloc.index('className="cp-gc-frise"') < bloc.index("<details"), (
        "la frise est AVANT le pli : elle ne se replie pas"
    )
    assert bloc.index("<details") < bloc.index('className={`cp-gc-duo'), (
        "ce sont les colonnes que le pli enveloppe"
    )


def test_la_these_est_la_poignee_et_precede_les_colonnes(composant):
    """« À déplacer avant À l'Assemblée » : la thèse introduit LES COLONNES, pas
    le parcours. Elle sert de `<summary>`, donc de poignée à ce qu'elle
    annonce."""
    bloc = _corps(composant, "function GrandsChiffres(", "export default function")
    assert '<summary className="cp-poignee">' in bloc
    assert bloc.index("a engagé, en chiffres") < bloc.index("cp-gc-tete-col"), (
        "la thèse se lit avant l'en-tête « À l'Assemblée »"
    )


def test_le_pli_porte_un_plus_visible(composant, feuille):
    """Un `<details>` sans marqueur ne dit pas qu'il s'ouvre. Le « + » est
    dessiné et non écrit — deux glyphes changeraient de chasse et feraient
    sauter la ligne."""
    bloc = _corps(composant, "function GrandsChiffres(", "export default function")
    assert 'className="cp-poignee-plus"' in bloc
    assert ".cp-pli[open] .cp-poignee-plus::after" in feuille, (
        "la barre verticale disparaît à l'ouverture : « + » devient « − »"
    )
    assert ".cp-poignee::-webkit-details-marker" in feuille, (
        "le triangle natif est retiré, sinon deux marqueurs cohabitent"
    )


def test_chaque_colonne_compte_contre_son_propre_total(regles):
    """« 580 situées » d'un côté, « 2 759 » de l'autre : le total du profil
    n'apparaît nulle part, et les deux colonnes ne se mélangent pas."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "cotes[cote]" in bloc, (
        "chaque cellule se calcule sur les interventions de SON côté, jamais "
        "sur la liste entière"
    )
    for interdit in ("cotes.parlement.length + ", "+ cotes.gouvernement.length"):
        assert interdit not in bloc, (
            "les deux colonnes ne s'additionnent jamais : ce sont deux métiers, "
            "pas deux parts d'un tout"
        )


def test_le_partage_des_interventions_est_date_jamais_global(regles):
    """`depuisLeBancDuGouvernement` rend une qualité pour TOUT le profil. Ici il
    faut savoir, prise de parole par prise de parole, de quel banc elle vient —
    et c'est la date d'appartenance qui le dit."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "const auBanc = (date) =>" in bloc
    assert "appartenances.some((a) => a.debut <= date && date <= (a.fin" in bloc
    assert "depuisLeBancDuGouvernement(" not in bloc, (
        "la qualité globale ne peut pas trancher un partage par date"
    )


def test_un_tiret_est_un_fait_sur_le_metier_pas_une_liste_vide(regles):
    """« Un ministre ne dépose pas d'amendement » n'est pas « la liste est
    vide » : confondre les deux ferait lire un trou de collecte là où il y a un
    fait institutionnel (§2 règle 5)."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "celluleAbsente('un ministre ne dépose pas d’amendement')" in bloc
    assert "celluleAbsente('un ministre ne siège pas en commission')" in bloc


def test_une_ligne_sans_aucun_chiffre_ne_s_affiche_pas(regles):
    """Cinq rangs vides ne décrivent pas une personne, ils décrivent le
    gabarit."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "const retenues = lignes.filter(" in bloc


def test_le_troisieme_cas_ne_rend_aucune_ligne(regles):
    """Trois des 13 candidats n'ont ni mandat parlementaire ni
    appartenance gouvernementale. Le bloc n'a rien à montrer, et il le dit
    plutôt que d'afficher cinq tirets : l'arbitrage sur le travail européen et
    municipal est ouvert, pas rendu."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "if (cas === CAS_RIEN_A_MONTRER)" in bloc
    assert "lignes: []" in bloc


# ── Ce que chaque chiffre porte ─────────────────────────────────────────────


def test_aucun_nombre_ne_domine_les_autres(feuille):
    """Forme « la phrase », retenue le 11/09/2026 : les grands chiffres donnaient
    à 3 933 interventions le poids visuel de 28 textes portés. Le nombre est en
    gras AU CORPS DU TEXTE, et l'objet se lit à la même taille, dans la même encre."""
    i = feuille.index(".cp-gc-n {")
    phrase = feuille[i : feuille.index("}", i)]
    j = feuille.index(".cp-gc-n small {")
    objet = feuille[j : feuille.index("}", j)]
    assert "font-size: 15px" in phrase and "font-size: 15px" in objet
    assert "color: var(--ink)" in objet
    assert "font-size: 24px" not in phrase


def test_le_total_du_rang_vient_en_tete(regles):
    """« 309 sur 3 595 », « 16 mandats sur 36 » : le détail passait avant le
    total qu'il détaille. Le nombre de la cellule est désormais le TOTAL."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "nombre: lot.length,\n      objet: pluriel(lot.length, 'mandat', 'mandats')" in bloc
    assert "nombre: lot.length,\n      objet: pluriel(lot.length, 'intervention', 'interventions')" in bloc
    assert "objet: 'amendements sur'" not in bloc


def test_la_concentration_ne_s_affirme_que_la_ou_elle_se_prouve(regles):
    """Une ligne « N d'entre eux sur X » n'apparaît que si ce texte porte plus
    que tous les autres RÉUNIS. Aucune constante arbitraire : c'est un fait, pas
    un seuil. Un percentile a été essayé et écarté — un P90 sélectionne toujours
    10 % des dossiers, donc il ne peut jamais se taire."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "tete.depots * 2 > totalAuteur" in bloc, (
        "le critère est « plus que tous les autres réunis », et il s'écrit sans "
        "constante"
    )
    assert not re.search(r"\b0\.(8|9)\b|percentile|P90", bloc), (
        "aucun seuil arbitraire ne décide qu'il y a une concentration"
    )


def test_les_roles_de_texte_sont_nommes_un_par_un(regles):
    """Être RAPPORTEUR d'une proposition n'est pas en être l'auteur : replier
    les rôles sur l'institution afficherait « 3 propositions de loi » pour 2
    propositions et 1 rapport."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "ROLES_PROPOSITION = ['auteur_proposition_de_loi', 'auteur_proposition_de_resolution']" in bloc
    assert "t.roleCle === 'initiateur_projet_de_loi'" in bloc


def test_le_seuil_de_publication_des_textes_se_dit(regles):
    """AGENTS.md §6 ne publie par défaut qu'un texte parvenu au moins en
    commission. Taire les autres ferait lire « 2 » comme « il n'en a déposé que
    2 » (§2 règle 5)."""
    bloc = _corps(regles, "export function grandsChiffres(", "\nexport ")
    assert "textes?.ecartes?.total" in bloc
    assert "parvenu au moins en commission" in bloc


# ── La frise : l'ossature ───────────────────────────────────────────────────


def test_la_teinte_d_un_banc_est_declaree_une_seule_fois(feuille):
    """La couleur fait le lien entre une piste, une colonne et un bloc de
    fonctions — encore faut-il que ce soit LA MÊME.

    Ce test vérifiait que DEUX copies du même bleu n'avaient pas divergé. Une
    valeur qu'un test doit surveiller pour rester unique est une valeur qui
    n'aurait pas dû être copiée : les deux teintes sont désormais déclarées une
    seule fois, sur `.cp-main`, et tous leurs lecteurs les lisent (#328). Le
    test vérifie donc l'unicité, plus la coïncidence."""
    fiche = _corps(feuille, ".cp-main {", "\n}")
    # Quatre institutions, quatre teintes, et une encre d'absence.
    #
    # RÉÉCRIT LE 16/09/2026, ET CE QU'IL TENAIT. Il exigeait `--senat:
    # var(--neutre)` : le Sénat n'avait pas de teinte propre, sa collecte étant
    # hors périmètre (#528), et la sarcelle lui était réservée « pour le jour où
    # elle serait rebranchée ». Ce jour est #885 — les appartenances sont
    # collectées —, la sarcelle a été retenue le 15/09 sur /couverture, et la
    # propriétaire l'a demandée sur la fiche le 16/09. Le gris passe aux mandats
    # locaux, qui ne sont pas une institution (`frise-segments-pleins-et-senat-885`
    # §4). La règle que le test protège ne change pas : chaque teinte déclarée
    # une seule fois, et lue par tous.
    teintes = {
        "--parl": "#803060", "--gouv": "#85510d", "--pe": "#003399",
        "--senat": "#169e9e", "--neutre": "#9a958d",
    }
    for jeton, valeur in teintes.items():
        assert f"{jeton}: {valeur}" in fiche, f"`{jeton}` est déclaré sur la fiche"
        assert feuille.count(valeur) == 1, (
            f"`{valeur}` une seule fois : une seconde occurrence est une copie qui divergera"
        )
    # Les mandats locaux POINTENT sur l'encre des absences, sans la recopier :
    # une valeur recopiée divergerait le jour où l'une bouge.
    assert "--local: var(--neutre)" in fiche, (
        "les mandats locaux lisent l'encre des absences, sans la recopier"
    )
    for regle, jeton in [
        (".cp-fs--parlement {", "var(--parl)"),
        (".cp-fs--senat {", "var(--senat)"),
        (".cp-fs--local {", "var(--local)"),
        (".cp-fs--gouvernement {", "var(--gouv)"),
        (".cp-fonctions-bloc--parlement {", "var(--parl)"),
        (".cp-fonctions-bloc--gouvernement {", "var(--gouv)"),
    ]:
        assert jeton in _corps(feuille, regle, "\n}"), f"{regle} lit la déclaration"


def test_aucune_feuille_ne_porte_de_theme_sombre(feuille):
    """L'UI n'a pas de mode nuit — `index.css` déclare `color-scheme: light` et
    aucun script ne pose `data-theme`. `.cp-gc` en portait pourtant un fragment,
    seul de tout `src/` : douze variables qui ne rendaient rien, mesurées au
    pixel près identiques sous les deux préférences système. Le lot
    institutionnel devait le doubler pour `--pe` et `--senat` ; il le retire.
    Un mode nuit se décide pour la fiche entière ou ne se décide pas
    (docs/decisions/bloc-sombre-mort-retire-328.md)."""
    assert "prefers-color-scheme" not in feuille
    assert "[data-theme='dark']" not in feuille

    racine = Path(__file__).resolve().parents[1] / "web" / "UI_finale" / "src"
    porteurs = [
        chemin.relative_to(racine).as_posix()
        for chemin in sorted(racine.rglob("*.css"))
        if "prefers-color-scheme" in chemin.read_text(encoding="utf-8")
        or "[data-theme=" in chemin.read_text(encoding="utf-8")
    ]
    assert porteurs == [], (
        "un thème sombre laissé sur un seul bloc repeint ce bloc et rien d'autre : "
        f"{porteurs}"
    )


def test_les_colonnes_ont_une_gouttiere(feuille):
    """Zéro espacement entre deux colonnes appariées les fait lire comme une
    seule mesure coupée en deux."""
    bloc = _corps(feuille, ".cp-gc-duo {", "\n}")
    assert "column-gap:" in bloc


# ── L'adaptateur ────────────────────────────────────────────────────────────


def test_aucune_mesure_n_est_refaite_dans_l_adaptateur(adaptateur):
    """Le bloc reçoit les objets DÉJÀ calculés. Recalculer ici ferait porter à la
    fiche deux comptes du même fait, qui divergeraient au premier ajustement —
    c'est la duplication que #672 a fermée sur `isWholeTextVote`."""
    bloc = _corps(adaptateur, "grandsChiffres: grandsChiffres({", "}),")
    for passe in ("roles", "mandats", "amendements", "textes", "interventions", "appartenances"):
        assert re.search(rf"^\s+{passe},$", bloc, re.M), f"`{passe}` n'est plus passé au bloc"

# ── L'écran étroit ──────────────────────────────────────────────────────────


def test_sous_le_seuil_le_tableau_defile_au_lieu_de_s_empiler(feuille):
    """Empilé, chaque titre de rang se lisait DEUX FOIS de suite — 10 titres pour
    5 rangs — et les deux en-têtes de rôle restaient en haut, séparés de leurs
    cellules par tout le tableau : plus aucune cellule ne disait à quel rôle elle
    appartenait. En défilement, l'en-tête ne quitte jamais sa colonne.

    Le gabarit a changé avec #328 : le rang est écrit UNE fois, dans une colonne
    de libellés en tête de ligne, et les institutions peuvent être quatre. Chaque
    largeur reprend donc `var(--gc-libelle)` avant ses colonnes, et la colonne
    des libellés reste collée à gauche pendant le défilement — un chiffre isolé
    ne dit plus de quoi il est le compte."""
    bloc = _media_etroit(feuille)
    for n, mot in ((2, "deux"), (3, "trois"), (4, "quatre")):
        attendu = f"grid-template-columns: var(--gc-libelle) repeat({n}, minmax(210px, 1fr))"
        assert attendu in bloc, (
            f"les {mot} colonnes restent côte à côte, avec une largeur plancher"
        )
    assert "overflow-x: auto" in bloc
    assert "position: sticky" in bloc, "la colonne des libellés ne quitte pas l'écran"
    assert "grid-template-columns: 1fr;" not in bloc, (
        "l'empilement est précisément ce que ce seuil ne fait PAS"
    )


def test_l_appariement_survit_a_l_ecran_etroit(regles, composant):
    """Tout le bloc repose sur « des objets de même nature se font face ». Des
    onglets par rôle ont été écartés pour cela : ils ne montrent jamais les deux
    ensemble. Une seule grille, donc, quel que soit l'écran.

    #328 ouvre le repli d'une colonne par le lecteur, ce que ce test interdisait
    en bannissant `useState`. Ce n'est pas le retour des onglets, et trois
    propriétés le garantissent — elles sont ce que ce test vérifie désormais :

    - toutes les colonnes sont OUVERTES au départ, sauf le Sénat nommément, qui
      ne porterait que des cellules vides (#528) ;
    - on ne peut jamais tout replier : la dernière colonne ouverte ne se replie
      pas, sans quoi il ne resterait que le gabarit ;
    - une colonne repliée reste NOMMÉE par sa puce, allumée ou éteinte : replier
      n'efface pas, et le lecteur défait son geste.

    Un onglet ne remplit aucune des trois : il choisit à la place du lecteur, et
    il ne montre jamais les deux ensemble.
    → docs/decisions/colonnes-repliables-en-bref-328.md
    """
    bloc = _corps(composant, "function GrandsChiffres(", "export default function")
    for interdit in ("onglet", "Tab", "role === "):
        assert interdit not in bloc, (
            f"`{interdit}` : le choix d'un rôle à l'écran romprait l'appariement"
        )
    assert "function repliParDefaut(colonnes)" in composant, (
        "l'état d'ouverture est nommé et justifié, pas improvisé dans le rendu"
    )
    assert "INSTITUTION_SENAT" in _corps(composant, "function repliParDefaut(", "\n}"), (
        "le Sénat est la SEULE colonne repliée d'entrée, et elle est nommée"
    )
    assert "ouvertes.length === 1" in bloc, "la dernière colonne ouverte ne se replie pas"
    assert 'aria-pressed={!replies.has(c)}' in bloc, (
        "une colonne repliée reste nommée par sa puce, et le geste se défait"
    )


def test_l_ombre_de_defilement_ne_ment_pas(feuille):
    """Sans signal, la colonne « Au gouvernement » n'existe pas pour le lecteur ;
    avec un dégradé permanent, elle mentirait une fois la course finie. Deux
    calques `local` masquent deux calques `scroll` : l'ombre n'apparaît que s'il
    reste du contenu de ce côté."""
    bloc = _media_etroit(feuille)
    assert bloc.count("no-repeat local") == 2, "deux calques suivent le contenu"
    assert bloc.count("no-repeat scroll") == 2, "deux calques restent aux bords"
    assert "var(--gc-ombre)" in bloc


def test_le_nombre_de_colonnes_ne_vient_pas_d_un_style_en_ligne(composant, feuille):
    """Une valeur en ligne ne se surcharge qu'avec `!important`, que le prochain
    ajustement oublierait. La classe porte la largeur, la media query la reprend
    sans forcer."""
    bloc = _corps(composant, "function GrandsChiffres(", "export default function")
    assert "gridTemplateColumns" not in bloc
    assert ".cp-gc-duo--deux {" in feuille
    i = feuille.index(".cp-gc {")
    assert "!important" not in feuille[i : feuille.index(".cp-section {")], (
        "aucune règle du bloc n'a besoin de `!important`"
    )

def test_le_bloc_reprend_la_frise_du_parcours_et_non_une_copie(composant):
    """Relevé en relecture d'écran le 03/09/2026 : « reprends exactement la même
    frise que dans la section parcours, avec la légende et le détail daté ».

    Le bloc en portait une SECONDE — pistes par institution, étiquettes propres,
    légende propre — et c'est exactement ce que #672 a fermé sur
    `isWholeTextVote` : deux définitions du même objet, qui divergent au premier
    ajustement. `Frise` porte déjà la bande, la légende et la liste datée."""
    bloc = _corps(composant, "function GrandsChiffres(", "export default function")
    assert "<Frise parcours={parcours} />" in bloc, (
        "le bloc appelle LE composant `Frise`, il n'en dessine pas un autre"
    )
    assert composant.count("function Frise(") == 1, "une seule frise dans le module"
    for mort in ("PisteFrise", "LegendePostures", "cp-gc-rail", "cp-gc-seg"):
        assert mort not in composant, f"`{mort}` était la seconde frise"


def test_la_fabrique_de_pistes_est_retiree_avec_la_copie(regles):
    """`pistesDuParcours` et son vocabulaire n'alimentaient que la seconde frise.
    Les laisser en place, exportés et testés, aurait maintenu une fabrique que
    plus rien n'appelle — et la prochaine vue s'en serait resservie."""
    for mort in ("pistesDuParcours", "ETIQUETTE_PISTE", "ORDRE_PISTES"):
        assert mort not in regles, f"`{mort}` n'a plus de consommateur"
    assert "LIBELLE_PISTE" in regles, (
        "il survit : il nomme les COLONNES, que la frise du parcours ne porte pas"
    )

def test_tous_les_plis_partagent_une_seule_poignee(composant, feuille):
    """« Ce que cette personne a engagé, en chiffres. » et « Détails du parcours »
    sont deux plis de MÊME NATURE. Leur donner deux tailles faisait crier l'un
    plus fort que l'autre sans raison — relevé à l'écran le 03/09/2026. Une seule
    classe, donc, et non deux qui divergeraient au premier ajustement.

    La règle a été écrite sur deux plis ; elle n'en visait pas le nombre. Depuis
    que « Les fonctions exercées » ouvre les siens (« N autres »), c'est la
    propriété qui compte qui est vérifiée : AUCUN pli ne se donne sa propre
    poignée. Compter les plis aurait fait échouer ce test à chaque pli ajouté,
    sans que rien de ce qu'il protège ait bougé."""
    poignees = composant.count('className="cp-poignee"')
    assert poignees >= 2, "les plis du bloc de tête portent la classe commune"
    assert composant.count("<summary") == poignees, (
        "chaque pli ouvre sur la poignée commune, aucun n'en invente une autre"
    )
    for morte in ("cp-gc-these", "cp-gc-plus", "cp-gc-plis"):
        assert morte not in composant and morte not in feuille, (
            f"`{morte}` était la forme propre au bloc"
        )


def test_les_deux_plis_sont_fermes_par_defaut(composant):
    """Le bloc s'ouvre sur la FRISE SEULE : elle est ce que le lecteur voit sans
    effort, les chiffres et le détail sont ce qu'il déplie s'il veut. C'est la §7
    de la décision appliquée aux deux moitiés du bloc plutôt qu'à l'ensemble."""
    assert "<details className=\"cp-pli\" open>" not in composant
    assert composant.count('<details className="cp-pli">') == 2


def test_le_detail_date_du_parcours_se_replie(composant):
    """Le détail daté n'a pas à s'imposer entre la frise et ce qui suit."""
    bloc = _corps(composant, "function Frise(", "\nfunction ")
    assert "Détails du parcours" in bloc
    assert bloc.index("<details") < bloc.index('<ul className="cp-roles">'), (
        "le pli enveloppe la liste datée"
    )


def test_la_legende_ne_porte_plus_de_note(composant):
    """La note disait « Majorité, minorité et opposition selon l'AN » — la seule
    phrase de la fiche qui rattachait les trois postures à l'Assemblée plutôt
    qu'à nous (§2 règle 2). Elle est partie avec ce qu'elle nommait : la frise ne
    porte plus la qualification du groupe, seulement l'institution.

    Ce que ce test garde, c'est le FAIT qu'elle portait, pas sa formulation. La
    qualification reste écrite en toutes lettres dans la liste des rôles, et son
    attribution à l'Assemblée est dite deux fois ailleurs : par la limite de
    couverture (« n'est pas déclarée par l'Assemblée sur N de ses M mandats ») et
    par la méthodologie. Si ces deux-là disparaissaient, la fiche publierait une
    qualification sans dire d'où elle vient."""
    assert 'className="cp-legende-note"' not in composant, (
        "la note est retirée avec les motifs de groupe qu'elle expliquait"
    )
    assert "selon l’AN" not in composant

    regles = MODULE_REGLES.read_text(encoding="utf-8")
    assert "n'est pas déclarée " in regles and "l'Assemblée" in regles, (
        "l'attribution des trois postures à l'Assemblée survit dans la limite de couverture"
    )


# ── Les teintes des stades : une déclaration, deux lectures ──────────────────
#
# Trois défauts de couleur ont vécu en production dans ce bloc, et aucun test ne
# les voyait — la suite était verte à 3 720 le jour où ils ont été trouvés à
# l'écran. Tous les trois viennent du même geste : une classe qui décide d'un
# FOND et qu'on pose sur autre chose qu'un fond.


def test_la_barre_des_stades_a_quitte_le_bloc(composant, regles):
    """Retirée le 11/09/2026 : le bloc ne garde que des nombres ; les stades se
    lisent dans la cascade de « Ce qu'il a proposé »."""
    assert 'className="cp-gc-barre"' not in composant
    assert "barreDesStades(" not in regles


def test_la_pastille_porte_la_teinte_et_le_libelle_reste_neutre(feuille):
    """`background: currentColor` rendait les cinq pastilles grises, donc
    identiques : la légende n'identifiait plus rien. La pastille prend la teinte,
    le libellé garde `--muted` — c'est la pastille qui identifie."""
    pastille = _corps(feuille, ".cp-gc-barre-leg em::before {", "\n}")
    assert "var(--teinte" in pastille
    legende = _corps(feuille, ".cp-gc-barre-leg {", "\n}")
    assert "color: var(--muted)" in legende


def test_la_famille_de_teintes_vient_de_la_cellule_pas_de_ses_freres(composant, feuille):
    """`.cp-gc-tete-col--gouvernement ~ * .cp-gc-part--promulgue` partait de
    l'en-tête « gouvernement » et descendait sur TOUS ses frères. Dans la
    grille, les cellules de la colonne parlementaire viennent après cet
    en-tête : la barre « 2 promulgué » de l'Assemblée était brune."""
    assert "cp-gc-tete-col--gouvernement ~" not in feuille, (
        "aucune couleur ne se décide par voisinage dans la grille"
    )
    assert "cp-gc-cell--${piste}" in composant, "la cellule porte sa colonne"
    assert "piste={c}" in composant, "et la colonne lui est passée"
    assert ".cp-gc-cell--gouvernement {" in feuille


def test_les_deux_colonnes_ont_chacune_leur_famille_entiere(feuille):
    """Seul `promulgue` basculait au brun : les quatre autres stades restaient
    bleus dans la colonne du gouvernement, qui affichait donc une barre à deux
    familles. La famille bascule en entier, ou elle ne veut rien dire."""
    parlement = _corps(feuille, ".cp-gc-cell {", "\n}")
    gouvernement = _corps(feuille, ".cp-gc-cell--gouvernement {", "\n}")
    for i in range(1, 6):
        assert f"--t{i}:" in parlement, f"la famille parlementaire déclare --t{i}"
        assert f"--t{i}:" in gouvernement, f"la famille gouvernementale déclare --t{i}"
    assert "--gouv" in gouvernement and "--parl" not in gouvernement


def test_la_rampe_des_cinq_stades_monte(feuille, regles):
    """`examine_commission` valait `--parl-line` et `inscrit_ordre_jour`
    `--parl-pale`, plus CLAIR : la rampe descendait puis remontait. Et
    `discute_seance` reprenait `--parl-line`, identique à
    `examine_commission` — deux segments voisins de la même couleur ne se
    distinguent pas. Un stade plus avancé n'est pas « mieux » (§2 règle 1) :
    c'est un ordre publié par la source, et la rampe le suit."""
    stades = re.search(r"STADES_PUBLIES = \[(.*?)\]", regles, re.DOTALL).group(1)
    ordre = re.findall(r"'([a-z_]+)'", stades)
    assert len(ordre) == 5
    degres = [
        re.search(rf"\.cp-gc-stade--{stade} \{{ --teinte: var\(--t(\d)\)", feuille)
        for stade in ordre
    ]
    assert all(degres), "chaque stade publié porte un degré de la rampe"
    assert [int(m.group(1)) for m in degres] == [1, 2, 3, 4, 5], (
        "la rampe suit l'ordre des stades, sans palier ni retour en arrière"
    )


def test_un_segment_de_siege_ne_porte_que_le_sigle_et_la_place(composant, regles):
    """Maquette « En bref » du 11/09/2026 : sur la frise, un siège ne dit que le
    sigle de son groupe et sa place dans l'hémicycle. Plus de nom long, plus de
    repli sur la fonction, qui répétait la légende ; un sigle ne se fabrique pas."""
    bloc = _corps(composant, "function candidatesEtiquette(", "\n}\n")
    assert "role.sigle" in bloc
    assert "candidates.push(role.role)" not in bloc
    assert "export function sigleDuSiege(" in regles
