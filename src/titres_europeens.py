"""La règle qui retire d'un titre européen les boutons de téléchargement (#938, #980).

Module sans dépendance, pour qu'une seule règle serve aux deux étages qui en ont
besoin : `parltrack_dumps`, qui nettoie à l'entrée du corpus, et `merge_profile`,
qui reconnaît à la fusion l'entrée publiée avant le nettoyage. `merge_profile` ne
peut pas importer `parltrack_dumps` : il est lu par le portail de qualité et par
tous les audits, et `parltrack_dumps` tire `zstandard` et les dumps européens.
"""

import re
from typing import Optional

#: La queue de boutons de téléchargement que ParlTrack scrape avec le titre :
#: « … on the Xylella emergency PDF (235 KB) DOC (64 KB) ».
#:
#: Volontairement étroite — un type de fichier, une taille chiffrée, une unité.
#: Un titre qui mentionnerait « PDF » sans cette forme n'est pas touché.
_QUEUE_FICHIERS = re.compile(
    r"\s*(?:PDF|DOC|DOCX)\s*\(\s*\d+(?:[.,]\d+)?\s*[KM]B\s*\)?", re.IGNORECASE)


def titre_sans_boutons(titre: Optional[str]) -> str:
    """Le titre d'une activité, débarrassé des boutons de téléchargement.

    ## Pourquoi on touche à un verbatim de source

    ParlTrack ne lit aucune base du Parlement européen : il **recopie la page**.
    Sur cette page, à côté du titre, se trouvent les boutons de téléchargement du
    document — et ils arrivent collés au titre. Mesuré le 15/09/2026 sur le dump
    `ep_mep_activities` : 27 576 des 40 146 titres d'activités portées (68,7 %)
    portent cette queue, et la pollution touche 7 des 13 types d'activité —
    `REPORT` 88,9 %, `IMOTION` 86,6 %, `REPORT-SHADOW` 80,7 %, `MOTION` 71,5 %,
    `WQ` 68,1 %, `OQ` 63,5 %, `MINT` 91,4 %. `CRE`, `WEXP`, `COMPARL`,
    `COMPARL-SHADOW` et `WDECL` n'en portent aucune.

    Retirer cette queue **n'ôte aucun fait** : « PDF (235 KB) » ne dit rien du
    texte, c'est le libellé d'un bouton. La traçabilité (§2 règle 2) reste
    entière, le `source_url` publié menant à la page d'origine.

    ## Ce qui n'est PAS corrigé, et pourquoi

    Deux autres traces du scraping subsistent, et elles restent telles quelles :

    - **l'intitulé répété** — « MOTION OF CENSURE ON THE COMMISSION MOTION OF
      CENSURE ON THE COMMISSION » ;
    - **les espaces manquants aux jointures** — « RESOLUTIONpursuant »,
      « Procedureon ».

    Aucune règle ne les distingue d'un titre légitimement redondant ou d'un mot
    composé, et les réparer serait **reconstruire** un intitulé que personne n'a
    écrit. Une limite déclarée vaut mieux qu'un titre inventé — c'est aussi ce
    que l'interface a demandé.

    ## Ce que la règle fait, mesuré sur le dump entier

    737 498 titres lus le 15/09/2026 : **85 952 modifiés (11,7 %)**, **aucun**
    ne perdant plus de 40 caractères, et **aucun** ne gardant de « PDF ( »
    résiduel. La règle ne coupe donc ni trop, ni trop peu.

    **1 035 titres deviennent vides** : ils n'étaient QUE des boutons, sans
    aucun intitulé. Le nettoyage n'y détruit rien — il **révèle** une absence
    que le faux titre masquait (§2 règle 5). Aucun n'appartient à notre
    population : sur les 383 textes portés européens publiés au 15/09/2026, 314
    sont nettoyés et **zéro** ne devient vide. Le jour où l'un d'eux entrerait,
    il sortirait `titre: ""` — la valeur que ce champ portait déjà quand la
    source ne donne rien, et qu'il vaut mieux qu'un libellé de bouton.
    """
    if not titre:
        return ""
    return re.sub(r"\s{2,}", " ", _QUEUE_FICHIERS.sub(" ", titre)).strip()
