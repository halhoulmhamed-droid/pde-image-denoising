# Notes orales — diffusion et débruitage

Support : slides/main.tex. Les identifiants entre parenthèses correspondent
aux labels Beamer. Vingt-cinq diapositives principales représentent environ
23 minutes, hors questions. Les sept réserves ne font pas partie de ce budget.
Les durées sont des indications de présentation, pas des mesures de calcul.

Les résultats proviennent uniquement des fichiers archivés de
results/extended. Aucun résultat d'une seule graine ne sert de moyenne.
Les propriétés démontrées du schéma sont distinguées des constats expérimentaux.

## 1. Titre (titre) — 0,5 minute

Présenter le sujet officiel et le périmètre : débruitage par chaleur et par
diffusion de Perona–Malik. C'est un mini-projet de Master associant
modélisation, analyse numérique et expérimentation reproductible, pas une
méthode nouvelle.

L'auteur et la formation sont ceux indiqués sur la page. Ne pas ajouter
d'encadrant, de date ou de revendication institutionnelle.

Transition : le bruit et les structures de l'image peuvent avoir tous deux
de fortes variations locales.

## 2. Question (question) — 0,8 minute

Formuler le compromis : diminuer les fluctuations indésirables sans déplacer
ou élargir excessivement les transitions utiles. Le mot « contour » désigne
ici une transition d'intensité visible, pas une segmentation calculée.

La question porte sur les conditions dans lesquelles la diffusion adaptative
modifie ce compromis. Ne pas annoncer que Perona–Malik gagne toujours :
l'étude contient des cas défavorables et des désaccords entre scores.

Transition : avant une comparaison, fixer le modèle d'observation.

## 3. Observation (observation) — 1 minute

L'image est d'abord une fonction sur un rectangle, puis un tableau de pixels.
La vérité terrain est dans [0,1]. Le bruit indépendant pixel par pixel est
gaussien, de moyenne nulle et d'écart-type sigma.

Une seule observation est générée pour chaque tuple image, sigma et graine,
puis utilisée par toutes les méthodes. Cela évite de comparer des méthodes
sur des bruits différents.

Ne pas tronquer l'observation : les valeurs hors de [0,1] appartiennent au
modèle statistique. L'affichage des images utilise une échelle commune
[0,1], tandis que les profils et les mesures gardent les valeurs réelles.

Source : datasets.py, noise.py, experiments.py et protocole archivé.
Transition : l'observation devient la condition initiale de la chaleur.

## 4. Chaleur (chaleur) — 1 minute

Le Laplacien représente l'effet des différences de l'image dans les
directions spatiales. Une valeur élevée entourée de valeurs plus faibles
diminue, une valeur faible entourée de valeurs élevées augmente.

La chaleur réduit les hautes fréquences, mais les transitions utiles peuvent
elles aussi contenir des hautes fréquences. Une durée trop longue élargit
les contours et finit par lisser fortement l'image.

Pour une solution suffisamment régulière, intégrer l'équation et utiliser
la condition de Neumann conserve la moyenne. Sur l'espace entier, le noyau
gaussien a une variance 2t par coordonnée. Le problème borné de Neumann a son
propre noyau : ne pas identifier naïvement ces deux représentations.

Source théorique de contexte : Weickert, 1998 ; démonstration dans le rapport.
Transition : on peut réduire le flux quand une variation locale est forte.

## 5. Perona–Malik (pm) — 1,2 minute

La conductance multiplie le gradient dans le flux continu. Les deux fonctions
sont proches de un pour une petite variation, puis diminuent. Pour un même
rapport s/K, la rationnelle décroît moins vite que l'exponentielle.

K est une échelle de variation, pas un nombre de pixels ni une durée.
Un K faible bloque plus tôt la diffusion. Une grande différence causée par
le bruit peut donc être préservée comme un contour. Le temps contrôle
combien de mises à jour ont lieu avec ces conductances.

La positivité de c ne règle pas tout au niveau continu. La dérivée du flux
g(s)=s c(s) peut être négative. La réserve reserve-continu donne le calcul
et les seuils exacts, sans confondre c et g.

Source primaire : Perona et Malik, 1990, équation de diffusion et
conductances ; détails et accès consignés dans le registre bibliographique.
Transition : distinguer le modèle présenté de sa variante implémentée.

## 6. Variante directionnelle (directionnel) — 1,2 minute

Sur l'arête horizontale, prendre la différence d'intensité entre les deux
pixels et la diviser par dx. La conductance voit sa valeur absolue. L'arête
verticale suit la même règle avec dy.

Le solveur ne reconstruit pas le vecteur gradient complet à l'interface :
les composantes horizontales et verticales alimentent des conductances
différentes. Le stencil contient quatre voisins. Son résultat peut dépendre
de l'orientation d'une transition par rapport à la grille.

Cette distinction est essentielle : la validation numérique porte sur
cette variante directionnelle, pas sur une approximation isotrope exacte
du modèle scalaire continu.

Source : perona_malik.py et boundaries.py.
Transition : comment utiliser ces différences sans perdre de masse au bord ?

## 7. Flux et bords (flux) — 1,2 minute

Le symbole « += » signifie ajouter au générateur une contribution
d'arête, pas modifier l'état u pendant l'étape d'Euler. Le facteur dx au
carré combine un gradient et une divergence discrets.

La contribution positive au pixel gauche est la contribution négative au
pixel droit. Une seule conductance est partagée. Au bord, il n'existe
aucune arête qui sorte du domaine : le flux sortant est nul.

Tous les flux sont calculés à partir du même état u^n. Le nouvel état est
distinct. Les checkpoints archivent des copies, afin qu'une mise à jour
ultérieure ne modifie pas un résultat déjà enregistré.

Propriété démontrable : la somme des contributions intérieures s'annule.
Source : code et équations du rapport.
Transition : la conservation ne garantit pas à elle seule l'absence
d'oscillations, d'où la condition de pas.

## 8. Stabilité (stabilite) — 1,2 minute

Écrire la mise à jour comme une combinaison de la valeur centrale et des
voisins. Les poids des voisins sont dt a/h². Leur somme est au plus
2dt(1/dx²+1/dy²). La condition affichée laisse donc un poids central
non négatif.

Avec dx=dy=1 et dt=0,20, le membre de gauche est 0,40, inférieur à 0,50.
La chaleur emploie a=1, et PM emploie 0≤a≤1. Moins de voisins au bord
n'aggrave pas cette borne.

Propriétés démontrées du schéma : constantes, conservation de la somme et
principe du maximum discret. Les extrema sont ceux de l'observation, pas
nécessairement 0 et 1. Une stabilité sur cette grille n'est ni une preuve
de convergence générale ni une preuve de bonne position du modèle continu.

Transition : la grille et les budgets doivent être communs dans l'étude.

## 9. Protocole (protocole) — 1,2 minute

Décrire brièvement les images. geometric_shapes associe des régions
constantes, un rectangle et un disque. ramps_and_edges combine une rampe,
un saut horizontal, une ellipse et une bande oblique. Ce sont deux
constructions déterministes, non des photographies.

Les trois sigma et dix graines produisent 60 observations. Neuf trajectoires
par observation donnent 540 trajectoires. Les lignes de mesure comprennent
la baseline bruitée, les checkpoints des neuf trajectoires et leurs états
initiaux. Il y a 4 380 lignes et 438 groupes.

Le plan étendu a été construit après l'exploration rapide. Une même graine
initialise le même générateur pour chaque cas : le même champ gaussien
standardisé réapparaît entre images et niveaux de bruit. Les cas ne sont
donc pas entièrement indépendants.

Temps t=n dt dans la convention pixel, distinct des secondes de calcul.
Source : configs/extended.json, config_used.json et CSV archivés.
Transition : les mesures utilisent une vérité terrain, indisponible en
débruitage réel.

## 10. Métriques (metriques) — 1,1 minute

MSE mesure l'erreur quadratique moyenne. Avec data_range=1, PSNR est
10 log10(1/MSE). Une MSE nulle donne un PSNR infini. L'erreur relative
normalise la norme de l'erreur par celle de la référence.

SSIM compare localement des moyennes, des variances et une covariance.
Ici les fenêtres uniformes sont de 7×7 pixels, seules les fenêtres
complètes entrent dans la moyenne, et les covariances utilisent 48 au
dénominateur. Ce choix diffère de la fenêtre gaussienne de l'article
original. Le score peut être négatif, aucune troncature à zéro.

Les bandes et les « ± » décrivent la dispersion échantillonnale entre dix
bruits, avec ddof=1. Ce ne sont pas des intervalles de confiance.
Le PSNR moyen est une moyenne des PSNR individuels et non le PSNR de la
MSE moyenne. La réserve SSIM développe les formules.

Sources : metrics.py ; Wang et al., 2004 ; documentation officielle
scikit-image, consultées et différenciées dans le registre.
Transition : les mesures ne valent que si les solveurs et les exports
ont subi des contrôles indépendants.

## 11. Vérification (verification) — 1 minute

Les 165 tests mentionnés sont ceux des validations et de l'audit antérieurs.
Ne pas présenter cet effectif comme une nouvelle suite exécutée pour la
rédaction. Les contrôles portent sur des propriétés, des paramètres,
les métriques, les résultats et leur intégrité.

La chaleur possède une validation indépendante par l'amplitude exacte d'un
mode propre discret de Neumann. Les raffinements contrôlent séparément
une diminution d'erreur spatiale et temporelle. Deux niveaux ne prouvent
pas un ordre général.

Deux constats distincts : égalité exacte du mode strict dans le Windows
enregistré ; reproduction numerical inter-environnements avec rtol=1e-10
et atol=1e-12, signalant les différences de hashes recalculés. Dans les
deux modes, l'intégrité des fichiers archivés reste exacte.

La durée 44,407302 secondes est celle du pipeline dans l'environnement
original. Les durées solveurs sont cumulatives aux checkpoints et incluent
les copies d'états ; ne pas les sommer sur tous les checkpoints.

Sources : verification.json, documentation de phase 4 et audit fourni
par l'utilisateur pour le constat inter-environnements.
Transition : observer d'abord le cas fixé, avant les scores moyens.

## 12. Comparaison visuelle (comparaison) — 1,2 minute

Ce cas était fixé avant calcul : geometric_shapes, sigma=0,10, graine 0,
n=20, K=0,10 pour PM. Il ne résulte pas d'une sélection de l'exemple
visuel le plus flatteur.

Montrer les cinq panneaux dans leur ordre. La chaleur réduit les
fluctuations mais élargit les transitions. L'exponentielle laisse des
points isolés clairs et sombres. La rationnelle donne ici moins de points
isolés avec des transitions visibles.

Ce sont des observations visuelles conditionnelles, pas une preuve
quantitative générale de préservation des contours. Les intensités des
images sont affichées sur la même échelle [0,1].

Source : results/extended/figures/comparison.pdf, tableaux représentatifs
archivés. Aucun agrégat sur dix graines dans cette figure.
Transition : une coupe fournit une lecture plus précise des transitions.

## 13. Profil (profil) — 1 minute

Le profil passe sur la ligne 42, soit 128//3 dans le code, et traverse
le rectangle. La vérité terrain fournit les marches de référence.

Les transitions de la chaleur s'étalent sur plusieurs pixels. La PM
exponentielle garde aussi des pics isolés issus du bruit. La rationnelle
atténue davantage ces pics dans ce cas.

L'axe vertical conserve les intensités hors de [0,1] ; ce profil n'applique
pas la borne d'affichage utilisée pour les images en niveaux de gris.
Ne pas en déduire une largeur numérique de contour qui n'a pas été mesurée.

Source : intensity_profile.pdf et profile_figure dans plotting.py.
Transition : une carte sur tout le domaine complète la coupe locale.

## 14. Gradients (gradients) — 0,8 minute

La norme affichée provient de np.gradient, avec dx=dy=1. Elle n'est pas
la conductance ni le gradient aux interfaces du solveur directionnel.
La couleur commune permet de comparer les structures visibles.

L'échelle supérieure est commune et construite à partir du maximum des
99es percentiles des cinq cartes, selon le script archivé. Les valeurs
plus grandes peuvent donc saturer la couleur. Les arrays sous-jacents
ne sont pas modifiés par cet affichage.

Les points résiduels dans l'exponentielle ont aussi un gradient élevé.
Une grande valeur de gradient ne distingue pas automatiquement une
structure utile d'une fluctuation.

Source : gradient_maps.pdf et gradient_figure dans plotting.py.
Transition : les figures suivantes passent à dix graines et à tous les K.

## 15. PSNR des formes (courbes-formes) — 0,7 minute

Ces courbes portent le suffixe image/sigma et utilisent les dix graines.
La figure metric_curves.pdf sans suffixe concerne seulement la graine
représentative et ne sert pas de courbe moyenne.

Lire d'abord la chaleur : le PSNR monte aux premiers checkpoints, puis
diminue avec le lissage prolongé. Les courbes PM diffèrent fortement selon
K. L'exponentielle aux faibles K reste près de la baseline bruitée.

Le panneau PSNR est recadré depuis le PDF original. La légende,
avec chaleur, bruitée et les huit variantes PM, est recomposée à droite
avec les mêmes couleurs, traits et marqueurs que la figure archivée. Aucun tracé ni checkpoint n'a été retiré.

Les bandes représentent un écart-type échantillonnal. Une petite dispersion
sur dix bruits d'une même image n'établit pas une performance sur une
population d'images.

Source : metric_curves_geometric_shapes_sigma0p1.pdf, summary.csv.
Transition : garder les mêmes trajectoires et lire le SSIM séparément.

## 16. SSIM des formes (courbes-formes-ssim) — 0,6 minute

Ce panneau est la moitié droite du même PDF agrégé. Le cas reste
geometric_shapes, sigma=0,10, dix graines, dt=0,20 et les huit checkpoints.
Les couleurs et les légendes conservent la correspondance avec le PSNR.

À n=20, comparer l'exponentielle K=0,10 et la chaleur : le tableau suivant
donnera les valeurs exactes du désaccord entre critères. Ne pas transformer
une bande d'écart-type en test statistique de supériorité.

Source : metric_curves_geometric_shapes_sigma0p1.pdf, panneau SSIM.
Transition : une image contenant des rampes teste un autre type de structure.

## 17. PSNR des rampes (courbes-rampes) — 0,6 minute

Garder les mêmes conventions que sur la figure précédente : sigma=0,10,
dix graines, dt=0,20, neuf trajectoires, tous les K prédéfinis.

Comparer la position et l'évolution des courbes, sans annoncer une règle
de classement identique à celle des formes constantes. La rampe fait partie
du signal à préserver. Les conductions et le temps ont donc un effet
sur une structure qui n'est pas seulement une région constante.

Les axes et la référence bruitée doivent se lire conjointement. Les cas
à faible sigma figurent dans le rapport et dans les archives, même s'ils
ne sont pas tous projetés. Le recadrage agrandit seulement le panneau
PSNR et conserve toutes les entrées de légende à droite, recomposées avec les mêmes codes visuels.

Source : metric_curves_ramps_and_edges_sigma0p1.pdf, summary.csv.
Transition : observer maintenant le critère local sur les mêmes rampes.

## 18. SSIM des rampes (courbes-rampes-ssim) — 0,6 minute

Le panneau SSIM utilise le même PDF, les mêmes dix graines et toutes les
configurations que le panneau PSNR précédent. Les courbes temporelles
n'ajoutent aucune interpolation de trajectoire scientifique : les segments
relient les seuls checkpoints enregistrés.

Lire l'évolution locale séparément de l'erreur quadratique. Certains
réglages ont des scores élevés pour un temps puis diminuent ; le meilleur
checkpoint observé n'est pas un optimum continu du temps.

Source : metric_curves_ramps_and_edges_sigma0p1.pdf, panneau SSIM.
Transition : isoler l'effet de K à des checkpoints communs.

## 19. Sensibilité PSNR des formes (sensibilite) — 0,7 minute

La figure compare les deux conductions à n=5, 20 et 80. L'axe K est
logarithmique ; le premier seuil est exactement 0,025, pas 0,03.
Les barres décrivent l'écart-type sur dix graines.

Un faible K ne constitue pas une bonne règle universelle. Il peut
bloquer le bruit, tandis qu'une longue diffusion avec la rationnelle
peut progressivement réduire celui-ci. Un K plus élevé peut d'abord
accélérer le débruitage puis conduire au sur-lissage.

Ces courbes publient les paramètres préfixés, sans enlever les cas
défavorables. Le panneau PSNR est agrandi ; la légende recomposée à droite
identifie les deux conductions, les checkpoints, la chaleur et la baseline.
La réserve correspondante fournit la sensibilité des rampes.

Source : k_sensitivity_geometric_shapes_sigma0p1.pdf, summary.csv.
Transition : lire l'effet du même seuil sur le SSIM.

## 20. Sensibilité SSIM des formes (sensibilite-ssim) — 0,6 minute

Même cas, même grille de K et mêmes checkpoints 5, 20 et 80 que la vue
PSNR précédente. Les couleurs indiquent le checkpoint, les lignes pleines
la PM exponentielle, les lignes tiretées la PM rationnelle, et les pointillés
la chaleur ou la baseline selon la légende. Toutes les configurations
restent visibles. Les barres sont des écarts-types échantillonnaux,
pas des intervalles de confiance.

Lire simultanément conduction et durée. Un faible K peut conserver des
fluctuations et empêcher une amélioration du critère local. Une évolution
favorable pour un réglage ne généralise pas à tous les K ou à toutes les images.

Source : k_sensitivity_geometric_shapes_sigma0p1.pdf, panneau SSIM.
Transition : le tableau à paramètres fixés précise le désaccord des critères.

## 21. Désaccord des critères (desaccord) — 1,5 minute

Le tableau provient de summary.csv via l'export documentaire.
Les scores sont des moyennes ± écarts-types sur dix graines.
Ils ne sont pas les scores de la seule graine 0 de la comparaison visuelle.

Fixer sigma=0,10, n=20 pour les solveurs et K=0,10 pour les PM.
L'exponentielle améliore le PSNR par rapport à la chaleur tout en ayant
un SSIM inférieur. La réduction d'une erreur quadratique globale peut
coexister avec des fluctuations locales qui pénalisent davantage SSIM.
Le profil et les cartes rendent cette lecture plausible dans le cas fixé,
sans attribuer au SSIM une mesure exacte des contours.

La rationnelle dépasse les deux autres solveurs selon les deux critères
dans cette comparaison. Insister sur « ici » et « paramètres fixés ».

Source : summary.csv, export report/generated/slides_fixed_case.tex.
Transition : chercher les maxima de la grille est une question différente.

## 22. Oracles (oracle) — 1 minute

L'oracle exploratoire maximise un score moyen sur les dix graines parmi
les configurations prédéfinies à n>0. L'indice theta inclut la méthode :
chaleur ou PM ; K et la conductance ne s'appliquent qu'à PM.
Le calcul utilise la vérité terrain.
Ce n'est ni un paramètre choisi par graine, ni une sélection sans référence.

Un oracle PSNR peut différer d'un oracle SSIM. Les résultats publiés
contiennent les deux, ainsi que les configurations non sélectionnées.
Quand le maximum observé se trouve à n=80, il touche la frontière du plan :
aucun optimum global du temps n'est établi.

Une règle déployable devrait sélectionner K et l'arrêt sans accès à
l'image propre. Ce travail n'a pas implémenté une telle règle.

Sources : tables/oracle_exploratory.csv, analysis.json, rapport.
Transition : cette distinction conduit aux limites de la conclusion.

## 23. Limites (limites) — 1 minute

Deux images synthétiques ne représentent pas la diversité des photographies.
Les dix graines donnent une dispersion conditionnelle du bruit, pas
dix observations indépendantes de différentes scènes.

Le plan est limité, post-exploration, et les cas liés par les graines.
La variante PM dépend de la grille. Aucun intervalle de confiance,
test de supériorité ou métrique de contours supplémentaire n'est avancé.

Les perspectives sont des travaux futurs : images naturelles de provenance
vérifiée, choix de paramètres sans référence, autres schémas. Catté et
collaborateurs lissent le gradient servant à la conductance afin de
régulariser le modèle. Cette méthode n'a pas été implémentée.

Sources : limitations archivées ; Catté et al., 1992 ; Weickert, 1998.
Transition : répondre précisément à la question initiale.

## 24. Conclusion (conclusion) — 1 minute

La dépendance aux variations locales change effectivement le compromis
dans la grille étudiée. Le sens et l'importance du changement dépendent
de K, du temps, de l'image et du critère.

Le cas fixé montre un gain des deux scores pour la rationnelle par rapport
à la chaleur. Les faibles K, le sur-lissage et le désaccord PSNR/SSIM
empêchent de convertir ce résultat en supériorité générale.

Séparer le bilan mathématique, propriétés démontrées du schéma conservatif,
du bilan empirique, observations sur deux images synthétiques.
Ne pas présenter les perspectives comme des résultats réalisés.

Transition : les références primaires et officielles permettent de situer
ce travail de cours et d'approfondir les modèles.

## 25. Références (references) — 0,3 minute

Indiquer le rôle des références : Perona–Malik pour le modèle, Weickert
pour le contexte mathématique, Catté et collaborateurs pour la
régularisation, Wang et collaborateurs pour SSIM, documentation
scikit-image pour les paramètres de la variante métrique.

Le registre references/source_ledger.md distingue les accès au texte
intégral, aux métadonnées et aux résumés. Le rapport expose les
démonstrations réalisées dans le projet. Ne pas prétendre avoir contrôlé
une démonstration inaccessible.

Ouvrir la discussion.

## Réserve 1. Conservation (reserve-conservation) — hors budget

Chaque arête intérieure contribue positivement à un pixel et négativement
à l'autre. La somme s'annule quel que soit l'état et quelle que soit la
conduction, tant que la conductance est partagée.

Sur cette grille uniforme, somme et moyenne sont équivalentes à un facteur
constant près. Sur une grille non uniforme, les volumes des cellules
devraient entrer dans la somme pondérée. Pour une constante, tous les flux
sont nuls. La démonstration n'exige pas un clipping.

## Réserve 2. Maximum (reserve-maximum) — hors budget

La borne des conductances et la condition de pas donnent une combinaison
convexe. Aucun voisin n'a de poids négatif, et les poids somment à un.
En répétant l'argument, la sortie reste entre les extrema de l'entrée.

Cette borne porte sur chaque trajectoire. Elle ne suffit pas à établir
une contraction entre deux trajectoires de PM, car les conductances
varient avec chacune des deux solutions.

## Réserve 3. SSIM (reserve-ssim) — hors budget

La formule combine une fraction de luminance avec une fraction de
contraste-structure. Les constantes empêchent les divisions fragiles
sur des régions presque constantes. Les fenêtres sont uniformes et
valides. Les covariances sont échantillonnales.

Pour une image 128×128, il existe 122×122 fenêtres complètes.
Une anticorrélation peut donner un SSIM négatif. La moyenne porte sur
les scores locaux et non sur une seule covariance globale.

Le logarithme étant non linéaire, moyenner les PSNR puis les calculer
à partir d'une MSE moyenne donne en général des résultats différents.

## Réserve 4. Neumann (reserve-neumann) — hors budget

Les centres des cellules sont décalés d'un demi-pas dans le mode cosinus.
Les angles utilisent les indices p et q et les dimensions Ny et Nx.
Le bord du Laplacien correspond aux arêtes absentes du schéma conservatif.

La valeur propre discrète donne l'amplitude exacte de la mise à jour
d'Euler : (1+dt lambda)^n. C'est une référence indépendante de la
routine de flux, et non une comparaison avec un autre appel au solveur.

Pour le raffinement, séparer l'amplitude du modèle semi-discret et celle
d'Euler afin de distinguer l'effet spatial et l'effet temporel.
La diminution d'erreur sur deux niveaux reste un contrôle local du test.

## Réserve 5. Sensibilité PSNR des rampes (reserve-sensibilite-rampes) — hors budget

Même représentation agrégée que la sensibilité des formes, cette fois
pour ramps_and_edges, sigma=0,10. Les checkpoints 5, 20 et 80 sont
communs aux deux conductions et à tous les K.

Lire les changements de courbes avec le contenu de l'image : une rampe
lisse et une discontinuité ne sont pas une même structure. Ne pas
interpréter une courbe comme un choix de paramètres déployable.

Le panneau PSNR recadré conserve les deux conductions, les quatre K,
les trois checkpoints, la chaleur et la référence bruitée. La légende
recomposée à droite conserve les couleurs, traits et marqueurs des courbes archivées.

Source : k_sensitivity_ramps_and_edges_sigma0p1.pdf, panneau PSNR, summary.csv.

## Réserve 6. Sensibilité SSIM des rampes (reserve-sensibilite-rampes-ssim) — hors budget

Même cas ramps_and_edges, sigma=0,10, dix graines, K=0,025/0,05/0,10/0,20
et checkpoints 5, 20 et 80 que la réserve PSNR. Le panneau SSIM provient du même PDF archivé ; la légende
est recomposée avec les mêmes couleurs, traits et marqueurs. Les barres décrivent un écart-type
échantillonnal. Aucun paramètre n'a été éliminé.

Comparer les évolutions des deux scores sans utiliser leur maximum pour
annoncer une sélection sans vérité terrain. Une rampe, un saut et une
fluctuation de bruit peuvent contribuer différemment aux statistiques locales.

Source : k_sensitivity_ramps_and_edges_sigma0p1.pdf, panneau SSIM, summary.csv.

## Réserve 7. Flux continu (reserve-continu) — hors budget

Calculer la dérivée de s exp(-(s/K)²) par la règle du produit.
Elle a le signe de 1-2(s/K)². Pour la rationnelle, appliquer la règle du
quotient : le signe est celui de 1-(s/K)². Les seuils sont donc
K/racine(2) et K, respectivement.

La matrice de linéarisation du flux continu a une valeur propre c(s)
dans la direction tangentielle et g'(s) dans la direction du gradient.
Une dérivée négative peut donc rompre la parabolicité. Cela ne contredit
pas la combinaison convexe du schéma directionnel sur la grille fixée :
les deux objets et les deux propriétés sont différents.

La régularisation de Catté et collaborateurs est une perspective.
Ne pas attribuer au solveur actuel les garanties de ce modèle régularisé.

## Préparation aux questions scientifiques

### Comment choisir K sans image propre ?

Cette étude ne résout pas cette sélection. K règle une échelle de
différence directionnelle d'intensité par pixel, et son effet dépend
de la conduction et du temps. Les maxima des tables sont des oracles
exploratoires utilisant la référence. Une règle basée sur le bruit estimé
ou une autre validation sans référence constituerait un travail futur.

### Pourquoi ne pas utiliser toujours le plus petit K ?

Parce que des différences causées par le bruit peuvent dépasser K.
La diffusion est alors inhibée sur ces fluctuations. Les valeurs
archivées et la figure de sensibilité montrent ce phénomène. Un petit
K peut néanmoins donner un bon score à un autre temps ou avec l'autre
conduction : la réponse doit rester conditionnelle.

### La condition de stabilité garantit-elle un meilleur score ?

Non. Elle garantit ici des coefficients de mise à jour non négatifs,
le principe du maximum et des propriétés de conservation.
Le PSNR ou le SSIM peuvent diminuer malgré cette stabilité,
notamment sous un lissage prolongé.

### Quel est le sens de la condition de flux nul ?

Aucune intensité ne traverse le bord externe du domaine dans le modèle
de diffusion. Dans le code, il n'y a pas d'arête sortante ni de voisin
pris sur le bord opposé. Les deux faces d'une arête intérieure reçoivent
des contributions opposées, donc la somme est conservée.

### Pourquoi le SSIM de l'exponentielle est-il inférieur à celui de la chaleur ?

Dans le cas fixé, les pics résiduels de l'exponentielle coexistent avec
un meilleur PSNR. SSIM dépend de statistiques locales différentes de
l'erreur quadratique globale. Le profil et les cartes rendent cette
interprétation plausible. Ce constat ne fait pas de SSIM une mesure
exacte ou universelle de la préservation des contours.

### Un SSIM négatif est-il une erreur ?

Pas nécessairement. Une covariance locale négative peut produire un
score négatif. La définition n'est pas bornée artificiellement à zéro.
Les tests indépendants de la variante utilisent notamment des images
anticorrélées. Un score inhabituel doit néanmoins être distingué
d'un défaut d'implémentation par les tests et la provenance.

### Les dix graines permettent-elles de conclure statistiquement ?

Elles décrivent dix réalisations du bruit sur chacune des deux images.
Les écarts-types donnent une dispersion conditionnelle. Ils ne sont
pas des intervalles de confiance, et les six couples image/sigma
recyclent les mêmes champs standardisés. Aucune généralisation à
une population d'images ni test de supériorité n'est établi.

### Pourquoi les oracles ne sont-ils pas un résultat déployable ?

Ils utilisent l'image propre pour maximiser un score après les mesures.
Cette image n'est pas disponible dans le problème réel. Ils servent
à étudier les possibilités et la sensibilité de la grille, pas à
annoncer un réglage choisi sans référence ni une généralisation.

### Pourquoi seulement des images synthétiques ?

Elles donnent une référence exacte et une provenance déterministe,
et isolent des structures simples. Elles ne reproduisent pas toutes
les textures d'une photographie. La validation sur images naturelles
de provenance vérifiée reste une perspective explicite.

### Quel lien avec les problèmes inverses et l'optimisation ?

Le débruitage cherche à reconstruire un signal à partir d'une observation
perturbée. La chaleur est un flot de gradient L2 de l'énergie de
Dirichlet, pour des solutions et conditions de bord adéquates.
Une interprétation variationnelle de PM peut être formelle avec une
densité non convexe ; elle ne garantit pas une minimisation globale.
Le projet n'a pas implémenté un problème inverse de défloutage ni une
méthode d'optimisation de paramètres.

### La stabilité discrète résout-elle le problème continu de Perona–Malik ?

Non. Les conductances entre zéro et un donnent une combinaison convexe dans
le schéma directionnel d'Euler sous la condition de pas. La dérivée
du flux continu peut pourtant être négative. La bonne position, la
consistance et la convergence exigent des analyses distinctes.

### Que signifient les 44,407302 secondes ?

La durée du pipeline complet enregistrée dans son environnement Windows
original. Elle comprend davantage que les seuls solveurs, et dépend de
la machine et des bibliothèques. Les temps des solveurs sont cumulés
jusqu'au checkpoint et incluent la copie de ses états. On ne les somme
pas sur tous les checkpoints d'une trajectoire.
