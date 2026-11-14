"""Paramètres de la régulation et de la simulation SUMO.

Toutes les hypothèses du carrefour fictif sont regroupées ici pour être
documentées et modifiées en un seul endroit.
"""

SEED = 42

# --- Dataset ----------------------------------------------------------------
STEP_S = 300          # un pas du dataset = 5 minutes
FLOW_REF = 800.0      # débit (véh / 5 min) = charge 100 %. Référence FIXE tirée
                      # de tout le dataset (max observé : 794), jamais du test seul.

# --- Carrefour fictif (SUMO) : 2 axes, 2 voies par sens, tout droit ---------
LANES_PER_APPROACH = 2
APPROACH_LENGTH_M = 400.0
SPEED_LIMIT_MS = 50 / 3.6            # 50 km/h
# Débit de saturation d'un axe (2 sens x 2 voies = 4 voies en vert) MESURÉ dans
# SUMO : 7100 à 7250 véh/h de vert, soit environ 1 800 véh/h/voie.
SAT_FLOW_AXIS_VPH = 7200.0
# Demande totale du carrefour (2 axes) quand le débit du dataset = FLOW_REF.
# 5400 véh/h = 75 % de la capacité théorique du carrefour au pic du dataset.
PEAK_TOTAL_VPH = 5400.0

# --- Feux -------------------------------------------------------------------
YELLOW_S = 4
ALL_RED_S = 1
CLEARANCE_S = YELLOW_S + ALL_RED_S   # temps de dégagement après chaque vert
FIXED_GREEN_S = 40        # cycle fixe : 40 + 40 + 2 x 5 = 90 s, partage 50/50
G_MIN_S = 10              # vert minimum (sécurité)
G_MAX_S = 60              # vert maximum
CYCLE_MIN_S = 40
CYCLE_MAX_S = 120
Y_MAX = 0.90              # plafond du taux de charge dans la formule de Webster

# --- Répartition de la demande entre les deux axes (hypothèse) --------------
# Le dataset n'a qu'une série : la part de l'axe principal (N-S) est une
# hypothèse. Plus chargé le matin (pic à 8 h), moins chargé le soir, plus un
# bruit AR(1) imprévisible (graine fixe).
SHARE_MEAN = 0.50
SHARE_AMP = 0.15
SHARE_PEAK_HOUR = 8.0
SHARE_NOISE_STD = 0.04
SHARE_NOISE_RHO = 0.9
SHARE_MIN, SHARE_MAX = 0.20, 0.80

# --- Niveau de congestion : seuils de Joel (models/model_info.json) ---------
# « tiers du débit du train », en véhicules par 5 minutes.
CONGESTION_LOW_FLOW = 303.0     # faible jusqu'à 303
CONGESTION_HIGH_FLOW = 537.0    # moyen jusqu'à 537, élevé au-delà

# --- Objectif ---------------------------------------------------------------
GAIN_TARGET_PCT = 15.0    # réduction visée du temps d'attente moyen
