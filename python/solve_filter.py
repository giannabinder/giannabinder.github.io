from rf_math import RFMath
import plot_config
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def run_simulation(zo_val, length_m):
    """
    Main entry point for Pyodide. Executes the simulation
    and generates a live Matplotlib plot.
    """
    # 1. Setup Simulation (Fixed er=2.2 for this project)
    freqs = np.linspace(4e9, 12e9, 1000) # Full-band sweep
    er = 2.2
    
    # 2. Build the network (J-Inverter -> TL -> J-Inverter)
    J_node = RFMath.abcd_Y_inverter(0.0043)
    TL = RFMath.abcd_TL(freqs, length_m, zo_val, er)
    
    # 3. Cascade and Convert to S-Parameters
    abcd_total = RFMath.cascade(J_node, TL, J_node)
    S = RFMath.abcd_to_s(abcd_total, zo_val)
    
    # 4. Calculate dB Response
    # S21 = Insertion Loss, S11 = Return Loss
    s21_db = 20 * np.log10(np.abs(S[:, 1, 0]))
    s11_db = 20 * np.log10(np.abs(S[:, 0, 0]))
    
    # 5. Generate Matplotlib Plot
    theme = plot_config.get_portfolio_style()
    plt.style.use(theme['style'])
    
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=theme['fig_color'])
    ax.set_facecolor(theme['ax_color'])
    
    ax.plot(freqs/1e9, s21_db, label='S21 (Insertion Loss)', color=theme['accent_blue'], linewidth=2)
    ax.plot(freqs/1e9, s11_db, label='S11 (Return Loss)', color=theme['accent_orange'], linewidth=1.5)
    
    # Professional Formatting
    ax.set_title("Filter System Response: Verified RFMath Solver", color=theme['text_color'], fontsize=12)
    ax.set_xlabel("Frequency (GHz)", color=theme['text_color'])
    ax.set_ylabel("Magnitude (dB)", color=theme['text_color'])
    ax.grid(True, linestyle='--', alpha=0.3, color=theme['grid_color'])
    ax.legend(frameon=True, facecolor=theme['fig_color'], edgecolor=theme['grid_color'])
    
    # Ensure standard S-param plot range
    ax.set_ylim(-60, 5)
    
    # 6. Convert the plot to a base64 string
    return plot_config.render_plot_to_base64(fig)