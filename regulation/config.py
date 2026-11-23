"""Paramètres de la régulation et de la simulation SUMO.

Toutes les hypothèses de l'axe fictif sont regroupées ici pour être
documentées et modifiées en un seul endroit.
"""

SEED = 42

# --- Dataset ----------------------------------------------------------------
STEP_S = 300          # un pas du dataset = 5 minutes
FLOW_REF = 800.0      # débit (véh / 5 min) = charge 100 %. Référence FIXE tirée
                      # de tout le dataset (max observé : 794), jamais du test seul.

# --- Carrefour fictif sur un axe (SUMO) --------------------------------------
# Un axe principal à sens unique (comme la série du dataset : un seul sens de
# circulation), 2 voies, 50 km/h, qui traverse 1 carrefour à feux ; une rue
# latérale à double sens (1 voie par sens) croise l'axe. Tout le monde va tout
# droit. N_JUNCTIONS peut être augmenté (axe à plusieurs feux coordonnés, voir
# OFFSET_S et PROGRESSION_FACTOR plus bas) ; la version de référence en a 1.
N_JUNCTIONS = 1
SPACING_M = 400.0            # distance entre deux carrefours (et longueur des tronçons d'entrée / de sortie)
SIDE_LENGTH_M = 200.0        # longueur de chaque branche de rue latérale
LANES_MAIN = 2
LANES_SIDE = 1
SPEED_LIMIT_MS = 50 / 3.6    # 50 km/h
# Débits de saturation (véh/h de vert) :
#  - axe principal : 2 voies x 1 800 véh/h/voie (valeur mesurée dans SUMO) ;
#  - rues latérales : 1 voie par sens, 2 sens ouverts en même temps, la voie la
#    plus chargée vaut la moitié de la demande de la rue -> même formule.
SAT_MAIN_VPH = 3600.0
SAT_SIDE_VPH = 3600.0
# Demande de l'axe principal (véh/h) quand le débit du dataset = FLOW_REF.
PEAK_MAIN_VPH = 2100.0

# --- Feux -------------------------------------------------------------------
YELLOW_S = 4
ALL_RED_S = 1
CLEARANCE_S = YELLOW_S + ALL_RED_S   # temps de dégagement après chaque vert
# Cycle fixe de référence : plan classique de 90 s, partage 56 / 24 s proche de
# la répartition moyenne de la demande (axe principal : 70 % du vert).
FIXED_MAIN_GREEN_S = 56
FIXED_SIDE_GREEN_S = 24      # cycle fixe : 56 + 24 + 2 x 5 = 90 s
G_MIN_S = 10              # vert minimum (sécurité)
G_MAX_S = 60              # vert maximum
CYCLE_MIN_S = 40
CYCLE_MAX_S = 120
# Seulement si N_JUNCTIONS > 1 (« onde verte ») : le programme de feux du
# carrefour k+1 est celui du carrefour k retardé de OFFSET_S secondes (temps de
# parcours d'un peloton entre deux carrefours). Identique pour le cycle fixe et
# pour l'IA. Avec un seul carrefour, ces deux paramètres ne servent pas.
OFFSET_S = 35
# Facteur de progression du retard de l'axe principal : 1 = arrivées au hasard
# (un seul carrefour). Avec plusieurs feux coordonnés, une valeur plus petite
# (0,3 mesuré avec 3 feux) tient compte de l'onde verte.
PROGRESSION_FACTOR = 1.0

# Marge de prudence sur la demande de la rue latérale (le contrôleur ne la voit pas,
# il n'en connaît que la tendance horaire).
SIDE_SAFETY = 1.3     # calibré sur la journée du 19 mai (essais 1,0 / 1,3 / 1,6 / 2,0)

# --- Répartition de la demande entre l'axe et les rues latérales (hypothèse) -
# Le dataset n'a qu'une série : la part de l'axe principal dans la demande d'un
# carrefour (axe + rue latérale) est une hypothèse. Tendance horaire douce
# (axe plus dominant à 8 h) plus un bruit AR(1) imprévisible (graine fixe).
SHARE_MEAN = 0.75
SHARE_AMP = 0.05
SHARE_PEAK_HOUR = 8.0
SHARE_NOISE_STD = 0.03
SHARE_NOISE_RHO = 0.9
SHARE_MIN, SHARE_MAX = 0.60, 0.90

# --- Niveau de congestion : seuils de Joel (models/model_info.json) ---------
# « tiers du débit du train », en véhicules par 5 minutes.
CONGESTION_LOW_FLOW = 303.0     # faible jusqu'à 303
CONGESTION_HIGH_FLOW = 537.0    # moyen jusqu'à 537, élevé au-delà

# --- Objectif ---------------------------------------------------------------
GAIN_TARGET_PCT = 15.0    # réduction visée du temps d'attente moyen
