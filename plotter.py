import matplotlib.pyplot as plt
import numpy as np
from sympy import lambdify


def create_solution_plot(sol_rhs, x_sym, x_range=None, num_points=1000, constants_values=None):
    """Create a plot of the solution with smart range selection."""
    if sol_rhs is None:
        return None, "Solution indisponible pour le graphe"

    try:
        # Check for free symbols other than x (like C1, C2)
        free_symbols_in_sol = sol_rhs.free_symbols
        unresolved_constants = [s for s in free_symbols_in_sol if s != x_sym and not s.is_number]

        # Apply provided constant values if any
        if constants_values and unresolved_constants:
            for const in list(unresolved_constants):
                if str(const) in constants_values:
                    sol_rhs = sol_rhs.subs(const, constants_values[str(const)])

            # Recheck remaining constants
            free_symbols_in_sol = sol_rhs.free_symbols
            unresolved_constants = [s for s in free_symbols_in_sol if s != x_sym and not s.is_number]

        if unresolved_constants and not constants_values:
            return None, unresolved_constants, "Les constantes doivent être précisées pour le graphe"

        # Prepare for numerical evaluation
        modules_for_lambdify = ['numpy', {'Heaviside': lambda x: np.heaviside(x, 0.5)}]
        y_numpy_func = lambdify(x_sym, sol_rhs, modules=modules_for_lambdify)

        # Determine interesting range if not specified
        if x_range is None:
            x_range = find_interesting_range(y_numpy_func)

        # Generate x values for plotting
        x_vals_plot = np.linspace(x_range[0], x_range[1], num_points)
        y_vals_plot = np.empty_like(x_vals_plot, dtype=float)

        # Evaluate safely
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

        return fig, unresolved_constants, ""
    except Exception as e:
        return None, None, f"Erreur de dessin: {e}"


def find_interesting_range(func, default_range=(-5, 5)):
    """Find an interesting range to plot a function."""
    try:
        # Start with wide test range
        test_points = np.linspace(-20, 20, 500)
        test_values = []

        # Sample function at test points
        for x in test_points:
            try:
                y = func(x)
                if np.isfinite(y) and not np.isnan(y) and abs(y) < 1e6:  # Avoid extreme values
                    test_values.append((x, y))
            except:
                pass

        if len(test_values) < 10:
            return default_range

        # Extract x and y values
        xs, ys = zip(*test_values)

        # Find y range, removing outliers
        ys_arr = np.array(ys)
        q1, q3 = np.percentile(ys_arr, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Filter to reasonable y range
        filtered_points = [(x, y) for x, y in test_values if lower_bound <= y <= upper_bound]

        if not filtered_points:
            return default_range

        filtered_xs = [x for x, y in filtered_points]

        # Find min and max x with interesting behavior
        min_x = min(filtered_xs)
        max_x = max(filtered_xs)

        # Center around 0 if possible
        if min_x < 0 < max_x:
            abs_range = max(abs(min_x), abs(max_x))
            return -abs_range, abs_range
        else:
            padding = (max_x - min_x) * 0.1
            return min_x - padding, max_x + padding
    except:
        return default_range
