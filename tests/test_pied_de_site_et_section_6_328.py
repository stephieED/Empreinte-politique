"""Le pied du site, le badge de source, et ce que §6 cesse de répéter (#328).

TROIS DÉFAUTS DE LA MÊME FAMILLE : la fiche disait plusieurs fois ce qui est
vrai une fois, et elle affirmait deux choses qu'elle ne mesure pas.

1. **Le pied.** Il y en avait trois — `landing-footer`, `explorer-footer`, et
   rien du tout sur les pages statiques : le contact et les deux comptes étaient
   absents de la méthodologie, des mentions légales et de la couverture. Un seul
   composant les rend désormais, sur les quatre carcasses.

2. **Le badge « Source vérifiée ».** Il n'atteste ni une vérification que nous
   ne faisons pas, ni une autorité qu'il ne mesure pas : il est vrai quand un
   `source_url` existe et qu'il est publié. « Source officielle » a été écarté
   sur mesure — sur les 23 499 liens publiés des 32 fiches candidats, des 19
   fiches de groupe et des 10 fiches de gouvernement, **511 pointent vers
   nosdeputes.fr**, un tiers. Le mot aurait été faux 511 fois.

3. **§6 répétait le corpus, et se répétait.** Sur la page rendue de
   `delphine-batho`, « aucun classement » apparaissait **trois fois** ; les
   preuves de borne pesaient **6 413 des 8 328 mots** rendus sur les 32 fiches ;
   et deux phrases affirmaient ce que rien ne vérifie.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici,
et **aucun test ne lit `pivot_data/`** — la CI monte le dépôt en sparse-checkout
sans le corpus (AGENTS.md §3b). Le rendu a été vérifié hors dépôt sur le paquet
construit : le pied sur les quatre pages (148 px, deux icônes), et §6 sur six
fiches — Mélenchon 358 → 185 mots, Retailleau 870 → 237, Tondelier 441 → 133.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
PIED = SRC / "components" / "PiedDeSite.jsx"
FICHE = SRC / "components" / "CandidateProfile.jsx"
PROFIL = SRC / "utils" / "profilCandidat.js"
LECTURE = SRC / "utils" / "lecture.js"
EXPLORATEUR = SRC / "components" / "ExplorerLayout.jsx"


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def fiche() -> str:
    return _sans_commentaires(FICHE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def profil() -> str:
    return _sans_commentaires(PROFIL.read_text(encoding="utf-8"))


# ── Le badge dit ce qu'il fait, et rien de plus ─────────────────────────────


def test_le_badge_ne_dit_plus_verifiee() -> None:
    """« Vérifiée » affirmait un contrôle que nous ne faisons pas."""
    donnees = LECTURE.read_text(encoding="utf-8")
    assert "export const SOURCE_BADGE_VERIFIED = 'Source';" in donnees
    assert "export const SOURCE_BADGE_UNPUBLISHED = 'Lien de source non publié';" in donnees, (
        "l'état absent parle de NOUS et reste juste : il ne bouge pas"
    )


def test_aucune_copie_du_libelle_n_est_ecrite_en_dur() -> None:
    """Trois composants portaient la chaîne à la main — trois divergences en attente."""
    for chemin in SRC.rglob("*.jsx"):
        source = chemin.read_text(encoding="utf-8")
        assert "Source vérifiée" not in source, f"{chemin.name} écrit le libellé en dur"
        assert "Fait vérifié" not in source, (
            f"{chemin.name} promet une vérification que le badge ne fait pas"
        )


# ── Le pied du site : un seul, sur toutes les pages ─────────────────────────


def test_le_pied_porte_l_adresse_en_clair() -> None:
    """C'est ce qui distingue ce rendu : l'adresse se copie sans survol ni clic."""
    source = PIED.read_text(encoding="utf-8")
    assert ">{CONTACT}</a>" in source.replace("\n", "").replace("  ", "")


def test_les_liens_sortants_lachent_la_main() -> None:
    source = _sans_commentaires(PIED.read_text(encoding="utf-8"))
    assert source.count('target="_blank"') == source.count('rel="noopener noreferrer"')
    assert source.count('target="_blank"') == 2


def test_l_entete_colle_porte_la_marque() -> None:
    """« Empreinte » seul n'est pas la marque. Depuis #951 la rangée collée porte
    le logo lui-même, et le lecteur ne le perd plus de vue en défilant."""
    entete = (EXPLORATEUR.parent / "EnTeteSite.jsx").read_text(encoding="utf-8")
    bloc = entete[entete.index('<header className="entete-site"') :][:200]
    assert "<Brand />" in bloc
    assert "<EnTeteSite" in EXPLORATEUR.read_text(encoding="utf-8")


# ── §6 : ce qui cesse d'être répété, et ce qui cesse d'être affirmé ─────────


def test_le_bloc_des_refus_a_quitte_la_fiche(fiche: str) -> None:
    assert "<Interdits" not in fiche


def test_le_pied_de_fiche_ne_garde_que_la_licence(fiche: str) -> None:
    """La phrase de refus qui l'accompagnait était la TROISIÈME occurrence de
    « aucun score, aucun classement » sur la même page."""
    bloc = fiche[fiche.index('<footer className="cp-pied">') :]
    bloc = bloc[: bloc.index("</footer>")]
    assert "{c.licence}" in bloc
    assert "classement" not in bloc
    assert "présence" not in bloc


def test_la_section_renvoie_a_la_couverture_du_corpus(fiche: str) -> None:
    """Les bornes ne disparaissent pas de la vue : elles changent de page."""
    assert 'to="/sources#frise"' in fiche
    assert 'to="/methodologie#couverture"' in fiche


def test_la_limite_projets_de_loi_a_disparu(profil: str, fiche: str) -> None:
    """Elle décrivait un corpus qui a changé.

    Mesuré sur les textes portés des 32 fiches de candidats déclarés : `role`
    sépare projets et propositions sur **570 des 575** —
    `initiateur_projet_de_loi` (313) contre `auteur_proposition_de_loi` (183) et
    `auteur_proposition_de_resolution` (59). Affirmer que « seul l'intitulé
    officiel les distingue » et qu'« aucun champ ne la porte » est faux (§2
    règle 2).

    Le FAIT reste publié — combien de textes sont des projets de loi signés
    comme ministre —, c'est l'affirmation sur le corpus qui part.

    LE FAIT A CHANGÉ DE FORME LE 10/09 : « 31 de ses 34 textes portés sont des
    projets de loi » disait en toutes lettres ce que la liste ouverte au clic
    sur le Sankey montre désormais, rangée en DEUX COLONNES — Assemblée et
    Gouvernement, aux teintes de « ce que cette personne a engagé, en chiffres ».
    Le test garde donc la distinction, pas la phrase qui la portait : une
    assertion calée sur une formulation casse au premier mot réécrit et ne dit
    rien du fait qu'elle prétend garder.
    """
    assert "'projets-de-loi'" not in profil, "la limite survit dans les limites déclarées"
    # La liste ouverte au clic vit dans `CascadeTextes.jsx` depuis #329 : la
    # fiche de lignée dessine la même figure.
    liste = _sans_commentaires((SRC / "components" / "CascadeTextes.jsx").read_text(encoding="utf-8"))
    assert "from './CascadeTextes'" in fiche
    assert "t.projetDeLoi" in liste, (
        "la distinction projet / proposition a été supprimée au lieu de la seule "
        "affirmation fausse : la liste ne la rend plus"
    )
    assert "aucun champ ne la porte" not in fiche
    assert "même rôle" not in fiche


def test_aucune_clause_n_est_affirmee_sans_etre_verifiee(profil: str) -> None:
    """« dont la législature en cours » était écrit en dur et vérifié nulle part :
    sur Bruno Retailleau, dont le mandat à l'Assemblée est clos, la fiche
    l'affirmait quand même."""
    assert "législature en cours" not in profil


def test_la_qualification_ne_se_declenche_pas_sur_un_mandat_unique(profil: str) -> None:
    """« la qualification n'est pas déclarée sur 1 des mandats » d'un profil qui
    n'en a qu'un ne décrit aucune lacune : c'est la situation ordinaire.

    Le vivier a changé de nom avec #328 — `aLAssemblee` et non plus `roles` :
    la phrase nomme l'Assemblée, elle ne peut donc compter que des mandats de
    députée ou de député. Le seuil, lui, est le même."""
    bloc = profil[profil.index("const sansPosition = aLAssemblee.filter") :]
    bloc = bloc[: bloc.index("'position-non-declaree'")]
    assert "sansPosition.length > 1" in bloc
    assert "parlementaires.length > 1" in bloc


def test_les_accords_suivent_le_nombre(profil: str) -> None:
    """« aucun de ses 1 mandats électifs » se lisait sur toutes les fiches à un
    seul mandat."""
    bloc = profil[profil.index("'suspension'") :]
    bloc = bloc[: bloc.index("});") + 3]
    assert "electifs.length > 1 ? 's' : ''" in bloc
