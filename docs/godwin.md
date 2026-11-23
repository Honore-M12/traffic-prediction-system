# Documentation Régulation et simulation : Godwin

> **Rôle :** Responsable Régulation et simulation
> **Projet :** Régulation intelligente des feux de circulation
> **Ce document couvre :** le scénario simulé et les raisons de ses choix (dont le niveau de charge du tronçon), le module de décision (trafic prévu → durées de vert), la simulation SUMO (feux à cycle fixe contre feux pilotés par l'IA), les résultats sur les 18 jours de test, et la fonction `predict_green_time()` pour le dashboard.
> **Lecteurs visés :** Joel (ML), Honoré (données), Fouchi et Mireille (dashboard)

---

## En bref

| | |
|---|---|
| **Simulateur** | SUMO 1.28.0, feux pilotés par TraCI |
| **Scénario** | un axe principal à sens unique (2 voies, 50 km/h) avec **un carrefour à feux** ; une rue latérale à double sens le croise ; tout le monde va tout droit |
| **Feux** | 2 phases : axe principal, rue latérale ; jaune 4 s + tout-rouge 1 s après chaque vert |
| **Scénario 1 (avant)** | cycle fixe de 90 s : 56 s pour l'axe, 24 s pour la rue latérale |
| **Scénario 2 (après)** | vert recalculé toutes les 5 minutes à partir du débit prévu par le modèle de Joel, avec bornes de sécurité |
| **Trafic** | débit du dataset mis à l'échelle (800 véh/5 min = 2 100 véh/h sur l'axe), arrivées de Poisson, graine 42, **mêmes véhicules pour les deux scénarios** |
| **Période simulée** | les 18 jours complets du jeu de test, du 14 au 31 mai 2020 (5 184 pas de 5 min, 618 551 véhicules par scénario) |
| **Résultat principal** | temps d'attente moyen **12,25 s → 8,06 s (−34,3 %)**, objectif de −15 % atteint les 18 jours (de −28,3 % à −38,2 %) |
| **Réserves** | le nombre d'arrêts par véhicule **augmente de 14 %** ; face à un cycle fixe réglé au mieux, le gain est d'environ 12 % (section 6.3) |
| **Fichiers produits** | `results/simulation.csv`, `results/simulation_summary.csv` |
| **Point d'entrée dashboard** | `regulation.decision.predict_green_time(conditions, predictor=None)` |

En une phrase : le trafic réel du dataset est rejoué sur un carrefour fictif, une fois avec des feux à cycle fixe et une fois avec des feux dont le vert est décidé d'après la prédiction de Joel, et les deux sont comparés avec exactement les mêmes véhicules.

---

## 1. Périmètre

### 1.1 Ce qui m'était demandé

- Un module de décision : à partir du trafic prévu, proposer des durées de vert, avec un vert minimum et maximum de sécurité et un temps de dégagement.
- Une simulation SUMO comparant cycle fixe et régulation IA.
- Des indicateurs : temps d'attente moyen, longueur de file, vitesse moyenne, nombre d'arrêts, CO2 en option. Objectif : réduire le temps d'attente d'au moins 15 %.
- `simulation.csv` et la fonction `predict_green_time()` utilisée par la page 6 du dashboard.
- Cette documentation et le dépôt GitHub.

### 1.2 Ce que je n'ai pas fait

- Je n'ai pas entraîné de modèle : j'utilise celui de Joel tel quel (`best_model.pkl`).
- Je n'ai pas construit la page 6 du dashboard : je fournis la fonction qu'elle appelle.
- Je ne simule pas un vrai réseau routier : le dataset ne contient qu'une série de trafic (limite 1).

---

## 2. Le scénario simulé et pourquoi

### 2.1 Schéma

```
                   rue latérale (nord)
                          |
   entrée ------------> [feu] ------------> sortie      axe principal, sens unique, 2 voies
   (400 m)                |                (400 m)
                   rue latérale (sud)
```

Une voie par sens sur la rue latérale (200 m de chaque côté). Le feu a deux phases : l'axe principal passe, puis la rue latérale passe.

### 2.2 Ce que le dataset permet et ne permet pas

Le dataset décrit **un seul tronçon d'autoroute, une seule série de trafic** (débit toutes les 5 minutes, un seul sens). Il ne contient ni carrefour, ni feu, ni rue latérale. Il fallait donc transposer ce trafic sur un carrefour fictif, et dire clairement ce qui vient des données et ce qui est supposé.

| Élément | Origine |
|---|---|
| Volume de trafic de l'axe principal et son évolution dans la journée | **Dataset réel** (débit observé du test) |
| Prévision du débit utilisée par le feu intelligent | **Modèle de Joel** |
| Rue latérale (environ le tiers de la demande de l'axe) | **Hypothèse simulée**, nécessaire pour que les deux phases du feu aient un sens |
| Géométrie (400 m, 2 voies, 50 km/h), échelle de 800 véh/5 min à 2 100 véh/h | **Hypothèses** |

### 2.3 Pourquoi un seul carrefour sur un axe à sens unique

- **Une seule série dans le dataset = un seul flux.** Un axe à sens unique le représente directement. Un carrefour à 4 branches obligeait à inventer un deuxième axe entier, avec ses deux sens.
- **Un feu, c'est exactement la chaîne du projet** : trafic prévu → durées de vert → comparaison avec un cycle fixe. C'est aussi ce que fait `predict_green_time()` pour la page 6.
- **Peu de paramètres inventés.** Avec un seul carrefour, il n'y a ni coordination entre feux, ni décalage à régler.

### 2.4 Les versions testées avant

| Version | Résultat | Pourquoi je ne l'ai pas gardée |
|---|---|---|
| Carrefour à 4 branches (2 axes) | −45 % d'attente | un deuxième flux entier à inventer ; le cycle fixe de référence (40 s / 40 s) était mal adapté, ce qui gonflait le gain |
| Axe à 3 feux coordonnés (onde verte) | −34 % contre le cycle de 90 s, mais environ −5 % contre le meilleur cycle fixe | trois feux, un décalage de 35 s et un facteur de progression à régler sur la simulation : trop d'hypothèses pour peu de valeur ajoutée |

---

## 3. Pourquoi ce niveau de charge du tronçon

C'est le paramètre le plus important de la simulation : combien de véhicules par heure l'axe reçoit quand le dataset est à son maximum. Il est fixé dans `config.py` : **`FLOW_REF` = 800 véh/5 min correspond à `PEAK_MAIN_VPH` = 2 100 véh/h.**

### 3.1 Capacité de l'axe

- Débit de saturation mesuré dans SUMO : environ 1 800 véh/h par voie, donc **3 600 véh/h** pour les 2 voies de l'axe pendant le vert.
- Avec le cycle fixe de référence (56 s de vert sur 90 s), la capacité réelle de l'axe est de 3 600 × 56 / 90 = **2 240 véh/h**.

### 3.2 Le choix de 2 100 véh/h

| Charge au pic du dataset | Part de la capacité du cycle fixe | Ce que ça donne |
|---|---|---|
| 1 500 véh/h | 67 % | trafic léger : peu à réguler, gain gonflé (43,8 %) |
| **2 100 véh/h (retenu)** | **94 %** | l'axe est chargé mais pas saturé : c'est là que les durées de vert comptent |
| 2 700 véh/h | 121 % | axe saturé : les files grossissent sans fin, résultats dominés par l'engorgement ; l'IA devient moins bonne que le cycle fixe (−24,8 %) |

Les raisons du choix :

1. **Le pic du dataset doit mettre l'axe sous tension sans le saturer.** À 2 100 véh/h, le maximum du dataset (800 véh/5 min, valeur fixe tirée de tout le dataset) charge le cycle fixe à 94 % de sa capacité. Sur le jeu de test, le pic réel est de 759 véh/5 min, soit 89 %.
2. **Les valeurs courantes restent réalistes.** Le débit moyen du test (407 véh/5 min) donne 1 069 véh/h, soit environ 48 % de la capacité du cycle fixe : un axe urbain chargé, pas bloqué.
3. **Au-delà de la capacité, la comparaison n'a plus de sens.** Un contrôleur qui ne voit pas les files (il n'a que le débit prévu) ne peut pas gérer un axe saturé. Je ne l'ai donc pas retenu comme cas de référence, mais je le **rapporte comme limite** (section 9).
4. **La forme du trafic est conservée.** Seule l'échelle change : les creux de la nuit, la montée du matin et le plateau de l'après-midi restent ceux du dataset. `FLOW_REF` est fixé sur tout le dataset (max 794), jamais sur le seul jeu de test.

### 3.3 La longueur du tronçon (400 m)

Les tronçons d'entrée et de sortie font 400 m, et chaque branche de la rue latérale 200 m. C'est assez long pour contenir les files sans qu'elles remontent jusqu'au bord du réseau : la file moyenne sur toute la période est de 4,7 véhicules pour le cycle fixe et 3,1 pour l'IA.

---

## 4. Module de décision

Fichier : `regulation/decision.py`.

### 4.1 Méthode

1. Le débit prévu (véh/5 min) est converti en demande de l'axe principal (véh/h).
2. On en déduit la demande de la rue latérale selon l'heure, multipliée par une marge de prudence `SIDE_SAFETY` = 1,3 (le contrôleur ne mesure pas cette rue).
3. On teste tous les cycles de 40 à 120 s (par pas de 5 s) et tous les partages du vert, et on garde celui qui **minimise le retard total estimé** : le débit multiplié par le retard moyen (retard uniforme du Highway Capacity Manual + retard de saturation), sur l'axe et sur la rue latérale.
4. Les verts restent toujours entre **10 s et 60 s**, le cycle entre **40 s et 120 s**.
5. Un dégagement de 5 s (jaune 4 s + tout-rouge 1 s) suit chaque vert.

### 4.2 Exemples (heure 8)

| Débit prévu (véh/5 min) | Congestion | Vert axe | Vert rue latérale | Cycle |
|---|---|---|---|---|
| 100 | faible | 20 s | 10 s | 40 s |
| 300 | faible | 20 s | 10 s | 40 s |
| 500 | moyen | 25 s | 10 s | 45 s |
| 700 | élevé | 34 s | 11 s | 55 s |

Le cycle reste court quand le trafic est modéré : sur les 18 jours, le cycle IA moyen est de 43,9 s (contre 90 s en fixe), 50 % des pas sont au cycle minimum de 40 s, et le plus long est de 70 s.

### 4.3 Niveaux de congestion

Seuils de Joel (`model_info.json`) : **faible** jusqu'à 303, **moyen** jusqu'à 537, **élevé** au-delà (véh/5 min), avec les couleurs vert / orange / rouge. Sur les 18 jours : 33,8 % de pas faibles, 35,2 % moyens, 31,0 % élevés.

### 4.4 Sécurité

- `test_decision.py` vérifie sur tous les débits de 0 à 800 et toutes les heures de 0 à 23 que les verts restent entre 10 et 60 s et le cycle entre 40 et 120 s.
- Le dégagement de 5 s est toujours respecté.
- Un appel prend environ 0,6 ms.

### 4.5 Une marge calibrée

La marge `SIDE_SAFETY` a été choisie sur la seule journée du 19 mai, avec la persistance comme prédicteur :

| Marge | 1,0 | **1,3 (retenue)** | 1,6 | 2,0 |
|---|---|---|---|---|
| Attente moyenne | 9,6 s | **8,4 s** | 9,2 s | 13,1 s |

Les autres journées valident ce réglage : elles donnent toutes entre 28 % et 38 % de gain.

---

## 5. Simulation SUMO

### 5.1 De la prévision aux véhicules : trois notions séparées

| Notion | Rôle dans la simulation |
|---|---|
| Débit **observé** (dataset) | fixe les arrivées réelles de véhicules (processus de Poisson) |
| Débit **prévu** (modèle de Joel) | ne sert qu'au feu intelligent pour décider ses durées de vert |
| Véhicules **présents** sur la route | mesurés par SUMO : ce sont eux qui font les files et l'attente |

Le feu ne voit donc jamais les véhicules réels : il décide d'après la prévision, comme le ferait le système en situation réelle.

### 5.2 Déroulement

Pour chaque jour, à chaque début de cycle, le script demande les durées de vert au module de décision et les applique dans SUMO via TraCI. Chaque phase est planifiée à la seconde près. Le cycle fixe passe par le même code, avec des durées constantes (56 s + 24 s). Le scénario fixe et le scénario IA rejouent **le même fichier de véhicules** : seule la gestion des feux change.

### 5.3 Indicateurs

| Indicateur | Définition |
|---|---|
| Temps d'attente moyen | `waitingTime` (arrêté) + délai éventuel avant d'entrer sur le réseau, en s par véhicule |
| Longueur moyenne des files | véhicules à l'arrêt sur les 3 approches du carrefour (axe, rue latérale nord et sud), relevés toutes les 5 s |
| Vitesse moyenne | distance totale / temps de trajet total, en km/h |
| Arrêts par véhicule | `waitingCount` |
| CO2 | g par véhicule (HBEFA4, option) |

---

## 6. Résultats (modèle de Joel, 18 jours, graine 42)

### 6.1 Résultat global

| Indicateur | Cycle fixe | Régulation IA | Variation |
|---|---|---|---|
| Temps d'attente moyen (s/véh) | 12,253 | 8,055 | **−34,3 %** |
| Longueur moyenne des files (véh à l'arrêt) | 4,710 | 3,127 | −33,6 % |
| Vitesse moyenne (km/h) | 33,826 | 35,612 | +5,3 % |
| Arrêts par véhicule | 0,548 | 0,625 | **+14,0 % (pire)** |
| CO2 (g/véh) | 149,385 | 145,102 | −2,9 % |

L'objectif de −15 % sur le temps d'attente est **atteint tous les jours** : −28,3 % le 30 mai (le plus faible), −38,2 % le 17 mai (le plus fort). Le gain est de 34,2 % en semaine et 34,8 % le week-end en moyenne.

### 6.2 Selon l'heure de la journée

| Heure | Débit (véh/5 min) | Attente fixe | Attente IA | Cycle IA | Gain |
|---|---|---|---|---|---|
| 03 h | 147 | 10,0 s | 5,3 s | 40 s | 47 % |
| 08 h | 450 | 10,6 s | 6,3 s | 44,7 s | 41 % |
| 12 h | 574 | 11,9 s | 7,8 s | 45,9 s | 34 % |
| 16 h | 617 | 14,2 s | 10,6 s | 52,9 s | 25 % |
| 20 h | 417 | 12,5 s | 7,1 s | 40,4 s | 43 % |

Le gain est le plus faible aux heures de pointe (15 h à 17 h : 22 à 25 %), quand le trafic est le plus dense. Il reste positif à toutes les heures. Sur l'ensemble des pas de 5 minutes, l'IA est moins bonne que le cycle fixe dans 2,8 % des cas seulement.

### 6.3 Comparaison avec d'autres cycles fixes

Le cycle fixe de 90 s est un plan classique, pas un plan optimisé. Pour juger l'IA honnêtement, voici l'attente moyenne du 19 mai selon le réglage du cycle fixe (mesurée à part, avec la persistance comme prédicteur ; le cycle fixe ne dépend pas du prédicteur) :

| Cycle fixe | 40 s | 45 s | 50 s | **55 s** | 60 s | 70 s | 80 s | 90 s | 110 s |
|---|---|---|---|---|---|---|---|---|---|
| Vert axe / rue latérale | 22 / 8 | 25 / 10 | 28 / 12 | **31 / 14** | 34 / 16 | 40 / 20 | 45 / 25 | 56 / 24 | 66 / 34 |
| Attente moyenne (s) | 44,1 | 12,7 | 9,8 | **9,2** | 9,5 | 10,4 | 12,1 | 12,5 | 15,3 |

Le meilleur cycle fixe est de 55 s (attente 9,2 s). L'IA donne 8,1 s dans le run complet, soit environ **−12 %** par rapport à ce meilleur cycle (valeur approximative : le tirage de véhicules diffère un peu entre les deux runs, de l'ordre de 1 %). Le gain de 34 % est mesuré contre le cycle classique de 90 s ; **les deux chiffres doivent être cités**.

### 6.4 Robustesse (19 mai, persistance comme prédicteur)

| Variante | Gain sur l'attente |
|---|---|
| Référence (graine 42, 2 100 véh/h au pic) | 32,6 % |
| Autre graine (7) | 32,0 % |
| Trafic plus léger (1 500 véh/h au pic) | 43,8 % |
| **Trafic plus lourd (2 700 véh/h au pic, axe saturé)** | **−24,8 % (attente 23,2 s contre 18,6 s en fixe)** |

### 6.5 Le modèle de Joel

Régression linéaire, 19 variables, MAE test 19,99 contre 23,01 pour la persistance (−13,1 %). Rechargement vérifié : MAE recalculé 19,991, écart de 0,0000 avec ses prédictions. Sur les 18 jours simulés, l'écart moyen entre débit prévu et débit réel est de 20,06 véh/5 min.

---

## 7. Vérifications effectuées

- Durées de vert, de jaune et de tout-rouge **exactement** celles planifiées (relevé seconde par seconde de l'état du feu), y compris au changement de plan toutes les 5 minutes.
- Bornes respectées : verts IA de 19 à 40 s (axe) et de 10 à 21 s (rue latérale), cycles de 40 à 70 s.
- `simulation.csv` : 5 184 lignes, du 14 mai 00:00 au 31 mai 23:55, un pas de 5 minutes sans trou, aucune valeur vide, cycle fixe toujours à 90 s.
- Même nombre de véhicules pour le cycle fixe et l'IA : 618 551.
- Résultats reproductibles (même graine, mêmes chiffres).

---

## 8. Fichiers produits

### 8.1 `results/simulation.csv` (5 184 lignes, 24 colonnes)

| Colonnes | Contenu |
|---|---|
| `datetime` | début du pas de 5 min |
| `traffic_flow`, `predicted_flow` | débit réel et débit prévu (véh/5 min) |
| `demand_total_vph`, `share_main` | demande totale injectée (axe + rue latérale, véh/h) et part de l'axe dans cette demande |
| `congestion_level` | faible / moyen / élevé |
| `fixed_*` | scénario fixe : `avg_wait_s`, `avg_queue_veh`, `avg_speed_kmh`, `stops_per_veh`, `co2_g_per_veh`, `n_vehicles`, `green_main_s` (axe), `green_secondary_s` (rue latérale), `cycle_s` |
| `ai_*` | mêmes 9 colonnes pour le scénario IA |

### 8.2 `results/simulation_summary.csv`

Colonnes : `scope`, `indicator`, `label`, `unit`, `fixed`, `ai`, `gain_pct`. 5 indicateurs pour le global puis pour chacun des 18 jours (95 lignes).

### 8.3 Arborescence

```
regulation/          code (config, decision, network, demand, indicators,
                     predictors, features, check_model, run_sumo, visualiser)
sumo_scenario/       réseau SUMO (5 fichiers xml)
results/             simulation.csv, simulation_summary.csv
test_decision.py     test du module de décision sans SUMO
README_regulation.md mode d'emploi
requirements.txt     dépendances
```

---

## 9. Installation et lancement

Toutes les commandes sont à taper dans **PowerShell** (Windows), pas dans l'invite Python `>>>` (pour en sortir : `exit()`), depuis la racine du dépôt.

### 9.1 Installation

```powershell
sumo --version
echo $env:SUMO_HOME
pip install -r requirements.txt
python -c "import traci, sumolib; print('traci OK')"
```

Il faut aussi les fichiers de Joel : `models/best_model.pkl`, `models/model_info.json` et le dossier `src/` avec `features.py` (le `.pkl` en a besoin pour se recharger).

### 9.2 Tests

```powershell
python test_decision.py
python -m regulation.check_model --data data/processed/test.csv --model-info models/model_info.json --predictions results/predictions_test.csv
```

Attendu : `bornes OK`, puis un MAE de 19,991 avec un écart de 0,0000.

### 9.3 Simulation complète (environ 30 à 40 minutes)

```powershell
python -m regulation.run_sumo --data data/processed/test.csv --predictor model --model-info models/model_info.json --days all --rebuild-net
```

Variantes : `--days 2020-05-19` (un jour), `--seed 7`, `--peak-vph 1500` (charge au pic), `--fixed-green 31 --fixed-side-green 14` (autre cycle fixe), `--predictor persistence` (sans modèle), `--out-dir dossier` (autre dossier de sortie).

### 9.4 Voir la simulation dans sumo-gui

```powershell
python -m regulation.visualiser --data data/processed/test.csv --day 2020-05-19 --window 07:30-09:00 --scenario both --predictor model --model-info models/model_info.json --screenshots 5
```

Le cycle fixe (véhicules **jaunes**) passe d'abord, puis la régulation IA (véhicules **bleus**), sur le même trafic. Chaque début de cycle s'affiche dans PowerShell, et les indicateurs du créneau sont écrits dans `results_view/indicateurs_creneau.csv`. Pour une démonstration, choisir un créneau du matin ou de la nuit : à 07:30-08:00 le gain est de l'ordre de 47 %, alors qu'il est plus faible en fin d'après-midi.

---

## 10. Utilisation dans le dashboard (page 6)

```python
from regulation.decision import predict_green_time
r = predict_green_time({"hour": 17, "minute": 30, "predicted_flow": 600})
# {'predicted_flow': 600.0, 'congestion_level': 'élevé', 'congestion_color': 'rouge',
#  'load_ratio': 0.616, 'green_main_s': 26, 'green_secondary_s': 14,
#  'clearance_s': 5, 'cycle_s': 50, 'offsets_s': [0]}
```

| Clé | Signification |
|---|---|
| `predicted_flow` | débit prévu (véh/5 min) |
| `congestion_level`, `congestion_color` | niveau et couleur d'alerte |
| `load_ratio` | taux de charge du carrefour |
| `green_main_s`, `green_secondary_s` | vert de l'axe principal et de la rue latérale (s) |
| `clearance_s` | dégagement après chaque vert (5 s) |
| `cycle_s` | durée totale du cycle |

Deux façons de l'appeler :

- avec `predicted_flow` déjà connu (le plus simple) ;
- avec un `predictor` (`ModelPredictor`) : il faut alors `historique` (au moins **36 observations** passées de `traffic_flow` et `speed_kmh`), `instant`, `temp_celsius`, `wind_speed_kmh`, `precip_mm` et `weather_condition`.

D'après la note de Joel, l'historique du débit pèse environ 99 % dans la prédiction : la météo saisie dans la page 6 n'a presque pas d'effet sur le résultat.

---

## 11. Difficultés rencontrées et solutions

| Problème | Solution |
|---|---|
| Aucun carrefour dans le dataset | Carrefour fictif sur un axe, hypothèses explicites (section 2) |
| Durées de vert décalées de +1 s dans SUMO | Phases planifiées à la seconde près, vérifiées par relevé de l'état du feu |
| Débit de saturation supposé à 3 600 véh/h par axe à 4 voies | Mesuré dans SUMO : environ 1 800 véh/h par voie ; échelle de la demande recalculée |
| Cycle fixe de référence mal adapté dans la première version (gain de 45 % surestimé) | Plan classique de 90 s au partage adapté, et comparaison avec le meilleur cycle fixe |
| Gain trop faible à l'heure de pointe, la rue latérale étant sous-servie | Marge de prudence de 1,3 sur sa demande (section 4.5) |
| `ModuleNotFoundError: src` au chargement du `.pkl` | Le modèle de Joel a besoin de `src/features.py` : dossier `src/` à la racine |
| Format de `model_info.json` modifié (A/B vers format plat) | `load_model_info` gère les deux formats |
| « Could not connect to TraCI server » | SUMO ne démarrait pas : réseau absent ou ancien ; relancer avec `--rebuild-net` |

---

## 12. Limites à connaître

1. **Carrefour fictif.** La rue latérale et la géométrie sont des hypothèses. Le résultat montre que la régulation adaptative aide dans ce scénario, pas qu'elle fera −34 % sur un vrai carrefour.
2. **Cycle fixe de référence modeste.** Contre le meilleur cycle fixe (55 s), le gain n'est que d'environ 12 %, sous l'objectif de 15 %. Le chiffre de −34 % est contre un cycle classique de 90 s.
3. **Axe saturé.** À 2 700 véh/h au pic, l'IA est moins bonne que le cycle fixe : le contrôleur n'a pas de détecteur pour voir les files. Le niveau de charge retenu (2 100 véh/h, section 3) évite cette zone.
4. **Nombre d'arrêts.** Il augmente de 14 % (0,548 contre 0,625 arrêt par véhicule), de façon stable : entre +10,5 % et +17,7 % selon les jours. Les cycles courts font plus d'arrêts pour les véhicules de la rue latérale.
5. **Le contrôleur connaît la tendance horaire de la rue latérale** (celle utilisée pour générer la demande), pas son bruit. La marge de 1,3 a été calibrée sur le 19 mai.
6. **Le modèle compte peu.** Le débit varie lentement d'un pas de 5 min au suivant, donc une prédiction parfaite ne donnerait presque pas mieux que la persistance : le gain vient surtout de l'adaptation des verts, pas de la finesse du modèle.
7. **Période COVID.** Le test porte sur mai 2020, une période de reprise partielle (débit moyen de 407 véh/5 min). Les gains valent pour cette période.
8. **Un seul carrefour.** Pas de coordination entre feux (pas d'onde verte), pas de tourne-à-gauche, pas de piétons.
9. **Page 6 en temps réel.** Le modèle exige 36 observations passées ; sans historique, la page doit passer `predicted_flow` directement.

---

## 13. Notes pour l'équipe

**Joel**
- J'utilise `best_model.pkl` tel quel, avec `src/features.py` importable et scikit-learn 1.9.1. Si tu changes le modèle ou le format de `model_info.json`, préviens-moi.
- Les seuils de congestion (303 et 537) viennent de ton fichier.

**Honoré**
- J'utilise uniquement `test.csv`, avec `traffic_flow` et `datetime`. La simulation couvre les 18 jours complets du 14 au 31 mai (le test commence le 13 mai à 20:45, je n'ai gardé que les journées entières).
- La référence de 800 véh/5 min est fixée sur le maximum du dataset entier (794), pas sur le test.

**Fouchi et Mireille (dashboard, page 6)**
- Appelez `predict_green_time(conditions)` : la fonction ne dépend pas de SUMO.
- Le plus simple : fournir `hour` (ou `instant`) et `predicted_flow`. Le retour contient la couleur, les durées de vert et le cycle.
- Dans `results/simulation.csv`, `green_main_s` désigne le vert de l'**axe principal** et `green_secondary_s` celui de la **rue latérale** ; ce ne sont pas des capteurs réels. Les colonnes `fixed_*` et `ai_*` se comparent directement.

---

## 14. Versions

| Élément | Version |
|---|---|
| SUMO / traci / sumolib | 1.28.0 |
| scikit-learn | 1.9.1 |
| Graine de simulation | 42 |
