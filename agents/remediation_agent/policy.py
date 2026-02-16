
# Only these risks can be auto-executed
AUTO_APPROVE_RISK = {"very low"}

# Minimum confidence to auto-remediate
CONFIDENCE_THRESHOLD = 0.95

# Scoring weights: S(a) = W1*γ + W2*ρ − W3*κ − W4*β
W1 = 0.40   # confidence
W2 = 0.30   # reversibility
W3 = 0.15   # cost
W4 = 0.15   # blast radius

SAFETY_THRESHOLD = 0.95   # θ_safe — auto-execute if score exceeds this