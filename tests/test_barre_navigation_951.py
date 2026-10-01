"""La barre des pages du site sur l'explorateur, et le symbole mobile (#951).

Ce que ces garde-fous protègent :

1. **Les quatre pages, dans l'ordre retenu** le 16/09/2026 : Explorateur,
   Méthodologie, Sources, FAQ.
2. **Le jaune souligne, il ne colore jamais le texte** : 1,05:1 sur le fond
   clair (DESIGN_SYSTEM §2).
3. **Le symbole porte des traits d'encre.** Il a porté les traits blancs de la
   variante pour fond sombre, et le logo mobile ne montrait plus que le point
   jaune.

CE QU'ILS NE COUVRENT PAS : aucun composant n'est rendu ici. Le comportement —
défilement stable, bouton, panneau, menu — a été vérifié au navigateur à 1 440,
600 et 390 px de large le 16/09/2026.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
NAV = UI / "src" / "components" / "NavigationSite.jsx"
NAV_CSS = UI / "src" / "components" / "NavigationSite.css"
SYMBOLE = UI / "public" / "brand" / "empreinte-symbol-light.svg"
ACCUEIL = UI / "src" / "pages" / "LandingPage.jsx"
EXPLORATEUR = UI / "src" / "components" / "ExplorerLayout.jsx"


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_les_cinq_pages_dans_l_ordre() -> None:
    """« Articles » (#1029) s'insère avant la FAQ : les articles sont une
    lecture du corpus, la FAQ reste la dernière entrée."""
    source = _sans_commentaires(NAV.read_text(encoding="utf-8"))
    libelles = re.findall(r"libelle: '([^']+)'", source)
    assert libelles == ["Explorateur", "Méthodologie", "Sources", "Articles", "FAQ"]


def test_les_instantanes_sont_une_page_statique_pas_une_route() -> None:
    """Servie telle quelle par Pages : un `<Link>` ferait démarrer le routeur
    sur une adresse qu'il ne connaît pas."""
    source = _sans_commentaires(NAV.read_text(encoding="utf-8"))
    assert "statique: true" in source
    assert re.search(r"<a key=\{page\.libelle\} href=\{page\.vers\}", source)


def test_la_page_courante_est_annoncee() -> None:
    source = _sans_commentaires(NAV.read_text(encoding="utf-8"))
    assert "aria-current={courante ? 'page' : undefined}" in source


def test_le_jaune_souligne_sans_colorer_le_texte() -> None:
    css = _sans_commentaires(NAV_CSS.read_text(encoding="utf-8"))
    bloc = css.split(".nav-site-lien--courante {")[1].split("}")[0]
    assert "var(--accent)" in bloc and "box-shadow" in bloc
    couleur = [l for l in bloc.splitlines() if l.strip().startswith("color:")]
    assert couleur and all("accent" not in l for l in couleur)


def test_le_menu_masque_a_sa_regle_css() -> None:
    """`display: flex` l'emporte sur le `[hidden]` du navigateur (#324)."""
    css = _sans_commentaires(NAV_CSS.read_text(encoding="utf-8"))
    assert "display: none" in css.split(".nav-site-menu-liste[hidden] {")[1].split("}")[0]


def test_le_symbole_porte_des_traits_d_encre() -> None:
    svg = SYMBOLE.read_text(encoding="utf-8")
    traits = set(re.findall(r'stroke="(#[0-9a-fA-F]{6})"', svg))
    assert traits == {"#17141f"}, traits


def test_l_accueil_et_l_explorateur_portent_la_meme_rangee() -> None:
    """Une seule rangée, pour qu'elle ne diverge pas d'une page à l'autre."""
    for page in (ACCUEIL, EXPLORATEUR):
        source = _sans_commentaires(page.read_text(encoding="utf-8"))
        assert "<EnTeteSite" in source, page.name
        assert "<Brand />" not in source, f"{page.name} : le logo vient de la rangée"


# ── La page /faq ────────────────────────────────────────────────────────────

APP = UI / "src" / "App.jsx"
PAGE_FAQ = UI / "src" / "pages" / "FaqPage.jsx"
PAGE_STATIQUE = UI / "src" / "components" / "StaticPage.jsx"
COUVERTURE = UI / "src" / "pages" / "CoveragePage.jsx"


def test_faq_mene_a_sa_page() -> None:
    nav = _sans_commentaires(NAV.read_text(encoding="utf-8"))
    assert "vers: '/faq'" in nav and "'/#faq'" not in nav
    assert '<Route path="/faq" element={<FaqPage />} />' in APP.read_text(encoding="utf-8")


def test_les_questions_ne_sont_ecrites_qu_une_fois() -> None:
    """La page lit les questions de l'accueil ; elle ne les recopie pas."""
    page = _sans_commentaires(PAGE_FAQ.read_text(encoding="utf-8"))
    assert "import { QUESTIONS } from '../components/landing/Faq';" in page
    assert "question:" not in page


def test_la_faq_est_un_accordeon_premiere_question_ouverte() -> None:
    """Forme B, retenue le 16/09/2026 entre trois maquettes."""
    page = _sans_commentaires(PAGE_FAQ.read_text(encoding="utf-8"))
    assert "<details" in page and "open={i === 0}" in page


def test_les_pages_statiques_portent_la_rangee_et_plus_le_fil_d_ariane() -> None:
    for page in (PAGE_STATIQUE, COUVERTURE):
        source = _sans_commentaires(page.read_text(encoding="utf-8"))
        assert "<EnTeteSite" in source, page.name
        assert "Retour à l'accueil" not in source, page.name


# ── La page /sources ────────────────────────────────────────────────────────

SCHEMA = UI / "src" / "data" / "schemaSources.js"
CONFIG = UI / "src" / "data" / "sources.config.js"


def test_sources_mene_a_sa_page() -> None:
    nav = _sans_commentaires(NAV.read_text(encoding="utf-8"))
    assert "vers: '/sources'" in nav and "'/couverture'" not in nav


def test_le_schema_et_les_cartes_nomment_les_memes_sources() -> None:
    """Une source dans les cartes sans place dans le schéma ferait mentir la
    figure ; l'inverse laisserait une source sans licence ni cadence."""
    schema = SCHEMA.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    renvois = set(re.findall(r"config: '([^']+)'", schema))
    cartes = set(re.findall(r"^    id: '([^']+)'", config, flags=re.M))
    assert renvois == cartes, (renvois ^ cartes)


def test_chaque_source_du_schema_ouvre_sa_page() -> None:
    """Demandé le 16/09/2026 : le pavé d'une source ouvre la source, dans un
    nouvel onglet."""
    schema = SCHEMA.read_text(encoding="utf-8")
    bloc = schema[schema.index("export const SOURCES_SCHEMA") : schema.index("export const DONNEES_SCHEMA")]
    ids = re.findall(r"\{ id: '([a-z]+)',", bloc)
    urls = re.findall(r"url: '(https://[^']+)'", bloc)
    assert len(urls) == len(ids) == 11
    composant = (UI / "src" / "components" / "SchemaSources.jsx").read_text(encoding="utf-8")
    assert 'target="_blank"' in composant and 'rel="noopener noreferrer"' in composant


def test_aucun_lien_ne_mene_encore_a_couverture() -> None:
    """La redirection sert les liens partagés ; le site, lui, pointe juste."""
    for chemin in (UI / "src").rglob("*.jsx"):
        if chemin.name == "App.jsx":
            continue
        source = chemin.read_text(encoding="utf-8")
        assert 'to="/couverture' not in source and "vers: '/couverture" not in source, chemin.name


def test_les_noeuds_portent_les_infos_et_les_cartes_quittent_sources() -> None:
    """Retenu le 16/09/2026 : infobulle à la souris, bande au doigt, choisies sur
    le pointeur et jamais sur la largeur. Les cartes repliées ne sont plus
    rendues sous le schéma."""
    composant = (UI / "src" / "components" / "SchemaSources.jsx").read_text(encoding="utf-8")
    assert "'(hover: hover) and (pointer: fine)'" in composant
    assert "ss-detail--bulle" in composant and "ss-detail--bande" in composant
    assert "import sourcesConfig from '../data/sources.config';" in composant
    page = (UI / "src" / "pages" / "CoveragePage.jsx").read_text(encoding="utf-8")
    assert "<SchemaSources />" in page and "CartesSources" not in page


def test_la_source_a_venir_ouvre_la_liste_et_ne_compte_pas() -> None:
    """Le Conseil constitutionnel, en tête et à venir, avant Wikipédia qu'il
    remplacera (16/09/2026). Ses dates sont celles de la loi, et l'accueil ne le
    compte pas parmi les sources publiques."""
    schema = SCHEMA.read_text(encoding="utf-8")
    bloc = schema[schema.index("export const SOURCES_SCHEMA") : schema.index("export const DONNEES_SCHEMA")]
    ids = re.findall(r"\{ id: '([a-z]+)',", bloc)
    assert ids[:2] == ["cc", "wp"]
    assert "statut: 'a-venir'" in bloc
    config = CONFIG.read_text(encoding="utf-8")
    entree = config[config.index("id: 'conseil-constitutionnel'") : config.index("id: 'assemblee-nationale-opendata'")]
    assert "aVenir: true" in entree
    assert "12 mars 2027 à 18 h" in entree and "26 mars 2027" in entree and "loi du 6 novembre 1962" in entree
    accueil = (UI / "src" / "components" / "landing" / "HowItWorks.jsx").read_text(encoding="utf-8")
    assert "sourcesConfig.filter((s) => !s.aVenir).length" in accueil


# ── La tête de méthodologie et la forme C de l'accueil ──────────────────────

METHODO = UI / "src" / "pages" / "MethodologyPage.jsx"


def test_la_methodologie_s_ouvre_sur_les_blocs_de_l_accueil() -> None:
    """« Comment ça marche » et « Ce que vous ne trouverez pas ici » ouvrent
    /methodologie, AVANT la première famille."""
    page = METHODO.read_text(encoding="utf-8")
    debut = page.index("const SECTIONS = [")
    assert page.index("{ famille: 'Les principes' }", debut) < page.index("<HowItWorks", debut)
    assert page.index("<HowItWorks", debut) < page.index("<WhatYouWontFind", debut) < page.index("{ famille: 'Fiche candidat' }", debut)


def test_l_accueil_est_le_hero_puis_l_entree_en_deux_temps() -> None:
    """Le Hero sans ses trois boutons, puis l'entrée refondue le 30/09/2026.

    La forme C du 16/09 ouvrait sur la grille des 31 candidats. Le recadrage
    éditorial en fait un volet borné : deux portes permanentes — groupes et
    gouvernements — et les candidats sous leur date.
    """
    accueil = _sans_commentaires(ACCUEIL.read_text(encoding="utf-8"))
    corps = accueil[accueil.index("<main"):accueil.index("</main>")]
    assert re.findall(r"<([A-Z][A-Za-z]+) />", corps) == ["Hero", "CommencerAExplorer"]
    hero = _sans_commentaires((UI / "src" / "components" / "landing" / "Hero.jsx").read_text(encoding="utf-8"))
    assert "landing-cta" not in hero and "Voir un profil" not in hero
    liste = (UI / "src" / "components" / "landing" / "CommencerAExplorer.jsx").read_text(encoding="utf-8")
    # LES TROIS FAMILLES SONT LUES, jamais écrites à la main : un candidat qui se
    # déclare, une lignée qui naît, un gouvernement qui tombe entrent au run suivant.
    for source in ("getCandidatesList", "getGroupsList", "getGovernmentsList"):
        assert source in liste, f"{source} n'alimente plus l'accueil"
    # LE TITRE EST LE SIEN (30/09/2026) : « Commencer à explorer » nommait le
    # geste, « Commencer l'exploration » la chose. Elle a donné le second.
    assert "Commencer l’exploration</h2>" in liste
    assert "cb-chip--sans-mandat" in liste, "le grisé de la barre de l'explorateur, infobulle comprise"
    assert 'to={`/groupes/${l.id}`}' in liste and 'to={`/gouvernements/${g.id}`}' in liste


def test_le_volet_candidats_porte_sa_borne() -> None:
    """« Ponctuel » se lit dans la FORME, pas dans une phrase explicative.

    Sans sa date, l'encart ne dit plus qu'une chose — que les candidats sont en
    dessous —, ce qui est une hiérarchie sans sa raison. La borne est ce qui
    distingue « volet borné par une élection » de « rubrique secondaire ».
    """
    liste = (UI / "src" / "components" / "landing" / "CommencerAExplorer.jsx").read_text(encoding="utf-8")
    assert "BORNE_CANDIDATS" in liste
    assert "2027" in liste, "la borne a perdu sa date"


def test_la_porte_des_groupes_garde_le_mot_du_lecteur() -> None:
    """« GROUPES PARLEMENTAIRES », ET PAS « LIGNÉES » (fermé le 01/10/2026).

    La porte mène aux 12 fiches de LIGNÉE, pas aux 29 groupes réels : le mot et
    l'objet ne désignent donc pas la même chose, et le point est resté ouvert
    depuis le 30/09. **La propriétaire l'a tranché** : « lignées, ça ne parle à
    personne donc on reste sur groupes parlementaires ».

    La raison n'est PAS que le concept serait obscur : l'histoire d'un groupe qui
    change de nom d'une législature à l'autre est parfaitement connue. C'est le
    MOT « lignée » qui est de nous — une terminologie que ce projet s'est donnée —,
    et un mot que nous avons inventé n'a pas à paraître dans l'interface.

    Ne pas « corriger » ce libellé en « lignées » au motif que c'est ainsi que la
    donnée s'appelle : c'est précisément ce qui a été refusé.
    """
    source = _sans_commentaires(
        (UI / "src" / "components" / "landing" / "CommencerAExplorer.jsx").read_text(encoding="utf-8"))
    assert 'libelle="Groupes parlementaires"' in source
    assert "ignée" not in source, "le mot du modèle de données a remplacé celui du lecteur"


def test_la_liste_des_candidats_dit_d_ou_elle_vient() -> None:
    """WIKIPÉDIA, ET JAMAIS WIKIDATA (30/09/2026).

    La liste des candidats déclarés est la seule du site qui ne vienne pas d'une
    source institutionnelle : elle est tenue à la main d'après l'article
    Wikipédia « Candidatures à l'élection présidentielle française de 2027 ».

    Wikidata ne fournit qu'une propriété — `P4123`, l'identifiant du candidat à
    l'Assemblée —, et elle a été ESSAYÉE pour découvrir les candidatures puis
    écartée sur mesure (#753) : la propriété qui les déclare rend 1 personne pour
    2027 contre plus de trente déclarées. L'erreur a déjà été proposée une fois,
    d'où cette garde : écrire « issue de Wikidata » contredirait `/sources` sur la
    provenance d'une liste publiée, ce qui relève de §2 règle 2 et non du style.
    """
    source = (UI / "src" / "components" / "landing" / "CommencerAExplorer.jsx").read_text(encoding="utf-8")
    rendu = _sans_commentaires(source)
    assert "explorer-provenance" in rendu, "la liste des candidats ne dit plus d'où elle vient"
    assert "Wikipédia" in rendu, "la provenance ne nomme plus sa source"
    assert "Wikidata" not in rendu, (
        "la liste vient de Wikipédia ; Wikidata ne fournit que l'identifiant AN (#753)"
    )
    # Elle ne vaut que pour la liste des candidats : au-dessus du bloc, elle
    # qualifierait aussi les groupes et les gouvernements, qui sont institutionnels.
    assert "hidden={ouverte !== 'candidats'}" in rendu

    # LA DATE EST ÉCRITE À DEUX ENDROITS, DONC ELLE PEUT DÉRIVER. Elle vient de
    # l'article 3 de la loi du 6 novembre 1962, et `/sources` la porte déjà sur
    # son entrée « Conseil constitutionnel ». Si l'une des deux bouge sans
    # l'autre, le site annonce deux dates pour le même fait.
    date = re.search(r"const DATE_LISTE_OFFICIELLE = '([^']+)'", source)
    assert date, "la mention n'annonce plus de date"
    config = (UI / "src" / "data" / "sources.config.js").read_text(encoding="utf-8")
    assert date.group(1) in config, (
        f"l'accueil annonce {date.group(1)}, que /sources ne dit nulle part"
    )


def test_explorateur_ne_parait_pas_sur_l_accueil() -> None:
    """Le lien menait à /candidats : il portait la hiérarchie que le recadrage défait.

    Il RESTE sur les autres pages, où il est le seul raccourci vers les fiches —
    d'où une règle conditionnelle à la route, et non une suppression.
    """
    nav = _sans_commentaires((UI / "src" / "components" / "NavigationSite.jsx").read_text(encoding="utf-8"))
    assert "pathname === '/'" in nav and "Explorateur" in nav, (
        "le lien a été retiré partout, ou la condition de route a disparu"
    )


def test_les_mandats_anterieurs_sont_nommes_sous_la_frise_de_sources() -> None:
    """La liste de l'accueil revient sur /sources (16/09/2026), réduite à la
    seule rubrique encore vraie : Sénat et mandats locaux sont collectés depuis
    #885 et #922."""
    page = (UI / "src" / "pages" / "CoveragePage.jsx").read_text(encoding="utf-8")
    frise = page[page.index('id="frise"'):page.index('id="manquants"')]
    assert "<MandatsHorsCouverture fiches={data.accueil?.horsCouverture?.anterieurs} />" in frise
    rendu = _sans_commentaires(page[page.index("function MandatsHorsCouverture"):page.index("function TableManquants")])
    assert "non exploitable" not in rendu and "Mandats locaux et autres" not in rendu


def test_wikipedia_et_wikidata_disent_ce_qu_elles_apportent() -> None:
    """Elles disent QUI est candidat (AGENTS.md §7). Leurs textes disaient
    « suivi biographique complémentaire » et, pour Wikipédia, « citations
    verbatim » — l'inverse de la règle : des faits, jamais de texte."""
    config = CONFIG.read_text(encoding="utf-8")
    wp = config[config.index("id: 'wikipedia-fr'"):config.index("id: 'wikidata'")]
    wd = config[config.index("id: 'wikidata'"):]
    for entree in (wp, wd):
        assert "Suivi biographique" not in entree and "verbatim" not in entree
    assert "nom: 'Wikipédia'" in wp and "jamais de texte" in wp
    assert "P4123" in wd
