# Reproductibilité

## Environnement

Le projet s'installe dans .venv et toutes les commandes invoquent directement
son interpréteur. Le calcul est NumPy float64 sur CPU. Les versions effectives
sont écrites dans environment.json de chaque expérience à l'exécution.
pytest appartient à l'extra optionnel de développement. S'il est absent,
environment_metadata() enregistre « not installed » ; cela ne bloque pas
l'exécution du paquet.

## Commandes

Depuis la racine du dépôt, sous PowerShell :

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe -m pde_image_denoising.run --config configs/quick.json
    .\.venv\Scripts\python.exe -m pde_image_denoising.verify --results results/quick

## Vérification des résultats existants

Une vérification seule utilise les fichiers déjà présents et recalcule les
valeurs pour les comparer, avec measure_time=False. Elle n'appelle pas le
runner expérimental, ne crée aucune figure et ne réécrit ni CSV ni arrays.

Le mode strict est le mode par défaut :

    .\.venv\Scripts\python.exe -m pde_image_denoising.verify --results results/quick

Il exige l'égalité exacte des métriques recalculées et des arrays. Les hashes
SHA-256 recalculés doivent également être identiques. Son compte rendu est
results/quick/verification.json.

Le mode numerical doit être choisi explicitement :

    .\.venv\Scripts\python.exe -m pde_image_denoising.verify --results results/quick --mode numerical

Il applique rtol=1e-10 et atol=1e-12 aux métriques et aux arrays de sorties
recalculés ainsi qu'aux statistiques agrégées. Pour une valeur stockée a et
une valeur de comparaison b, la condition est

    |a-b| <= 1e-12 + 1e-10 * |b|.

Ces tolérances sont des seuils de vérification pour des écarts d'arrondi,
pas des marges de performance scientifique. Les NaN sont rejetés ; une
infinité éventuelle doit avoir exactement le même signe des deux côtés.
Le rapport results/quick/verification_numerical.json indique le mode, les
tolérances et chaque différence de hash entre sorties archivées/enregistrées
et recalculées. Il porte exact_reproduction=false, même si aucune différence
n'est constatée : ce mode certifie uniquement un accord dans les tolérances.

Dans les deux modes, schémas CSV, identités des configurations, ensembles de
clés, dimensions, dtype et groupes de graines sont contrôlés exactement.
Les arrays d'entrée restent soumis à l'égalité exacte. Les hashes enregistrés
doivent correspondre exactement aux arrays archivés ; une corruption
archivale n'est pas tolérée, même si ses valeurs ne diffèrent que de très peu.
Toutes les entrées et sorties représentatives sont archivées ; les autres
sorties n'ont que leur hash enregistré, comparé à celui du recalcul.

## Agrégats et durées

Le schéma de summary.csv est commun au writer et au vérificateur. Les clés de
regroupement sont image, sigma, method, conduction, K, dx, dy, dt, n et
diffusion_time. Chaque groupe doit contenir exactement une ligne par graine
configurée ; les graines dupliquées, les clés répétées et un n_seeds incorrect
sont rejetés.

Le vérificateur recalcule depuis metrics.csv les moyennes arithmétiques et
écarts-types échantillonnaux (ddof=1) de MSE, erreur L2 relative, PSNR, SSIM et
duration_seconds. Une seule graine donne une dispersion de zéro conformément
à la convention existante. Les durées vérifiées sont exclusivement les
valeurs déjà enregistrées dans metrics.csv ; aucun nouveau chronométrage
n'intervient dans leur contrôle. Les horodatages ne sont pas comparés.

## Déterminisme et configuration

Les générateurs utilisent numpy.random.default_rng avec une graine explicite.
Une observation n'est jamais régénérée entre méthodes. Les arrays float64 sont
hashés en incluant forme, dtype et octets contigus. La vérification recalcule
les valeurs et compare les colonnes déterministes selon le mode demandé.
validate_config() rejette les graines négatives et les doublons de graines,
de niveaux sigma ou de valeurs K afin que les groupes et comptages soient
univoques.

## Données et affichage

Les vérités terrain sont générées par le package, sans téléchargement. Les
arrays numériques restent non tronqués. Matplotlib borne uniquement l'échelle
d'affichage à [0,1].

## LaTeX

En phase 5, le rapport et le Beamer ont été rédigés complètement en sources,
avec notes orales et tableaux documentaires. Leur compilation n'a pas été
validée : pdflatex, latexmk, bibtex, lualatex et tectonic n'ont pas été trouvés
dans le PATH inspecté. Aucun outil LaTeX n'a été installé. Les commandes et
les limites sont consignées dans docs/phase5_build.md ; aucun PDF final
de rapport ou de présentation n'est annoncé comme produit.

## Phase 4 — protocole, coût et archivage

configs/extended.json et docs/extended_protocol.md ont été figés avant le
pilote ; leurs SHA-256 sont conservés dans docs/phase4_protocol_freeze.json.
Le plan a été construit après l'exploration de phase 3 et n'utilise que deux
images synthétiques. Il ne constitue pas une validation sur images naturelles.

Le pilote a produit 73 lignes et 9 trajectoires en 6.8015153 s. L'estimation
conservative prédéfinie, 60 fois cette durée globale, vaut 408.090918 s,
inférieure à 1 200 s. La somme terminale des durées de solveur du pilote est
0.2949189 s, soit une estimation solveurs seuls de 17.695134 s. Ces valeurs et
la décision de passage sont dans docs/phase4_runtime_estimate.json.

Une seule exécution complète chronométrée a produit 60 observations, 540
trajectoires, 4 380 lignes et 438 groupes en 44.407302 s pour le pipeline.
La somme des durées terminales de solveur enregistrées vaut 16.5264453 s.
Ne jamais sommer les durées des checkpoints intermédiaires : elles sont
cumulatives. Comme dans quick, elles comprennent les copies aux checkpoints
mais excluent bruit, métriques, hashes, sérialisation et figures. La durée
globale est mesurée séparément (son périmètre exact est le runner avant
écriture de son journal et de son manifeste).

results/extended contient 62 arrays d'entrée et 74 arrays représentatifs dans
deux NPZ, 17 paires de figures PNG/PDF, les CSV et tables, ainsi que la
configuration, l'environnement, le journal, analysis.json et manifest.json.
Les fichiers de vérification ne font pas partie du manifeste, car ils sont
créés après sa fixation. Tous les autres fichiers sont contrôlés exactement
(chemin relatif sécurisé, inventaire complet, taille et SHA-256), y compris
en mode numerical. Les paires de figures des six cas sont exigées.

Le contrôle strict local a réussi sans recourir au mode numerical pour
extended : 4 380 statistiques agrégées contrôlées à partir des valeurs
enregistrées, 60 observations communes, 62 arrays d'entrée, 74 arrays
représentatifs, 663 hashes de sorties contre des arrays archivés. Pour les
autres sorties, leur hash enregistré est comparé au recalcul, car leurs arrays
ne sont pas tous archivés. Aucune différence de hash n'a été observée.

Les courbes par couple image/σ utilisent les moyennes et écarts-types
échantillonnaux de summary.csv sur dix graines. La figure metric_curves.png
sans suffixe reste une courbe de la seule graine représentative, distincte des
six figures metric_curves_{image}_sigma{valeur}.png/pdf agrégées. Les bandes
et barres représentent ± un écart-type, ni erreur standard ni intervalle de
confiance. Une même graine réinitialise le générateur pour chaque image/σ :
le même champ gaussien standardisé est donc réutilisé entre ces cas. Les
groupes ne doivent pas être interprétés comme des populations indépendantes.

Les choix de tables/oracle_exploratory.csv maximisent une métrique moyenne
sur les dix graines parmi la grille entière à n>0, avec accès à la vérité
terrain. Ils sont des oracles exploratoires, pas des choix sans référence.
Les tables/extended_common_checkpoints.csv/.tex publient toutes les variantes
aux sept checkpoints positifs ; comparison_n désigne le budget commun,
tandis que la baseline bruitée conserve toujours n=0.

## Protéger quick pendant les vérifications

Les 35 empreintes préalables sont dans docs/phase4_protection_before.json ;
le contrôle final est dans docs/phase4_protection_after.json. Aucun fichier de
results/quick, y compris les deux comptes rendus antérieurs, n'est réécrit.
Le nouvel argument --report permet de conserver les comptes rendus ailleurs :

    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --report results/phase4_checks/quick_strict.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --mode numerical --report results/phase4_checks/quick_numerical.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended_probe
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended

## Recalcul dans un nouveau répertoire

Le runner extended refuse de réécrire un répertoire non vide. Dans une copie
ne contenant pas encore les résultats, les commandes CLI du README suffisent.
Dans le projet déjà calculé, choisir explicitement des destinations neuves,
sans supprimer ni modifier les sorties archivées. Exemple PowerShell pour une
future reproduction autorisée (non exécutée pendant cette phase) :

```powershell
$reproductionCode = @'
from pathlib import Path
from pde_image_denoising.experiments import load_config, run_and_write
config = load_config('configs/extended.json')
config['output_dir'] = 'results/extended_reproduction'
run_and_write(config, Path(config['output_dir']))
'@
$reproductionCode | & .\.venv\Scripts\python.exe -B -
.\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended_reproduction
```

Le protocole numérique est inchangé ; seul output_dir diffère et est enregistré
dans la configuration de la reproduction. Appliquer également le contrôle de
coût du pilote avant tout nouveau calcul complet. Les durées, horodatages et
métadonnées PDF ne sont pas des grandeurs déterministes entre exécutions.
L'arrêt de phase 4 a été respecté ; la phase 5 a ensuite été autorisée
explicitement pour la rédaction uniquement. Aucun calcul scientifique n'est
relancé pendant cette phase. L'arrêt reste obligatoire avant la phase 6.

## Phase 5 — reproduction documentaire et protections

docs/phase5_protection_before.json fixe 126 fichiers : tous les résultats
quick/extended, pilote et contrôles de phase 4, les configurations, le code
scientifique et les tests (hors caches), ainsi que le protocole étendu et
les dépendances déclarées. report/main.tex, report/references.bib et
slides/main.tex sont expressément révisables pour cette rédaction.
Le contrôle final des tailles, SHA-256 et inventaires ne modifie pas ces
fichiers. Aucun solveur, calcul de nouvelles métriques, vérificateur
scientifique ou expérience n'est relancé.

Commandes documentaires depuis le projet :

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py
    .\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
    .\.venv\Scripts\python.exe -B scripts/check_documentation.py --report docs/phase5_documentary_checks.json

L'export lit metrics.csv, summary.csv et les JSON archivés. Il recalcule
uniquement les 4 380 statistiques agrégées depuis les valeurs CSV existantes,
y compris les durées enregistrées. Les CSV exportés conservent les chaînes
sources ; source_values.json identifie les lignes et les SHA-256 des sources.
Le contrôle automatique compare aussi les fichiers LaTeX générés exactement
aux rendus attendus de ces valeurs. Les figures PDF existantes sont intégrées
par liens relatifs, jamais régénérées.

Deux constats antérieurs sont distingués : la vérification stricte Windows
figure dans results/extended/verification.json ; le succès numerical
inter-environnements avec rtol=1e-10 et atol=1e-12 est celui de l'audit
indépendant communiqué par l'utilisateur. Aucun nouveau rapport numerical
extended n'est inventé ni recalculé pour la rédaction.

Les empreintes exactes assurent l'intégrité des fichiers archivés ; les
tolérances assurent un accord numérique des sorties recalculées, pas une
identité bit à bit. Les durées et horodatages restent non déterministes.
L'archive de phase 5 ne contient pas les grands NPZ déjà audités : elle
suffit à relire les documents et leurs valeurs CSV, pas à exécuter seule
le vérificateur scientifique. La compilation et l'inspection des deux
documents PDF restent à faire dans un environnement LaTeX disponible.

### Correction documentaire v2

Les références de protection originales restent inchangées. Le contrôle
v2 lit le même inventaire de 126 fichiers et écrit son propre compte rendu :

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
    .\.venv\Scripts\python.exe -B scripts/check_documentation.py --report docs/phase5_v2_documentary_checks.json

Il contrôle aussi les 25 diapositives principales, sept réserves, 32 labels
et notes uniques et ordonnés, pour un budget indicatif de 23 minutes.
L'exporteur est lancé uniquement avec --check : les exports et résultats
archivés ne sont pas réécrits.

La compilation réelle demeure bloquée par Windows Application Control
avant le lancement du Tectonic portable officiel téléchargé à la demande.
Métadonnées, SHA-256 et message exact : docs/phase5_v2_build/.
Une version téléchargée et une syntaxe documentaire contrôlée ne sont
ni une compilation réussie ni une validation visuelle. Les deux PDF
et l'archive v2 restent à produire avec un compilateur autorisé.
Voir docs/phase5_build.md pour l'état de reprise et les exclusions du ZIP.
