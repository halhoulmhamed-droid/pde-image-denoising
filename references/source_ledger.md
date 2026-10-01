# Registre des sources

Vérification effectuée le 2026-09-30 à partir de sources primaires ou
officielles. « Accessible » décrit ce qui a été effectivement inspecté dans
cette passe, pas ce qui pourrait être obtenu avec un autre abonnement.

## Perona et Malik (1990)

- Source institutionnelle :
  https://authors.library.caltech.edu/records/1p8h5-5x870
- Métadonnées vérifiées : Pietro Perona ; Jitendra Malik ; “Scale-Space and
  Edge Detection Using Anisotropic Diffusion” ; IEEE Transactions on Pattern
  Analysis and Machine Intelligence ; volume 12 ; numéro 7 ; pages 629–639 ;
  1990 ; DOI 10.1109/34.56205.
- Accès : page de dépôt, résumé et fichier PDF signalé comme téléchargeable.
  Le texte intégral n'a pas été relu ligne à ligne dans cette passe.
- Affirmations soutenues ici : diffusion à coefficient spatialement variable,
  lissage privilégié à l'intérieur des régions et motivation de préservation
  des frontières. La date 2006 du dépôt n'est pas l'année de publication.

## Weickert (1998)

- Page de l'auteur :
  https://www.mia.uni-saarland.de/weickert/index.shtml
- Métadonnées vérifiées : Joachim Weickert ; Anisotropic Diffusion in Image
  Processing ; Teubner ; Stuttgart ; 1998.
- Accès : notice bibliographique sur la page de l'auteur, qui propose un lien
  d'information/téléchargement. Le livre intégral n'a pas été relu dans cette
  passe.
- DOI : aucun DOI vérifié, donc aucun champ DOI ajouté.
- Affirmation soutenue ici : l'ouvrage constitue une référence de synthèse sur
  la diffusion anisotrope et le traitement d'images.

## Catté, Lions, Morel et Coll (1992)

- Page éditeur / DOI :
  https://doi.org/10.1137/0729012
- Métadonnées vérifiées : Francine Catté ; Pierre-Louis Lions ; Jean-Michel
  Morel ; Tomeu Coll ; “Image Selective Smoothing and Edge Detection by
  Nonlinear Diffusion” ; SIAM Journal on Numerical Analysis ; volume 29 ;
  numéro 1 ; pages 182–193 ; février 1992 ; DOI 10.1137/0729012.
- Accès : métadonnées et résumé sur la page SIAM ; texte intégral indiqué sous
  contrôle d'accès et non lu ici.
- Affirmation soutenue ici : une version régularisée de la théorie de
  Perona–Malik est proposée avec résultats d'existence, unicité et stabilité
  annoncés dans le résumé. La date de mise en ligne 2006 n'est pas l'année
  bibliographique.

## Documentation scikit-image

- Documentation officielle :
  https://scikit-image.org/docs/stable/api/skimage.metrics.html
- Version affichée lors de la vérification web : 0.26.0.
- Éléments vérifiés : signatures de peak_signal_noise_ratio et
  structural_similarity ; signification de data_range ; avertissement que
  l'inférence automatique peut être incorrecte pour les images flottantes.
- Accès : documentation complète de l'API.
- Affirmation soutenue ici : data_range=1.0 doit être passé explicitement pour
  les vérités terrain normalisées utilisées dans le projet.

## Approfondissement pour la phase 5 — 2026-10-01

Les notices précédentes conservent l'état de consultation initial. Les
compléments ci-dessous décrivent les lectures effectivement réalisées pour
la rédaction, sans prétendre à une lecture intégrale de chaque ouvrage.

### Perona–Malik : vérification et limite d'accès

- La notice Caltech confirme à nouveau auteurs, titre, revue, année 1990,
  12(7), 629–639 et DOI 10.1109/34.56205.
- Copie sur le site de Jitendra Malik :
  https://people.eecs.berkeley.edu/~malik/papers/MP-aniso.pdf
- Le PDF auteur est accessible (11 pages), mais sa copie est numérisée et
  n'offre pas de texte extractible dans l'outil utilisé. Le téléchargement
  via la notice Caltech a échoué dans cet outil. Les extraits indexés de
  l'introduction et la notice ont été consultés ; aucune démonstration
  complète ni aucun numéro de théorème n'est attribué à cette lecture.
- Le rapport mobilise la référence pour l'origine et la motivation du modèle.
  Ses calculs de dérivées du flux, primitives et Hessienne sont montrés dans
  le rapport, non annoncés comme des théorèmes vérifiés dans le PDF.
  Les réserves sur le modèle avant–arrière sont aussi étayées par les
  passages effectivement lus de Weickert ci-dessous.

### Weickert : passages techniques effectivement lus

- Notice auteur :
  https://www.mia.uni-saarland.de/weickert/book.html
- Texte intégral auteur :
  https://www.mia.uni-saarland.de/weickert/Papers/book.pdf
- Métadonnées confirmées : Joachim Weickert, Teubner, Stuttgart, 1998.
  Aucun DOI vérifié ; il reste omis. Le livre est accessible librement
  sur le site de l'auteur ; aucun PDF tiers n'est ajouté au projet.
- §1.2.1, pages imprimées 3–4 (indices PDF 14–15) : diffusion linéaire,
  noyau gaussien sur l'espace entier et lissage des fréquences. Soutient
  le cadre de la relation chaleur/Gaussienne et ses conventions d'échelle.
- §1.3.1, pages imprimées 15–18 (indices PDF 26–29) : diffusion
  Perona–Malik, dérivée du flux rationnel, directions tangentielles et
  normales et difficulté avant–arrière. Soutient la mise en garde contre
  l'assimilation conductance positive/parabolicité.
- §1.3.2, pages imprimées 20–21 (indices PDF 31–32), notamment équation
  (1.43) : dépendance du coefficient à un gradient spatialement lissé et
  présentation de la régularisation de Catté et collaborateurs.
- Seules ces sections ont été lues pour les affirmations utilisées.
  Le livre entier n'a pas été relu. Les preuves de conservation et du
  maximum du schéma du projet sont établies directement à partir des
  flux codés, et ne sont pas attribuées à un théorème du livre.

### Catté et collaborateurs : résumé seulement

- Page éditeur consultée :
  https://epubs.siam.org/doi/10.1137/0729012
- Métadonnées et résumé accessibles ; texte intégral sous contrôle d'accès,
  non consulté. La notice confirme 29(1), 182–193, 1992 et le DOI.
- Le résumé annonce existence, unicité et stabilité d'un modèle modifié.
  Les hypothèses et démonstrations de ces résultats n'ont pas été vérifiées
  dans l'article ; aucun résultat formel précis n'est transposé au code.
- La description de lissage du gradient est également appuyée par
  Weickert §1.3.2 effectivement lu. Cette régularisation reste une
  perspective bibliographique, jamais une méthode implémentée ou testée.

### Wang, Bovik, Sheikh et Simoncelli : publication SSIM originale

- Page auteur :
  https://ece.uwaterloo.ca/~z70wang/publications/ssim.html
- Page de présentation et ressources de l'auteur :
  https://ece.uwaterloo.ca/~z70wang/research/ssim/
- Texte intégral auteur :
  https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf
- DOI éditeur :
  https://doi.org/10.1109/TIP.2003.819861
- Métadonnées vérifiées : Zhou Wang, Alan C. Bovik, Hamid R. Sheikh,
  Eero P. Simoncelli ; “Image Quality Assessment: From Error Visibility
  to Structural Similarity” ; IEEE Transactions on Image Processing ;
  13(4), 600–612 ; avril 2004. Le « 2003 » du DOI n'est pas l'année
  bibliographique. Ces éléments concordent avec la référence figurant
  dans la documentation officielle scikit-image.
- Le PDF auteur possède une pagination interne 1–14 distincte des pages
  de revue ; les repères qui suivent concernent ce PDF, pas les pages
  600–612 : §III, équation (13), page interne 6, formule locale simplifiée ;
  équations (14)–(16), page interne 7, pondération gaussienne normalisée
  11×11 avec écart-type 1.5 ; texte et équation (17), page interne 8,
  K1=0.01, K2=0.03 et moyenne des scores locaux.
- Ces passages du texte intégral ont été lus. Ils soutiennent la
  motivation luminance/contraste/structure et la distinction entre la
  configuration gaussienne originale et celle du projet, uniforme valide
  7×7 à covariances échantillonnales. La configuration pondérée originale
  ne reprend pas la correction 49/48 du code étudié.
- Le rapport ne reproduit aucune mesure expérimentale de cet article.
  Les valeurs SSIM présentées sont celles des CSV du projet.

### Documentation officielle des métriques : conventions complétées

- URL :
  https://scikit-image.org/docs/stable/api/skimage.metrics.html
- Sections structural_similarity : Parameters, Other Parameters, Notes ;
  peak_signal_noise_ratio : Parameters et Returns. Documentation
  affichée 0.26.0, consultée le 2026-10-01.
- Vérification de data_range, use_sample_covariance, gaussian_weights,
  sigma, K1 et K2. Les Notes indiquent les options nécessaires pour
  reproduire la configuration de Wang : pondération gaussienne, sigma=1.5,
  covariance non échantillonnale et plage passée explicitement.
- La documentation sert de référence de conventions, non de preuve que
  scikit-image a calculé les sorties : le projet emploie son implémentation
  NumPy, documentée et testée, sans import runtime de scikit-image.

## Vérifications et limites restantes

- Une image naturelle reste une perspective ; aucune provenance ou
  permission de redistribution n'est supposée vérifiée pour des données
  absentes du projet.
- Le texte intégral Catté n'a pas été lu et le PDF numérisé Perona–Malik
  n'a pas permis une lecture technique complète dans l'outil disponible.
  Ces limites sont explicites ; les calculs utilisés sont soit développés
  dans le rapport soit appuyés par les sections réellement lues de Weickert.
- Les liens de sources sont conservés ; aucun PDF tiers, DOI inventé,
  encadrant, affiliation additionnelle ou licence nouvelle n'est ajouté.
