# Protocole expérimental rapide

## But et statut

Ce protocole est exploratoire. Il teste le pipeline et fournit des premières
observations, sans benchmark définitif ni conclusion statistique générale.

## Données

Deux images propres synthétiques de 128×128 en [0,1] :

- geometric_shapes : régions constantes, rectangle et disque ;
- ramps_and_edges : rampe lisse, ruptures, ellipse et bande diagonale.

Pour chaque image, σ∈{0.05,0.10} et graine∈{0,1}. Une observation
f=u_true+η est générée une seule fois et réutilisée par toutes les méthodes.
Elle n'est pas tronquée.

## Méthodes et budget

- baseline bruitée ;
- chaleur ;
- Perona–Malik directionnelle à quatre voisins, conduction exponentielle ;
- même variante, conduction rationnelle.

Paramètres : dx=dy=1 pixel, dt=0.20, checkpoints n={0,5,10,20},
K={0.05,0.10}. Chaque solveur reçoit le même budget de 20 pas pour une
comparaison à checkpoint commun.

Le plan contient 8 observations, 8 trajectoires de chaleur et 32 trajectoires
Perona–Malik, soit 40 trajectoires de solveur. metrics.csv doit contenir
8 lignes de baseline, 32 lignes de chaleur et 128 lignes Perona–Malik :
168 lignes au total. summary.csv agrège les deux graines et doit contenir
84 configurations.

## Mesures

- MSE = moyenne de (u-u_true)² ;
- erreur relative L2 = ||u-u_true||₂ / ||u_true||₂ ;
- PSNR avec data_range=1.0 ;
- SSIM avec data_range=1.0 ;
- durée cumulative du solveur jusqu'au checkpoint.

Les durées excluent génération du bruit, métriques, sérialisation et figures.
La moyenne et l'écart-type échantillonnal sont publiés sur les deux graines.
Le SSIM est la moyenne de la carte locale calculée sur toutes les fenêtres
valides uniformes 7×7, avec variances/covariance échantillonnales et constantes
K1=0.01, K2=0.03. Cette définition NumPy explicite évite une dépendance SciPy
dont le chargement est interdit par la politique d'application de la machine.

## Traçabilité

Chaque ligne contient paramètres, temps n*dt, hashes SHA-256 de la vérité,
de l'observation partagée et de la sortie, ainsi que la durée. La configuration
exacte, les versions, les arrays d'entrée et les sorties représentatives sont
archivés. Les métriques déterministes et arrays sont recalculés lors de la
vérification ; durées et horodatages sont exclus de cette égalité.

## Figures fixées avant calcul

Le cas représentatif est geometric_shapes, σ=0.10, graine 0, n=20, K=0.10.
Il alimente comparaison visuelle, courbes, comparaison K, profil horizontal et
cartes de gradient. Ce choix prédéfini n'est pas un optimum oracle.
