# Phase 5 v2 — export de sources pour compilation externe

Cette archive contient des **sources non compilées**. Elle ne contient
ni PDF compilé du rapport ni PDF compilé du Beamer. Le rendu des
**25 diapositives principales et 7 réserves** reste à vérifier ; les
notes orales prévoient un exposé indicatif de 23 minutes. La pagination,
les liens PDF, l'absence de débordements et la lisibilité des recadrages
ne sont pas validés par cet export.

Les PDF dans results/extended/figures sont les figures expérimentales
archivées, réutilisées sans modification ; ce ne sont pas des documents
LaTeX nouvellement compilés.

## Périmètre et mécanisme

Le mode distinct du mécanisme existant est :

    .\.venv\Scripts\python.exe -B scripts/archive_phase5.py --name phase5-v2-sources

Destination de base, hors dépôt :
D:\academic-projects\pde-image-denoising-audit-phase5-v2-sources.zip.
Un suffixe numéroté est choisi automatiquement si elle existe déjà.
Le mode phase5-v2 conserve l'exigence des deux PDF compilés ; le nouveau
mode n'assouplit que son propre périmètre, avec ses sources et
justificatifs obligatoires.

Les chemins sont relatifs à la racine du projet. Sont inclus :

- rapport, sections, bibliographie et exports de report/generated ;
- Beamer et notes orales ;
- figures PDF et PNG archivées, tables, CSV/JSON et journal étendus ;
- scripts documentaires, documentation, registre des références et
  configurations ;
- empreintes de référence, comptes rendus de protection et de
  vérification documentaire, métadonnées et extrait du blocage local.

Les NPZ volumineux déjà audités, sources scientifiques src, tests et
résultats quick sont hors du lot documentaire, comme pour l'archive
de phase 5 précédente. Environnements, exécutables, caches,
prévisualisations et fichiers auxiliaires/temporaires sont exclus.
Cette archive permet la compilation et l'audit documentaires ; elle
n'est pas une reproduction scientifique autonome complète.

Le script utilise la bibliothèque standard Python zipfile. Après
création, il rouvre le ZIP en lecture seule et contrôle le CRC,
l'unicité et l'inventaire des entrées, leurs tailles et leurs SHA-256
contre les sources. Il compare aussi le périmètre archivé avant/après.

## État technique conservé

La compilation locale est bloquée avant lancement par Windows Application
Control. Voir docs/phase5_v2_build/compiler.json,
docs/phase5_v2_build/launch_failure.txt et docs/phase5_build.md.
Les anciens comptes rendus conservent leur contexte et leur date :
ils ne sont pas transformés en validation de compilation réussie.

Seuls le mode d'archivage et cette notice sont ajoutés pour cet export.
Aucune correction du rapport/Beamer, recherche de compilateur,
expérience, exécution de solveur ou nouveau calcul de métriques.
Les fichiers scientifiques et les empreintes de référence restent
inchangés. Aucun staging, commit, push ou publication.
