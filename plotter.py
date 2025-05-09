import matplotlib.pyplot as plt
import numpy as np
from sympy import lambdify


def create_solution_plot(sol_rhs, x_sym, x_range=(-5, 5), num_points=1000):
    """Create a plot of the solution."""
    if sol_rhs is None:
        return None, "Solution indisponible pour le graphe"

    try:
        # Check for free symbols other than x (like C1, C2)
        free_symbols_in_sol = sol_rhs.free_symbols
        unresolved_constants = [s for s in free_symbols_in_sol if s != x_sym and not s.is_number]

        if unresolved_constants:
            return None, f"Les constantes {unresolved_constants} doivent être précisées pour le graphe"

        # Prepare for numerical evaluation
        modules_for_lambdify = ['numpy', {'Heaviside': lambda x: np.heaviside(x, 0.5)}]
        y_numpy_func = lambdify(x_sym, sol_rhs, modules=modules_for_lambdify)

        # Generate x values for plotting
        x_vals_plot = np.linspace(x_range[0], x_range[1], num_points)
        y_vals_plot = np.empty_like(x_vals_plot, dtype=float)

        # Evaluate y_numpy_func safely
        for i, val in enumerate(x_vals_plot):
            try:
                y_vals_plot[i] = y_numpy_func(val)
            except (NameError, TypeError, ValueError):
                y_vals_plot[i] = np.nan

        # Create the plot
        fig, ax = plt.subplots()
        ax.plot(x_vals_plot, y_vals_plot)
        ax.set_xlabel("x")
        ax.set_ylabel("y(x)")
        ax.set_title("Graphe de la solution")
        ax.grid(True)
        ax.set_xlim(x_range)

        return fig, ""
    except Exception as e:
        return None, f"Erreur de dessin: {e}"
