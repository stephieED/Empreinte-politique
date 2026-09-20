"""« Ses divergences » : la bande, et ce qu'elle ne comptera jamais (#328).

La section publiait la seule liste des scrutins où la position d'une personne
diffère de la position majoritaire de son groupe. Elle était juste, et muette
pour dix des treize candidats déclarés : trois ont une base réelle et zéro
divergence, six n'ont aucune fiche de groupe publiée.

Elle porte maintenant une BANDE — un scrutin par colonne, dans l'ordre du
temps — qui donne à voir, sans compter, si la personne s'écarte et dans quel
groupe.

Ce que ces garde-fous protègent est éditorial, et une seule règle décide de la
forme entière : **AGENTS.md §2 règle 7 interdit de publier le NOMBRE de
divergences.** « A voté contre son groupe 47 fois » y est nommé mot pour mot
comme l'indice individuel mesuré contre la moyenne d'un groupe, par un autre
chemin. Trois conséquences, toutes tentantes à défaire :

1. **La bande fait lire d'abord ce que fait le GROUPE**, la divergence en
   second. Une figure qui met les divergences au premier plan est le compte par
   un troisième chemin.
2. **Le nombre de scrutins communs toutes natures confondues n'est plus
   affiché.** Posé à côté des divergences, il servait de dénominateur à une
   division que le lecteur faisait seul — et avec le mauvais nombre : 2 831
   chez Jérôme Guedj quand la base réelle est 172.
3. **Trois faits, trois éléments visuels.** Deux encodages successifs ont
   coloré la colonne par la position majoritaire du groupe tout en la
   dimensionnant par les votes qui ne la suivaient pas : deux faits opposés sur
   un seul objet.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : comme
`test_votes_par_periode_328.py`, ils ne rendent aucun composant React. La
figure — alignement des étiquettes sur leurs rangs, densité des colonnes,
repli sous 720 px — a été vérifiée hors dépôt sur `jerome-guedj`,
`gabriel-attal`, `nathalie-arthaud` (aucune fiche) et `bruno-retailleau`
(fiche sans scrutin commun), à 1 280, 760, 620 et 390 px. Rien de tout cela
n'est rejoué ici.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"

MODULE = SRC / "utils" / "ecartsGroupe.js"
COMPOSANT = SRC / "components" / "EcartsGroupe.jsx"
FEUILLE = SRC / "components" / "EcartsGroupe.css"
ADAPTATEUR = SRC / "data" / "pivotAdapter.js"
FICHE = SRC / "components" / "CandidateProfile.jsx"
REGLES = SRC / "utils" / "profilCandidat.js"
METHODO = SRC / "pages" / "MethodologyPage.jsx"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Indispensable ici : les en-têtes EXPLIQUENT pourquoi le compte est interdit
    et citent la phrase proscrite. Un test qui la chercherait dans tout le
    fichier échouerait sur le commentaire qui l'interdit.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def module() -> str:
    return sans_commentaires(MODULE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def composant() -> str:
    return sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def feuille() -> str:
    return sans_commentaires(FEUILLE.read_text(encoding="utf-8"))


# ── Le calcul est séparé du rendu ───────────────────────────────────────────


def test_les_trois_fichiers_existent() -> None:
    for chemin in (MODULE, COMPOSANT, FEUILLE):
        assert chemin.exists(), f"{chemin.relative_to(RACINE)} manquant"


def test_le_module_de_calcul_ne_connait_ni_react_ni_jsx(module: str) -> None:
    """Un calcul dans le composant est un calcul qu'aucun test ne peut lire."""
    assert "react" not in module.lower()
    assert "useState" not in module
    assert "</" not in module


def test_la_regle_a_quitte_profilCandidat_sans_etre_dupliquee() -> None:
    regles = sans_commentaires(REGLES.read_text(encoding="utf-8"))
    assert "ecartsAvecLeGroupe" not in regles, (
        "une seule implémentation : elle vit dans utils/ecartsGroupe.js"
    )
    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    assert "from '../utils/ecartsGroupe'" in adaptateur


# ── Règle 1 : le nombre de divergences n'est JAMAIS publié ──────────────────


def test_le_module_ne_publie_aucun_compte_de_divergences(module: str) -> None:
    """§2 règle 7 : « a voté contre son groupe N fois » est l'indice interdit.

    Le module rend la LISTE des divergences — chacune est un fait publiable —
    et le compte des scrutins où le GROUPE s'est divisé, qui est un fait de
    groupe portant son dénominateur. Aucune clé ne totalise ses écarts à elle.
    """
    corps = module.split("export function ecartsAvecLeGroupe(")[1]
    retour = corps.split("return {")[-1]
    assert "ecarts," in retour, "la liste est publiée"
    assert "divises:" in retour, "la dispersion du groupe est publiée, avec sa base"
    for interdit in ("nbEcarts", "totalEcarts", "tauxCohesion", "ecarts.length"):
        assert interdit not in retour, f"{interdit} publierait l'indice individuel"


def test_le_composant_n_affiche_pas_le_nombre_de_divergences(composant: str) -> None:
    """`ecarts.ecarts.length` ne sert qu'à DÉCIDER d'afficher un bloc.

    Il ne doit jamais atteindre le rendu : ni dans une phrase, ni dans un
    compteur. Les deux seuls usages admis sont un test de présence.
    """
    for usage in re.findall(r"[^\n]*ecarts\.ecarts\.length[^\n]*", composant):
        assert re.search(r"(length\s*(?:[>?]|===\s*0)|length\s*&&|\?\s*\()", usage), (
            f"usage suspect du compte de divergences : {usage.strip()}"
        )
    assert "formatNumber(ecarts.ecarts.length)" not in composant


# ── Règle 2 : le mauvais dénominateur ne revient pas ────────────────────────


def test_les_scrutins_communs_toutes_natures_ne_sont_pas_affiches(composant: str) -> None:
    """2 831 chez Guedj quand la base réelle est 172 : deux populations.

    `communs` reste CALCULÉ — il distingue « aucune fiche ne recouvre ses
    votes » de « des fiches les recouvrent, mais aucun vote sur l'ensemble » —
    et il n'est jamais rendu.
    """
    assert "communs" not in composant
    module = sans_commentaires(MODULE.read_text(encoding="utf-8"))
    assert "communs," in module, "il reste calculé pour distinguer deux vides"


def test_la_base_affichee_est_celle_des_divergences(composant: str) -> None:
    """Le dénominateur montré est la longueur de la bande, pas autre chose."""
    assert "formatNumber(bande.length)" in composant


# ── Règle 3 : trois faits, trois éléments ──────────────────────────────────


def test_trois_elements_visuels_distincts(feuille: str, composant: str) -> None:
    """Socle, barre, point : un fait chacun, jamais deux sur le même objet.

    Deux encodages successifs ont coloré la colonne par la position majoritaire
    du groupe tout en la dimensionnant par les votes qui ne la suivaient pas.
    """
    for classe in (".eg-socle", ".eg-part", ".eg-lui"):
        assert classe in feuille, f"{classe} manquant"
    # La barre porte l'encre, jamais une teinte de position : c'est un NOMBRE.
    bloc = feuille.split(".eg-part {")[1].split("}")[0]
    assert "background: var(--ink)" in bloc
    for hexa in ("#007A45", "#E53420", "#8B8794", "#007a45", "#e53420", "#8b8794"):
        assert hexa not in bloc


def test_les_teintes_de_position_viennent_de_vote_style(composant: str, feuille: str) -> None:
    """Une couleur écrite deux fois est une couleur qui divergera."""
    assert "VOTE_STYLE" in composant
    for hexa in ("#007A45", "#8B8794", "#007a45", "#8b8794"):
        assert hexa not in feuille


def test_la_couleur_du_repere_est_reservee_aux_divergences(composant: str) -> None:
    """Colorer les 172 repères faisait de la teinte une texture, pas un signal."""
    assert "x.ecart ? { background: teinte(x.position) } : undefined" in composant


def test_la_divergence_garde_un_signal_de_forme(feuille: str) -> None:
    """Sur 172 repères, un point cerclé se trouve plus vite qu'une teinte — et
    deux gris de la palette sont proches, donc le fait ne doit pas dépendre du
    seul œil."""
    bloc = feuille.split(".eg-col--ecart .eg-lui {")[1].split("}")[0]
    assert "border-radius: 50%" in bloc
    assert "box-shadow" in bloc


# ── Le critère de division, et sa base ─────────────────────────────────────


def test_un_groupe_est_divise_des_que_ses_exprimes_ne_sont_pas_unanimes(module: str) -> None:
    """Aucun seuil : un membre qui s'abstient quand 67 votent pour suffit.

    Les absents et les non-votants sont hors du critère — ne pas voter n'est
    pas voter autrement.
    """
    corps = module.split("export function groupeDivise(")[1].split("\n}")[0]
    assert "entree.pour, entree.contre, entree.abstention" in corps
    assert "absents" not in corps
    assert "length > 1" in corps


def test_la_part_dissidente_se_rapporte_a_l_effectif_eligible(module: str) -> None:
    """31 membres au groupe SOC de la XVIe, 68 à celui de la XVIIe : sans ce
    dénominateur, deux législatures ne se comparent pas."""
    corps = module.split("export function partDissidente(")[1].split("\n}")[0]
    assert "membresEligibles" in corps


# ── Les quatre conditions d'entrée dans la bande ───────────────────────────


def test_seuls_les_votes_sur_l_ensemble_entrent_dans_la_bande(module: str) -> None:
    """Sur un article ou un amendement, la position majoritaire d'un groupe se
    déplace d'un vote à l'autre pour des raisons que le corpus ne porte pas."""
    corps = module.split("export function ecartsAvecLeGroupe(")[1]
    assert "isWholeTextVote(mien.scrutin)" in corps
    assert "c.position_majoritaire" in corps
    assert "POSITIONS_COMPARABLES.includes(mien.position)" in corps


def test_un_scrutin_sans_quorum_est_publie_avec_sa_reserve(module: str, composant: str) -> None:
    """L'écarter reviendrait à choisir les faits qui arrangent.

    §2 règle 7 refuse un ratio sans couverture suffisante : la fiche le DIT au
    lieu de taire le scrutin.
    """
    assert "quorum: c.quorum_atteint !== false" in module
    assert "!x.quorum" in composant
    assert "moins de la moitié du groupe" in composant


# ── Les deux ordres, et pourquoi ils diffèrent ─────────────────────────────


def test_la_bande_va_dans_le_sens_du_temps_et_la_liste_a_l_envers(module: str) -> None:
    """La bande raconte une carrière ; une liste se lit par le haut, et le haut
    d'une liste de faits est ce qui vient de se passer."""
    corps = module.split("export function ecartsAvecLeGroupe(")[1]
    assert "bande.sort((a, b) => String(a.date" in corps, "bande : ordre croissant"
    assert ".reverse()" in corps, "liste : ordre décroissant"


# ── Les trois vides ne se confondent pas ───────────────────────────────────


def test_trois_vides_trois_causes(composant: str) -> None:
    """Deux sont des faits sur NOTRE couverture, un sur la personne.

    Les confondre ferait lire « aucune fiche n'est publiée » comme « il n'a
    jamais divergé » (§2 règle 5).
    """
    assert "Rien n’est comparable" in composant
    assert "ne recouvrent aucun de ses votes" in composant
    assert "sa position ne s’écarte jamais" in composant


# ── L'interactivité ne promet que ce qu'elle tient ─────────────────────────


def test_seule_une_divergence_est_cliquable(composant: str, feuille: str) -> None:
    """Une colonne ordinaire ne mène nulle part : aucune ligne ne lui correspond.

    Un objet qui a l'air interactif et ne réagit pas est pire qu'un objet
    inerte — il fait douter de la figure entière. Les colonnes ordinaires
    gardent leur infobulle, qui ne promet rien.
    """
    assert 'return x.ecart ? (' in composant
    assert '<button' in composant.split('return x.ecart ? (')[1].split(') : (')[0]
    ordinaire = composant.split(') : (')[1].split('}')[0]
    assert '<span className="eg-col"' in ordinaire
    assert "button.eg-col {" in feuille, "seul le bouton porte le curseur"


def test_le_theme_du_texte_apparait_partout_ou_il_manque(composant: str) -> None:
    """Le thème est affiché DANS l'infobulle du point ET dans la ligne, absent
    compris : une puce qui disparaît se lirait comme un texte sans commission
    saisie au fond, alors que c'est notre rattachement qui manque (§2 règle 5).
    """
    assert "x.matiere || 'matière non établie'" in composant
    assert composant.count("x.matiere || 'matière non établie'") == 2, (
        "une fois dans l'infobulle du point, une fois dans la puce de la ligne"
    )


def test_la_matiere_vient_de_l_adaptateur_et_n_est_pas_reconstruite() -> None:
    """La même jointure que « ce qu'il a voté » — scrutin → dossier (#758), puis
    dossier → commission saisie au fond (#328) —, écrite une seule fois."""
    module = sans_commentaires(MODULE.read_text(encoding="utf-8"))
    assert "matiereDuScrutin = () => null" in module, "paramètre, jamais reconstruit ici"
    assert "commissions_dossiers" not in module

    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    assert "const matiereDuScrutin = (scrutinId) => {" in adaptateur
    assert "ecartsAvecLeGroupe(votes, fichesGroupe, matiereDuScrutin)" in adaptateur


def test_le_titre_du_texte_est_nettoye(module: str) -> None:
    """La source écrit « l'ensemble du projet de loi … (première lecture). ».

    Publier ce libellé ferait lire la mécanique du scrutin à la place du texte.
    Le repli sur l'intitulé brut garde la source quand le nettoyage ne rend
    rien — un titre approximatif vaut mieux qu'un titre absent.
    """
    assert "titreDuTexteVote(mien.texte) || mien.texte || null" in module


def test_la_phrase_ne_subsiste_que_la_ou_la_figure_ne_dit_rien(composant: str) -> None:
    """Les trois rangs sont nommés à leur hauteur : une phrase qui les répète
    fait lire la consigne à la place du dessin, et elle est retirée.

    Elle survit dans UN cas, et il est nécessaire : sans divergence, un rang de
    repères sans aucun point ne se distingue pas d'un rang qui n'a pas fini de
    charger, et la carte des scrutins n'existe pas non plus. Rien à l'écran ne
    porterait alors le fait (§2 règle 5).
    """
    assert composant.count('className="eg-dit"') == 1
    assert "ecarts.ecarts.length === 0 && (" in composant


# ── Le renvoi mène quelque part ────────────────────────────────────────────


def test_le_renvoi_methodo_est_ancre_et_la_cible_existe() -> None:
    """Un lien posé sous un chiffre doit déposer le lecteur DEVANT la règle.

    L'ancre `#ecarts` n'existait pas quand la maquette a été validée ; la
    section ne pouvait pas être livrée sans elle, sinon la traçabilité était
    déplacée et non assurée (§2 règle 2).
    """
    composant = COMPOSANT.read_text(encoding="utf-8")
    assert '"/methodologie#ecarts"' in composant

    methodo = METHODO.read_text(encoding="utf-8")
    assert "id: 'ecarts'," in methodo
    for attendu in (
        "scrutin par scrutin",
        "ensemble d'un texte",
        "moins de la moitié",
        "trois choses différentes",
    ):
        assert attendu in methodo, f"la méthodologie doit porter « {attendu} »"


def test_l_ancienne_section_a_disparu_de_la_fiche() -> None:
    fiche = sans_commentaires(FICHE.read_text(encoding="utf-8"))
    assert "function Ecarts(" not in fiche
    assert "<EcartsGroupe" in fiche
