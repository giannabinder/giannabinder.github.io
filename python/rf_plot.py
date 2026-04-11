import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
import io
import base64

# Assuming RFMatching is imported here or in the main script
# from rf_math import RFMatching 

class RFPlotter:
    """Visualization module customized for Web Portfolio integration."""

    @staticmethod
    def get_portfolio_style():
        """Defines a reusable professional engineering dark-mode theme."""
        return {
            'style': 'dark_background',
            'fig_color': '#161b22',
            'ax_color': '#0d1117',
            'text_color': '#e6edf3',
            'accent_blue': '#58a6ff',
            'accent_orange': '#f0883e',
            'grid_color': '#30363d'
        }

    @staticmethod
    def render_plot_to_base64(fig):
        """Renders a Matplotlib figure to a base64 encoded PNG string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def draw_smith_chart():
        """Generates the base Smith Chart canvas using the portfolio theme."""
        theme = RFPlotter.get_portfolio_style()
        plt.style.use(theme['style'])
        
        fig, ax = plt.subplots(figsize=(8, 8))
        fig.patch.set_facecolor(theme['fig_color'])
        ax.set_facecolor(theme['ax_color'])
        
        # 1. The Unit Circle (Bounding Box)
        unit_circle = Circle((0, 0), 1, color=theme['text_color'], fill=False, linewidth=1.5)
        ax.add_patch(unit_circle)
        
        # 2. Desmos Arrays
        r_values = [0, 1/3, 1, 3, 5/3, 7, 3/5, 1/7]
        x_values = [1/3, 1, 3, -1/3, -1, -3, 5/3, 7, 3/5, 1/7, -5/3, -7, -3/5, -1/7]
        
        # 3. Draw Resistance (R) Circles
        for r in r_values:
            center = (r / (r + 1), 0)
            radius = 1 / (r + 1)
            r_circle = Circle(center, radius, color=theme['grid_color'], fill=False, linestyle='-', alpha=0.8)
            ax.add_patch(r_circle)
            
        # 4. Draw Reactance (X) Circles
        for x in x_values:
            center = (1, 1 / x)
            radius = abs(1 / x)
            x_circle = Circle(center, radius, color=theme['accent_blue'], fill=False, linestyle='--', alpha=0.5)
            x_circle.set_clip_path(unit_circle) 
            ax.add_patch(x_circle)
        
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect('equal')
        ax.axis('off')
        
        return fig, ax

    @staticmethod
    def plot_single_stub_match(gamma_target, stub_type='open'):
        """
        Generates a visual Smith Chart showing the single-stub matching path.
        Returns the base64 image string.
        """
        # 1. Get the base dark-mode Smith Chart
        fig, ax = RFPlotter.draw_smith_chart()
        theme = RFPlotter.get_portfolio_style()
        
        # 2. Get the math solutions (Requires RFMatching)
        sol1, sol2, gd1, gd2 = RFMatching.single_stub_match(gamma_target, stub_type)
        
        # 3. Draw the Constant VSWR Circle (The path of the series transmission line)
        rho = np.abs(gamma_target)
        vswr_circle = Circle((0, 0), rho, color=theme['accent_blue'], fill=False, linestyle='-', linewidth=2, alpha=0.7)
        ax.add_patch(vswr_circle)
        
        # 4. Draw the 1+jb Matching Circle (Target destination before the stub)
        match_circle = Circle((0.5, 0), 0.5, color=theme['accent_orange'], fill=False, linestyle='--', linewidth=2, alpha=0.8)
        ax.add_patch(match_circle)
        
        # 5. Plot the Data Points
        # Starting Load
        ax.plot(np.real(gamma_target), np.imag(gamma_target), 'o', color='white', markersize=8, label='Target $\Gamma_L$')
        
        # Intersection Solutions (where the stub is attached)
        ax.plot(np.real(gd1), np.imag(gd1), 'x', color=theme['accent_orange'], markersize=10, label=f'Sol 1 (d={sol1[0]:.3f}λ, l={sol1[1]:.3f}λ)')
        ax.plot(np.real(gd2), np.imag(gd2), 'x', color=theme['accent_blue'], markersize=10, label=f'Sol 2 (d={sol2[0]:.3f}λ, l={sol2[1]:.3f}λ)')
        
        # Center Match (The Goal)
        ax.plot(0, 0, '*', color='#2ea043', markersize=12, label='Matched (50Ω)')
        
        # 6. Formatting
        ax.set_title(f"Single Stub Matching ({stub_type.capitalize()} Stub)", color=theme['text_color'], pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1), facecolor=theme['fig_color'], edgecolor=theme['grid_color'])
        
        # Return as Base64 for the web using the class method
        return RFPlotter.render_plot_to_base64(fig)