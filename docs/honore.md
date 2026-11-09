# Documentation Data Engineering : Honoré

> **Rôle :** Responsable Données
> **Projet :** Régulation intelligente des feux de circulation
> **Ce document couvre :** le choix du dataset, son nettoyage, les variables créées et le découpage train / val / test.
> **Lecteurs visés :** Joel (ML), Godwin (simulation), Fouchi et Mireille (dashboard)

---

## En bref

| | |
|---|---|
| **Dataset** | *US Traffic Data with Weather and Calendar* (Kaggle, Maryam Shoaei) |
| **Fichier brut** | `data/raw/traffic_weather_full2020.csv` (17 colonnes) |
| **Période** | 1er février au 31 mai 2020, une mesure toutes les 5 minutes |
| **Lignes** | 34 823 au départ, **34 820** après nettoyage |
| **Cible (y)** | `traffic_flow` : nombre de véhicules par intervalle de 5 minutes |
| **Fichiers produits** | `data/processed/` : `train.csv`, `val.csv`, `test.csv`, `dataset_A_cleaned.csv` |
| **Découpage** | chronologique 70 % / 15 % / 15 % |
| **À retenir** | Le trafic chute d'environ 40 % entre février et avril 2020 (COVID), voir section 8 |

Ce que j'ai fait en une phrase : j'ai trié les données dans le temps, retiré 8 colonnes inutiles, converti tout en unités SI, ajouté des variables de temps et de décalage, puis découpé sans jamais mélanger le passé et le futur.

---

## 1. Origine du dataset

### 1.1 Source

- **Plateforme :** Kaggle, *US Traffic Data with Weather and Calendar Dataset*, publié par Maryam Shoaei.
- **Lien :** https://www.kaggle.com/datasets/maryamshoaei/us-traffic-data-with-weather-and-calendar-dataset
- **Article de recherche associé :** *Twitter-informed Prediction for Urban Traffic Flow Using Machine Learning* (IEEE Xplore, document 10185516, https://ieeexplore.ieee.org/document/10185516). Les auteurs demandent de le citer si on utilise leur dataset, donc il sera cité dans le rapport.

### 1.2 Ce que contient le dataset

Le dataset fusionne trois sources sur la même période.

| Type de données | Origine | Détail |
|---|---|---|
| **Trafic** | PeMS (Caltrans, Californie) | Débit et vitesse sur les voies en direction de l'est de la Ventura Highway, à Los Angeles. Une mesure toutes les 5 minutes. |
| **Météo** | Wunderground, station KLAX (Los Angeles) | Relevés **horaires**. Les auteurs ont supposé que la météo reste constante pendant chaque heure, donc la même valeur est répétée sur les 12 intervalles de 5 minutes. Température d'origine en Fahrenheit. |
| **Calendrier** | Construit par les auteurs | Jour de la semaine et indicateur de jour non travaillé (voir section 7). |

### 1.3 Un traitement déjà fait par les auteurs

Quand un capteur PeMS était en panne ou bruité, la valeur manquante a été remplacée par la **moyenne** (*mean imputation*) avant la publication du dataset. Je n'ai pas refait ce traitement et je ne peux pas le défaire (voir la section 8).

---

## 2. Nettoyage et transformations

J'ai appliqué les étapes dans cet ordre.

| # | Étape | Ce que j'ai fait |
|---|---|---|
| 1 | **Temps** | Conversion de la colonne `5 Minutes` en vrai `datetime`, puis tri chronologique strict. |
| 2 | **Valeurs manquantes** | `Condition` avait 24 valeurs manquantes, remplies par propagation de la dernière valeur connue (`ffill`). `Wind` en avait 168, mais cette colonne n'est pas conservée. |
| 3 | **Sélection des colonnes** | Réduction de 17 à 9 colonnes (section 3). |
| 4 | **Nettoyage des types** | Extraction de la partie numérique des colonnes météo (par exemple `55 F` devient `55`) avec une expression régulière et `pd.to_numeric`. |
| 5 | **Unités SI et noms** | Conversions et renommages (section 4). |
| 6 | **Nouvelles variables** | Heure, minute, week-end, décalages (section 5). |
| 7 | **Bornes** | Suppression des 3 premières lignes (valeurs vides créées par les décalages). |
| 8 | **Découpage et export** | Train / val / test chronologiques (section 6). |

Après nettoyage, il ne reste **aucune valeur manquante** et aucun horodatage en double.

---

## 3. Colonnes gardées et colonnes retirées

Le fichier brut a 17 colonnes. J'en garde 9 et j'en retire 8.

### Gardées (9)

| Colonne d'origine | Rôle |
|---|---|
| `5 Minutes` (devenue `datetime`) | Horodatage, base du découpage chronologique |
| `Flow` | **Cible** : débit de véhicules |
| `(mph)` | Vitesse moyenne du trafic |
| `week_day` | Jour de la semaine |
| `holidays` | Jour non travaillé (voir section 7) |
| `Temperature` | Température |
| `Wind Speed` | Vitesse du vent |
| `Precip.` | Précipitations |
| `Condition` | État du ciel (texte) |

### Retirées (8)

| Colonne | Pourquoi je l'ai retirée |
|---|---|
| `Hour`, `Day`, `Time` | Redondantes avec `datetime`. |
| `Wind` | Direction du vent en texte (`NNE`, `CALM`, `VAR`...), peu exploitable telle quelle. |
| `Pressure` | Peu liée au comportement des conducteurs. |
| `Humidity` | Surtout utile pour le brouillard, déjà visible dans `Condition`. |
| `Dew Point` | Redondante avec la température et l'humidité. |
| `Wind Gust` | Redondante avec `Wind Speed`. |

Ce sont des choix d'ingénierie, pas des règles absolues. Si Joel veut tester l'une de ces colonnes, elle est toujours dans le fichier brut.

---

## 4. Conversion en unités SI

| Nouvelle colonne | Calcul | Unité | Plage observée |
|---|---|---|---|
| `speed_kmh` | `(mph)` × 1,60934 | km/h | 38,79 à 114,42 |
| `wind_speed_kmh` | `Wind Speed` × 1,60934 | km/h | 0 à 57,94 |
| `temp_celsius` | (°F − 32) × 5/9 | °C | 1,67 à 36,67 |
| `precip_mm` | `Precip.` (pouces) × 25,4 | mm | 0 à 17,78 |

Tout est arrondi à 2 décimales. J'ai aussi renommé `Flow` en `traffic_flow` et `Condition` en `weather_condition`.

La météo étant répétée sur 12 lignes par heure, **il ne faut pas sommer `precip_mm` d'une ligne à l'autre** : chaque ligne répète la valeur de l'heure.

---

## 5. Variables créées

| Variable | Définition | Pourquoi |
|---|---|---|
| `hour` | Heure de la journée (0 à 23) | Le trafic suit un rythme journalier |
| `minute` | Minute du relevé (0, 5, 10... 55) | Position dans l'heure |
| `is_weekend` | 1 si samedi ou dimanche, sinon 0 | Le week-end ne ressemble pas à un jour de semaine |
| `traffic_flow_lag_1` | Débit 5 min plus tôt (t − 5 min) | Valeur immédiatement précédente |
| `traffic_flow_lag_3` | Débit 15 min plus tôt (t − 15 min) | Tendance récente |

**Sur les décalages et les fuites de données :** un décalage ne regarde que le passé, donc il ne fait fuiter aucune information du futur. Au début de `val.csv` et de `test.csv`, les décalages utilisent les dernières lignes de l'ensemble précédent, ce qui est normal : en situation réelle, on connaît aussi le passé récent. J'ai vérifié que les deux colonnes de décalage correspondent exactement au débit décalé de 1 et de 3 lignes.

**Une nuance :** les décalages sont calculés par **ligne**, pas par durée. Le dataset a 3 petits trous dans le temps (voir section 8), donc juste après chacun d'eux, un décalage « 5 min » regarde en réalité plus loin dans le passé. L'effet est négligeable (au plus 3 lignes après chaque trou).

---

## 6. Découpage chronologique et fichiers produits

Je n'ai **pas** mélangé les lignes au hasard. Mélanger ferait entrer dans l'entraînement des mesures proches du test, et les scores seraient trop beaux pour être vrais. J'ai coupé le temps en trois blocs qui se suivent, sans chevauchement.

| Fichier | Part | Lignes | Début | Fin | Débit moyen | Usage |
|---|---|---|---|---|---|---|
| `train.csv` | 70 % | 24 374 | 1er févr., 00:15 | 25 avr., 17:25 | 416,0 | Entraînement des modèles |
| `val.csv` | 15 % | 5 223 | 25 avr., 17:30 | 13 mai, 20:40 | 377,6 | Réglage des hyperparamètres |
| `test.csv` | 15 % | 5 223 | 13 mai, 20:45 | 31 mai, 23:55 | 406,3 | Évaluation finale, utilisé une seule fois |
| `dataset_A_cleaned.csv` | 100 % | 34 820 | 1er févr., 00:15 | 31 mai, 23:55 | 408,7 | Dataset complet nettoyé (14 colonnes) |

Vérification : 24 374 + 5 223 + 5 223 = 34 820, et la concaténation de `train`, `val` et `test` redonne exactement `dataset_A_cleaned.csv`.

Les coupures tombent en milieu de journée (17:30 et 20:45). C'est la conséquence d'un découpage par pourcentage de lignes, ce n'est pas gênant.

```
data/processed/
├── dataset_A_cleaned.csv   # 34 820 lignes, 14 colonnes
├── train.csv               # 24 374 lignes
├── val.csv                 #  5 223 lignes
└── test.csv                #  5 223 lignes
```

---

## 7. Dictionnaire des variables finales (14 colonnes)

| # | Colonne | Type | Unité | Description |
|---|---|---|---|---|
| 1 | `datetime` | date et heure | n/a | Instant de la mesure, pas de 5 min |
| 2 | `traffic_flow` | entier | véhicules / 5 min | **Cible**, de 87 à 794 |
| 3 | `speed_kmh` | décimal | km/h | Vitesse moyenne du trafic |
| 4 | `week_day` | entier | n/a | **1 = lundi, 2 = mardi... 7 = dimanche** (le 1er février 2020 était un samedi et vaut 6) |
| 5 | `holidays` | binaire | n/a | **1 = jour non travaillé** : tous les samedis et dimanches, plus 2 vrais jours fériés (17 février, Presidents' Day, et 25 mai, Memorial Day) |
| 6 | `temp_celsius` | décimal | °C | Température |
| 7 | `wind_speed_kmh` | décimal | km/h | Vitesse du vent |
| 8 | `precip_mm` | décimal | mm | Précipitations (valeur de l'heure, répétée) |
| 9 | `weather_condition` | texte | n/a | État du ciel, laissé brut volontairement (15 valeurs, ci-dessous) |
| 10 | `hour` | entier | h | 0 à 23 |
| 11 | `minute` | entier | min | 0, 5, 10... 55 |
| 12 | `is_weekend` | binaire | n/a | 1 si samedi ou dimanche |
| 13 | `traffic_flow_lag_1` | décimal | véhicules / 5 min | Débit à t − 5 min |
| 14 | `traffic_flow_lag_3` | décimal | véhicules / 5 min | Débit à t − 15 min |

**Attention à `holidays` :** malgré son nom, cette colonne n'est pas un simple indicateur de jour férié. Elle vaut 1 tous les week-ends, donc elle est presque identique à `is_weekend`. Le vrai signal « jour férié » ne concerne que 2 jours dans tout le dataset.

### Valeurs de `weather_condition`

| Valeur | Lignes | | Valeur | Lignes |
|---|---|---|---|---|
| Fair | 22 736 | | Fair / Windy | 72 |
| Cloudy | 5 268 | | Fog | 72 |
| Mostly Cloudy | 2 172 | | Mostly Cloudy / Windy | 60 |
| Partly Cloudy | 2 052 | | Blowing Dust | 60 |
| Light Rain | 1 476 | | Partly Cloudy / Windy | 36 |
| Rain | 456 | | Cloudy / Windy | 36 |
| Haze | 192 | | Thunder in the Vicinity | 12 |
| Heavy Rain | 120 | | | |

Plusieurs catégories sont très rares (12 lignes pour `Thunder in the Vicinity`, soit une seule heure). Elles peuvent n'apparaître que dans un seul des trois ensembles.

---

## 8. Limites à connaître

Je les écris ici pour que personne ne les découvre trop tard.

1. **Une seule série de trafic.** Le dataset décrit un seul tronçon d'autoroute, pas des voies séparées d'un carrefour. Le débit va jusqu'à 794 véhicules par 5 minutes, soit environ 9 500 véhicules par heure : c'est bien plus que ce qu'une seule voie peut écouler (de l'ordre de 2 000 véhicules par heure). C'est donc un débit **cumulé sur plusieurs voies**. Le filtre « voie » du dashboard et la répartition du vert entre plusieurs voies demandent une hypothèse de simulation (à définir avec Godwin).
2. **Changement de régime lié à la COVID-19.** Le débit hebdomadaire moyen est d'environ 500 véhicules / 5 min de février à début mars, tombe à environ 300 fin mars et en avril, puis remonte à environ 410 fin mai. Les moyennes mensuelles sont 500,6 (février), 408,0 (mars), 333,0 (avril) et 396,9 (mai). Conséquences : `train.csv` contient les deux régimes, `val.csv` tombe dans la période creuse puis la reprise, et `test.csv` est une période de reprise partielle. Les scores sur le test ne diront donc pas comment le modèle se comporterait en année normale, et le rapport doit le préciser.
3. **Imputation faite par les auteurs.** Les trous de capteurs ont été comblés par la moyenne. Si cette moyenne est calculée sur toute la période, elle contient un peu d'information du futur. Je ne peux pas le corriger, seulement le signaler.
4. **Météo en escalier.** La météo est horaire, répétée sur 12 intervalles. Elle ne change jamais au milieu d'une heure.
5. **Trois trous dans le temps.** Il manque 25 lignes par rapport aux 34 848 attendues : 12 lignes le 8 mars à 03:00 (passage à l'heure d'été), 12 lignes le 21 mars à 01:00, et 1 ligne le 2 avril à 10:00. Je n'ai rien comblé.

---

## 9. Notes pour l'équipe

### Pour Joel (ML)

- `train.csv` et `val.csv` sont prêts pour l'entraînement et le réglage.
- J'ai gardé `weather_condition` en texte. **Le choix de l'encodage (One-Hot, Target Encoding, etc.) t'appartient**, à intégrer dans ta pipeline pour éviter toute fuite de données. Pense aux catégories très rares (section 7).
- `holidays` et `is_weekend` sont presque redondantes (section 7).
- Les 8 colonnes que j'ai retirées (section 3) sont dans le fichier brut si tu veux les tester.
- Pour comparer les modèles honnêtement, garde en tête le changement de régime de la section 8.

### Pour Godwin (régulation et simulation)

- `test.csv` (13 mai au 31 mai) est la référence pour évaluer le modèle final et alimenter la simulation.
- Lis la limite 1 de la section 8 : il faudra définir ensemble comment passer d'un débit unique à plusieurs voies.

### Pour Fouchi et Mireille (dashboard)

- Variables proposées pour le formulaire de la page 6 : `temp_celsius`, `wind_speed_kmh`, `precip_mm`, `weather_condition`, `holidays`, `is_weekend`, `hour`, `minute`.
- Les deux décalages (`traffic_flow_lag_1` et `_3`) ne se saisissent pas à la main. Il faudra les remplir depuis l'historique ou les fixer à une valeur par défaut.
- Pour la page d'exploration, la courbe du débit hebdomadaire montre très clairement la chute de mars-avril (section 8, limite 2). Elle mérite un graphique.
