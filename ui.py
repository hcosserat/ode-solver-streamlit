import pyperclip
import streamlit as st
import sympy

from plotter import create_solution_plot
from solver import x_sym, f_x, parse_ode, solve_ode, get_solution_rhs


def setup_page():
    """Initial page configuration."""
    st.set_page_config(layout="wide")
    st.title("Solveur d'équations différentielles ordinaires")


def initialize_session_state():
    """Initialize the session state variables."""
    if 'ode_string' not in st.session_state:
        st.session_state.ode_string = "f'(x) - 3*f(x) = cos(x)"
    if 'ode_parsed_successfully' not in st.session_state:
        st.session_state.ode_parsed_successfully = True
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

    st.session_state.ode_eq = ode_eq

    if error_message:
        st.sidebar.error(error_message)
        st.session_state.ode_parsed_successfully = False
        st.session_state.ode_eq = None
        st.session_state.ode_order = 0
    else:
        st.session_state.ode_parsed_successfully = True
        st.session_state.ode_order = ode_order
        try:
            st.sidebar.latex(sympy.latex(st.session_state.ode_eq))
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
                deriv_label = "f" + "".join(["'" for _ in range(i)])
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
                ics_dict[f_x.subs(x_sym, x_val)] = y_val
            else:
                # Condition for n-th derivative y^(n)(x0)
                ics_dict[f_x.diff((x_sym, i)).subs(x_sym, x_val)] = y_val
    return ics_dict


def render_solve_button():
    """Render the solve button and handle solving."""
    ode_ready_to_be_solved = st.session_state.ode_eq is not None and st.session_state.ode_parsed_successfully
    if st.sidebar.button("Résoudre", type="primary", use_container_width=True,
                         disabled=(not ode_ready_to_be_solved)):

        if ode_ready_to_be_solved:
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
    if st.session_state.solution is not None:
        col1, col2 = st.columns([10, 1], vertical_alignment="bottom")  # col1 for header, col2 for "copy" button

        with col1:
            st.header(":material/lightbulb: Solution")

        if isinstance(st.session_state.solution, str):  # Error message
            st.error(st.session_state.solution)

        elif st.session_state.solution is None:  # Empty list or None if dsolve fails quietly
            st.warning("Aucune solution n'a été trouvée, l'équation est peut-être triviale (par exemple 0=0).")

        else:
            current_solution = st.session_state.solution

            if isinstance(current_solution, list):
                st.info(f"Plusieurs ({len(current_solution)}) solutions ont été trouvées :")
                for solution in current_solution:
                    try:
                        st.latex(sympy.latex(solution))
                    except Exception as e:
                        st.warning(f"Échec du rendu LaTeX : {e}")
                        st.text(sympy.latex(solution))  # Show raw LaTeX if rendering fails
            else:
                try:
                    st.latex(sympy.latex(current_solution))
                except Exception as e:
                    st.warning(f"Échec du rendu LaTeX : {e}")
                    st.text(sympy.latex(current_solution))  # Show raw LaTeX if rendering fails

                with col2:
                    with st.popover(":material/content_copy:"):
                        if st.button("LaTeX", type="tertiary"):
                            pyperclip.copy(sympy.latex(current_solution))
                        if st.button("Texte", type="tertiary"):
                            pyperclip.copy(f"f(x) = {current_solution.rhs}")

                # Plot the solution if possible
                st.subheader("Graphe")
                sol_rhs = get_solution_rhs(current_solution, f_x)
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
        1.  Entrez votre EDO ci-dessous. Utilisez `f(x)` pour la fonction solution et `x` pour la variable.
            * Pour les dérivées, vous pouvez utiliser `f'''(x)`, `f^(3)(x)` ou `Derivative(f(x), (x, 3))`
            * Vous pouvez écrire des équations comme `f'(x) + f(x) = 0` ou simplement l'expression `f'(x) + f(x)` (qui sera supposément égale à zéro).
        2.  L'application détectera l'ordre de l'équation et propose de rentrer des conditions initiales. Les réponses seront données avec des variables si aucune condition n'est précisée.
        4.  Appuyez sur "Résoudre" pour obtenir une solution et un graphe si possible.

        ### :material/assignment: Exemples :
        
        #### Équations linéaires de 1er ordre

        $f'(x) = -k f(x)$ : `f'(x) = -k*f(x)`

        #### Oscillateurs

        $f''(x) + \omega^2 f(x) = 0$ : `f''(x) + omega^2 * f(x)`

        $f''(x) + 2\zeta \omega f'(x) + \omega^2 f(x) = 0$ : `f''(x) + 2 * zeta * omega * f'(x) + omega^2 * f(x)`

        $f''(x) + 2\zeta \omega f'(x) + \omega^2 f(x) = F_0 \cos(\Omega x)$ : `f''(x) + 2 * zeta * omega * f'(x) + omega^2 * f(x) = F0 * cos(Omega * x)`

        #### Équations issues de la physique

        $m f''(x) = -mg - \gamma f'(x)$ : `m * f''(x) = -mg - gamma * f'(x)`

        $f'(x) = -\\rho f(x)$ : `f'(x) = -rho * f(x)`

        $f'(x) = r f(x)\left(1 - \dfrac{f(x)}{K}\\right)$ : `f'(x) = r * f(x) * (1 - f(x)/K)`

        #### Équations non linéaires

        $f''(x) + \dfrac{g}{L} \sin(f(x)) = 0$ : `f''(x) + (g/L) * sin(f(x))`

        $f''(x) - \mu (1 - f(x)^2)f'(x) + f(x) = 0$ : `f''(x) - mu * (1 - f(x)**2) * f'(x) + f(x)`

        #### Équations spéciales

        $f'(x) + p(x)f(x) = q(x)f(x)^n$ (équation de Bernoulli), par exemple : `f'(x) + 2*f(x)/x = f(x)^3`

        $f'(x) = a(x)f(x)^2 + b(x)f(x) + c(x)$ (équation de Riccati), par exemple : `f(x) = cos(x)*f(x)**2 - f(x)/(x^2) + 2`
        """)
    st.markdown("""---""")
    st.markdown("""Fait avec :streamlit: Streamlit, SymPy et Matplotlib""")
