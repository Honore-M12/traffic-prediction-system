# Régulation des feux : module de décision et simulation SUMO

Partie « Régulation et simulation » du projet de régulation intelligente des feux.

- **Module de décision** (`regulation/decision.py`) : transforme le débit prévu en durées de vert, avec vert minimum, vert maximum et temps de dégagement.
- **Simulation SUMO** : un carrefour fictif, même trafic rejoué avec un **cycle fixe** puis avec la **régulation IA** (feux pilotés par TraCI).
- **Livrables** : `results/simulation.csv`, `results/simulation_summary.csv` et la fonction `predict_green_time()` (page 6 du dashboard).

> **État des résultats** : les chiffres ci-dessous ont été obtenus avec le **modèle sauvegardé de Joel** (`models/best_model.pkl`, régression linéaire), après vérification qu'il est bien rechargé (voir « Validation finale »).

## Installation

Prérequis : Python 3.12, SUMO 1.28 (variable `SUMO_HOME` définie, c'est le cas avec l'installateur Windows).

```powershell
pip install -r requirements.txt
pip install scikit-learn==1.9.1
```

La version de scikit-learn doit être celle de Joel (indiquée dans `models/model_info.json`) pour recharger le `.pkl`.

**Le dossier `src/` de Joel est indispensable.** Le `.pkl` fait référence à `src/features.py` (classe `RegresseurBorne`, variables cycliques). Dans le dépôt, `src/` est déjà à la racine, à côté de `regulation/` : il suffit de lancer toutes les commandes depuis cette racine. Dans un dossier de test à part, copier son dossier `src/` à côté de `regulation/`.

## Lancer la simulation

À exécuter à la racine du dépôt (là où se trouve le dossier `regulation/`).

```powershell
# 1. Test rapide, sans modèle (prédiction = débit des 5 minutes précédentes)
python -m regulation.run_sumo --data data/processed/test.csv

# 2. Avec les prédictions déjà produites par Joel
python -m regulation.run_sumo --data data/processed/test.csv --predictor csv --predictions results/predictions_test.csv

# 3. Validation finale : avec le modèle sauvegardé
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json
```

Options utiles :

| Option | Rôle |
|---|---|
| `--days 2020-05-19,2020-05-23` | journées à simuler (défaut : un mardi et un samedi) ; `--days all` simule les 18 journées complètes (long) |
| `--peak-vph 4500` | niveau de charge du carrefour (défaut 5400 véh/h au pic du dataset) |
| `--fixed-green 30` | vert par axe du cycle fixe de référence (défaut 40 s) |
| `--seed 42` | graine (résultats identiques à chaque lancement) |
| `--gui` | ouvre `sumo-gui` pour voir la simulation (non testé dans l'environnement de développement, qui n'a pas d'écran) |

Durée : environ 2 à 3 minutes par journée simulée (cycle fixe + IA).

Avant la validation finale, vérifier que le modèle est bien rechargé et qu'il reproduit les résultats de Joel :

```powershell
python -m regulation.check_model --data data/processed/test.csv --model-info models/model_info.json --predictions results/predictions_test.csv
```

Ce contrôle recalcule le MAE sur `test.csv` et le compare à `performances_test.MAE` de `model_info.json` (19,99).

**Les variables d'historique** (retards, moyennes glissantes sur 12 et 36 pas) sont calculées par la fonction de Joel `charger_donnees_modele`, à partir de `train.csv`, `val.csv` et `test.csv` qui doivent se trouver dans le **même dossier** que le fichier passé à `--data` (le début du test utilise la fin de la validation, comme à l'entraînement).

## Utiliser `predict_green_time()` dans le dashboard

```python
from regulation.decision import predict_green_time

# Cas 1 : le débit prévu est déjà connu
predict_green_time({"hour": 17, "minute": 30, "predicted_flow": 740})

# Cas 2 : on passe le modèle, qui calcule le débit à partir des conditions
from regulation.predictors import ModelPredictor, load_model_info
info = load_model_info("models/model_info.json")
model = ModelPredictor("models/" + info["fichier"], info["variables_entree"])
# historique : DataFrame des observations passées (au moins 36 lignes, pas de 5 min,
# colonnes traffic_flow et speed_kmh), qui précèdent l'instant demandé
predict_green_time({"historique": historique, "instant": "2020-05-19 17:30",
                    "temp_celsius": 18, "wind_speed_kmh": 10, "precip_mm": 0,
                    "weather_condition": "Fair", "ferie": False}, predictor=model)
```

Retour :

| Clé | Signification |
|---|---|
| `predicted_flow` | débit prévu (véh / 5 min) |
| `congestion_level` / `congestion_color` | `faible` / `moyen` / `élevé` et `vert` / `orange` / `rouge` |
| `load_ratio` | taux de charge du carrefour (0 à 1) |
| `green_main_s`, `green_secondary_s` | vert de l'axe principal (N-S) et de l'axe secondaire (E-O), en secondes |
| `clearance_s` | temps de dégagement après chaque vert (5 s) |
| `cycle_s` | durée totale du cycle |

**Page 6 : ce qu'il faut fournir.** Le modèle utilise l'historique récent du débit et de la vitesse : il faut au moins **36 observations passées** (3 heures, pas de 5 min) avant l'instant prédit. La page doit donc proposer un instant du jeu de données (l'historique est alors connu) et le transmettre avec la météo saisie. `predict_green_time` appelle pour cela `construire_entree` de Joel. D'après sa note, l'historique du débit représente environ 99 % de l'importance : **la météo saisie n'influencera pratiquement pas la prédiction.** Sans historique, la page peut aussi appeler `predict_green_time({"hour": ..., "predicted_flow": ...})` avec un débit déjà prévu.

## Logique de décision

1. Le débit prévu est mis à l'échelle du carrefour fictif : `FLOW_REF` = 800 véh/5 min correspond à `PEAK_TOTAL_VPH` = 5400 véh/h.
2. Il est réparti entre l'axe principal et l'axe secondaire selon l'heure.
3. La durée du cycle suit la formule de Webster simplifiée `C = (1,5 L + 5) / (1 - Y)`, bornée entre 40 s et 120 s (`L` = temps perdu, `Y` = taux de charge).
4. Le vert est réparti proportionnellement à la demande de chaque axe et borné entre **10 s** et **60 s**.
5. Chaque vert est suivi de **5 s** de dégagement (jaune 4 s + tout-rouge 1 s).
6. Le niveau de congestion utilise les seuils de Joel (`seuils_niveaux_trafic`) : **faible** jusqu'à 303, **moyen** jusqu'à 537, **élevé** au-delà (véh / 5 min).

Tous les paramètres sont dans `regulation/config.py`.

## Simulation SUMO

- **Réseau** (`regulation/network.py`) : carrefour à 4 branches de 400 m, 2 voies par sens, 50 km/h, véhicules en tout droit uniquement. Feux à 2 phases : axe principal N-S, axe secondaire E-O.
- **Trafic** (`regulation/demand.py`) : le débit de chaque intervalle de 5 min est mis à l'échelle, réparti entre les deux axes, puis converti en véhicules (arrivées de Poisson, graine fixe). **Le même fichier de véhicules sert au cycle fixe et à l'IA.**
- **Contrôle** (`regulation/run_sumo.py`) : à chaque début de cycle, la boucle TraCI demande les durées à `decide_green()` et les applique. Le cycle fixe passe par le même code avec des durées constantes (40 s + 40 s).
- **Indicateurs** (`regulation/indicators.py`) :

| Indicateur | Définition |
|---|---|
| Temps d'attente moyen | `waitingTime` (arrêté, vitesse < 0,1 m/s) + délai éventuel avant d'entrer sur le réseau |
| Longueur moyenne des files | véhicules à l'arrêt sur les 4 approches, relevés toutes les 5 s |
| Vitesse moyenne | distance totale / temps de trajet total |
| Nombre moyen d'arrêts | `waitingCount` de SUMO |
| CO2 (optionnel) | émissions SUMO (HBEFA4), en g par véhicule |

Les véhicules sont rattachés à l'intervalle de 5 min où ils devaient partir. Après la fenêtre simulée, la simulation continue jusqu'à ce que le réseau soit vide.

## Visualiser la simulation dans sumo-gui

`run_sumo.py` lance SUMO sans fenêtre (plus rapide). Pour **voir** le carrefour, par exemple pour la soutenance, `visualiser.py` simule un créneau court dans `sumo-gui` : d'abord le cycle fixe, puis la régulation IA, sur exactement le même trafic.

```powershell
python -m regulation.visualiser --data data/processed/test.csv --predictor model --model-info models/model_info.json
```

Par défaut : mardi 19 mai 2020, créneau 07:30-09:00 (pointe du matin), précédé de 30 minutes de mise en route pour que le carrefour soit déjà chargé.

| Option | Rôle |
|---|---|
| `--window 17:00-18:30` | créneau à regarder (HH:MM-HH:MM, par pas de 5 min) |
| `--day 2020-05-23` | journée |
| `--scenario fixed` ou `ai` | un seul scénario au lieu des deux |
| `--delay 40` | ralenti, en millisecondes par seconde simulée (0 = pleine vitesse) |
| `--screenshots 10` | enregistre une capture toutes les 10 minutes simulées dans `results_view/captures/` |
| `--warmup 30` | minutes de mise en route avant le créneau, sans ralenti |
| `--headless` | sans fenêtre (pour tester) |

**Ce qu'on voit** : un carrefour en croix, 2 voies par sens, vu de dessus et centré. Les **véhicules jaunes** sont ceux du cycle fixe, les **véhicules bleus** ceux de la régulation IA. À chaque ligne d'arrêt, un trait **vert ou rouge** indique l'état du feu. Dans le terminal, chaque début de cycle affiche l'heure, les verts choisis et la durée du cycle (toujours 40 s / 40 s / 90 s en cycle fixe).

À la fin, un tableau d'indicateurs du créneau (mise en route exclue) est écrit dans `results_view/indicateurs_creneau.csv`. Ces chiffres illustrent la simulation sur 1 h 30 ; la mesure officielle reste celle de `run_sumo.py`, sur des journées complètes. Il ne faut pas fermer la fenêtre avant la fin : le programme s'arrête alors proprement, sans résultats.

## Hypothèses

Le dataset décrit un seul tronçon d'autoroute (débit cumulé, jusqu'à ~9 500 véh/h), pas un carrefour.

| Hypothèse | Valeur |
|---|---|
| Mise à l'échelle | la forme du trafic du dataset est conservée, ramenée à la capacité du carrefour ; `FLOW_REF` = 800, fixé sur tout le dataset (max 794) et non sur le test |
| Capacité du carrefour | débit de saturation **mesuré dans SUMO** : environ 7 200 véh/h de vert par axe (1 800 véh/h/voie) |
| Charge au pic du dataset | 75 % de la capacité (5400 véh/h) |
| Répartition entre axes | part de l'axe principal = 50 % + 15 % × cos(2π (h - 8) / 24) + bruit AR(1) (écart-type 0,04) : axe principal plus chargé le matin, moins le soir |
| Sens | chaque axe est réparti à parts égales entre ses deux sens |
| Cycle fixe de référence | 40 s + 40 s + 2 × 5 s = 90 s |

## Résultats (modèle de Joel, mardi 19 et samedi 23 mai 2020, graine 42)

| Indicateur | Cycle fixe | Régulation IA | Gain |
|---|---|---|---|
| Temps d'attente moyen (s/véh) | 15,2 | 8,3 | **-45,2 %** |
| Longueur moyenne des files (véh) | 11,6 | 6,2 | -46,8 % |
| Vitesse moyenne (km/h) | 33,6 | 36,8 | +9,5 % |
| Arrêts moyens (arrêts/véh) | 0,635 | 0,648 | légèrement pire (-2,2 %) |
| CO2 (g/véh) | 170,9 | 159,1 | -6,9 % |

Objectif de -15 % sur le temps d'attente : **atteint**. Le détail par journée est dans `results/simulation_summary.csv`.

### Robustesse (temps d'attente, mardi 19 mai)

Avec le modèle de Joel :

| Variante | Gain |
|---|---|
| Référence (graine 42, charge au pic 5400 véh/h) | 45,4 % |
| Autre graine (7) | 45,5 % |
| Charge au pic de 4500 véh/h | 50,7 % |
| **Meilleur cycle fixe testé** (vert 20 s, cycle de 50 s) | **25,6 %** |

Avec le prédicteur « persistance » (mesures faites avant la validation finale) :

| Variante | Gain |
|---|---|
| Charge au pic de 3000 / 4500 / 5400 / 6300 véh/h | 52,5 % / 50,3 % / 44,8 % / 46,9 % |
| Vert du cycle fixe de 20 / 25 / 30 / 40 / 50 s (cycle de 50 / 60 / 70 / 90 / 110 s) | 24,7 % / 27,2 % / 33,4 % / 44,8 % / 54,1 % |
| Prédiction parfaite au lieu de la persistance | 44,6 % (contre 44,8 %) |

## Vérifications effectuées

- Les durées de vert obtenues dans SUMO sont **exactement** celles demandées (écart nul sur 540 cycles) ; jaune et tout-rouge sont toujours respectés. Les bornes min/max ne sont jamais dépassées (verts observés de 10 s à 32 s avec la persistance, de 10 s à 30 s avec le modèle de Joel).
- Tous les véhicules injectés arrivent à destination (67 114 et 66 842 sur les deux journées).
- Les résultats sont reproductibles (même graine, mêmes chiffres) : le cycle fixe donne exactement les mêmes valeurs d'un poste à l'autre.
- Contrôles du fichier `simulation.csv` : 288 lignes par journée, aucune valeur manquante, cycle fixe toujours à 90 s, même nombre de véhicules pour le cycle fixe et pour l'IA (67 114 le 19 mai).

## Limites

- **Résultats valables pour ce carrefour fictif, pas pour une route réelle.** Une seule intersection isolée, tout droit uniquement (pas de tourne-à-gauche ni de piétons).
- **Le gain vient surtout de l'adaptation de la durée du cycle.** Le contrôleur raccourcit le cycle quand la charge est modérée (cycle moyen de 42 s contre 90 s en fixe), ce qui réduit l'attente aux feux rouges. Face à un cycle fixe réglé au mieux (50 s), le gain est de 25,6 %.
- **Le contrôleur connaît la tendance horaire de la répartition entre axes** (celle utilisée pour générer la demande). Seul le bruit lui est imprévisible.
- **Le nombre d'arrêts n'est pas amélioré** (+2 %) : les cycles plus courts font plus de changements de phase.
- **La simulation discrimine peu la qualité du modèle de prédiction** : une prédiction parfaite donne le même gain que la persistance, car le débit varie lentement d'un pas de 5 min au suivant. Le modèle de Joel ne réduit d'ailleurs le MAE que de 13 % par rapport à la persistance : le gain mesuré vient surtout de la régulation adaptative, pas du modèle.
- **Période COVID** : `test.csv` (13 au 31 mai 2020) est une période de reprise partielle (débit moyen ~406 véh/5 min contre ~500 en février). Les gains valent pour cette période, pas pour une année normale.

## Validation finale (faite)

Le modèle final de Joel (`best_model.pkl`) est une régression linéaire dont le code (`RegresseurBorne`, calcul des variables) est dans son `src/features.py`.

1. **Modèle rechargé** : `python -m regulation.check_model ...` donne un MAE de **19,991** (19,9906 dans `model_info.json`) et un écart de **0,0000** avec `results/predictions_test.csv`.
2. **Simulation avec le modèle** : `python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --out-dir results` a produit `results/simulation.csv` et `results/simulation_summary.csv` (résultats ci-dessus).

## Format de `results/simulation.csv`

Une ligne par intervalle de 5 min des journées simulées.

| Colonnes | Description |
|---|---|
| `datetime`, `traffic_flow` | horodatage et débit du dataset |
| `predicted_flow` | débit prévu utilisé par le contrôleur |
| `demand_total_vph`, `share_main` | demande simulée et part de l'axe principal |
| `congestion_level` | `faible`, `moyen` ou `élevé` (seuils de Joel : 303 et 537 véh/5 min) |
| `fixed_*` et `ai_*` | `avg_wait_s`, `avg_queue_veh`, `avg_speed_kmh`, `stops_per_veh`, `co2_g_per_veh`, `n_vehicles`, `green_main_s`, `green_secondary_s`, `cycle_s` |

`results/simulation_summary.csv` : indicateurs globaux et par journée (`scope`, `indicator`, `label`, `unit`, `fixed`, `ai`, `gain_pct`).

**Pour le dashboard** : le filtre « voie » correspond aux **deux axes simulés** (principal N-S et secondaire E-O), pas à des capteurs réels.

## Structure

```
regulation/
    config.py          paramètres et hypothèses
    decision.py        module de décision, predict_green_time()
    predictors.py      sources de prédiction (persistance, CSV, modèle) et lecture de model_info.json
    features.py        préparation des colonnes d'entrée du modèle (vérifie les colonnes manquantes)
    network.py         construction du carrefour SUMO
    demand.py          dataset -> véhicules SUMO
    run_sumo.py        simulation fixe vs IA (TraCI), écriture des CSV
    visualiser.py      mode visualisation dans sumo-gui (créneau court, captures)
    indicators.py      calcul des indicateurs
    check_model.py     vérification du modèle rechargé
src/                   dossier de Joel (features.py), non inclus ici, requis par le .pkl
sumo_scenario/         réseau SUMO généré (c.net.xml, ...)
results/               simulation.csv, simulation_summary.csv
```

## Versions

Python 3.12, SUMO 1.28.0, eclipse-sumo/traci/sumolib 1.28.0, numpy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1 (pour charger le modèle et pour `src/features.py`), joblib 1.6.0.
