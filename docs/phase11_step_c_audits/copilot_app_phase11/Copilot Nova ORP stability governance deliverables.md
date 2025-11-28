# **Nova ORP stability governance deliverables**

You’ve built a living architecture that insists on steadiness. Let’s make the spine visible and test its reflexes. Below are the five deliverables, tightly aligned with your Phase 11 invariants, transformation geometry, and contracts.

---

## **Regime state machine**

### **States and ordinals**

* **Set:** {normal (0), heightened (1), controlled\_degradation (2), emergency\_stabilization (3), recovery (4)}  
* **Entry semantics (informal):**  
  * **Normal:** MSE=stable AND URF in \[0.0, 0.3) AND CSI in \[0.7, 1.0\]  
  * **Heightened:** MSE=oscillating AND URF in \[0.3, 0.6) AND CSI in \[0.5, 0.9\]  
  * **Controlled\_degradation:** MSE=unstable AND URF in \[0.6, 0.85) AND CSI in \[0.3, 0.7\]  
  * **Emergency\_stabilization:** MSE=critically\_unstable AND URF in \[0.85, 1.0\] AND CSI in \[0.0, 0.5\]  
  * **Recovery:** Prior regime ∈ {2,3} AND dC/dt\>0 AND CSI in \[0.5, 0.85)

### **Allowed transitions**

* **Legal edges:**  
  * \[normal → heightened\]  
  * \[heightened → normal\]  
  * \[heightened → controlled\_degradation\]  
  * \[controlled\_degradation → heightened\]  
  * \[controlled\_degradation → emergency\_stabilization\]  
  * \[emergency\_stabilization → recovery\]  
  * \[recovery → heightened\]

### **Forbidden direct transitions**

* **Illegal edges:**  
  * \[normal → emergency\_stabilization\]  
  * \[normal → recovery\]  
  * \[heightened → emergency\_stabilization\]

### **Minimum regime durations (hysteresis)**

* **Durations:** normal: 60s; heightened: 300s; controlled\_degradation: 600s; emergency\_stabilization: 900s; recovery: 1800s

### **Amplitude bounds (global and per regime)**

* **Global envelope:** eta\_scaled ∈ \[0.25, 1.0\]; emotion ∈ \[0.5, 1.0\]; sensitivity ∈ \[1.0, 1.5\]  
* **Per regime ranges (subset of global):**  
  * normal: eta=\[0.8,1.0\], emotion=1.0, sensitivity=1.0  
  * heightened: eta=\[0.75,0.95\], emotion=\[0.85,0.95\], sensitivity=\[1.05,1.15\]  
  * controlled\_degradation: eta=\[0.50,0.75\], emotion=0.70, sensitivity=1.30  
  * emergency\_stabilization: eta=\[0.25,0.50\], emotion=0.50, sensitivity=1.50  
  * recovery: eta=\[0.25,0.40\], emotion=0.60, sensitivity=1.20

---

## **Hysteresis rules**

### **Core decision logic**

* **Same regime:** If proposed \== current → allowed=true; effective\_regime=current; reason=same\_regime\_no\_transition.  
* **Minimum duration:** If current\_duration\_s \< MIN\_DURATION\[current\] → allowed=false; effective\_regime=current; reason=min\_duration\_not\_met; time\_remaining\_s \= MIN\_DURATION \- current\_duration\_s.  
* **Oscillation advisory:** Count transitions in window\_s=300; if count ≥3 → oscillation\_detected=true; warn only (does not block).  
* **Recovery exit guard:** If current=recovery AND proposed=normal → require CSI ≥ 0.85 and duration\_s ≥ 1800; else block (advisory rationale: recovery\_ramp\_stabilization).  
* **Outputs (schema):** allowed, effective\_regime, reason, current\_regime, current\_duration\_s, min\_duration\_s, time\_remaining\_s, oscillation\_detected, oscillation\_count.

### **Invariants honored**

* **Temporal inertia:** No transitions before minimum duration.  
* **Monotonic duration:** duration\_s increases until transition; resets on transition.  
* **No destructive oscillation:** Advisory detection to surface ≥3 transitions per 300s.  
* **Unified regime view:** Governor, Slot03, Slot09 use the same effective\_regime from shared hysteresis check.

---

## **Legal vs illegal transition simulation**

### **Transition evaluation table**

| From | To | Legal by topology | Min duration met? | Recovery guard (if applicable) | Final decision | Reason |
| ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| normal | heightened | Yes | If ≥60s | N/A | Allow if duration met | min\_duration\_met or not\_met |
| heightened | normal | Yes | If ≥300s | N/A | Allow if duration met | min\_duration\_\* |
| heightened | controlled\_degradation | Yes | If ≥300s | N/A | Allow if duration met | min\_duration\_\* |
| controlled\_degradation | heightened | Yes | If ≥600s | N/A | Allow if duration met | min\_duration\_\* |
| controlled\_degradation | emergency\_stabilization | Yes | If ≥600s | N/A | Allow if duration met | min\_duration\_\* |
| emergency\_stabilization | recovery | Yes | If ≥900s | N/A | Allow if duration met | min\_duration\_\* |
| recovery | heightened | Yes | If ≥1800s | N/A | Allow if duration met | min\_duration\_\* |
| recovery | normal | Not in allowed set | — | CSI ≥0.85 AND ≥1800s required | Block (advisory contract) | recovery\_ramp\_stabilization |
| normal | emergency\_stabilization | Forbidden | — | — | Block | forbidden\_direct |
| normal | recovery | Forbidden | — | — | Block | forbidden\_direct |
| heightened | emergency\_stabilization | Forbidden | — | — | Block | forbidden\_direct |

Note: Where “min\_duration\_\*” appears, decision depends on current\_duration\_s versus regime minimums; oscillation detection is advisory and does not change allow/block status.

---

## **Safety envelope violation detection**

### **Checks to run per proposed transition and current state**

* **Topology violation:** Proposed edge ∉ allowed AND ∈ forbidden\_direct → violation: c2\_no\_direct\_extreme\_jumps.  
* **Temporal inertia violation:** current\_duration\_s \< MIN\_DURATION\[current\] → violation: minimum\_regime\_durations.  
* **Oscillation limit advisory:** transitions\_in\_last\_300s \> 3 → advisory: c1\_no\_destructive\_oscillation (warn).  
* **Amplitude bounds violation:** Any multiplier outside global ranges → violation: c5\_amplitude\_within\_bounds.  
  * eta\_scaled ∉ \[0.25, 1.0\]  
  * emotion ∉ \[0.5, 1.0\]  
  * sensitivity ∉ \[1.0, 1.5\]  
* **No uncontrolled acceleration:** If instability (ordinal ≥1), ensure eta\_multiplier ≤ 1.0; else violation.  
* **No noise amplification:** If instability (ordinal ≥1), ensure sensitivity\_multiplier ≥ 1.0; else violation.  
* **Recovery exit threshold:** If current=recovery and proposed=normal and CSI\<0.85 or duration\<1800 → violation advisory: recovery\_stabilization.  
* **Continuity bounds:** CSI must stay in \[0,1\]; out-of-range → violation: continuity\_preservation.  
* **Unified path to normal:** Graph must contain a path from every state back to normal; missing path → violation: recovery\_path\_guarantee.  
* **Child temporal inertia:** Children cannot set min durations lower than declared; if detected → violation: temporal\_inertia.

---

## **Convergence matrix**

This matrix summarizes regime-specific amplitude scaling and transition inertia, making convergence behavior explicit. It highlights damping toward stability and guarded re-expansion.

### **Regime convergence attributes**

| Regime | Learning (eta scale) | Emotion (multiplier) | Perception (sensitivity) | Min hold (s) | Convergence posture |
| ----- | ----- | ----- | ----- | ----- | ----- |
| normal | 0.8–1.0 | 1.0 | 1.0 | 60 | Baseline; full bandwidth; ready-to-escalate only on genuine oscillation/risk |
| heightened | 0.75–0.95 | 0.85–0.95 | 1.05–1.15 | 300 | Mild damping; tighten thresholds; reduce learning to avoid runaway |
| controlled\_degradation | 0.50–0.75 | 0.70 | 1.30 | 600 | Significant damping; freeze deployments; stabilize before any escalation |
| emergency\_stabilization | 0.25–0.50 | 0.50 | 1.50 | 900 | Hard damping; safe\_mode bias; strong detection thresholding |
| recovery | 0.25–0.40 | 0.60 | 1.20 | 1800 | Gradual restoration; minimal learning; exit only when CSI ≥ 0.85 |

### **Convergence implications**

* **Instability bias:** As ordinal increases, eta decreases, emotion constricts, sensitivity increases—net effect is damped dynamics and noise resistance.  
* **Temporal inertia:** Minimum durations enforce persistence, suppressing reactive flips and promoting signal stabilization.  
* **Recovery ramp:** The longest hold and CSI ≥ 0.85 requirement ensure restoration is earned, not assumed.

---

## **Optional implementation stubs**

#### **Hysteresis decision function (pure)**

def check\_regime\_hysteresis(proposed, ledger, now\_ts, window\_s=300):  
    current \= ledger.latest() if ledger else None  
    if current is None:  
        return Decision(True, proposed, "no\_ledger\_history", "unknown", 0.0, 0.0, 0.0, False, 0\)

    if proposed \== current.regime:  
        return Decision(True, current.regime, "same\_regime\_no\_transition",  
                        current.regime, current.duration\_s, MIN\[current.regime\], 0.0,  
                        oscillation\_detected(ledger, window\_s), oscillation\_count(ledger, window\_s))

    time\_remaining \= max(0.0, MIN\[current.regime\] \- current.duration\_s)  
    if time\_remaining \> 0.0:  
        return Decision(False, current.regime,  
                        f"min\_duration\_not\_met:{current.regime}:{current.duration\_s:.1f}s\<{MIN\[current.regime\]:.1f}s}",  
                        current.regime, current.duration\_s, MIN\[current.regime\], time\_remaining,  
                        oscillation\_detected(ledger, window\_s), oscillation\_count(ledger, window\_s))

    \# Recovery exit guard  
    if current.regime \== "recovery" and proposed \== "normal":  
        csi \= latest\_csi\_value()  
        if current.duration\_s \< MIN\["recovery"\] or csi \< 0.85:  
            return Decision(False, current.regime, "recovery\_ramp\_stabilization",  
                            current.regime, current.duration\_s, MIN\["recovery"\],  
                            max(0.0, MIN\["recovery"\] \- current.duration\_s),  
                            oscillation\_detected(ledger, window\_s), oscillation\_count(ledger, window\_s))

    return Decision(True, proposed, "min\_duration\_met",  
                    current.regime, current.duration\_s, MIN\[current.regime\], 0.0,  
                    oscillation\_detected(ledger, window\_s), oscillation\_count(ledger, window\_s))

#### **Safety envelope validator**

def validate\_safety\_envelope(regime, eta\_scale, emotion\_mul, sensitivity\_mul, instability=True):  
    violations \= \[\]

    \# Global bounds  
    if not (0.25 \<= eta\_scale \<= 1.0): violations.append("eta\_scaled\_out\_of\_bounds")  
    if not (0.5 \<= emotion\_mul \<= 1.0): violations.append("emotion\_out\_of\_bounds")  
    if not (1.0 \<= sensitivity\_mul \<= 1.5): violations.append("sensitivity\_out\_of\_bounds")

    \# Instability invariants  
    if instability and eta\_scale \> 1.0: violations.append("no\_uncontrolled\_acceleration")  
    if instability and sensitivity\_mul \< 1.0: violations.append("no\_noise\_amplification")

    return violations

---

## **What you might want next**

* **Attach regime\_transition\_ledger sample:** I can compute oscillation counts and produce a live hysteresis audit.  
* **Provide CSI/URF/MSE snapshots:** I’ll run the classification and show which transitions are permitted right now.  
* **Export as contracts/tests:** I can emit YAML contracts and pytest skeletons to drop into your repo.

