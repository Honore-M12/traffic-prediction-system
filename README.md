# Régulation des feux : module de décision et simulation SUMO

Partie « Régulation et simulation » du projet de régulation intelligente des feux.

- **Module de décision** (`regulation/decision.py`) : transforme le débit prévu en durées de vert, avec vert minimum, vert maximum et temps de dégagement.
- **Simulation SUMO** : un **carrefour à feux sur un axe fictif**, même trafic rejoué avec un **cycle fixe** puis avec la **régulation IA** (feux pilotés par TraCI).
- **Livrables** : `results/simulation.csv`, `results/simulation_summary.csv` et la fonction `predict_green_time()` (page 6 du dashboard).

> **État des résultats** : les chiffres de la section « Résultats » ont été obtenus avec le prédicteur « persistance » (débit des 5 minutes précédentes) sur 3 journées. **Le run final avec le modèle de Joel sur les 18 journées est à relancer** (voir « Validation finale »), puis les tableaux sont à remplacer par ses chiffres.

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
| `--peak-vph 1500` | demande de l'axe principal au pic du dataset (défaut 2100 véh/h) |
| `--fixed-green 34 --fixed-side-green 16` | verts du cycle fixe de référence (défaut 56 s axe / 24 s rues latérales, cycle 90 s) |
| `--offset 35` | seulement si `N_JUNCTIONS` > 1 dans `config.py` : décalage entre deux carrefours, en secondes |
| `--seed 42` | graine (résultats identiques à chaque lancement) |
| `--gui` | ouvre `sumo-gui` pour voir la simulation (non testé dans l'environnement de développement, qui n'a pas d'écran) |

Durée : environ 2 minutes par journée simulée (cycle fixe + IA), donc 30 à 40 minutes pour `--days all`.

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
| `load_ratio` | taux de charge du carrefour (axe + rue latérale) |
| `green_main_s`, `green_secondary_s` | vert de l'**axe principal** et des **rues latérales**, en secondes |
| `clearance_s` | temps de dégagement après chaque vert (5 s) |
| `cycle_s` | durée totale du cycle |
| `offsets_s` | décalage de chaque carrefour (`[0]` avec un seul carrefour) |

**Page 6 : ce qu'il faut fournir.** Le modèle utilise l'historique récent du débit et de la vitesse : il faut au moins **36 observations passées** (3 heures, pas de 5 min) avant l'instant prédit. La page doit donc proposer un instant du jeu de données (l'historique est alors connu) et le transmettre avec la météo saisie. `predict_green_time` appelle pour cela `construire_entree` de Joel. D'après sa note, l'historique du débit représente environ 99 % de l'importance : **la météo saisie n'influencera pratiquement pas la prédiction.** Sans historique, la page peut aussi appeler `predict_green_time({"hour": ..., "predicted_flow": ...})` avec un débit déjà prévu.

## Logique de décision

1. Le débit prévu est mis à l'échelle de l'axe principal : `FLOW_REF` = 800 véh/5 min correspond à `PEAK_MAIN_VPH` = 2100 véh/h.
2. On en déduit la demande de la rue latérale selon l'heure (part de l'axe principal : hypothèse, voir plus bas), multipliée par une marge de prudence `SIDE_SAFETY` = 1,3 : le contrôleur ne mesure pas cette demande, il n'en connaît que la tendance horaire.
3. On teste tous les cycles de 40 à 120 s (par pas de 5 s) et tous les partages du vert, et on garde celui qui **minimise le retard total estimé** : débit multiplié par le retard moyen (retard uniforme du HCM + retard de saturation), sur l'axe et sur la rue latérale.
4. Les verts sont toujours entre **10 s** et **60 s**, le cycle entre **40 s** et **120 s**.
5. Chaque vert est suivi de **5 s** de dégagement (jaune 4 s + tout-rouge 1 s).
6. Le niveau de congestion utilise les seuils de Joel (`seuils_niveaux_trafic`) : **faible** jusqu'à 303, **moyen** jusqu'à 537, **élevé** au-delà (véh / 5 min).

Tous les paramètres sont dans `regulation/config.py`. Un appel à `decide_green` prend environ 0,5 ms.

## Simulation SUMO

- **Réseau** (`regulation/network.py`) : un axe principal à **sens unique** (comme la série du dataset), 2 voies, 50 km/h, avec **un carrefour à feux** à 400 m de l'entrée. Une rue latérale à double sens (1 voie par sens, 200 m de chaque côté) croise l'axe. Tout le monde va tout droit. Feux à 2 phases : axe principal, rue latérale. (`N_JUNCTIONS` dans `config.py` permet d'ajouter d'autres carrefours coordonnés ; seule la version à 1 carrefour est validée.)
- **Trafic** (`regulation/demand.py`) : le débit de chaque intervalle de 5 min est mis à l'échelle (axe principal), la demande de la rue latérale en découle, puis tout est converti en véhicules (arrivées de Poisson, graine fixe). **Le même fichier de véhicules sert au cycle fixe et à l'IA.**
- **Contrôle** (`regulation/run_sumo.py`) : à chaque début de cycle, `decide_green()` donne les durées de vert, planifiées à la seconde près par TraCI. Le cycle fixe passe par le même code avec des durées constantes (56 s + 24 s + 2 × 5 s = 90 s).
- **Indicateurs** (`regulation/indicators.py`) :

| Indicateur | Définition |
|---|---|
| Temps d'attente moyen | `waitingTime` (arrêté, vitesse < 0,1 m/s) + délai éventuel avant d'entrer sur le réseau |
| Longueur moyenne des files | véhicules à l'arrêt sur les 3 approches (axe, rue latérale nord et sud), relevés toutes les 5 s |
| Vitesse moyenne | distance totale / temps de trajet total |
| Nombre moyen d'arrêts | `waitingCount` de SUMO |
| CO2 (optionnel) | émissions SUMO (HBEFA4), en g par véhicule |

Les véhicules sont rattachés à l'intervalle de 5 min où ils devaient partir. Après la fenêtre simulée, la simulation continue jusqu'à ce que le réseau soit vide.

## Visualiser la simulation dans sumo-gui

`run_sumo.py` lance SUMO sans fenêtre (plus rapide). Pour **voir l'impact de l'IA pendant la simulation**, `visualiser.py` simule un créneau court dans `sumo-gui` : **deux fenêtres côte à côte** avancent en même temps sur exactement le même trafic.

```powershell
python -m regulation.visualiser --data data/processed/test.csv --predictor model --model-info models/model_info.json
```

- **Fenêtre de gauche : cycle fixe. Fenêtre de droite : régulation IA.**
- Les véhicules sont colorés selon leur temps d'attente (même code dans les deux fenêtres) : **vert** = ils roulent, **jaune** = ils attendent environ 15 s, **rouge** = ils attendent 30 s ou plus. Moins de rouge à droite = l'IA agit.
- Un **compteur en direct** s'affiche dans le terminal chaque minute simulée : file d'attente, attente maximale, cycle de l'IA, et l'écart de file moyenne entre l'IA et le cycle fixe.
- Un tableau d'indicateurs du créneau est écrit à la fin dans `results_view/indicateurs_creneau.csv`.

Par défaut : mardi 19 mai 2020, créneau 07:30-09:00, précédé de 30 minutes de mise en route pour que l'axe soit déjà chargé.

| Option | Rôle |
|---|---|
| `--window 17:00-18:30` | créneau à regarder (HH:MM-HH:MM, par pas de 5 min) |
| `--day 2020-05-23` | journée |
| `--delay 100` | ralenti, en millisecondes par seconde simulée (défaut 40 ; 0 = pleine vitesse) |
| `--successif` | les deux scénarios l'un après l'autre dans une seule fenêtre (véhicules jaunes puis bleus) |
| `--colors scenario` | couleur par scénario (jaune = cycle fixe, bleu = IA) au lieu de la couleur d'attente |
| `--scenario fixed` ou `ai` | un seul scénario, dans une seule fenêtre |
| `--win-width 660 --win-height 620` | taille de chaque fenêtre (deux fenêtres de 660 px tiennent sur un écran de 1366 px) |
| `--report-every 60` | secondes simulées entre deux lignes du compteur en direct |
| `--screenshots 5` | enregistre une capture toutes les 5 minutes simulées dans `results_view/captures/` |
| `--warmup 30` | minutes de mise en route avant le créneau |
| `--focus J1` | zoom sur un carrefour (utile seulement si `N_JUNCTIONS` > 1) |
| `--headless` | sans fenêtre (pour tester) |

Les chiffres du créneau illustrent la simulation sur un créneau court ; la mesure officielle reste celle de `run_sumo.py`, sur des journées complètes. Il ne faut pas fermer les fenêtres avant la fin : le programme s'arrête alors proprement, sans résultats. Les deux fenêtres sont placées côte à côte en haut de l'écran ; si elles se chevauchent, réduire `--win-width`.

## Hypothèses

Le dataset décrit un seul tronçon d'autoroute (débit cumulé), pas un carrefour urbain : le réseau ci-dessous est une **transposition**, le dataset fournit le volume et son évolution dans la journée.

| Hypothèse | Valeur |
|---|---|
| Mise à l'échelle | la forme du trafic du dataset est conservée sur l'axe principal ; `FLOW_REF` = 800, fixé sur tout le dataset (max 794) et non sur le test ; 800 véh/5 min = 2100 véh/h |
| Capacité | débit de saturation de l'axe : 2 voies × 1 800 véh/h/voie = 3 600 véh/h (valeur mesurée dans SUMO) |
| Rue latérale | sa demande vaut environ le tiers de celle de l'axe : part de l'axe principal = 75 % + 5 % × cos(2π (h - 8) / 24) + bruit AR(1) (écart-type 0,03), bornée entre 60 % et 90 % |
| Sens | l'axe est à sens unique ; la rue latérale est répartie à parts égales entre ses deux sens |
| Cycle fixe de référence | 56 s + 24 s + 2 × 5 s = 90 s (plan classique, 70 % du vert pour l'axe) |
| Marge de prudence `SIDE_SAFETY` | 1,3, calibrée sur la simulation du 19 mai (essais 1,0 / 1,3 / 1,6 / 2,0 : attente 9,6 / 8,4 / 9,2 / 13,1 s) |

## Résultats (prédicteur « persistance », 19, 23 et 27 mai 2020, graine 42)

À remplacer par les chiffres du modèle de Joel sur les 18 journées (voir « Validation finale »).

| Indicateur | Cycle fixe | Régulation IA | Gain |
|---|---|---|---|
| Temps d'attente moyen (s/véh) | 12,2 | 8,1 | **-33,5 %** |
| Longueur moyenne des files (véh) | 4,8 | 3,2 | -32,8 % |
| Vitesse moyenne (km/h) | 33,8 | 35,5 | +5,1 % |
| Arrêts moyens (arrêts/véh) | 0,550 | 0,627 | **pire** (-13,9 %) |
| CO2 (g/véh) | 149,5 | 145,4 | -2,8 % |

Objectif de -15 % sur le temps d'attente : **atteint**, avec 32,6 % (19 mai), 32,9 % (23 mai) et 35,0 % (27 mai). Le réglage de la marge de prudence n'a utilisé que le 19 mai : les deux autres journées le valident.

### Robustesse (temps d'attente, mardi 19 mai, persistance)

| Variante | Gain |
|---|---|
| Référence (graine 42, 2100 véh/h au pic) | 32,6 % |
| Autre graine (7) | 32,0 % |
| Demande plus faible (1500 véh/h au pic) | 43,8 % |
| **Demande plus forte (2700 véh/h au pic, axe proche de la saturation)** | **-24,8 % (l'IA est moins bonne que le cycle fixe)** |
| **Meilleur cycle fixe testé** (31 s / 14 s, cycle de 55 s) | **8,4 %** |

Attente moyenne le 19 mai selon le réglage du cycle fixe (en s) : cycle 40 s (22 / 8) : 44,1 (saturé) ; 45 s : 12,7 ; 50 s : 9,8 ; 55 s : 9,2 ; 60 s : 9,5 ; 70 s : 10,4 ; 80 s : 12,1 ; 90 s : 12,5 ; 110 s : 15,3. La régulation IA donne 8,4.

## Vérifications effectuées

- Les durées de vert, de jaune et de tout-rouge obtenues dans SUMO sont **exactement** celles planifiées (relevé seconde par seconde de l'état du feu, y compris au changement de plan toutes les 5 minutes). Les bornes min/max ne sont jamais dépassées (verts IA de 19 à 45 s sur l'axe et de 10 à 23 s sur la rue latérale, cycles de 40 à 75 s, jamais en dessous de 40 s).
- Même nombre de véhicules pour le cycle fixe et pour l'IA (105 545 sur les 3 journées), aucune valeur manquante dans `simulation.csv`, 288 lignes par journée, 24 colonnes.
- Les résultats sont reproductibles (même graine, mêmes chiffres).

## Limites

- **Résultats valables pour ce carrefour fictif, pas pour une route réelle.** Un seul sens sur l'axe, tout droit uniquement (pas de tourne-à-gauche ni de piétons).
- **Face à un cycle fixe réglé au mieux (55 s), le gain n'est que de 8,4 %**, sous l'objectif de 15 %. Le gain de 33 % est mesuré contre un cycle classique de 90 s. Les deux chiffres doivent être cités.
- **Axe proche de la saturation (2700 véh/h au pic) : l'IA est moins bonne que le cycle fixe** (attente 23,2 s contre 18,6 s). Le contrôleur choisit des cycles courts et n'a pas de détecteur pour voir les files.
- **Le contrôleur ne mesure pas le trafic de la rue latérale** : il n'en connaît que la tendance horaire (celle utilisée pour générer la demande), d'où la marge de prudence de 1,3. Le bruit lui est imprévisible.
- **Paramètre calibré dans la simulation** : la marge de prudence a été choisie sur le 19 mai ; les journées du 23 et du 27 mai la valident.
- **Le nombre d'arrêts n'est pas amélioré** (-14 %) : les cycles courts font plus d'arrêts des véhicules de la rue latérale.
- **La simulation discrimine peu la qualité du modèle de prédiction** (le débit varie lentement d'un pas de 5 min au suivant). Le gain vient surtout de la régulation adaptative.
- **Période COVID** : `test.csv` (13 au 31 mai 2020) est une période de reprise partielle. Les gains valent pour cette période, pas pour une année normale.

## Validation finale (à refaire avec le modèle de Joel)

Le modèle final de Joel (`best_model.pkl`) est une régression linéaire dont le code (`RegresseurBorne`, calcul des variables) est dans son `src/features.py`.

1. **Modèle rechargé** : `python -m regulation.check_model ...` doit donner un MAE de **19,991** et un écart de **0,0000** avec `results/predictions_test.csv`.
2. **Simulation avec le modèle, toutes les journées** :

```powershell
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --days all --rebuild-net
```

`--rebuild-net` reconstruit le réseau : l'ancien réseau (carrefour à 4 branches) ne convient plus.

## Format de `results/simulation.csv`

Une ligne par intervalle de 5 min des journées simulées.

| Colonnes | Description |
|---|---|
| `datetime`, `traffic_flow` | horodatage et débit du dataset |
| `predicted_flow` | débit prévu utilisé par le contrôleur |
| `demand_total_vph`, `share_main` | demande totale injectée (axe + rue latérale, véh/h) et part de l'axe principal dans la demande du carrefour |
| `congestion_level` | `faible`, `moyen` ou `élevé` (seuils de Joel : 303 et 537 véh/5 min) |
| `fixed_*` et `ai_*` | `avg_wait_s`, `avg_queue_veh`, `avg_speed_kmh`, `stops_per_veh`, `co2_g_per_veh`, `n_vehicles`, `green_main_s` (axe), `green_secondary_s` (rues latérales), `cycle_s` |

`results/simulation_summary.csv` : indicateurs globaux et par journée (`scope`, `indicator`, `label`, `unit`, `fixed`, `ai`, `gain_pct`).

**Pour le dashboard** : les colonnes `green_main_s` et `green_secondary_s` désignent maintenant l'**axe principal** et les **rues latérales**, pas des capteurs réels.

## Structure

```
regulation/
    config.py          paramètres et hypothèses
    decision.py        module de décision, predict_green_time()
    predictors.py      sources de prédiction (persistance, CSV, modèle) et lecture de model_info.json
    features.py        préparation des colonnes d'entrée du modèle (vérifie les colonnes manquantes)
    network.py         construction du réseau SUMO (axe, carrefour à feux, rue latérale)
    demand.py          dataset -> véhicules SUMO
    run_sumo.py        simulation fixe vs IA (TraCI), écriture des CSV
    visualiser.py      visualisation dans sumo-gui : deux fenêtres côte à côte (fixe / IA), compteur en direct
    indicators.py      calcul des indicateurs
    check_model.py     vérification du modèle rechargé
src/                   dossier de Joel (features.py), non inclus ici, requis par le .pkl
sumo_scenario/         réseau SUMO généré (c.net.xml, ...)
results/               simulation.csv, simulation_summary.csv
```

## Versions

Python 3.12, SUMO 1.28.0, eclipse-sumo/traci/sumolib 1.28.0, numpy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1 (pour charger le modèle et pour `src/features.py`), joblib 1.6.0.
