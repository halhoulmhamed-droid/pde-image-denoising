# Limites

- Deux images synthétiques et deux graines ne constituent pas un benchmark.
- Aucune image naturelle n'est évaluée dans cette passe.
- Les K et checkpoints sont une petite grille prédéfinie, sans méthode de
  sélection utilisable lorsque la vérité terrain est inconnue.
- La variante directionnelle à quatre voisins est sensible à la grille et ne
  reconstruit pas exactement la norme isotrope du gradient aux interfaces.
- Le modèle continu classique de Perona–Malik peut être mal posé dans certains
  régimes. La stabilité observée du schéma ne résout pas cette question.
- La régularisation de Catté–Lions–Morel–Coll, qui lisse le gradient entrant
  dans la conductance et possède de meilleures propriétés théoriques, est une
  perspective non implémentée.
- PSNR et SSIM décrivent une fidélité à une vérité connue ; ils ne suffisent
  pas à caractériser la qualité perceptuelle ni le choix en déploiement.
- Les temps CPU dépendent de la machine et ne doivent pas être comparés comme
  des valeurs reproductibles bit à bit.
- Aucun résultat de phase 4, rapport final ou présentation finale n'est inclus.
