# Le président de la République est dans AMO30 ; la cohabitation reste une piste fermée (#330) (2026-10-23)

`2026-10-23`

> **En bref** — `fiche-de-gouvernement-330` (18/09/2026) fermait la piste de la cohabitation sur deux motifs, dont « le nom du président n'est dans aucun corpus ». Ce motif est faux : AMO30 publie des mandats `PRESREP` pour François Hollande et Emmanuel Macron (pas pour Nicolas Sarkozy). La piste reste fermée pour l'autre motif, qui tient : aucune source primaire ne qualifie un gouvernement de cohabitation, et la déduire du parti du président et de celui du Premier ministre serait un jugement. Question reposée par la session UI le 23/10/2026, pour la frise de l'accueil (#1329).

## Ce qui a été mesuré (23/10/2026)

Archive AMO30 courante du 22/10/2026, mandats `typeOrgane == "PRESREP"` :

| Acteur | Mandats |
| --- | --- |
| `PA1654` François Hollande | 15/05/2012 → 14/05/2017, et un second enregistrement daté du 15/05/2012, **sans date de fin** |
| `PA702992` Emmanuel Macron | depuis le 14/05/2017, sans date de fin (un seul enregistrement pour les deux mandats) |
| Nicolas Sarkozy | aucun |

Les fiches de gouvernement publiées commencent avec Fillon I (2007) : le
président de 2007-2012 manque à la source.

## Ce qui ne change pas

**La cohabitation n'est pas publiée.** Aucune source primaire ne qualifie un
gouvernement de cohabitation : ni AMO30, ni le Journal officiel, ni Légifrance.
Le décompte des trois cohabitations (1986, 1993, 1997) se lit dans des textes
commentés, par exemple un discours de Philippe Séguin du 02/05/1998 publié sur
vie-publique.fr, pas dans une donnée. La déduire en comparant le parti du
président à celui du Premier ministre (organes `PARPOL` d'AMO30) qualifierait de
cohabitation Bayrou (MoDem) et Barnier (LR), un allié et le seul cas débattu :
trancher serait un jugement (§2 règle 1).

## Ce qui est corrigé

Le premier motif de `fiche-de-gouvernement-330` (« le nom du président n'est dans
aucun corpus ») ne tient plus. Une piste qui aurait besoin du président (le
nommer sur une fiche de gouvernement, par exemple) partira de `PRESREP`, avec les
deux limites ci-dessus : Sarkozy absent, et un mandat de Hollande sans date de
fin à ne pas lire comme un mandat en cours.

## Non vérifié

- La réponse à la session UI : la propriétaire ne l'a pas encore autorisée au
  23/10/2026.
