# Modèle mathématique et discrétisation

## Observation

Soit Ω un rectangle et u_true: Ω → [0,1] l'image propre. L'observation est

    f(x,y) = u_true(x,y) + η(x,y),

où les η sont indépendants, gaussiens, de moyenne nulle et d'écart-type σ.
La donnée initiale des EDP est u(x,y,0)=f(x,y). Le bruit peut donc placer f
hors de [0,1]. Aucun clipping n'est effectué pour les calculs.

## Modèles continus

La diffusion linéaire vérifie

    ∂_t u = Δu dans Ω,
    ∂_n u = 0 sur ∂Ω.

Sur l'espace entier, la solution est la convolution de f avec un noyau
gaussien dont la variance par coordonnée vaut 2t. Sur un rectangle avec bord
de Neumann, la solution relève du semi-groupe de Neumann (ou d'extensions
réfléchies) : l'égalité naïve avec une convolution gaussienne sur R² n'est pas
identique sans réserve.

Le modèle de Perona–Malik est

    ∂_t u = div(c(|∇u|) ∇u),
    c_exp(s) = exp(-(s/K)^2),
    c_rat(s) = 1/(1+(s/K)^2), K>0.

Le temps t règle l'échelle du lissage. K règle la transition entre diffusion
forte pour les faibles différences et diffusion inhibée sur les différences
plus grandes. Un K trop petit peut préserver du bruit ; un K grand rapproche
le schéma de la chaleur.

## Grille et semi-discrétisation conservative

Les pixels sont u[i,j], avec i vertical (pas dy) et j horizontal (pas dx).
Pour une arête horizontale entre (i,j) et (i,j+1), poser

    δx = u[i,j+1] - u[i,j],
    a_x = c(|δx|/dx).

Sa contribution au générateur semi-discret est +a_x δx/dx² au pixel gauche et
-a_x δx/dx² au pixel droit. Pour une arête verticale entre (i,j) et (i+1,j),

    δy = u[i+1,j] - u[i,j],
    a_y = c(|δy|/dy),

avec contributions opposées ±a_y δy/dy². La chaleur correspond à a_x=a_y=1.
Chaque flux intérieur est donc partagé et exactement opposé ; aucune arête ne
sort du domaine, ce qui impose le flux nul et conserve la somme discrète.

Dans Perona–Malik, il s'agit de la **variante discrète directionnelle à quatre
voisins**. Les quantités |δx|/dx et |δy|/dy sont des différences
directionnelles sur chaque arête, pas une reconstruction isotrope exacte de
|∇u|. Le schéma peut donc être sensible à l'orientation de la grille.

## Euler explicite

Avec L_h(u^n) défini par les flux précédents,

    u^(n+1) = u^n + dt L_h(u^n).

Les flux et conductances sont tous évalués à u^n et l'array u^(n+1) est
distinct. Aucune périodicité, aucun np.roll et aucun clipping ne sont utilisés.

Comme 0≤a≤1, une condition suffisante pour que chaque mise à jour soit une
combinaison convexe de la valeur centrale et de ses voisins est

    dt (1/dx² + 1/dy²) ≤ 1/2.

Elle vaut pour la chaleur et pour cette variante non linéaire. Avec dx=dy=1,
dt≤1/4 ; le protocole choisit dt=0.20. Un dt invalide provoque une erreur.

## Niveaux de modélisation

Le modèle continu, l'ODE semi-discrète définie par les flux et l'algorithme
Euler explicite sont trois objets distincts. Conservation, principe du maximum
et stabilité sur une grille fixée ne prouvent pas la bonne position du modèle
continu de Perona–Malik. La régularisation par gradient lissé de
Catté–Lions–Morel–Coll est une perspective théorique, non une méthode
implémentée ici.

## Propriétés vérifiées

Les tests contrôlent conservation de la moyenne, invariance des constantes,
principe du maximum, dissipation quadratique de la chaleur, absence de
couplage périodique, bornes des conductances et limite K→∞. La chaleur est
validée indépendamment sur les modes propres du Laplacien discret de Neumann

    φ_pq[i,j] = cos(π p(i+1/2)/Ny) cos(π q(j+1/2)/Nx),

dont la valeur propre est

    λ_pq = -4 sin²(πp/(2Ny))/dy² - 4 sin²(πq/(2Nx))/dx².

Après n pas d'Euler, l'amplitude exacte du modèle entièrement discret vaut
(1+dt λ_pq)^n.
