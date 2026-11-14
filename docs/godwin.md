# Documentation Régulation et simulation : Godwin

> **Rôle :** Responsable Régulation et simulation
> **Projet :** Régulation intelligente des feux de circulation
> **Ce document couvre :** le module de décision (trafic prévu → durées de vert), la simulation SUMO (feux fixes contre feux pilotés par l'IA), les indicateurs, les résultats et la fonction `predict_green_time()` pour le dashboard.
> **Lecteurs visés :** Joel (ML), Honoré (données), Fouchi et Mireille (dashboard)

---

## En bref

| | |
|---|---|
| **Simulateur** | SUMO 1.28.0, contrôle des feux par TraCI |
| **Carrefour** | fictif, 4 branches de 400 m, 2 voies par sens, 50 km/h, tout droit uniquement |
| **Phases** | 2 : axe principal N-S et axe secondaire E-O |
| **Scénario de référence** | cycle fixe de 90 s (vert 40 s par axe, dégagement 5 s après chaque vert) |
| **Scénario IA** | vert calculé à chaque pas de 5 min à partir du débit prévu par le modèle de Joel |
| **Demande** | débit du dataset mis à l'échelle (800 véh/5 min = 5 400 véh/h), arrivées de Poisson, graine 42, **même fichier de véhicules pour les deux scénarios** |
| **Fenêtre simulée** | 19 et 23 mai 2020 (2 jours, 576 pas de 5 min), extraits de `test.csv` |
| **Résultat principal** | temps d'attente moyen **15,24 s → 8,35 s (−45,2 %)**, objectif de −15 % dépassé |
| **Fichiers produits** | `results/simulation.csv`, `results/simulation_summary.csv` |
| **Point d'entrée dashboard** | `regulation.decision.predict_green_time(conditions, predictor=None)` |

Ce que j'ai fait en une phrase : j'ai construit un carrefour dans SUMO, fait rejouer à ce carrefour le trafic du dataset de test une fois avec des feux à cycle fixe et une fois avec des feux dont le vert est décidé à partir de la prédiction de Joel, puis comparé les deux avec les mêmes véhicules.

---

## 1. Périmètre

### 1.1 Ce qui m'était demandé

- Un module de décision : à partir du trafic prévu, proposer des durées de vert, avec des bornes de sécurité (minimum, maximum) et un temps de dégagement.
- Une simulation SUMO comparant cycle fixe et régulation IA.
- Des indicateurs : temps d'attente moyen, longueur de file, vitesse moyenne, nombre d'arrêts, CO2 en option. Objectif : réduction du temps d'attente d'au moins 15 %.
- Un fichier `simulation.csv` et une fonction `predict_green_time()` utilisée par la page 6 du dashboard.
- Cette documentation et le dépôt GitHub.

### 1.2 Ce que je n'ai pas fait

- Je n'ai pas entraîné de modèle : j'utilise celui de Joel tel quel (`best_model.pkl`).
- Je n'ai pas construit la page 6 du dashboard : je fournis la fonction qu'elle appelle.
- Je n'ai pas simulé un vrai réseau routier : le dataset ne décrit qu'un tronçon d'autoroute (voir limite 1).

---

## 2. Hypothèses du scénario

Le dataset ne contient qu'**une seule série de trafic**. Il n'y a ni carrefour, ni deuxième axe. Pour simuler un carrefour, j'ai donc posé des hypothèses, toutes écrites dans `regulation/config.py`.

| Hypothèse | Valeur | Pourquoi |
|---|---|---|
| Géométrie | 4 branches de 400 m, 2 voies par sens, 50 km/h | carrefour urbain simple, assez long pour absorber les files |
| Mouvements | tout droit uniquement | pas de tourne-à gauche, donc 2 phases suffisent |
| Échelle de la demande | 800 véh/5 min = 5 400 véh/h au total | 800 est fixe, tiré du maximum du dataset entier (794) ; ne dépend pas de la fenêtre simulée |
| Répartition entre axes | `part_principal = 0,50 + 0,15·cos(2π(h−8)/24)` + bruit AR(1) | l'axe principal est plus chargé vers 8 h ; bruit d'écart-type 0,04, ρ = 0,9, borné entre 0,20 et 0,80 |
| Arrivées | processus de Poisson, graine 42 | reproductible |
| Débit de saturation | 7 200 véh/h de vert par axe | **mesuré dans SUMO** (≈ 1 800 véh/h/voie, 2 sens × 2 voies) |
| Jaune / tout-rouge | 4 s / 1 s, soit 5 s de dégagement | valeurs usuelles |

Conséquence directe : la **part** de trafic entre les deux axes est inventée (le dataset n'a qu'un total). Le **volume total** et son évolution dans le temps viennent, eux, du dataset.

---

## 3. Module de décision

Fichier : `regulation/decision.py`. Méthode de Webster simplifiée.

### 3.1 Étapes

1. Le débit prévu (véh/5 min) est converti en demande du carrefour (véh/h).
2. La demande est répartie entre axe principal et secondaire selon l'heure.
3. Taux de charge de chaque axe : `y = demande_axe / 7 200`, et `Y = y_principal + y_secondaire`.
4. Durée du cycle : `C = (1,5·L + 5) / (1 − Y)` avec `L = 2 × 5 s = 10 s` de temps perdu, `Y` plafonné à 0,90.
5. Le cycle est borné entre **40 s et 120 s**.
6. Le vert total `C − L` est réparti proportionnellement à la demande de chaque axe.
7. Chaque vert est borné entre **10 s et 60 s** (sécurité), puis arrondi à la seconde.
8. Un dégagement fixe de 5 s suit chaque vert.

### 3.2 Exemples (heure 8)

| Débit prévu (véh/5 min) | Congestion | Vert N-S | Vert E-O | Cycle |
|---|---|---|---|---|
| 100 | faible | 20 s | 10 s | 40 s |
| 300 | faible | 20 s | 10 s | 40 s |
| 500 | moyen | 20 s | 10 s | 40 s |
| 700 | élevé | 31 s | 17 s | 58 s |

Le cycle reste au minimum de 40 s tant que le trafic n'est pas très élevé : sur la simulation, **69 % des intervalles** sont au cycle minimum, le cycle IA moyen est de 42,0 s (min 40, max 62).

### 3.3 Niveaux de congestion

Seuils repris de Joel (`model_info.json`) : faible jusqu'à 303, moyen jusqu'à 537, élevé au-delà (véhicules par 5 min). Couleurs d'alerte : vert / orange / rouge.

### 3.4 Sécurité

- Vert minimum 10 s, maximum 60 s, cycle entre 40 et 120 s : testés par `test_decision.py` sur tous les débits de 0 à 800 et toutes les heures de 0 à 23.
- Le temps de dégagement (5 s) est toujours respecté après chaque vert.
- Le calcul prend environ 2,8 µs par appel.

---

## 4. Simulation SUMO

### 4.1 Déroulement

Pour chaque pas de 5 min de la fenêtre, le script :

1. lit le débit prévu (modèle de Joel, ou persistance / oracle / CSV pour les tests) ;
2. calcule les durées de vert avec le module de décision ;
3. les applique à chaque cycle dans SUMO via TraCI ;
4. enregistre les indicateurs de la période.

Le scénario fixe et le scénario IA rejouent **exactement les mêmes véhicules** (même fichier de routes), seul le contrôle des feux change.

### 4.2 Indicateurs

| Indicateur | Définition |
|---|---|
| Temps d'attente moyen | `waitingTime + departDelay` par véhicule (s), départ retardé compris |
| Longueur de file | véhicules à l'arrêt sur les 4 branches, échantillonnés toutes les 5 s |
| Vitesse moyenne | km/h, calculée sur la durée de trajet |
| Arrêts par véhicule | `waitingCount` |
| CO2 | g par véhicule (HBEFA4, option) |

### 4.3 Précision des durées

SUMO ajoute 1 s à la durée demandée avec `setPhaseDuration`. J'applique donc `g − 1`. Vérifié : 0 s d'écart sur 540 cycles.

---

## 5. Résultats

### 5.1 Résultat principal (modèle de Joel, 19 et 23 mai 2020)

| Indicateur | Cycle fixe | IA | Variation |
|---|---|---|---|
| Temps d'attente moyen | 15,24 s | 8,35 s | **−45,2 %** |
| Longueur de file | | | −46,8 % |
| Vitesse moyenne | | | +9,5 % |
| Arrêts par véhicule | | | −2,2 % (légèrement **pire**) |
| CO2 par véhicule | | | −6,9 % |

L'objectif de −15 % sur le temps d'attente est largement atteint. Les arrêts par véhicule ne s'améliorent pas : je le signale tel quel.

### 5.2 Robustesse

| Test | Résultat (gain en temps d'attente) |
|---|---|
| Autre graine (7) | −45,5 % |
| Demande de pointe 4 500 véh/h | −50,7 % |
| Meilleur cycle fixe (vert 20 s, cycle 50 s) | −25,6 % |
| Pointe 3 000 / 4 500 / 5 400 / 6 300 véh/h (persistance) | 52,5 / 50,3 / 44,8 / 46,9 % |
| Vert fixe 20 / 25 / 30 / 40 / 50 s (persistance) | 24,7 / 27,2 / 33,4 / 44,8 / 54,1 % |
| Prédicteur oracle (parfait) contre persistance | 44,6 % contre 44,8 % |

À retenir : le gain est positif dans tous les cas, **même face au meilleur cycle fixe** (−25,6 %). Et un prédicteur parfait ne fait pas mieux que la persistance : la qualité de la prédiction pèse peu ici, c'est surtout l'adaptation du vert à la demande qui rapporte.

### 5.3 Modèle de Joel

Régression linéaire, 19 variables d'entrée, MAE test 19,99 contre 23,01 pour la persistance (−13,1 %). Rechargement vérifié : MAE recalculé 19,991, écart de 0,0000 avec ses prédictions.

---

## 6. Fichiers produits

### 6.1 `results/simulation.csv` (576 lignes, 24 colonnes)

| Colonnes | Contenu |
|---|---|
| `datetime` | début du pas de 5 min |
| `traffic_flow`, `predicted_flow` | débit réel et débit prévu (véh/5 min) |
| `demand_total_vph`, `share_main` | demande injectée (véh/h) et part de l'axe principal |
| `congestion_level` | faible / moyen / élevé |
| `fixed_*` | scénario fixe : `avg_wait_s`, `avg_queue_veh`, `avg_speed_kmh`, `stops_per_veh`, `co2_g_per_veh`, `n_vehicles`, `green_main_s`, `green_secondary_s`, `cycle_s` |
| `ai_*` | mêmes 9 colonnes pour le scénario IA |

### 6.2 `results/simulation_summary.csv`

Colonnes : `scope`, `indicator`, `label`, `unit`, `fixed`, `ai`, `gain_pct`. Une ligne par indicateur, pour le global et par période.

### 6.3 Arborescence

```
regulation/          code (config, decision, network, demand, indicators,
                     predictors, features, check_model, run_sumo, visualiser)
sumo_scenario/       réseau et définition des feux (5 fichiers xml)
results/             simulation.csv, simulation_summary.csv
test_decision.py     test du module de décision sans SUMO
README_regulation.md mode d'emploi
requirements.txt     dépendances
```

---

## 7. Installation et lancement

Toutes les commandes sont à taper dans **PowerShell** (Windows), pas dans l'invite Python `>>>`. Pour quitter Python : `exit()`.

### 7.1 Installation

1. Installer SUMO (version 1.28.0) avec l'installateur Windows officiel, puis vérifier :

```powershell
sumo --version
echo $env:SUMO_HOME
```

2. Installer les dépendances Python depuis la racine du dépôt :

```powershell
pip install -r requirements.txt
python -c "import traci, sumolib; print('traci OK')"
```

3. Vérifier que les fichiers de Joel sont en place : `models/best_model.pkl`, `models/model_info.json`, et le dossier `src/` contenant `features.py` (le `.pkl` en a besoin pour se recharger).

### 7.2 Test du module de décision (sans SUMO)

```powershell
python test_decision.py
```

Sortie attendue : `bornes OK`, puis 4 exemples (voir section 3.2).

### 7.3 Vérification du modèle de Joel

```powershell
python -m regulation.check_model --data data/processed/test.csv --model-info models/model_info.json --predictions results/predictions_test.csv
```

Sortie attendue : MAE recalculé 19,991 et écart de 0,0000 avec ses prédictions, les deux suivis de `OK`.

### 7.4 Lancer la simulation et la régulation

Run principal (modèle de Joel, 19 et 23 mai) : il produit `results/simulation.csv` et `results/simulation_summary.csv`.

```powershell
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json
```

Variantes utilisées pour les tests de robustesse :

```powershell
# autre graine
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --seed 7
# autre demande de pointe
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --peak-vph 4500
# autre cycle fixe de référence
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --fixed-green 20
# prédicteurs de comparaison
python -m regulation.run_sumo --data data/processed/test.csv --predictor persistence
python -m regulation.run_sumo --data data/processed/test.csv --predictor oracle
# tous les jours du test (long)
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --days all
```

Options utiles : `--days "2020-05-19,2020-05-23"` (défaut), `--out-dir`, `--rebuild-net` (reconstruit le réseau), `--gui` (ouvre sumo-gui pendant le calcul).

### 7.5 Voir la simulation dans sumo-gui

```powershell
python -m regulation.visualiser --day 2020-05-19 --window 07:30-09:00 --scenario both
```

Véhicules **jaunes** = cycle fixe, **bleus** = régulation IA. Autres options : `--scenario fixed` ou `ai`, `--delay 40` (vitesse d'animation), `--warmup 30`. Les indicateurs du créneau sont écrits dans `results_view/indicateurs_creneau.csv`.

### 7.6 Appel depuis le dashboard (page 6)

```python
from regulation.decision import predict_green_time
r = predict_green_time({"hour": 8, "predicted_flow": 600})
```

Retour : `predicted_flow`, `congestion_level`, `congestion_color`, `load_ratio`, `green_main_s`, `green_secondary_s`, `clearance_s`, `cycle_s`.

Deux façons de l'appeler :

- avec `predicted_flow` déjà connu (le plus simple) ;
- avec un `predictor` (ModelPredictor) : il faut alors `historique` (au moins **36 observations** passées de `traffic_flow` et `speed_kmh`), `instant`, `temp_celsius`, `wind_speed_kmh`, `precip_mm`, `weather_condition`.

---

## 8. Difficultés rencontrées et solutions

| Problème | Solution |
|---|---|
| Aucun carrefour dans le dataset | Carrefour fictif, hypothèses explicites (section 2) |
| Durées de vert décalées de +1 s dans SUMO | `setPhaseDuration(g − 1)`, vérifié sur 540 cycles |
| Débit de saturation supposé à 3 600 véh/h | Mesuré dans SUMO : ≈ 7 200 véh/h par axe ; configuration corrigée |
| `ModuleNotFoundError: src` au chargement du `.pkl` | Le modèle de Joel a besoin de `src/features.py` : dossier `src/` à la racine |
| Format de `model_info.json` changé (A/B vers format plat) | `load_model_info` gère les deux formats |
| Affichage vide dans sumo-gui | Le carrefour est en (400, 400) et non (0, 0) : caméra centrée sur sa position réelle |

---

## 9. Limites à connaître

1. **Carrefour fictif.** La part entre axes est une hypothèse (section 2). Le résultat prouve que la régulation adaptative aide dans ce scénario, pas qu'elle fera −45 % sur un vrai carrefour.
2. **Cycle fixe de référence modeste.** 40 s + 40 s est une référence simple. Face au meilleur cycle fixe testé, le gain tombe à −25,6 %. C'est ce chiffre qu'il faut citer si on veut être prudent.
3. **Période courte.** 2 jours (19 et 23 mai) sur les 18 jours de test. L'option `--days all` existe mais n'a pas été lancée.
4. **Régime COVID.** Le trafic de mai 2020 est atypique (voir limite d'Honoré sur le changement de régime).
5. **Arrêts par véhicule.** Pas d'amélioration (−2,2 %, légèrement pire).
6. **Le modèle compte peu.** Un oracle ne fait pas mieux qu'une persistance. Le gain vient du calcul des verts, pas de la finesse de la prédiction.
7. **Page 6 en temps réel.** Le modèle exige 36 observations passées ; si le dashboard n'en dispose pas, il faut passer `predicted_flow` directement.
8. **Un seul tronçon.** Aucun lien entre carrefours : pas de coordination ("onde verte").

---

## 10. Notes pour l'équipe

**Joel**
- J'utilise `best_model.pkl` tel quel, avec `src/features.py` importable et scikit-learn 1.9.1. Si tu changes le modèle ou le format de `model_info.json`, préviens-moi.
- Les seuils de congestion (303 / 537) viennent de ton fichier.

**Honoré**
- J'utilise `test.csv` uniquement (jamais train ni val) ; je prends `traffic_flow` et `datetime`.
- La référence de 800 véh/5 min est fixée à partir du maximum du dataset entier (794).

**Fouchi et Mireille (dashboard, page 6)**
- Appelez `predict_green_time(conditions)` ; la fonction ne dépend pas de SUMO.
- Le plus simple : fournir `hour` (ou `instant`) et `predicted_flow`. Le retour contient tout pour l'affichage (couleur, durées de vert, cycle).
- Pour `results/simulation.csv`, les colonnes `fixed_*` et `ai_*` se comparent directement ; `congestion_level` donne la couleur.

---

## 11. Versions

| Élément | Version |
|---|---|
| SUMO / traci / sumolib | 1.28.0 |
| scikit-learn | 1.9.1 |
| Graine | 42 |
