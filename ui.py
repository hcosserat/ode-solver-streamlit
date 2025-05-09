import streamlit as st
import sympy

from plotter import create_solution_plot
from solver import x_sym, y_x, parse_ode, solve_ode, get_solution_rhs


def setup_page():
    """Initial page configuration."""
    st.set_page_config(layout="wide")
    st.title("Solveur d'équations différentielles ordinaires")


def initialize_session_state():
    """Initialize the session state variables."""
    if 'ode_string' not in st.session_state:
        st.session_state.ode_string = "Derivative(y(x), x) + y(x)"
    if 'ode_eq' not in st.session_state:
        st.session_state.ode_eq = None
    if 'ode_order' not in st.session_state:
        st.session_state.ode_order = 0
    if 'solution' not in st.session_state:
        st.session_state.solution = None
    if 'ics_values' not in st.session_state:
        st.session_state.ics_values = {}
    if 'use_ics' not in st.session_state:
        st.session_state.use_ics = False


def render_equation_input():
    """Render the ODE input section."""
    st.sidebar.header("Équation")
    st.session_state.ode_string = st.sidebar.text_area(
        "Entrez votre EDO :",
        value=st.session_state.ode_string,
        height=100
    )

    ode_eq, ode_order, error_message = parse_ode(st.session_state.ode_string)

    if error_message:
        st.sidebar.error(error_message)
        st.session_state.ode_eq = None
        st.session_state.ode_order = 0
    else:
        st.session_state.ode_eq = ode_eq
        st.session_state.ode_order = ode_order
        st.sidebar.success(f"Parsing réussi, ordre détécté : {st.session_state.ode_order}")
        try:
            st.sidebar.latex(f"\\text{{EDO : }} {sympy.latex(st.session_state.ode_eq)}")
        except Exception as e:
            st.sidebar.warning(f"Échec du rendu LaTeX : {e}")

    return ode_eq, ode_order


def render_initial_conditions():
    """Render the initial conditions input section."""
    st.sidebar.header("Conditions initiales :")
    if st.session_state.ode_order > 0:
        st.session_state.use_ics = st.sidebar.checkbox(
            "Rentrer des conditions initiales ?",
            value=st.session_state.use_ics
        )

        if st.session_state.use_ics:
            st.session_state.ics_values = {}  # Reset if checkbox state changes
            st.sidebar.markdown(f"Rentrez jusqu'à {st.session_state.ode_order} conditions :")
            for i in range(st.session_state.ode_order):
                deriv_label = "y" + "".join(["'" for _ in range(i)])
                cols = st.sidebar.columns([2, 1, 1])
                with cols[0]:
                    condition_label = f"{deriv_label}(x₀) = y₀"
                    st.markdown(condition_label)
                with cols[1]:
                    x0_val = st.number_input(f"x₀ pour {deriv_label}", value=0.0, key=f"x0_{i}", format="%.2f")
                with cols[2]:
                    y0_val = st.number_input(f"y₀ pour {deriv_label}", value=1.0, key=f"y0_{i}", format="%.2f")

                # Store IC: y_val at x_val for the i-th derivative
                st.session_state.ics_values[i] = {'x0': x0_val, 'y0': y0_val}
    else:
        st.sidebar.info("Entrez une EDO valide pour rentrer les conditions initiales.")
        st.session_state.use_ics = False  # Disable if no order

    return st.session_state.use_ics, st.session_state.ics_values


def prepare_ics_dict(use_ics, ics_values):
    """Prepare the initial conditions dictionary for dsolve."""
    ics_dict = {}
    if use_ics and ics_values:
        for i, vals in ics_values.items():
            x_val = vals['x0']
            y_val = vals['y0']
            if i == 0:
                # Condition for y(x0)
                ics_dict[y_x.subs(x_sym, x_val)] = y_val
            else:
                # Condition for n-th derivative y^(n)(x0)
                ics_dict[y_x.diff((x_sym, i)).subs(x_sym, x_val)] = y_val
    return ics_dict


def render_solve_button():
    """Render the solve button and handle solving."""
    if st.sidebar.button("Résoudre", type="primary", use_container_width=True,
                         disabled=(st.session_state.ode_eq is None)):
        if st.session_state.ode_eq is not None:
            ics_dict = prepare_ics_dict(st.session_state.use_ics, st.session_state.ics_values)

            with st.spinner("Chargement..."):
                solution, error = solve_ode(st.session_state.ode_eq, ics_dict)

            if error:
                st.error(error)
                st.session_state.solution = error
            else:
                st.session_state.solution = solution
        else:
            st.error("Entrez une EDO valide avant de résoudre.")


def display_solution():
    """Display the solution and plot if available."""
    st.header(":material/lightbulb: Solution")
    if st.session_state.solution is not None:
        if isinstance(st.session_state.solution, str):  # Error message
            st.error(st.session_state.solution)
        elif st.session_state.solution is None:  # Empty list or None if dsolve fails quietly
            st.warning("Aucune solution n'a été trouvée, l'équation est peut-être triviale (par exemple 0=0).")
        else:
            # If dsolve returns a list, take the first one for simplicity
            current_solution = st.session_state.solution
            if isinstance(current_solution, list):
                if not current_solution:
                    st.warning("Aucune solution n'a été trouvée, l'équation est peut-être triviale (par exemple 0=0).")
                    current_solution = None  # skip further processing
                else:
                    st.info(f"Plusieurs ({len(current_solution)}) solution(s) ont été trouvée(s), affichage de la première.")
                    current_solution = current_solution[0]

            if current_solution is not None:
                st.subheader("Version texte :")
                st.code(str(current_solution), language=None)

                st.subheader("Version LaTeX :")
                try:
                    st.latex(sympy.latex(current_solution))
                except Exception as e:
                    st.warning(f"Échec du rendu LaTeX : {e}")
                    st.text(sympy.latex(current_solution))  # Show raw LaTeX if rendering fails

                # Plot the solution if possible
                st.subheader("Graphe")
                sol_rhs = get_solution_rhs(current_solution, y_x)
                fig, error = create_solution_plot(sol_rhs, x_sym)

                if fig:
                    st.pyplot(fig)
                elif error:
                    st.info(error)
    else:
        st.info("Entrez une EDO et cliquez sur \"Résoudre\" pour calculer une solution.")


def show_intructions():
    st.markdown("""
        ### :material/info: Instructions :
        1.  Entrez votre EDO ci-dessous. Utilisez `y(x)` pour la fonction solution et `x` pour la variable.
            * Pour les dérivées, utilisez `Derivative(y(x), x)` pour $y'(x)$ et `Derivative(y(x), (x, n))` pour $y^(n)(x)$.
            * Vous pouvez écrire des équations comme `Eq(Derivative(y(x), x) + y(x), 0)` ou simplement l'expression `Derivative(y(x), x) + y(x)` (qui sera supposément égale à zéro).
        2.  L'application détectera l'ordre de l'équation et propose de rentrer des conditions initiales. Les réponses seront données avec des variables si aucune condition n'est précisée.
        4.  Appuyez sur "Résoudre" pour obtenir une solution et un graphe si possible.

        ### :material/assignment: Exemples :
        
        #### Équations linéaires de 1er ordre

        $y'(x) = -k y(x)$ : `Eq(Derivative(y(x), x), -k * y(x))`

        #### Oscillateurs

        $y''(x) + \omega^2 y(x) = 0$ : `Eq(Derivative(y(x), x, x) + omega**2 * y(x), 0)`

        $y''(x) + 2\zeta \omega y'(x) + \omega^2 y(x) = 0$ : `Eq(Derivative(y(x), x, x) + 2*zeta*omega*Derivative(y(x), x) + omega**2 * y(x), 0)`

        $y''(x) + 2\zeta \omega y'(x) + \omega^2 y(x) = F_0 \cos(\Omega x)$ : `Eq(Derivative(y(x), x, x) + 2*zeta*omega*Derivative(y(x), x) + omega**2 * y(x), F0 * cos(Omega * x))`

        #### Équations issues de la physique

        $m y''(x) = -mg - \gamma y'(x)$ : `Eq(m * Derivative(y(x), x, x), -m*g - gamma * Derivative(y(x), x))`

        $y'(x) = -\lambda y(x)$ : `Eq(Derivative(y(x), x), -lam * y(x))`

        $y'(x) = r y(x)\left(1 - \dfrac{y(x)}{K}\\right)$ : `Eq(Derivative(y(x), x), r * y(x) * (1 - y(x)/K))`

        #### Équations non linéaires

        $y''(x) + \dfrac{g}{L} \sin(y(x)) = 0$ : `Eq(Derivative(y(x), x, x) + (g/L) * sin(y(x)), 0)`

        $y''(x) - \mu (1 - y(x)^2)y'(x) + y(x) = 0$ : `Eq(Derivative(y(x), x, x) - mu * (1 - y(x)**2) * Derivative(y(x), x) + y(x), 0)`

        #### Équations spéciales

        $y'(x) + p(x)y(x) = q(x)y(x)^n$ (équation de Bernoulli) : `Eq(Derivative(y(x), x) + p(x)*y(x), q(x)*y(x)**n)`

        $y'(x) = a(x)y(x)^2 + b(x)y(x) + c(x)$ (équation de Riccati) : `Eq(Derivative(y(x), x), a(x)*y(x)**2 + b(x)*y(x) + c(x))`
        """)
    st.markdown("""---""")
    st.markdown("""Fait avec :streamlit: Streamlit et SymPy""")
