from rf_math import RFNetworks, RFFilters
from rf_plot import RFPlotter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def simulate_2port(zo_val, length_m, spot_freq_ghz=8.1):
    """
    Main entry point for Pyodide. Executes the simulation
    and generates a live Matplotlib plot.
    """
    # 1. Setup Simulation (Fixed er=2.2 for this project)
    start_freq = max(0.1, spot_freq_ghz - 4) * 1e9 # Prevent negative frequencies
    end_freq = (spot_freq_ghz + 4) * 1e9
    freqs = np.linspace(start_freq, end_freq, 1000) # Dynamic full-band sweep
    er = 2.2
    
    # 2. Build the network (J-Inverter -> TL -> J-Inverter)
    J_node = RFNetworks.abcd_Y_inverter(0.0043)
    TL = RFNetworks.abcd_TL(freqs, length_m, zo_val, er)
    
    # 3. Cascade and Convert to S-Parameters
    abcd_total = RFNetworks.cascade(J_node, TL, J_node)
    S = RFNetworks.abcd_to_s(abcd_total, zo_val)
    
    # 4. Calculate dB Response
    # S21 = Insertion Loss, S11 = Return Loss
    s21_db = 20 * np.log10(np.abs(S[:, 1, 0]) + 1e-12)
    s11_db = 20 * np.log10(np.abs(S[:, 0, 0]) + 1e-12)
    
    # 5. Package data for JS plotting library
    result = {
        "freqs_ghz": (freqs / 1e9).tolist(),
        "s21_db": s21_db.tolist(),
        "s11_db": s11_db.tolist(),
        "spot_freq_ghz": spot_freq_ghz
    }
    return json.dumps(result)


def simulate_chebyshev_bpf(N, ripple_dB, f0_ghz, fractional_bw, R0=50):
    """
    Main entry point for Pyodide. Dynamically constructs a Chebyshev BPF of any order, 
    cascades the ABCD matrices, and returns a JSON string for JS frontend plotting.
    """
    f0 = f0_ghz * 1e9
    
    # 1. Setup Dynamic Frequency Sweep
    sweep_range = max(0.2, fractional_bw * 4) 
    start_freq = max(0.1, f0_ghz - (f0_ghz * sweep_range)) * 1e9 
    end_freq = (f0_ghz + (f0_ghz * sweep_range)) * 1e9
    
    freqs = np.linspace(start_freq, end_freq, 1000)
    omega = 2 * np.pi * freqs
    
    # 2. Get Exact Component Values
    components = RFFilters.design_lumped_bpf(N, ripple_dB, f0, fractional_bw, R0)
    
    # Fetch the distributed parameters to get the J-values
    dist_params = RFFilters.design_admittance_inverters(N, ripple_dB, fractional_bw, R0)
    j_vals = dist_params["J_values"] # <--- Extract the J-values array
    
    # 3. Build the Network Chain (Lumped Simulation)
    stages = []
    for k in range(1, N + 1):
        if k % 2 != 0:
            L = components[f'L{k}_series']
            C = components[f'C{k}_series']
            Z = 1j * omega * L + 1 / (1j * omega * C)
            stages.append(RFNetworks.abcd_Z(Z))
        else:
            L = components[f'L{k}_shunt']
            C = components[f'C{k}_shunt']
            Y = 1 / (1j * omega * L) + 1j * omega * C
            stages.append(RFNetworks.abcd_Y(Y))
            
    # 4. Cascade Matrices and Convert to S-Parameters
    abcd_total = RFNetworks.cascade(*stages)
    S = RFNetworks.abcd_to_s(abcd_total, R0)
    
    s21_db = 20 * np.log10(np.abs(S[:, 1, 0]) + 1e-12)
    s11_db = 20 * np.log10(np.abs(S[:, 0, 0]) + 1e-12)
    
    # 5. Package data for JS plotting library
    result = {
        "freqs_ghz": (freqs / 1e9).tolist(),
        "s21_db": s21_db.tolist(),
        "s11_db": s11_db.tolist(),
        "center_freq_ghz": f0_ghz,
        "j_values": j_vals.tolist() # <--- Convert to list and add to JSON
    }
    return json.dumps(result)