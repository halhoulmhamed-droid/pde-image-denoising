# Phase 5 — sources et compilation

État actuel, correction v2 du 2026-10-01 : **compilation bloquée avant
lancement par le contrôle d'application Windows**. Les corrections de
composition et les contrôles statiques sont réalisés ; aucun PDF
documentaire n'est produit, aucune pagination ni validation de rendu
n'est revendiquée. Voir le journal v2 en fin de document.

## Historique de la première rédaction

État lors de la première rédaction du 2026-10-01 : rédaction complète des sources ; **non compilé :
outils absents du PATH inspecté**. Aucun PDF du rapport ni du Beamer n'a
été produit pendant cette phase. Le nombre de pages du rapport et la
lisibilité des documents rendus ne sont donc pas validés.

## Outils effectivement recherchés

Commande PowerShell en lecture seule :

    Get-Command pdflatex,latexmk,bibtex,lualatex,tectonic,pdftoppm -ErrorAction SilentlyContinue | Select-Object Name,Source

Aucun outil n'a été trouvé. La commande renvoie 1 en l'absence de ces
commandes ; ce résultat ne correspond pas à une tentative de compilation.
Aucune installation, modification de PATH, configuration système ou
ExecutionPolicy n'a été effectuée. La présence des packages ne peut pas
être contrôlée indépendamment d'une distribution LaTeX accessible.

Python utilisé pour les contrôles documentaires :

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py
    .\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
    .\.venv\Scripts\python.exe -B scripts/check_documentation.py --report docs/phase5_documentary_checks.json

Ces scripts utilisent la bibliothèque standard et les CSV/JSON existants.
Ils n'appellent ni solveur, ni runner, ni fonction de calcul de métriques,
ni génération de figures. L'option -B évite les écritures de caches Python.
La vérification des moyennes et écarts-types lit les valeurs enregistrées,
y compris les durées ; elle ne chronomètre aucun calcul nouveau.

## Commandes de compilation proposées — non exécutées ici

Depuis D:\academic-projects\pde-image-denoising, avec les outils déjà
présents dans l'environnement choisi :

~~~powershell
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error report/main.tex
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error slides/main.tex
~~~

Sans latexmk, mais avec pdflatex et bibtex :

~~~powershell
Push-Location .\report
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
Pop-Location

Push-Location .\slides
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
Pop-Location
~~~

Le rapport utilise BibTeX (report/references.bib, style plain). Le
Beamer emploie cinq entrées locales thebibliography, de mêmes clés :
BibTeX n'est pas nécessaire pour lui. Les passes supplémentaires
résolvent les citations et références. Aucun shell-escape n'est requis.
Packages courants : babel, fontenc, inputenc, lmodern, amsmath/amssymb,
graphicx, booktabs, tabularx, xcolor ; le rapport ajoute amsthm,
longtable/array, geometry, microtype, listings, caption et hyperref.
Beamer charge déjà les fonctions hyperref nécessaires.

## Chemins et sorties attendues

- Point d'entrée du rapport : report/main.tex, six chapitres, résumés
  français/anglais, notations, bibliographie et deux annexes.
- Sections : report/sections/ ; exports : report/generated/.
- Point d'entrée des diapositives : slides/main.tex, 22 principales et
  six réserves ; notes : slides/speaker_notes.md, environ 23 minutes.
- Figures : PDF déjà présents dans results/extended/figures/, jamais
  régénérés ou modifiés. Les courbes avec suffixe image/sigma sont les
  agrégats sur dix graines ; la courbe sans suffixe n'est pas présentée
  comme un agrégat.
- Sorties futures attendues seulement : report/main.pdf et
  slides/main.pdf. Elles sont absentes à cette livraison.

L'option -cd ou les Push-Location sont indispensables pour résoudre
correctement les chemins relatifs. La présentation référence la table
documentaire située dans ../report/generated/.

## Contrôles effectués et portée

Les contrôles statiques et la relecture scientifique portent sur :
équations et conventions du code archivé, valeurs CSV sélectionnées,
agrégats, source des figures, bibliographie et clés de citation,
liens des fichiers, structure des sources, notes synchronisées et
empreintes du périmètre protégé. Le compte rendu automatique est
docs/phase5_documentary_checks.json. La relecture a corrigé la description
des lignes à n=0 et évité l'affichage nul de dispersions non nulles.

Des PNG archivés de comparaison, profil, gradient, courbes et sensibilité
ont été réellement ouverts pour la préparation ; cela ne constitue
**pas** une inspection visuelle du rapport ou des diapositives rendus.

Après une compilation future, contrôler au minimum :

~~~powershell
Select-String -Path report/main.log,slides/main.log -Pattern 'Overfull|Underfull|undefined|LaTeX Warning|Package .* Warning'
~~~

Ouvrir les deux PDF, vérifier le nombre de pages, les figures doubles,
les tables, l'accentuation, les liens et la taille des légendes projetées.
En particulier, les courbes exhaustives comportent plusieurs variantes :
leur lisibilité réelle doit être examinée à la résolution d'exposé.
Ne pas réduire abusivement les fontes pour corriger un débordement ;
préférer répartir le contenu ou déplacer les détails en réserve/annexe.

La validation statique n'est ni une compilation réussie, ni une
certification d'absence de débordements. Cette limite reste ouverte à
l'audit documentaire suivant ; elle ne remet pas en cause l'intégrité
des expériences déjà auditées.

Résultats finaux des contrôles : 126 fichiers protégés inchangés,
47 entrées de manifeste, 17 exports exacts et 476 occurrences de lignes
sources, 512 lignes LaTeX avec terminateurs contrôlés, cinq références
bibliographiques connues et 36 références internes. Les 22+6 labels des
notes sont synchronisés. Quatre contrôles négatifs documentaires en
mémoire détectent quatre altérations. Le JSON automatique donne le détail
et l'effectif actualisé des textes contrôlés ; aucune suite scientifique
n'est réexécutée.

## Correction v2 : sources et contrôle documentaire

Les six zones signalées par la compilation indépendante ont été
recomposées : tableau des notations sans indentation, formules
d'agrégation hors du paragraphe, identifiants et chemins avec coupures
possibles. La couverture désactive les ancres de page avant le passage
à la numérotation romaine ; les ancres sont ensuite réactivées. La
table des matières imprimée retient chapitres et sections ; les
sous-sections demeurent dans le texte et dans les signets PDF.
Ces dispositions sont des corrections de sources, **pas** la preuve
que les débordements et la destination dupliquée ont disparu au rendu.

Le Beamer contient désormais 25 diapositives principales et sept
réserves, toutes munies de labels uniques et de notes correspondantes,
pour un budget principal indicatif de 23 minutes. PSNR et SSIM sont
séparés pour les courbes des deux images à sigma=0.10 et pour les
sensibilités à K. Les recadrages explicites en points PDF agrandissent
chaque panneau et réutilisent la légende complète originale à droite.
Aucune courbe, configuration ni figure archivée n'est supprimée ou
modifiée. Les PNG sources ont été ouverts ; cela n'est pas un contrôle
visuel du Beamer compilé.

Commandes documentaires exécutées pendant la correction v2, depuis
la racine du projet :

~~~powershell
.\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
.\.venv\Scripts\python.exe -B scripts/check_documentation.py --report docs/phase5_v2_documentary_checks.json
~~~

Le compte rendu v2 contrôle notamment les 126 fichiers protégés,
les 47 entrées du manifeste, les 17 exports, les valeurs sources,
les chemins et références, l'unicité/ordre des 32 labels et notes,
le budget de 23 minutes, les textes non suivis et quatre contrôles
négatifs documentaires en mémoire. Le contrôle de syntaxe emploie
AST, sans import ni exécution du code scientifique.

## Tectonic officiel téléchargé, mais lancement interdit

Le programme stable Tectonic 0.17.0, cible Windows x86_64 MSVC,
a été identifié à partir de la documentation et de la publication
officielles, puis téléchargé et décompressé dans le seul répertoire
autorisé D:\academic-projects\_tools\tectonic.
Il ne s'agit ni d'une version continuous ni d'un composant Rust interne.

- Documentation : https://tectonic-typesetting.github.io/book/latest/installation/
- Publication : https://github.com/tectonic-typesetting/tectonic/releases/tag/tectonic%400.17.0
- Binaire : https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip
- Taille du téléchargement : 21 060 223 octets.
- SHA-256 du ZIP, identique au digest fourni par l'API officielle :
  f61ce51f0b0ade1015b7de7ef368541c5424e9756ecbd0d7af97d6d48030845f.
- SHA-256 de l'exécutable extrait :
  99ffcfdbf1ebf8bdda9e791942e3d06aedb12463fddc33f07de6f5211c8bf08d.

Commande de lancement réellement tentée :

~~~powershell
& 'D:\academic-projects\_tools\tectonic\0.17.0\tectonic.exe' --version
~~~

Résultat : échec avant exécution, code de sortie du contrôle PowerShell 1.
Windows indique : « Une stratégie de contrôle d'application a bloqué ce
fichier », avec NativeCommandFailed. La version 0.17.0 est celle des
métadonnées de publication ; elle n'a pas pu être confirmée par
l'exécutable. Voir phase5_v2_build/compiler.json et
phase5_v2_build/launch_failure.txt. Ce dernier conserve un extrait
identifié de la sortie réellement reçue, **pas** un journal LaTeX.

Un diagnostic en lecture seule des emplacements habituels MiKTeX,
TeX Live et Tectonic n'a trouvé aucun autre compilateur ; la liste
exacte est dans compiler.json. Aucun contournement, déblocage de
fichier, modification de politique de sécurité, installation globale,
changement d'ExecutionPolicy ou modification permanente de PATH
n'a été effectué. Les ressources LaTeX n'ont pas été téléchargées,
puisque le programme n'a pas démarré.

## Reprise nécessaire et limites réelles

Il faut un compilateur déjà autorisé sur ce PC, dont le chemin sera
fourni ou approuvé par l'utilisateur, avant de poursuivre. Avec un
Tectonic légitimement autorisé, commandes proposées seulement,
**non exécutées dans cette passe** :

~~~powershell
$env:TECTONIC_CACHE_DIR = 'D:\academic-projects\_tools\tectonic\cache'
Push-Location 'D:\academic-projects\pde-image-denoising\report'
& 'D:\academic-projects\_tools\tectonic\0.17.0\tectonic.exe' --keep-logs --keep-intermediates --print main.tex
Pop-Location
Push-Location 'D:\academic-projects\pde-image-denoising\slides'
& 'D:\academic-projects\_tools\tectonic\0.17.0\tectonic.exe' --keep-logs --keep-intermediates --print main.tex
Pop-Location
~~~

Le cache est alors limité à la session et au dossier portable autorisé.
Conserver les sorties console et les journaux, stabiliser références
et bibliographie, rechercher erreurs, Overfull/Underfull, références
indéfinies, destinations dupliquées et caractères manquants.
Ne retirer la réserve de compilation sur la couverture qu'après
compilation et contrôle effectifs. Le chiffre de 51 pages est le
constat de l'audit indépendant de l'ancien rapport, pas une pagination
locale v2 validée.

Un moteur de rendu PDF natif Windows est accessible. Il n'a rendu
aucune page documentaire : report/main.pdf et slides/main.pdf sont
absents. Liens du sommaire, débordements, nombre réel de pages,
lisibilité des recadrages et caractères ne sont donc pas validés.

## Archive documentaire v2 : attente des deux PDF

Le script scripts/archive_phase5.py accepte --name phase5-v2,
exige les deux PDF avant toute création, choisit un suffixe numéroté
sans écraser, puis contrôle CRC, inventaire, tailles et SHA-256 des
entrées. Ses contrôles de filtres et de refus préalable des PDF
absents ont été exercés en mémoire ; **aucun ZIP v2 n'a été créé**.
L'archive de première rédaction demeure inchangée.

Le périmètre prévu reste documentaire : README, report, slides,
notes, exports, scripts, docs et justificatifs, références,
configurations, CSV/JSON/journal étendus, tables et figures.
Comme dans l'archive précédente, les gros NPZ déjà audités ne sont
pas inclus ; src, tests et résultats quick ne font pas partie de
ce lot documentaire. Environnements, exécutables, caches,
prévisualisations et fichiers auxiliaires temporaires sont exclus.
Les captures pertinentes de compilation seront conservées dans
docs/phase5_v2_build au format texte, sans altérer leurs messages.

Arrêt avant phase 6. Aucun calcul scientifique, staging, commit,
push, publication ni intervention dans les autres projets.
