# Cahier des charges conservé — phases 1 à 3

## Identité et périmètre

- Sujet officiel : « Traitement d'images par des EDP ».
- Titre de travail : « Débruitage d'images par EDP : diffusion linéaire et
  diffusion de Perona–Malik ».
- Titre anglais : “Image Denoising with PDEs: Linear Heat Diffusion and
  Perona–Malik Diffusion”.
- Auteur : Mhamed Halhoul.
- Formation : M2 « Modélisation, Mathématiques Appliquées et Apprentissage »,
  Abdelmalek Essaâdi University.
- Nature : travail de cours reproductible, sans revendication de recherche
  nouvelle.

Cette première exécution est limitée aux phases suivantes :

1. inspection, cadrage, architecture, documentation scientifique initiale,
   bibliographie et squelettes LaTeX ;
2. solveurs, métriques, automatisation et tests ;
3. expérience exploratoire rapide, sorties réelles et audit interne.

Arrêt obligatoire après la phase 3. Les expériences complètes, le rapport
final de 20 à 30 pages, la présentation finale et la publication sont exclus.

## Question scientifique

« Dans quelles conditions la diffusion dépendant du gradient modifie-t-elle le
compromis entre réduction du bruit et préservation des contours, par rapport à
la diffusion linéaire ? »

“Under what conditions does gradient-dependent diffusion change the trade-off
between noise reduction and edge preservation compared with linear heat
diffusion?”

La comparaison ne doit pas présupposer la supériorité de Perona–Malik. Elle
comprend vérité terrain, observation bruitée, chaleur, Perona–Malik
exponentielle et Perona–Malik rationnelle, y compris les cas défavorables.

## Modèles imposés

Sur un rectangle Ω, la vérité terrain u_true prend ses valeurs dans [0,1] et
l'observation est f = u_true + η, avec η gaussien indépendant, centré,
d'écart-type σ. La donnée initiale est u(0)=f.

- chaleur : ∂_t u = Δu ;
- Perona–Malik : ∂_t u = div(c(|∇u|)∇u) ;
- c_exp(s) = exp(-(s/K)^2) ;
- c_rat(s) = 1/(1+(s/K)^2), K>0 ;
- flux nul au bord.

L'observation et les sorties numériques ne sont pas tronquées pour les
métriques. Seul l'affichage peut être borné. Il faut distinguer modèle continu,
semi-discrétisation et Euler explicite, et ne pas transformer une stabilité
discrète en résultat de bonne position du modèle continu. La régularisation de
Catté–Lions–Morel–Coll appartient aux limites/perspectives, pas aux solveurs.

## Discrétisation imposée

NumPy float64, grille rectangulaire, stencil à quatre voisins, Euler explicite,
flux conservatifs partagés sur les arêtes intérieures, flux nul sur le bord,
aucune connexion périodique et aucune mise à jour en place.

La condition suffisante est

    dt * (1/dx^2 + 1/dy^2) <= 1/2.

Le protocole rapide fixe dx=dy=1 pixel et dt=0.20. Le temps n*dt est un temps
de diffusion numérique, distinct du temps machine.

La méthode non linéaire autorisée ici est la « variante discrète directionnelle
à quatre voisins » : la conductance d'une arête utilise
|u_voisin-u_pixel|/h. Ce n'est pas une reconstruction isotrope exacte de la
norme complète du gradient continu et elle est sensible à l'orientation de la
grille.

## Architecture et reproductibilité

Le dépôt doit fournir README, métadonnées Python, configuration JSON,
documentation mathématique et expérimentale, ledger bibliographique, package
en src-layout, tests, résultats rapides traçables, ainsi que des squelettes
LaTeX de rapport et Beamer. Aucun notebook ne doit être nécessaire.

L'environnement est un .venv local. Les commandes utilisent explicitement
.\.venv\Scripts\python.exe. Aucune installation Python globale, installation
LaTeX, dépense, API payante, connexion externe ou GPU obligatoire n'est
autorisée. Aucun commit, staging, push ou remote.

## Batterie de tests attendue

Les tests déterministes couvrent :

1. invariance des constantes ;
2. identité à zéro itération ;
3. dimensions et finitude ;
4. non-mutation des entrées ;
5. reproductibilité du bruit ;
6. conservation de la moyenne sous flux nul ;
7. absence de couplage des bords opposés et grilles non carrées ;
8. principe du maximum discret ;
9. dissipation L2 de la chaleur ;
10. mode propre discret de Neumann indépendant ;
11. études séparées de raffinement spatial et temporel ;
12. bornes des conductances et limite K grand ;
13. rejet des paramètres invalides ;
14. cas exacts des métriques ;
15. reproduction des arrays et métriques, hors durées et horodatages.

Aucun test ne doit exiger que Perona–Malik surpasse la chaleur.

## Protocole rapide autorisé

- taille : 128 × 128 ;
- une image géométrique (régions, rectangle, disque) ;
- une seconde image synthétique indépendante si la provenance d'une image
  naturelle n'est pas auditée ;
- σ ∈ {0.05, 0.10}, graines {0,1} ;
- dx=dy=1, dt=0.20 ;
- checkpoints n ∈ {0,5,10,20} ;
- K ∈ {0.05,0.10} pour les conductions exponentielle et rationnelle.

Une seule réalisation bruitée est créée par tuple (image, σ, graine) et
réutilisée par toutes les méthodes. La vérité terrain sert aux mesures, non à
une règle de sélection déployable. Toute sélection après observation de la
vérité terrain serait dite « oracle exploratoire ». Tous les paramètres
prédéfinis doivent figurer dans les tableaux.

## Mesures et sorties

MSE, erreur L2 relative, PSNR, SSIM et temps du solveur sont requis.
data_range=1.0 est imposé pour PSNR et SSIM. Le cas MSE=0 donne PSNR=+∞ ; si la
norme de la référence est nulle, l'erreur relative vaut 0 pour une estimation
nulle et +∞ autrement.

Les sorties automatiques comprennent metrics.csv, summary.csv, configuration,
environnement, journal, hashes, arrays compacts, figures PNG/PDF, profils et
cartes de gradient, ainsi que des tables LaTeX générées depuis les CSV.
L'agrégation sur deux graines doit publier moyenne et dispersion sans
prétendre à une conclusion statistique générale.

## Bibliographie et LaTeX

Les métadonnées doivent être vérifiées sur archives institutionnelles, pages
d'auteur, éditeurs et documentation officielle. Le ledger distingue texte
intégral, résumé et métadonnées. Aucun DOI ne doit être inventé.

Le rapport français et le Beamer ne sont que des squelettes provisoires,
compilables sans figure. Les sections de résultats et conclusions restent
explicitement à compléter après audit.

## Contrôle de fin de passe

Relancer pytest et l'expérience rapide, vérifier imports, chemins, fichiers,
partage des observations, reproduction hors durées, nouveaux fichiers texte,
références en attente et état de phase. Exécuter git status --short et
git diff --check dans ce dépôt seulement, sans staging, commit ni push.
Confirmer l'arrêt avant les phases 4 à 6.
