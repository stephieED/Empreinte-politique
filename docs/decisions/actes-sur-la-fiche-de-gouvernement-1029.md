<a id="actes-sur-la-fiche-de-gouvernement-1029"></a>

# Ce qu'un gouvernement a fait entrer en vigueur (#1029) (2026-09-25)

`2026-09-25`

> **En bref** — La voie 1 de #1029 versait 389 000 décrets, arrêtés et ordonnances au pivot depuis le 22/09/2026, et **aucun fichier de l'interface ne les lisait** : ni les actes, ni les 1 015 textes promulgués, ni la jointure de #1108. La fiche de gouvernement gagne une cinquième section, arbitrée en maquette les 24 et 25/09/2026. Elle montre, sur la fenêtre du gouvernement : combien d'actes ont paru, **combien sont des actes de personne** — retirés —, puis, sur ce qui touche au droit, quel ministère signe et **ce que le titre déclare d'une loi**. Deux filtres règlent le flux et le détail ; « lié à une loi » ouvre les lois elles-mêmes, chacune dépliant ses actes. Le lien est lu dans le **titre**, jamais dans `liens_lois` : la qualification structurée de Légifrance n'est plus posée — **un acte sur les 19 041 de Lecornu II la porte**, contre 972 dont le titre la déclare.

## Le contexte

`docs/decisions/part-d-application-non-publiable-1029.md` a écarté la figure qui
reposait sur la part d'application : la qualification de Légifrance tombe de
42 % en 2012 à 0 % depuis 2024, et rien dans les données ne sépare le retard du
changement de pratique. La voie 1 restait donc invisible, faute de forme.

La sortie est venue d'une mesure : **les titres disent ce que le champ ne dit
plus**. Sur la fenêtre de Lecornu II, 972 actes déclarent un lien à une loi dans
leur intitulé — « portant application de l'article 2 de la loi n° 2025-568 » —,
et 395 la nomment par son numéro. C'est la seule source utilisable, et elle est
immune au différé de qualification.

## Ce que la section publie

- **Un entonnoir** : les actes parus, moins les **actes de personne**
  (nomination, cessation, admission, promotion, radiation, désignation,
  naturalisation — 7 920 des 19 041 sur Lecornu II), égale ce qui touche au
  droit. Les garder ferait de « ce que le gouvernement a concrétisé » un
  décompte de carrières.
- **Un flux à deux colonnes** : le ministère qui signe, puis ce que le titre
  déclare. Cinq ministères colorés et un regroupement — **pas six** : à huit
  teintes, deux paires tombent sous le seuil de séparation du validateur, y
  compris en vision normale.
- **Deux filtres** qui agissent sur le flux **et** sur le détail. Les brins fins
  ne se visent pas : « lié à une loi » pèse 9 % du total, donc un brin de
  ministère vers ce bloc fait quelques pixels et n'est atteignable ni au doigt
  ni au clavier.
- **Les lois, nommées.** 49 lois sur Lecornu II, dont 41 retrouvées dans
  `textes_promulgues.json` — titre, commission, nature, date —, et 12 nées
  d'une proposition de loi. Chaque loi déplie ses actes, avec le lien Légifrance.

## Les trois choses qu'aucune formule n'a le droit de laisser croire

1. **« Le titre ne le dit pas » n'est pas « sans loi ».** L'absence de mention
   ne dit rien de l'acte (§2 règle 5). La section l'écrit en clair, et
   `tests/test_actes_gouvernement_1029.py` refuse les formules « décret sans
   attache », « acte sans loi », « sans base légale ».
2. **Le délai d'une loi est celui de son premier acte DE CETTE PÉRIODE.** Une
   loi de 2014 qui reçoit un acte en 2026 en a peut-être reçu dix avant :
   « délai 12 ans » se lirait sinon comme douze ans d'inaction.
3. **Les actes qui nomment une loi se concentrent.** 308 des 395 nomment la
   même — la loi de financement de la sécurité sociale pour 2007, par des
   arrêtés fixant la liste des praticiens autorisés à exercer. Lire « 395 actes
   appliquent une loi » comme 395 mesures serait faux ; la section le dit.

## Les choix d'implémentation, et leur raison

- **Les 238 fichiers mensuels sont lus UNE fois** (`projeterLesActes` dans
  `sync-data.mjs`), et chaque acte est rangé dans les gouvernements dont la
  fenêtre le couvre. Une passe par gouvernement relirait 197 Mo dix-sept fois.
- **Seule la projection est publiée** — `<id>.actes.json`, ~0,35 Mo par
  gouvernement, 5,9 Mo pour les dix-sept —, jamais les fichiers mensuels. Elle
  est chargée à l'affichage de la section, pas avec la fiche.
- **Le flux est dessiné à la main**, une douzaine de rubans en SVG : charger
  une librairie de graphiques pèserait plus que toute la fiche.

## L'alternative écartée

**Attendre que Légifrance requalifie.** Le fonds se corrige par l'arrière — un
acte redélivré voit ses liens repris (`corriger_les_liens`) — mais rien ne dit
quand, et la fiche d'un gouvernement récent serait vide en attendant. Le titre,
lui, est écrit le jour de la parution.
