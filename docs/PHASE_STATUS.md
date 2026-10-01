# État de reprise — phase 4

Dernière mise à jour : 2026-10-01.

Statut : phases 1 à 3 auditées ; phase 4 exécutée et validée ; arrêt avant 5–6.

## État initial vérifié

- chemin initial : D:\academic-projects ;
- cible créée : D:\academic-projects\pde-image-denoising ;
- parent initialement vide, cible absente, aucun AGENTS.md applicable ;
- parent hors dépôt Git ; dépôt local initialisé uniquement dans la cible ;
- aucun remote, commit, staging ou push ;
- Python 3.14.6 via py et python ;
- Git 2.53.0.windows.2 ;
- pdflatex et latexmk absents, aucune installation tentée ;
- CPU : AMD Ryzen 3 PRO 4450U, 4 cœurs / 8 processeurs logiques.

## Phase 1 — terminée

- architecture src-layout et configuration JSON rapide ;
- cahier des charges, hypothèses, modèle mathématique, schéma conservatif,
  stabilité, protocole, reproductibilité et limites ;
- ledger vérifié sur CaltechAUTHORS, page de l'auteur de Weickert, SIAM et
  documentation officielle scikit-image ;
- BibTeX et squelettes provisoires du rapport et du Beamer ;
- sources LaTeX non compilées : outils absents.

## Phase 2 — terminée

- chaleur et variante Perona–Malik directionnelle conservative à quatre
  voisins, Euler explicite float64 ;
- données synthétiques, bruit, MSE, erreur L2 relative, PSNR, SSIM NumPy,
  hashes, CLI, agrégation, figures et vérificateur ;
- blocage rencontré puis respecté : Windows Application Control refuse une DLL
  SciPy lors de l'import de skimage.metrics. Aucun contournement ; métriques
  NumPy définies et documentées, dépendance scikit-image retirée ;
- premier passage après adaptation : 65 tests réussis, 1 échec de
  sérialisation d'un booléen NumPy ; correction ciblée ;
- passage final : 67 tests réussis en 7.03 s, aucun échec.

Commande finale :

    .\.venv\Scripts\python.exe -m pytest -q

## Phase 3 — terminée

Commandes finales :

    .\.venv\Scripts\python.exe -m pde_image_denoising.run --config configs/quick.json
    .\.venv\Scripts\python.exe -m pde_image_denoising.verify --results results/quick

Résultats de la dernière exécution :

- 8 observations bruitées partagées ;
- 40 trajectoires de solveur ;
- 168 lignes dans metrics.csv ;
- 84 lignes dans summary.csv ;
- 10 arrays d'entrée et 22 arrays représentatifs comparés bit à bit ;
- 5 figures PNG et 5 PDF générées ;
- 7.2995 s pour le pipeline complet de la dernière exécution ;
- reproduction des colonnes déterministes réussie, durées exclues ;
- validation du mode propre discret : erreur max 3.6082e-16 ;
- erreurs spatiales d'amplitude : 5.2007e-4 (N=16), 1.3011e-4 (N=32) ;
- erreurs temporelles d'amplitude : 1.4342e-4 (8 pas), 7.1566e-5 (16 pas) ;
- aucun ordre de convergence déduit de seulement deux niveaux.

Les cinq PNG ont été ouverts et inspectés. Le profil a été déplacé sur une
ligne traversant le rectangle et la barre de couleur des gradients a été
placée sur un axe séparé avant la dernière exécution.

## Blocages et limites connus

- aucune image naturelle auditée ;
- deux graines dans quick ; dix dans extended, toujours sur deux images synthétiques ;
- pas de compilation LaTeX faute d'outil ;
- scikit-image/SciPy présents dans l'environnement à la suite de la tentative
  initiale, mais non requis ni utilisés par le paquet final à cause du blocage
  de DLL documenté ;
- licence toujours à confirmer.

## Prochaine étape autorisée

La phase 4, explicitement autorisée le 2026-10-01, est maintenant terminée.
Les résultats sont prêts pour audit ; ne pas relancer le protocole complet.
La phase 5 (rapport/Beamer finaux) et la phase 6 (publication/audit final)
restent interdites sans nouvelle instruction.

## Corrections de l'audit indépendant — terminées

Les corrections restent dans les phases 1 à 3. Modèles, solveurs, définition
du SSIM et paramètres du protocole rapide sont conservés. Le runner
expérimental n'a pas été relancé ; les vérifications recalculent uniquement
pour comparaison, sans nouveaux chronométrages ni génération de figures.

Changements :

- verify.py vérifie le schéma partagé de summary.csv, les clés des groupes,
  l'ensemble exact des graines distinctes et n_seeds ;
- les 10 statistiques de chaque groupe (moyenne/écart-type pour MSE, erreur
  L2 relative, PSNR, SSIM et durée) sont recalculées depuis metrics.csv ;
- les durées sont comparées uniquement à leurs valeurs enregistrées ;
- le mode strict exige l'égalité exacte et reste le mode par défaut ;
- le mode numerical doit être explicite, avec rtol=1e-10 et atol=1e-12 :
  structure et intégrité des archives restent exactes, les différences de
  hashes recalculés sont signalées, exact_reproduction reste false ;
- absence de pytest enregistrée « not installed » dans environment_metadata ;
- doublons seeds/sigmas/K_values et graines négatives rejetés ;
- tests négatifs des agrégats, de la structure, des graines et des hashes ;
- tests des différences minuscule/significative dans le mode numerical ;
- références SSIM indépendantes 0.975474975647084 et -0.954873020229685,
  avec tolérance absolue 1e-12 et sans troncature du SSIM négatif.

Commandes réellement exécutées après correction :

    .\.venv\Scripts\python.exe -B -m pytest -q
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --mode numerical

Validations obtenues :

- 115 tests réussis, aucun échec, en 7.62 s ;
- strict : passed, exact_reproduction=true, rtol=atol=0 ;
- numerical : passed, exact_reproduction=false, rtol=1e-10, atol=1e-12 ;
- dans chaque mode : 168 lignes de métriques, 84 groupes et 840 statistiques
  vérifiées ; 8 observations partagées ; 10 arrays d'entrée et 22 arrays
  représentatifs comparés ;
- aucune différence de hash des sorties ou des arrays recalculés ;
- 63 hashes de sorties contrôlés contre leurs arrays archivés (sorties à n=0
  ou représentatives) ; les autres sorties sont comparées au seul recalcul ;
- erreur du mode propre discret de Neumann inchangée : 3.6082e-16.

Le compte rendu strict est results/quick/verification.json ; le compte rendu
numerical est results/quick/verification_numerical.json. Seuls ces comptes
rendus sont écrits dans les résultats rapides. Les CSV, NPZ, figures, journaux,
configuration, environnement de l'exécution initiale et sources des solveurs
restent inchangés.

La compilation LaTeX n'est pas validée. Aucun outil LaTeX ni paquet n'a été
installé. Aucun staging, commit, push ou accès au portfolio/profil GitHub.
Arrêt maintenu avant les phases 4 à 6.

## Phase 4 — état initial conservé avant calcul

- Consignes locales et ce document lus ; aucun AGENTS.md applicable trouvé.
- Empreintes préalables de 35 fichiers dans
  docs/phase4_protection_before.json, incluant tous les résultats quick, les
  solveurs, les métriques, quick.json et les squelettes LaTeX.
- configs/extended.json et docs/extended_protocol.md figent les paramètres,
  les comptages, le cas représentatif et la règle de coût avant toute simulation.
- configs/extended_probe.json définit le pilote séparé.
- Adaptation du runner et du vérificateur en cours ; aucun calcul étendu
  exécuté à ce stade initial (voir validation ci-dessous).

## Phase 4 — exécutée et validée

### Changements dans le périmètre

- experiments.py autorise quick et extended, refuse l'écrasement d'une
  destination extended non vide, identifie l'expérience dans le journal,
  conserve le schéma CSV et le chronométrage des solveurs, ajoute un manifeste.
- run.py décrit les deux protocoles autorisés.
- verify.py vérifie inventaire, chemins et empreintes du manifeste étendu,
  exige les figures par cas et accepte --report pour préserver les anciens
  comptes rendus quick. Les modes strict/numerical restent inchangés.
- extended_analysis.py génère depuis les CSV les courbes agrégées, la
  sensibilité à K, les tables communes/oracles et les classements.
- Tests ajoutés : test_extended_runner.py, test_extended_analysis.py,
  test_extended_verification.py ; les tests antérieurs sont conservés.
- README.md, reproductibilité, protocole et observations de phase 4 mis à jour.
- Configurations nouvelles : extended.json et extended_probe.json. Empreintes
  figées avant calcul dans docs/phase4_protocol_freeze.json.

### Commandes réellement exécutées

Depuis D:\academic-projects\pde-image-denoising, interpréteur local et CPU :

    .\.venv\Scripts\python.exe -B -m pytest -q
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.run --config configs/extended_probe.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended_probe
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.run --config configs/extended.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --report results/phase4_checks/quick_strict.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --mode numerical --report results/phase4_checks/quick_numerical.json

pytest a été exécuté avant le pilote (154 réussites en 12.01 s) puis après
les derniers contrôles/corrections (165 réussites en 15.35 s). Le pilote a
été vérifié une première fois avant le passage, puis une dernière fois après
correction de l'affichage de sa table. Le calcul complet chronométré n'a été
exécuté qu'une seule fois ; le vérificateur recalcule sans mesurer de nouvelles
durées et ne lance pas le runner expérimental.

Les lectures/relevés ont utilisé Get-Content -Encoding UTF8, rg/Get-ChildItem
et Get-FileHash -Algorithm SHA256. Aucun AGENTS.md applicable trouvé.
Le lancement sandbox a échoué avant démarrage avec helper_unknown_error ;
les commandes ont ensuite été exécutées par le mécanisme d'approbation prévu,
sans contournement. Aucune installation de dépendance ou d'outil système.

Une correction de présentation était nécessaire : le format de K à deux
décimales aurait affiché 0.025 comme 0.03 dans representative_summary.tex.
Il utilise désormais le format g, couvert par un test. Les deux tables
représentatives étendues et leurs manifestes ont été régénérés depuis les CSV
existants, sans calcul de trajectoire. Les autres tables affichaient déjà K
correctement. Une tentative python -c a échoué sur le quoting PowerShell
(SyntaxError avant exécution) ; l'appel par here-string ci-dessous a réussi :

```powershell
$phase4TableCode = @'
from pathlib import Path
from pde_image_denoising.experiments import load_config, write_latex_summary_from_csv, write_result_manifest
for directory in (Path('results/extended_probe'), Path('results/extended')):
    write_latex_summary_from_csv(directory / 'summary.csv', directory / 'tables/representative_summary.tex', load_config(directory / 'config_used.json'))
    write_result_manifest(directory, 'extended')
'@
$phase4TableCode | & .\.venv\Scripts\python.exe -B -
```

### Coût et résultats obtenus

| Sortie | Pilote | Étude complète |
|---|---:|---:|
| Observations communes | 1 | 60 |
| Trajectoires | 9 | 540 |
| Lignes metrics.csv | 73 | 4 380 |
| Groupes summary.csv | 73 | 438 |
| Durée globale pipeline (s) | 6.8015153 | 44.4073020 |
| Somme des durées terminales solveurs (s) | 0.2949189 | 16.5264453 |
| Figures PNG/PDF, fichiers | 14 | 34 |

La règle de coût figée 60 × durée globale pilote donne 408.090918 s,
inférieurs à 1 200 s. Décision enregistrée avant calcul dans
docs/phase4_runtime_estimate.json. Le protocole demandé n'a pas été réduit.

Vérification stricte complète : passed, égalité exacte, rtol=atol=0 ;
47 fichiers manifestés contrôlés, 438 groupes/4 380 statistiques (durées
incluses depuis metrics.csv seulement), 60 observations partagées, 62 arrays
d'entrée, 74 arrays représentatifs et 663 hashes de sorties archivées.
Aucune différence de hash recalculé. Le pilote final passe aussi en strict
(27 fichiers manifestés). Aucune difficulté numérique n'a nécessité le mode
numerical sur extended.

Régression quick : les deux modes passent, chacun vérifiant 168 lignes,
84 groupes/840 statistiques, 8 observations, 10 arrays d'entrée et 22 arrays
représentatifs ; aucune différence de hash. Les rapports sont exclusivement
dans results/phase4_checks, pas dans results/quick.

Validation indépendante de la chaleur : erreur max 3.608224830031759e-16
sur le mode propre discret de Neumann ; erreurs d'amplitude spatiale et
temporelle décroissantes, sans nouvel ordre de convergence revendiqué.

### Artefacts, inspection et protection

- results/extended : metrics.csv, summary.csv, config_used.json,
  environment.json, arrays/inputs.npz, arrays/representative_outputs.npz,
  figures (17 paires), tables (representative_summary.tex,
  extended_common_checkpoints.csv/.tex et oracle_exploratory.csv/.tex),
  analysis.json, manifest.json, run.log et verification.json.
- Les 420 lignes de la table commune ont été contrôlées contre summary.csv ;
  ses 12 sélections oracle sont explicitement basées sur la vérité terrain.
- Les 34 figures existent, leurs signatures PNG/PDF et tailles sont contrôlées.
  Ouvertes réellement : comparison.png, intensity_profile.png,
  gradient_maps.png, metric_curves_geometric_shapes_sigma0p1.png et
  k_sensitivity_ramps_and_edges_sigma0p1.png. Pas d'affirmation d'inspection
  visuelle exhaustive ni de compilation LaTeX.
- Revue numérique indépendante en lecture seule : agrégats et classements
  recomptés depuis les CSV, cohérents avec le vérificateur et analysis.json.
- docs/phase4_protection_after.json : 35/35 empreintes et tailles inchangées ;
  les 20 fichiers quick, leurs deux comptes rendus et leur inventaire sont
  inchangés. Les configurations/protocole figés gardent leurs empreintes.
- Solveurs, métriques, bruit, jeux synthétiques, dépendances et squelettes
  LaTeX inchangés. Portfolio et profil GitHub non consultés ni modifiés.

Premières observations et limites détaillées dans docs/extended_findings.md.
À geometric_shapes, σ=0.10, n=20, K=0.10 : PM exponentielle améliore le PSNR
par rapport à la chaleur (28.344885 contre 23.648227 dB) mais réduit le SSIM
(0.625369 contre 0.801713). Petits K exponentiels préservent du bruit ; grand
K/temps long peuvent sur-lisser. Dix graines ne généralisent pas à une
population d'images naturelles ; les meilleurs réglages sont des oracles
exploratoires et plusieurs sont à la frontière temporelle de la grille.

### Arrêt

Contrôles Git locaux exécutés : git status --short, git diff --check,
git ls-files --stage et git remote -v. diff --check retourne 0 sans sortie ;
l'index et les remotes sont vides. Status indique uniquement les fichiers
et répertoires non suivis (état initial du dépôt sans commit) :

```text
?? .gitignore
?? CITATION.cff
?? README.md
?? configs/
?? docs/
?? pyproject.toml
?? references/
?? report/
?? requirements.txt
?? results/
?? slides/
?? src/
?? tests/
```

git diff --check ne vérifie pas les fichiers non suivis. Un contrôle local
complémentaire a lu les 81 fichiers texte du projet hors environnements et
caches : UTF-8, absence de blancs de fin de ligne, conflits et octets NUL,
fin de ligne finale ; aucune anomalie. Les points en attente non bloquants
restent la licence à confirmer, les articles dont seul le résumé a été lu,
la comparaison naturelle et la rédaction/compilation finale différées.

Phase 4 terminée. Rapport et Beamer restent des squelettes inchangés, compilation
non validée (outils absents lors de l'inspection initiale ; aucune installation).
Attendre l'audit et une instruction avant phases 5–6. Aucun staging, commit ou
push ; aucun dépôt distant créé.

## Phase 5 — rédaction autorisée, 2026-10-01

L'utilisateur a autorisé exclusivement la rédaction après audit des phases
1–4. L'état de phase 4 ci-dessus est historique et n'est pas effacé.
Aucune nouvelle expérience, vérification scientifique recalculant les
solveurs, génération de figures ou relance des 165 tests n'est effectuée.

### Protection et état de reprise

- Consignes locales et documents existants lus ; aucun AGENTS.md applicable
  trouvé dans les chemins inspectés.
- Avant rédaction, docs/phase5_protection_before.json enregistre les tailles
  et SHA-256 de 126 fichiers dans results/quick, results/extended,
  results/extended_probe, results/phase4_checks, configs, src et tests, hors
  caches/egg-info, plus le protocole figé et les déclarations de dépendances.
- Rapport et Beamer expressément révisables ; aucune modification du
  périmètre numérique autorisée. Portfolio et profil GitHub hors périmètre.
- Six chapitres du rapport et sections réparties dans report/sections/,
  deux résumés, notations, conclusion, bibliographie et annexes rédigés.
- Beamer 16:9 : 22 diapositives principales et six réserves ; notes pour
  les 28 labels, budget principal indicatif de 23 minutes et préparation
  aux questions scientifiques.
- scripts/export_report_material.py écrit seulement report/generated :
  17 fichiers documentaires, 438 groupes et 4 380 statistiques vérifiées
  depuis les CSV archivés, 60 observations partagées. Aucun appel scientifique.
- sources primaires réexaminées : Weickert §§1.2.1/1.3.1/1.3.2 et Wang
  §III effectivement lus ; Catté limité au résumé ; PDF numérisé PM non
  intégralement lu. Limites détaillées dans references/source_ledger.md.
- Aucun outil pdflatex, latexmk, bibtex, lualatex, tectonic ou pdftoppm trouvé
  dans le PATH inspecté. Aucune compilation tentée ou installation.

### Commandes déjà exécutées dans cette phase

Get-Content et rg pour inspection ; Get-Command pour les outils disponibles ;
Python local -B pour les empreintes et exports documentaires. Exports :

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py

Rédaction et corrections par apply_patch. Des patchs refusés pour syntaxe
ou contexte ont été corrigés avant application, sans opération destructive.
Les commandes exécutées nécessitent l'approbation de lancement dans cet
environnement ; aucune restriction réseau ou système n'est contournée.

### Validation documentaire finale

Contrôles documentaires exécutés, sans import scientifique ni calcul
nouveau de trajectoire :

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
    .\.venv\Scripts\python.exe -B scripts/check_documentation.py --report docs/phase5_documentary_checks.json

- Les 17 exports correspondent exactement aux sources CSV/JSON ; 476
  occurrences de lignes sources sont identifiées, sur sept fichiers
  d'entrée hachés. L'annexe conserve les 438 groupes ; les tables ciblées
  ne remplacent pas la grille complète.
- Toutes les 4 380 statistiques agrégées recalculées depuis les valeurs
  enregistrées sont cohérentes, durées incluses ; 60 observations communes.
- docs/phase5_protection_after.json : 126/126 tailles et SHA-256 inchangés ;
  aucun fichier ajouté ou retiré du périmètre numérique protégé.
- Manifeste extended : 47 entrées, inventaire, tailles et SHA-256 exacts ;
  configuration utilisée identique à son empreinte. Les comptes rendus de
  vérification restent les artefacts antérieurs, jamais régénérés.
- Références/chemins/environnements/accolades contrôlés statiquement,
  cinq clés bibliographiques connues, 36 références internes du rapport,
  512 lignes de tableaux LaTeX, 17 PDF graphiques présents et protégés.
- Notes synchronisées avec 22 diapositives et six réserves ; durée
  indicative de 23 minutes. Réponses aux questions scientifiques incluses.
- Quatre contrôles négatifs en mémoire détectent quatre altérations
  documentaires (table, valeur source, accolade, environnement). Ils ne
  sont pas assimilés à de nouveaux tests scientifiques.
- Contrôle séparé des textes documentaires hors baseline : UTF-8,
  absence de blancs finaux/conflits/NUL, fin de ligne finale ; aucune
  anomalie. L'effectif final figure dans le JSON automatique.
- Aucun placeholder critique dans le rapport/Beamer/notes. La mention
  de compilation non validée est une limite réelle, non un placeholder.
- Comparaison et courbe agrégée ramps_and_edges sigma=0.10 réellement
  ouvertes pendant la revue finale ; d'autres PNG ont été inspectés
  lors de la préparation. Aucun PDF documentaire rendu n'a été inspecté.

Contrôles Git exécutés séparément : git status --short, git diff --check,
git ls-files --stage et git remote -v. Tous retournent 0 ; diff --check
est sans sortie, l'index et les remotes sont vides. L'ensemble du projet
reste non suivi, sans commit initial ; scripts/ s'ajoute à l'inventaire
non suivi précédent. Sorties exactes dans docs/phase5_git_checks.json.
git diff --check ne couvre pas les fichiers non suivis : le contrôle
documentaire local ci-dessus les traite séparément, sans staging.

### Compilation et arrêt

Sources rédigées : six chapitres et 13 sections scientifiques, deux
annexes, résumés français/anglais, notations, bibliographie ; Beamer
22+6 et notes orales. Aucun PDF de rapport ni de présentation produit,
aucun nombre de pages validé, aucun contrôle de débordement ou de rendu
revendiqué. docs/phase5_build.md contient les commandes à exécuter avec
des outils disponibles, sans installation dans cette phase.

Archive documentaire de revue préparée par le script standard-library
scripts/archive_phase5.py, après les contrôles :

    .\.venv\Scripts\python.exe -B scripts/archive_phase5.py

Destination prévue : D:\academic-projects\pde-image-denoising-audit-phase5.zip,
avec suffixe numéroté si nécessaire. Le script crée uniquement le ZIP hors
du dépôt, puis contrôle en lecture seule CRC, inventaire et SHA-256 de
toutes les entrées ; il compare aussi les sources avant/après archivage.
Les NPZ déjà audités sont exclus conformément à l'archive documentaire
demandée. Le chemin, la taille et le comptage réellement obtenus sont
rapportés à l'issue de cette dernière commande.

Phase 5 achevée pour les sources et contrôles documentaires ; compilation
et validation visuelle PDF restent à effectuer. Arrêt avant la phase 6,
publication et toute nouvelle simulation. Attendre la revue documentaire.
Aucun staging, commit, push, installation ou changement du portfolio/profil
GitHub ; les 165 tests sont ceux des validations antérieures.

## Phase 5 — correction de composition et compilation v2, 2026-10-01

Nouvelle instruction autorisant uniquement les corrections documentaires,
la compilation réelle et une archive de revue v2. Contrôle préalable
en lecture seule réussi : 126 fichiers protégés inchangés, aucun ajout
ni retrait dans leur inventaire ; les références SHA-256 existantes sont
conservées. État Git : fichiers non suivis, git diff --check sans sortie,
aucun staging/commit/push. Aucun AGENTS.md applicable trouvé.

Aucun compilateur LaTeX trouvé dans le PATH ; Windows X64. Le programme
stable officiel Tectonic 0.17.0 Windows x86_64 MSVC a été téléchargé et
décompressé dans D:\academic-projects\_tools\tectonic\0.17.0, conformément
à l'autorisation. Son ZIP de 21 060 223 octets a pour SHA-256 :
f61ce51f0b0ade1015b7de7ef368541c5424e9756ecbd0d7af97d6d48030845f,
identique au digest de la publication officielle. URLs et SHA-256 de
l'exécutable dans docs/phase5_v2_build/compiler.json.

### Corrections effectuées, sans calcul scientifique

- Rapport : tableau pleine largeur sans indentation, formules de
  moyenne/écart-type en équation séparée, chemins et identifiants
  sécables, ancres de page désactivées sur la couverture puis réactivées
  après passage aux pages romaines. Sommaire imprimé limité aux chapitres
  et sections, sous-sections conservées dans le corps et les signets.
- Conclusion présentée comme celle du mini-projet, sans commentaire
  interne sur les phases. Mention de compilation non validée conservée
  sur la couverture, faute de compilation réelle.
- Beamer : courbes et sensibilités réparties en panneaux PSNR et SSIM ;
  recadrages explicites des PDF originaux, légendes complètes et
  paramètres indiqués. Aucune configuration supprimée, aucune figure
  archivée modifiée.
- 25 diapositives principales et sept réserves, 32 labels et notes
  correspondants, budget indicatif de 23 minutes.
- Contrôles documentaires et archiveur adaptés : vérification de l'ordre
  et de l'unicité des notes, maintien des contrôles de correspondance,
  journal v2 séparé. ZIP v2 refusé si un des deux PDF est absent.

### Commandes réellement exécutées et blocage

Lectures PowerShell/Get-Content/rg, détection Get-Command, lecture de
l'API publique de publication officielle Tectonic, téléchargement
Invoke-WebRequest, Get-FileHash et Expand-Archive dans le répertoire
portable autorisé. Aucune installation globale ni modification de PATH.

Tentative réelle :

    & 'D:\academic-projects\_tools\tectonic\0.17.0\tectonic.exe' --version

Échec avant lancement : « Une stratégie de contrôle d'application a
bloqué ce fichier » ; NativeCommandFailed, contrôle PowerShell exit 1.
Aucune commande de compilation n'a démarré. Aucun PDF ni journal LaTeX
n'a été produit et aucune ressource LaTeX n'a été téléchargée.
Un diagnostic simple des emplacements habituels de compilateurs
existants n'a trouvé aucun autre outil. Aucun contournement de sécurité.
L'extrait réel du blocage est docs/phase5_v2_build/launch_failure.txt.

Contrôles documentaires depuis le projet :

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
    .\.venv\Scripts\python.exe -B scripts/check_documentation.py --report docs/phase5_v2_documentary_checks.json

Les contrôles en lecture seule ont réussi : protections, exports,
manifeste, syntaxe, références, chemins et notes synchronisées. Aucun
solveur, runner, recalcul de métriques ni suite scientifique relancé.
Les agrégats contrôlés sont recomposés uniquement depuis les CSV archivés.
Le journal v2 consigne les effectifs et le résultat final.

Résultat final effectivement obtenu : exports --check exit 0,
17 fichiers exacts, 4 380 lignes de métriques, 438 groupes,
4 380 statistiques d'agrégats contrôlées et 60 observations partagées ;
check_documentation exit 0, aucune erreur, 47 entrées du manifeste,
126 fichiers protégés identiques, quatre contrôles négatifs détectés,
36 références internes, 512 lignes de tables et 32 notes synchronisées.
La syntaxe AST des trois scripts documentaires est conforme.

docs/phase5_v2_protection_check.json confirme aussi que les deux fichiers
de référence de protection originaux et le ZIP de première rédaction
gardent exactement leurs SHA-256 initiaux. Ils ne sont pas remplacés.
Git status --short : 14 entrées non suivies ; git diff --check :
exit 0 sans sortie ; index et remotes vides. Sorties exactes dans
docs/phase5_v2_git_checks.json. Le contrôle séparé des textes non suivis
est celui du compte rendu documentaire, sans staging.

### État de reprise : phase 5 partielle, compilation bloquée

Les deux PDF attendus n'existent pas ; aucun nombre de pages local ni
contrôle de journal/rendu, de liens du sommaire ou de débordements n'est
validé. Le moteur natif Windows de rendu PDF est accessible, mais
aucun document compilé n'est disponible pour l'inspection.

L'archive D:\academic-projects\pde-image-denoising-audit-phase5-v2.zip
n'est pas créée : elle doit impérativement contenir les deux PDF.
Le ZIP précédent et les empreintes de référence sont conservés.
Les contrôles de filtres et de refus préalable des PDF absents ont réussi
en mémoire ; ils ne sont pas une vérification d'un ZIP effectivement créé.
Les exclusions documentaires antérieures, notamment les NPZ volumineux,
restent celles décrites dans docs/phase5_build.md.

Prochaine étape nécessitant une instruction ciblée : obtenir le chemin
d'un compilateur déjà autorisé sur ce PC, compiler depuis report/ et
slides/, résoudre les messages réels, inspecter les PDF, vérifier les liens,
puis retirer la réserve de couverture et créer/contrôler l'archive v2.
Ne pas changer la politique de sécurité ni relancer le calcul scientifique.
Arrêt avant phase 6, sans staging, commit, push ou publication ;
portfolio, profil GitHub et autres projets non touchés.

## Phase 5 v2 — compilation externe réalisée, 2026-10-01

Le ZIP sources reçu, SHA-256
`a4dd74ed8b83596c8f55270ffa08a414bc5ca019381a02166f56d703651381e0`,
a été vérifié puis compilé dans une copie externe sous Linux avec
pdfTeX 1.40.25 et BibTeX 0.99d. Les dépendances françaises manquantes ont
été chargées dans un espace temporaire, sans installation globale ni
modification de la sécurité Windows. Le blocage local antérieur et les
comptes rendus de phases précédentes conservent leur contexte.

Le rapport final compte 49 pages et le Beamer 32 diapositives, dont 25
principales et 7 réserves. Toutes les pages ont été rendues et examinées.
Le sommaire tient sur une page et les destinations internes PDF sont
résolues. Les légendes de huit panneaux ont été recomposées en LaTeX/TikZ ;
les quatre débordements de légende détectés à la première compilation
sont résolus. Les couleurs, styles et libellés correspondent aux figures
archivées, qui n’ont pas été modifiées. La réserve de couverture a été
retirée après compilation effective. Les notes restent synchronisées avec
les 32 labels, pour 23 minutes indicatives hors réserves et questions.

Les 17 exports documentaires correspondent exactement aux CSV/JSON :
4 380 lignes de métriques, 438 groupes, 4 380 statistiques contrôlées et
60 observations partagées. Quatre contrôles négatifs documentaires sont
détectés. Les 52 fichiers protégés disponibles dans ce lot ont les mêmes
empreintes que l’inventaire original ; les 74 autres entrées sont absentes
de l’archive documentaire. Aucun contrôle complet des arrays omis ni
nouveau lancement des 165 tests scientifiques n’est revendiqué.

Les deux messages typographiques mineurs du rapport sont détaillés dans
`docs/phase5_v2_external_compilation.json`. Aucun débordement, caractère
manquant, référence ou citation non résolue n’apparaît au journal final.
Le Beamer n’a aucun avertissement final. Les journaux réels, les PDF,
les sources corrigées et les contrôles accompagnent l’édition compilée.
Aucun calcul scientifique, staging, commit, push ou publication.
Arrêt avant la phase 6. Prochaine étape : revue et réintégration
documentaire ciblée dans le projet complet sur le PC.
