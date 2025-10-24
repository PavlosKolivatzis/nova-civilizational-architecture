"""
Simulation of the extraction–harm–regulation feedback model.
Plots how profit (P), harm (H), and regulation (R) evolve over time.

Run:
    python scripts/simulate_extraction_dynamics.py
"""

import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Parameters
# -----------------------------
alpha = 0.25   # self-reinforcing profit incentive
beta  = 0.05   # regulation pressure on profit
gamma = 0.02   # empathy / voluntary care
delta = 0.15   # profit -> harm conversion
epsilon = 0.04 # regulation reduces harm
eta = 0.02     # reactivity of regulation
Hc = 1.5       # harm threshold triggering regulation

dt = 0.1
T = 400

# Initial states
P, H, R = 1.0, 0.1, 0.0
P_hist, H_hist, R_hist = [P], [H], [R]

# -----------------------------
# Simulation
# -----------------------------
for _ in range(int(T/dt)):
    dP = alpha*P - beta*R - gamma*H
    dH = delta*P - epsilon*R
    dR = eta*max(0, H - Hc)

    P += dP*dt
    H += dH*dt
    R += dR*dt

    P_hist.append(P)
    H_hist.append(H)
    R_hist.append(R)

# -----------------------------
# Plot
# -----------------------------
time = np.linspace(0, T, len(P_hist))
plt.figure(figsize=(10,5))
plt.plot(time, P_hist, label='Profit (P)', color='green')
plt.plot(time, H_hist, label='Harm (H)', color='red')
plt.plot(time, R_hist, label='Regulation (R)', color='blue')
plt.xlabel('Time')
plt.ylabel('Relative magnitude')
plt.title('Extraction–Harm–Regulation Dynamics')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()