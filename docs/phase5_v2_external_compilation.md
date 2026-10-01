# Édition compilée externe — phase 5 v2

Le rapport (49 pages) et le Beamer (32 diapositives : 25 principales,
7 réserves) ont été compilés et inspectés le 1er octobre 2026.
Les notes accompagnent un exposé indicatif de 23 minutes.
Les deux PDF se trouvent dans report/main.pdf et slides/main.pdf.
Ils peuvent être lus directement sans compilateur LaTeX sur le PC.

## Contenu et portée

Ce ZIP documentaire contient les sources LaTeX, la bibliographie, les
exports tabulaires, les figures scientifiques archivées et les PDF finaux.
Les résultats scientifiques, leurs CSV/JSON et les configurations incluses
conservent leurs empreintes. Aucun solveur, runner expérimental ou test
scientifique n’a été relancé. Les 165 tests sont ceux de la phase 4 et de
l’audit antérieur.

Le contrôle externe a comparé les 52 fichiers protégés présents avec
l’inventaire original. Les 74 autres entrées (dont src, tests, résultats
quick et grands arrays NPZ) sont absentes de ce lot. Ce ZIP ne remplace pas
le dépôt scientifique complet sur le PC.

Les sources reçues et les traces du blocage Windows sont conservées dans
leur contexte historique. Les notices phase5_build.md et
phase5_v2_sources_export.md décrivent les étapes précédentes ; l’état
actuel figure dans phase5_v2_external_compilation.json.

## Corrections et preuves

La composition du sommaire et des légendes a été ajustée. Les figures
expérimentales ne sont pas régénérées : les panneaux du Beamer proviennent
des PDF originaux, avec des légendes LaTeX/TikZ aux mêmes libellés et styles.
La couverture du rapport indique maintenant son état effectivement compilé.
Les autres changements précisent le suivi documentaire.

- phase5_v2_external_changes.diff : différences avec le ZIP reçu ;
- phase5_v2_external_compilation.json : commandes, versions, nombres de pages,
  contrôles PDF et messages typographiques résiduels ;
- phase5_v2_external_documentary_checks.json : contrôles de sources, exports,
  notes et références ;
- phase5_v2_external_protection.json : les 52 fichiers protégés contrôlés et
  les 74 entrées absentes ;
- phase5_v2_build/external_*.txt : journaux réels de compilation ;
- phase5_v2_external_bundle_inventory.json : inventaire SHA-256 des fichiers
  de l’édition, hors cet inventaire lui-même.

Les journaux finaux ne signalent ni débordement, ni référence/citation non
résolue, ni destination dupliquée, ni caractère manquant. Deux messages
mineurs du rapport sont conservés : un espacement bibliographique sous-rempli
et un remplacement de variante de police dans les légendes. Le rendu a été
inspecté avec ces messages.

## Réintégration dans le projet local

Extraire le ZIP dans un dossier de revue distinct, puis comparer le diff
avec D:\academic-projects\pde-image-denoising. Les fichiers documentaires
modifiés sont report/main.tex, report/sections/appendices.tex,
slides/main.tex, slides/speaker_notes.md, README.md et docs/PHASE_STATUS.md.
Les PDF et les nouveaux comptes rendus externes peuvent ensuite accompagner
ces sources dans le projet complet. La liste des fichiers ajoutés figure
dans l’inventaire. Aucune publication, aucun staging, commit ou push ne fait
partie de cette édition.

Pour une nouvelle compilation, une distribution LaTeX avec French Babel,
les motifs de césure français, Latin Modern, Beamer et TikZ permet les
commandes latexmk documentées dans README.md. Les PDF déjà fournis ne
nécessitent aucune installation.
