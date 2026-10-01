# Protocole étendu figé avant calcul — phase 4

Date de fixation : 2026-10-01. La configuration exécutable est
configs/extended.json. Le plan a été construit après l'exploration de phase 3 :
il ne constitue donc pas un protocole indépendant de cette exploration.
Il porte exclusivement sur deux images synthétiques, geometric_shapes et
ramps_and_edges, générées en 128×128 et normalisées dans [0,1].

## Plan prédéfini

| Paramètre | Valeurs |
|---|---|
| σ | 0.025, 0.05, 0.10 |
| Graines | Dix entiers de 0 à 9 |
| dx, dy | 1 pixel |
| dt | 0.20 |
| Checkpoints n | 0, 1, 2, 5, 10, 20, 40, 80 |
| Temps de diffusion n·dt | 0, 0.2, 0.4, 1, 2, 4, 8, 16 |
| Méthodes | Baseline bruitée, chaleur, PM exponentielle, PM rationnelle |
| K | 0.025, 0.05, 0.10, 0.20 pour chacune des deux conductances |
| data_range | 1.0 pour PSNR et SSIM |

Les solveurs sont inchangés : Euler explicite float64, flux nul conservatif,
variante directionnelle à quatre voisins pour Perona–Malik. La condition
dt(1/dx²+1/dy²)≤1/2 est satisfaite. Le temps de diffusion est une échelle
numérique, distincte du temps machine.

Le cas représentatif est fixé avant exécution : geometric_shapes, σ=0.10,
graine 0, K=0.10, checkpoint 20. Ses figures ne sont pas choisies après examen
des meilleurs scores.

## Comptages et observations partagées

Le plan prévoit 60 observations bruitées, chacune créée une seule fois par
tuple (image, σ, graine), puis partagée sans modification entre la chaleur et
les huit variantes PM. Ni le bruit ni les sorties ne sont tronqués.

- 60 × (1 chaleur + 2 conductances × 4 K) = 540 trajectoires ;
- 60 × [1 baseline + 8 checkpoints × 9 trajectoires] = 4 380 lignes CSV ;
- 6 couples image/σ × 73 configurations = 438 groupes de résumé.

Les schémas de metrics.csv et summary.csv restent ceux de quick. Chaque groupe
publie la moyenne arithmétique et l'écart-type échantillonnal (ddof=1) sur les
dix graines. Les écarts-types décrivent la dispersion du bruit pour ces images,
pas l'incertitude liée à une population d'images.

## Pilote et seuil de coût

configs/extended_probe.json utilise une image (geometric_shapes), σ=0.10 et
la graine 0, avec les mêmes méthodes, K, checkpoints et tailles. Les sorties
sont enregistrées séparément dans results/extended_probe.

Le pilote comporte 1 observation, 9 trajectoires et 73 lignes/groupes.
La dispersion est conventionnellement zéro avec une seule graine ; elle ne
constitue aucune estimation statistique.

Avant le calcul complet, l'estimation conservative du coût du runner complet
est 60 fois le temps global du pilote. Cette règle surévalue les coûts fixes
de figures, tableaux et écritures. L'estimation des solveurs seuls est
60 fois la somme des durées au checkpoint final n=80, sans sommer les durées
des checkpoints intermédiaires (qui sont cumulatives).

Si l'estimation globale dépasse 1 200 s, arrêt après le pilote sans changement
du protocole. Sinon, une seule exécution du protocole complet est autorisée.
La vérification stricte recalcule pour contrôle, sans nouvelle mesure de durée ;
elle ne constitue pas une deuxième exécution expérimentale chronométrée.

## Mesures et sorties prédéfinies

MSE, erreur relative L2, PSNR et SSIM conservent exactement leurs définitions.
Le SSIM est calculé par NumPy sur fenêtres valides uniformes 7×7, covariances
échantillonnales, K1=0.01 et K2=0.03. Une valeur négative n'est pas bornée.

Les durées de chaque solveur sont cumulatives jusqu'au checkpoint, avec
exclusion du bruit, des métriques, des écritures et des figures. Les durées
globales du pipeline sont enregistrées séparément. Comme dans quick, le
chronométrage du solveur inclut les copies d'états aux checkpoints.

Les sorties contiennent :

- configuration, environnement, CSV et hashes des arrays ;
- arrays des entrées et de tous les checkpoints du cas représentatif ;
- manifeste SHA-256 des fichiers générés ;
- courbes PSNR/SSIM moyenne ± écart-type pour les six couples image/σ ;
- sensibilité à K pour les deux conductances à checkpoints fixes ;
- tableaux à checkpoints communs, sans omettre les réglages défavorables ;
- comparaison visuelle, profil et gradients du cas représentatif fixé ;
- tables LaTeX dérivées directement des CSV ;
- compte rendu de vérification stricte et journal.

## Lecture des résultats

Les comparaisons à K et n fixés sont distinguées des meilleurs réglages
observés parmi les configurations de la grille. Toute sélection maximisant
PSNR ou SSIM à l'aide de la vérité terrain est un « oracle exploratoire ».
Elle ne propose pas un arrêt ou un K déployable sans image propre.

L'analyse recherchera réduction du bruit, maintien ou élargissement des
contours, sensibilité à K et au temps, sur-lissage et éventuels classements
différents entre PSNR et SSIM. Les gradients/profils sont des visualisations,
pas une métrique quantitative de contours ajoutée à la définition des scores.

## Protection et arrêt

docs/phase4_protection_before.json contient les empreintes préalables des
solveurs, métriques, configs/quick.json et de tous les fichiers quick.
Les comptes rendus de régression quick seront écrits hors results/quick.
Les mêmes empreintes seront contrôlées en fin de phase.

Arrêt après la phase 4. Les sources du rapport et du Beamer demeurent des
squelettes non compilés ; aucune rédaction finale ni installation LaTeX.
