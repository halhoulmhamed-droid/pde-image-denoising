# Hypothèses et décisions de cette passe

1. Aucune date d'exposé, aucun enseignant et aucune exigence institutionnelle
   supplémentaire ne sont supposés.
2. Aucune licence n'est choisie : « licence à confirmer » avant publication.
3. L'exécution est CPU en float64 ; aucun résultat GPU n'est revendiqué.
4. Deux images synthétiques déterministes sont utilisées. La provenance et les
   conditions d'utilisation de skimage.data.camera n'ont pas été auditées dans
   cette passe ; une comparaison sur image naturelle reste donc à faire.
5. Les lignes de résumé agrègent les deux graines avec moyenne arithmétique et
   écart-type échantillonnal (ddof=1). Deux graines ne donnent pas une
   inférence statistique générale.
6. Le cas représentatif des figures est fixé dans configs/quick.json avant
   l'exécution. Il ne constitue pas une sélection oracle.
7. Le temps du solveur est cumulatif jusqu'au checkpoint et exclut métriques,
   écritures et figures. Il dépend de la machine et n'est pas déterministe.
8. L'affichage utilise vmin=0 et vmax=1, mais les arrays et métriques ne sont
   jamais tronqués.
9. PSNR et SSIM utilisent data_range=1.0. L'erreur L2 relative suit la règle
   explicite décrite dans docs/BRIEF.md lorsque la référence est nulle.
10. Le nom Perona–Malik désigne dans le code la variante discrète directionnelle
    conservative à quatre voisins, et non une approximation isotrope exacte de
    la norme complète du gradient aux interfaces.
11. LaTeX n'étant pas installé lors de l'inspection initiale, les sources seront
    livrées mais non compilées, sans installation supplémentaire.
12. L'import de skimage.metrics a été bloqué par Windows Application Control
    lors du chargement d'une DLL SciPy. Sans contourner cette politique, les
    métriques sont donc implémentées en NumPy : PSNR par sa formule et SSIM
    locale sur fenêtres valides uniformes 7×7, covariances échantillonnales,
    K1=0.01 et K2=0.03. scikit-image n'est pas requis à l'exécution.
