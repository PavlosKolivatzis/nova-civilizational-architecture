"""
Extraction–Harm–Regulation with Power-Shield (S).
Run: python scripts/simulate_extraction_dynamics_shield.py
"""
import numpy as np
import matplotlib.pyplot as plt

# ---------------- Parameters ----------------
alpha   = 0.25   # profit self-reinforcement
beta    = 0.05   # regulation pressure on profit
gamma   = 0.02   # empathy / voluntary care

delta   = 0.15   # profit -> harm conversion
epsilon = 0.04   # regulation reduces harm

eta     = 0.02   # regulation reactivity to visible harm
Hc      = 1.5    # harm threshold

# --- Power-shield parameters ---
phi     = 0.75   # how strongly S suppresses regulation (0..1)
sigma   = 0.04   # profit -> shield growth
rho     = 0.03   # regulation erodes shield
mu      = 0.02   # shield natural decay
kappa   = 0.03   # shield dampens R growth (drag term)

# Simulation config
dt = 0.1
T  = 400
yscale_log = False  # set True if values explode

# ---------------- Initial state --------------
P, H, R, S = 1.0, 0.1, 0.0, 0.1
P_hist, H_hist, R_hist, S_hist = [P], [H], [R], [S]

# ---------------- Simulation -----------------
steps = int(T/dt)
for _ in range(steps):
    R_eff = R * max(0.0, 1.0 - phi * S)  # bounded in [0, R]

    dP = alpha*P - beta*R_eff - gamma*H
    dH = delta*P - epsilon*R_eff
    dR = eta*max(0.0, H - Hc) - kappa*S*R
    dS = sigma*P - rho*R - mu*S

    P += dP*dt;  H += dH*dt;  R += dR*dt;  S += dS*dt
    P = max(P, 0.0); H = max(H, 0.0); R = max(R, 0.0); S = max(S, 0.0)

    P_hist.append(P); H_hist.append(H); R_hist.append(R); S_hist.append(S)

# ---------------- Plot -----------------------
t = np.linspace(0, T, len(P_hist))
plt.figure(figsize=(10,5))
if yscale_log: plt.yscale("log")
plt.plot(t, P_hist, label="Profit (P)")
plt.plot(t, H_hist, label="Harm (H)")
plt.plot(t, R_hist, label="Regulation (R)")
plt.plot(t, S_hist, label="Power-Shield (S)")
plt.xlabel("Time"); plt.ylabel("Relative magnitude")
plt.title("Extraction–Harm–Regulation with Power-Shield (S)")
plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
plt.show()