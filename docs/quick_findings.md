# Premières observations de l'expérience rapide

Ces observations proviennent exclusivement de results/quick/metrics.csv et
results/quick/summary.csv. Elles portent sur deux images synthétiques et deux
graines ; elles ne constituent ni un benchmark, ni une conclusion générale.
Les valeurs « ± » sont moyenne ± écart-type échantillonnal sur les graines 0
et 1. Les paramètres non mentionnés sont dx=dy=1 et dt=0.20.

## Cas géométrique, σ=0.10

À n=20 (temps de diffusion 4.0), les valeurs agrégées sont :

| Méthode | K | MSE | PSNR (dB) | SSIM |
|---|---:|---:|---:|---:|
| Observation bruitée, n=0 | — | 0.0099111 | 20.0388 | 0.2174 |
| Chaleur | — | 0.0043127 | 23.6525 | 0.8000 |
| PM exponentielle | 0.05 | 0.0075553 | 21.2175 | 0.2467 |
| PM exponentielle | 0.10 | 0.0014304 | 28.4456 | 0.6311 |
| PM rationnelle | 0.05 | 0.00045175 | 33.4511 | 0.8331 |
| PM rationnelle | 0.10 | 0.00034244 | 34.6550 | 0.9277 |

Dans ce cas et à ce checkpoint fixé, la conduction rationnelle K=0.10 a les
meilleures MSE, PSNR et SSIM parmi les paramètres testés. Cela ne constitue pas
une règle de sélection sans vérité terrain.

Le cas PM exponentielle K=0.05 est défavorable : il améliore peu l'observation
et reste moins bon que la chaleur sur les trois métriques. L'inspection de
k_comparison.png et gradient_maps.png montre de nombreux gradients ponctuels
résiduels, cohérents avec un K trop faible qui inhibe aussi la diffusion du
bruit.

## Dépendance au temps et sur-lissage

Pour geometric_shapes, σ=0.10, graine 0, le PSNR de la chaleur passe de
20.0336 dB à n=0 à 26.1156 dB à n=5, puis redescend à 25.0176 dB à n=10 et
23.6542 dB à n=20. Les contours visibles dans comparison.png sont alors
élargis. Le temps de diffusion supplémentaire n'est donc pas uniformément
bénéfique.

Pour σ=0.05, la chaleur à n=20 est même moins fidèle que l'observation non
traitée sur les deux images :

- geometric_shapes : MSE 0.0042382 contre 0.0024778 ;
- ramps_and_edges : MSE 0.0040326 contre 0.0024778.

Ce résultat illustre un sur-lissage à budget fixé, et non une incapacité
générale de la chaleur à débruiter.

## Sensibilité à K et à l'image

Au checkpoint n=20, le plus petit MSE parmi les configurations prédéfinies
change avec le niveau de bruit :

- geometric_shapes, σ=0.05 : PM rationnelle K=0.05, MSE 0.00006269,
  PSNR 42.0280 dB, SSIM 0.9830 ;
- geometric_shapes, σ=0.10 : PM rationnelle K=0.10, MSE 0.00034244,
  PSNR 34.6550 dB, SSIM 0.9277 ;
- ramps_and_edges, σ=0.05 : PM rationnelle K=0.05, MSE 0.00012399,
  PSNR 39.0712 dB, SSIM 0.9749 ;
- ramps_and_edges, σ=0.10 : PM rationnelle K=0.05, MSE 0.00054583,
  PSNR 32.6294 dB, SSIM 0.8420.

Cette lecture est un **choix oracle exploratoire** effectué après comparaison à
la vérité terrain. Elle ne fournit pas une procédure de réglage déployable et
ne permet pas d'affirmer qu'une même valeur de K domine hors de ce petit plan.

## Inspection visuelle

Les cinq PNG ont été ouverts. comparison.png confirme la différence entre
flou de la chaleur et inhibition des flux de PM. intensity_profile.png montre
que PM rationnelle K=0.10 suit plus abruptement les marches du rectangle que la
chaleur dans le cas représentatif. La même figure rappelle toutefois que les
sorties ne sont pas tronquées : quelques excursions liées au bruit peuvent
subsister. Les PDF correspondants sont destinés à une intégration LaTeX
ultérieure.
