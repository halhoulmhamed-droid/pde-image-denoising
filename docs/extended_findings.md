# Observations mesurées — phase 4

État : étude paramétrique exécutée et vérifiée, observations conditionnelles,
pas rapport final ni conclusion de généralisation. Le plan a été construit
après l'exploration de phase 3. Sources numériques : results/extended/metrics.csv,
summary.csv, tables/extended_common_checkpoints.csv et
tables/oracle_exploratory.csv ; classements dans analysis.json.

## Exécution et contrôle

Deux images synthétiques 128×128, trois σ, dix graines 0–9, dt=0.20,
dx=dy=1, huit checkpoints et huit variantes PM plus la chaleur. Les 60
observations bruitées sont chacune partagées entre toutes les méthodes.
Les arrays numériques ne sont pas tronqués, data_range=1.0 reste fixe. Le
contrôle des entrées archivées relève effectivement des observations allant
de -0.3261081810 à 1.3145549687, hors de l'intervalle d'affichage [0,1].

Le pilote (9 trajectoires, 73 lignes) a pris 6.8015153 s. L'estimation
conservative de 408.090918 s était inférieure au seuil de 20 minutes.
L'unique calcul complet chronométré a pris 44.407302 s ; la somme des durées
terminales des 540 trajectoires est 16.5264453 s, hors métriques et figures.
Les CSV comportent exactement 4 380 lignes et 438 groupes à dix graines.

La vérification stricte locale est passée : 4 380 statistiques d'agrégation,
62 arrays d'entrée, 74 arrays représentatifs, observations communes et hashes
recalculés conformes. Aucun mode numerical nécessaire pour les résultats
étendus. Le passage final des tests compte 165 réussites, zéro échec.

## Comparaison à paramètres fixés

geometric_shapes, σ=0.10, n=20 (t=4), K=0.10 pour les deux PM. Les valeurs
ci-dessous sont les moyennes ± écarts-types échantillonnaux sur dix graines,
et non les scores de la seule graine représentative.

| Méthode | PSNR (dB) | SSIM |
|---|---:|---:|
| Bruitée, n=0 | 19.998888 ± 0.045764 | 0.216790 ± 0.001288 |
| Chaleur, n=20 | 23.648227 ± 0.043245 | 0.801713 ± 0.002319 |
| PM exponentielle, K=0.10 | 28.344885 ± 0.235089 | 0.625369 ± 0.013708 |
| PM rationnelle, K=0.10 | 34.652954 ± 0.297408 | 0.929244 ± 0.002746 |

Les deux PM réduisent ici l'erreur quadratique davantage que la chaleur au
budget fixé. Cela ne suffit pas à établir une supériorité générale : la PM
exponentielle K=0.10 obtient un SSIM inférieur à celui de la chaleur, malgré
un PSNR supérieur. La rationnelle K=0.10 est meilleure selon les deux scores
dans ce cas précis.

Le cas visuel était fixé avant calcul : même image/σ, graine 0, n=20 et K=0.10.
Ses scores individuels sont distincts des agrégats : chaleur 23.654220 dB /
0.800089 ; exponentielle 28.471563 / 0.628816 ; rationnelle 34.739243 / 0.926545.

Les figures comparison.png, intensity_profile.png et gradient_maps.png ont
réellement été ouvertes. La chaleur élargit les transitions du rectangle ;
l'exponentielle laisse des pixels isolés et des pics, tandis que la rationnelle
atténue davantage ces fluctuations en gardant des frontières visibles. Le
profil horizontal ligne 42 montre ces pics et la différence de largeur de
transition. Les cartes de gradient partagent la même échelle ; ce sont des
visualisations calculées par np.gradient, pas une nouvelle métrique de contours
ni la reconstruction du gradient aux interfaces du solveur directionnel.

## Sensibilité à K, temps et cas défavorables

Les six couples image/σ possèdent chacun des courbes PSNR/SSIM moyenne ±
écart-type et une figure de sensibilité à K. Tous les paramètres préfixés
restent publiés ; les valeurs ci-dessous citent des configurations présentes
dans summary.csv.

- Sur geometric_shapes, σ=0.10 et n=20, l'exponentielle K=0.025 atteint
  seulement 20.126870 ± 0.048298 dB et SSIM 0.219596 ± 0.001332, proches de
  l'observation non traitée. K=0.05 donne 21.164604 ± 0.061666 dB et
  0.245523 ± 0.001782. Un faible K peut donc préserver le bruit aussi bien
  que les forts sauts d'intensité.
- Un petit K n'est pas intrinsèquement mauvais : la rationnelle K=0.025
  sur ce même cas passe de 23.755589 dB à n=20 à 36.445741 dB à n=80.
  Il faut considérer ensemble la conduction, K et le temps.
- La chaleur atteint 26.724356 ± 0.072401 dB à n=2, puis 23.648227 à n=20
  et 20.665487 ± 0.033664 à n=80. Son SSIM passe de 0.801713 à n=20 à
  0.713769 à n=80 : la poursuite du lissage n'améliore pas indéfiniment
  la fidélité à la référence.
- La PM rationnelle peut aussi sur-lisser : K=0.20 donne sur le même cas
  31.325294 dB à n=5, 26.997506 à n=20 puis 21.199882 à n=80. K=0.10
  diminue de 34.652954 dB à n=20 à 28.893715 à n=80.
- À faible bruit (geometric_shapes, σ=0.025), une seule itération de chaleur
  réduit le PSNR de 32.040088 dB (bruitée) à 30.469103 dB, tout en augmentant
  le SSIM de 0.664633 à 0.874023. Réduction des fluctuations et fidélité
  pixel à pixel ne produisent pas le même classement.

## Classements PSNR / SSIM

À checkpoints communs, les meilleurs réglages selon les deux moyennes
diffèrent dans 13 des 42 couples cas/checkpoint positif. Il existe 172 paires
discordantes sur 1 512 comparaisons de paires sans égalité. Ces comptages sont
des descriptions de la grille observée, pas des tests statistiques.

Exemple à budget fixé : ramps_and_edges, σ=0.10, n=20. La rationnelle K=0.05
donne PSNR 32.565114 ± 0.184109 dB, SSIM 0.842160 ± 0.007036 ; l'exponentielle
K=0.20 donne 32.393012 ± 0.253043 dB, SSIM 0.920908 ± 0.002311. Le faible écart
de PSNR et les dispersions invitent à ne pas surinterpréter le rang, mais le
désaccord des deux critères est explicite.

Autre interaction : sur geometric_shapes, σ=0.10, exponentielle K=0.20,
le PSNR diminue de 35.705616 à n=20 à 34.786583 à n=80 tandis que le SSIM
augmente de 0.937782 à 0.952455. Un choix d'arrêt dépend donc aussi du critère.

## Meilleurs réglages observés : oracle exploratoire

Le tableau suivant maximise le PSNR **moyen sur les dix graines**, avec accès
à la vérité terrain, parmi les seules configurations prédéfinies à n>0.
C'est un oracle exploratoire, ni une sélection déployable ni une performance
de généralisation. Les tables CSV/LaTeX générées contiennent aussi les choix
selon SSIM, ainsi que toutes les variantes à budget fixé.

| Image | σ | Conduction | K | n | PSNR moyen ± std (dB) | SSIM moyen ± std |
|---|---:|---|---:|---:|---:|---:|
| geometric_shapes | 0.025 | exponentielle | 0.05 | 80 | 56.205452 ± 1.072393 | 0.999757 ± 0.000041 |
| geometric_shapes | 0.05 | rationnelle | 0.025 | 80 | 46.186189 ± 0.647663 | 0.996673 ± 0.000378 |
| geometric_shapes | 0.10 | rationnelle | 0.05 | 40 | 37.042188 ± 0.573369 | 0.961086 ± 0.003503 |
| ramps_and_edges | 0.025 | exponentielle | 0.05 | 20 | 47.619376 ± 0.282098 | 0.994845 ± 0.000426 |
| ramps_and_edges | 0.05 | rationnelle | 0.025 | 40 | 42.067066 ± 0.295280 | 0.987437 ± 0.000868 |
| ramps_and_edges | 0.10 | rationnelle | 0.025 | 80 | 34.513714 ± 0.311687 | 0.922906 ± 0.005338 |

Les cinq premiers choix oracle PSNR et SSIM coïncident. Pour ramps_and_edges,
σ=0.10, l'oracle SSIM est au contraire la rationnelle K=0.05, n=40 :
SSIM 0.946522 ± 0.002460 et PSNR 34.234035 ± 0.296494 dB.
Plusieurs maxima atteignent n=80, frontière de la grille ; ce ne sont pas
des optima globaux en temps. Aucun calcul supplémentaire n'a été lancé.

## Inventaire et limites

Dans results/extended/figures, 17 paires PNG/PDF existent :

- comparison, metric_curves, k_comparison, intensity_profile, gradient_maps ;
- metric_curves_{image}_sigma{token} pour les six couples ;
- k_sensitivity_{image}_sigma{token} pour les mêmes six couples.

Images : geometric_shapes et ramps_and_edges. Tokens σ : 0p025, 0p05, 0p1.
Les cinq premiers graphiques concernent la graine représentative ; les douze
derniers utilisent les agrégats. Les deux NPZ sont arrays/inputs.npz et
arrays/representative_outputs.npz. Les tables communes comportent 420 lignes
(baseline n=0 répétée à chaque budget), la table oracle 12 lignes. Les tables
LaTeX ont été générées depuis les CSV, sans compilation LaTeX validée.

Limites restantes : deux images synthétiques seulement ; dix réalisations
du bruit, non dix images ; aucun intervalle de confiance ni test de supériorité ;
plan post-exploration ; oracles utilisant la référence ; variante PM
directionnelle dépendant de la grille ; absence de garantie de bonne position
du modèle continu par la seule stabilité discrète. Une graine commune recycle
le même champ gaussien standardisé entre images/σ : les résultats de ces cas
ne sont pas indépendants. Pas d'image naturelle, de nouveau modèle ou de
métrique quantitative de contours dans cette phase.

Arrêt à la phase 4. Le rapport et le Beamer restent des squelettes inchangés.
