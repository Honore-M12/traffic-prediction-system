# Joel, ML (modèles classiques et avancés)

> **Rôle :** responsable de l'apprentissage automatique
> **Projet :** régulation intelligente des feux de circulation
> **Ce document couvre :** la préparation des variables, l'entraînement et la comparaison de 8 modèles, la sélection du modèle final, son évaluation et sa livraison.
> **Lecteurs visés :** Honoré (données), Godwin (simulation), Fouchi et Mireille (dashboard)

---

## En bref

| | |
|---|---|
| **Modèle livré** | Régression linéaire, avec historique du débit, calendrier et météo en entrée |
| **Fichier** | `models/best_model.pkl` (un seul fichier, pipeline incluse) |
| **Ce qu'il prédit** | `traffic_flow` : nombre de véhicules sur les 5 prochaines minutes |
| **Performance (test)** | MAE 19,99 véhicules / 5 min, R² 0,974, erreur ≈ 4,9 % du trafic |
| **Référence à battre** | Persistance (valeur d'il y a 5 min) : MAE 23,01 |
| **Gain sur la persistance** | 13,1 % sur le test (13,6 % sur la validation) |
| **À retenir** | Gain réel mais modeste : le trafic des 5 prochaines minutes se déduit surtout des minutes précédentes |

---

## 1. Périmètre

Prédire `traffic_flow` à partir de l'historique récent du trafic, du calendrier et de la météo ; comparer plusieurs modèles de familles différentes ; choisir le meilleur de façon objective ; livrer un modèle utilisable par la simulation (Godwin) et par le dashboard (Fouchi et Mireille). Notebook : `notebooks/03_models.ipynb`.

## 2. Travail réalisé

1. **Chargement et contrôle des données** produites par Honoré (`train.csv`, `val.csv`, `test.csv`) : trois jeux chronologiques sans chevauchement ni valeur manquante.
2. **Visualisation du dataset** (6 graphiques commentés) : évolution dans le temps, profil horaire, carte de chaleur jour × heure, distribution, corrélations, effet de la météo.
3. **Variables** (`src/features.py`) : calendrier encodé de façon cyclique, météo, historique du débit (5, 10, 15, 30 et 60 minutes, moyennes sur 1 et 3 heures, tendance) et de la vitesse passée.
4. **Baselines** : persistance, moyenne par heure, moyenne globale.
5. **Huit modèles** : régression linéaire, Decision Tree, Random Forest, KNN, SVM, XGBoost, LightGBM, MLP, réglés par validation croisée temporelle.
6. **Comparaison** (tableaux, graphiques, rapport à la persistance par bloc de validation).
7. **Sélection** par la grille pondérée du cahier des charges, analyse de sensibilité aux poids, tests statistiques (bootstrap par blocs d'une journée).
8. **Évaluation finale** : réentraînement sur train + validation, évaluation unique sur le test, importance des variables par permutation.
9. **Export** de `models/best_model.pkl` et des fichiers de résultats, avec trois vérifications automatiques.

## 3. Décisions et justifications

| Décision | Justification |
|---|---|
| **`speed_kmh` exclue** des variables d'entrée | Mesurée au même instant que la cible : fuite de données. Seules ses valeurs passées sont utilisées. |
| **Découpage chronologique** 70 / 15 / 15 | Un mélange aléatoire ferait entrer dans l'entraînement des mesures voisines du test et gonflerait les scores. |
| **Persistance comme référence principale** | Le débit est corrélé à 0,98 avec celui d'il y a 5 minutes : battre la moyenne ne prouve rien. |
| **Pipeline à colonnes brutes** | Le calcul des variables cycliques est dans la pipeline (`src/features.py`) : le dashboard n'a pas à le recoder. |
| **Sortie bornée à 0** (`RegresseurBorne`) | Une régression linéaire peut, en théorie, prédire un débit négatif. |
| **Stabilité mesurée par blocs de validation** | L'écart-type de la validation croisée reflétait la difficulté des plis (changement de régime du trafic) plus que la stabilité du modèle. |
| **Modèle retenu : régression linéaire** | Première de la grille pondérée dans les quatre pondérations testées (cahier des charges, sans temps d'inférence, performance renforcée, interprétabilité renforcée). |
| **Réentraînement sur train + validation** avant le test | Plus de données récentes, donc plus proches du régime actuel du trafic. |

## 4. Résultats clés

**Validation** (modèles entraînés sur le train, classés par MAE, en véhicules par 5 minutes) :

| Modèle | MAE | R² | Écart val − train | Blocs gagnés sur 6 |
|---|---|---|---|---|
| LightGBM | 18,87 | 0,971 | +0,43 | 6 |
| XGBoost | 19,07 | 0,971 | −0,31 | 6 |
| MLP | 19,10 | 0,971 | −0,34 | 6 |
| Random Forest | 19,17 | 0,970 | +2,99 | 6 |
| **Régression linéaire (retenue)** | **19,42** | **0,970** | **−1,37** | **6** |
| Decision Tree | 21,06 | 0,965 | +0,60 | 6 |
| SVM (1/3 du train) | 21,53 | 0,965 | +6,10 | 4 |
| *Persistance (baseline)* | *22,47* | *0,960* | *−0,96* | *n/a* |
| KNN | 26,07 | 0,952 | +3,41 | 0 |
| *Moyenne par heure (baseline)* | *51,57* | *0,822* | *−35,52* | *0* |
| *Moyenne globale (baseline)* | *136,53* | *−0,060* | *−24,96* | *0* |

**Lecture :**
- tous les modèles sauf le KNN battent la persistance ; les cinq premiers sont séparés par moins de 0,6 véhicule de MAE ;
- LightGBM a la MAE la plus basse et l'écart avec la régression linéaire (0,54 véhicule, soit 2,8 %) est statistiquement réel, mais très faible en pratique ;
- la régression linéaire est première de la grille pondérée (score ≈ 91 sur 100, devant LightGBM et XGBoost à ≈ 90) dans les quatre pondérations testées ;
- le classement est donc **serré** : le choix de la régression linéaire repose sur la règle définie à l'avance et sur sa simplicité, pas sur une supériorité de précision.

**Test** (modèle final réentraîné sur train + validation, évalué une seule fois) :

| | MAE | RMSE | R² | Erreur / trafic | Biais |
|---|---|---|---|---|---|
| **Régression linéaire (finale)** | **19,99** | 27,92 | 0,974 | 4,92 % | +0,59 |
| Persistance | 23,01 | 31,62 | 0,967 | 5,66 % | −0,04 |
| Moyenne par heure | 45,33 | 60,70 | 0,877 | 11,16 % | −7,40 |

L'écart avec la persistance (−3,02 véhicules, intervalle de confiance à 95 % de −3,35 à −2,75) est statistiquement fiable et régulier : le modèle bat la persistance dans les 6 blocs du test.

**Importance des variables** (permutation) : l'historique du débit représente environ 99 % de l'importance cumulée, le calendrier environ 1 % (surtout l'heure), la vitesse passée et la météo (température, vent, précipitations, état du ciel) sont sans effet mesurable. Conséquence pour la page 6 du dashboard : la météo saisie n'influencera pratiquement pas la prédiction.

## 5. Fichiers produits

| Fichier | Contenu |
|---|---|
| `models/best_model.pkl` | Modèle final, pipeline incluse |
| `models/model_info.json` | Colonnes d'entrée, conventions, performances, versions, seuils de niveaux de trafic |
| `results/metrics.csv` | Tous les modèles et baselines (validation), score pondéré, métriques complémentaires |
| `results/metrics_test.csv` | Résultats finaux sur le test |
| `results/predictions_test.csv` | Date, valeur réelle, prédiction du modèle, persistance |
| `results/feature_importance.csv` | Importance par permutation |
| `src/features.py` | Variables, pipeline, chargeur de données, `construire_entree`, `RegresseurBorne` |
| `notebooks/03_models.ipynb` | Tout le travail, commenté |

## 6. Utiliser le modèle (Godwin, Mireille, Fouchi)

Le dossier racine du projet doit être dans le chemin d'import (le fichier du modèle fait référence à `src.features`) et les versions de bibliothèques doivent être celles de `requirements.txt`.

- **Chargement** : `joblib.load("models/best_model.pkl")`.
- **Construction de l'entrée** : `construire_entree(historique, instant, temp_celsius, wind_speed_kmh, precip_mm, weather_condition, ferie=False)` dans `src/features.py`.
- **Historique** : au moins **36 observations** (3 heures) au pas de 5 minutes, avant l'instant prédit, avec les colonnes `traffic_flow` et `speed_kmh`.
- **Jour de la semaine** : `week_day` va de 1 (lundi) à 7 (dimanche), à calculer avec `isoweekday()` et non `weekday()`.
- **`holidays`** vaut 1 pour un jour férié **et** pour tous les week-ends (codage du dataset) ; `construire_entree` s'en charge.
- **Sortie** : débit prévu en véhicules par 5 minutes, jamais négatif.

## 7. Difficultés et solutions

| Difficulté | Solution |
|---|---|
| **Changement de régime du trafic** (confinement de 2020) : le débit moyen passe d'environ 502 en février à 333 en avril. | Persistance comme référence principale ; limite signalée dans le notebook et dans cette fiche. |
| **Fuite de données** possible via la vitesse mesurée au même instant. | Exclusion de `speed_kmh` ; seules ses valeurs passées sont utilisées. |
| **Modèle initialement inutilisable par le dashboard** : les variables cycliques étaient calculées dans le notebook. | Pipeline à colonnes brutes, vérifiée dans un processus séparé et avec `construire_entree`. |
| **Écart-type de la validation croisée trompeur** pour juger la stabilité. | Remplacé par la stabilité par blocs de validation. |
| **SVM très lent** sur 24 000 lignes. | Entraîné sur une ligne sur trois du train, sans réglage ; limite signalée. |
| **Classement serré** entre les meilleurs modèles. | Analyse de sensibilité aux poids et tests statistiques ; choix discuté dans le notebook. |

## 8. Limites et pistes d'amélioration

**Limites :** quatre mois de données sur un seul tronçon, avec un changement de régime ; validation et test de 18 jours ; **test déjà consulté une fois dans une version précédente du notebook** (il n'est pas vierge) ; un seul horizon (5 minutes) ; grilles d'hyperparamètres réduites ; temps de calcul mesurés sur une machine ; les niveaux de trafic décrivent un volume et non la congestion ; pas de découpage par voie (le module de décision attend un trafic par voie, une hypothèse de répartition reste à définir avec la simulation).

**Pistes :** tester d'autres horizons ; ajouter un indicateur du niveau récent du trafic (débit de la veille) ; intervalles de prédiction par régression par quantiles pour les bornes de durée de vert ; prédire aussi la vitesse ; évaluer sur une période plus longue et plusieurs capteurs.
