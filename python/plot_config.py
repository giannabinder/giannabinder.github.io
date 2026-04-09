import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

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

def render_plot_to_base64(fig):
    """
    Renders a Matplotlib figure to a base64 encoded PNG string.
    Essential for web integration without a backend server.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    
    # Encode buffer to base64 string
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig) # Prevent memory leaks
    
    return f"data:image/png;base64,{img_str}"