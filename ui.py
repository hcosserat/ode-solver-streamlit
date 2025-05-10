import pyperclip
import streamlit as st
import sympy

from plotter import create_solution_plot
from solver import x_sym, f_x, parse_ode, solve_ode, get_solution_rhs
from utils import show_error


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
    if 'is_system' not in st.session_state:
        st.session_state.is_system = False
    if 'system_equations' not in st.session_state:
        st.session_state.system_equations = []
    if 'system_funcs' not in st.session_state:
        st.session_state.system_funcs = []


def render_equation_input():
    """Render the ODE input section."""
    st.sidebar.header("Équation")
    st.session_state.ode_string = st.sidebar.text_input(
        "Entrez votre EDO :",
        value=st.session_state.ode_string,
        icon=":material/function:"
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


def render_system_input():
    """Render the system of ODEs input section."""
    if st.session_state.is_system:
        st.sidebar.header("Système d'EDO")

        # Display existing equations
        for i, eq in enumerate(st.session_state.system_equations):
            cols = st.sidebar.columns([8, 1], vertical_alignment="bottom")
            with cols[0]:
                updated_eq = st.text_input(
                    f"Équation {i + 1}",
                    value=eq,
                    key=f"system_eq_{i}"
                )

                ode_eq, _, error_message = parse_ode(updated_eq)

                if error_message:
                    st.sidebar.error(error_message)
                else:
                    try:
                        st.sidebar.latex(sympy.latex(ode_eq))
                    except Exception as e:
                        st.sidebar.warning(f"Échec du rendu LaTeX : {e}")

                st.session_state.system_equations[i] = updated_eq
            with cols[1]:
                if st.button("🗑", key=f"delete_eq_{i}"):
                    st.session_state.system_equations.pop(i)
                    st.session_state.system_funcs.pop(i)
                    st.rerun()

        # Add new equation button
        if st.sidebar.button("Ajouter une équation", use_container_width=True):
            # Generate next function name (g, h, p, q, etc. after f)
            func_names = ['f', 'g', 'h', 'p', 'q', 'r', 's', 't']
            next_idx = len(st.session_state.system_funcs)
            if next_idx < len(func_names):
                next_func_name = func_names[next_idx]
            else:
                next_func_name = f"f{next_idx}"

            # Create new function symbol
            next_func = sympy.Function(next_func_name)(x_sym)
            st.session_state.system_funcs.append(next_func)

            # Add empty equation template
            st.session_state.system_equations.append(f"{next_func_name}'(x) = 0")
            st.rerun()


def render_solve_button():
    """Render the solve button and handle solving."""
    ode_ready_to_be_solved = st.session_state.ode_eq is not None and st.session_state.ode_parsed_successfully

    solve_button = st.sidebar.button("Résoudre", type="primary", use_container_width=True,
                                     disabled=(not ode_ready_to_be_solved))
    system_button = st.sidebar.button(":gray[:material/list_alt: Système]", type="tertiary", use_container_width=True)

    # Handle system button click
    if system_button:
        st.session_state.is_system = True
        # Add the first equation to the system
        if st.session_state.ode_eq is not None:
            st.session_state.system_equations = [st.session_state.ode_string]
            st.session_state.system_funcs = [f_x]  # Start with f(x)
        st.rerun()

    if solve_button:
        solve_single_ode()


def render_solve_system_button():
    """Render the solve button and handle solving, for systems."""
    ode_ready_to_be_solved = (st.session_state.ode_eq is not None
                              and st.session_state.ode_parsed_successfully
                              and len(st.session_state.system_equations) > 1)

    solve_button = st.sidebar.button("Résoudre", type="primary", use_container_width=True,
                                     disabled=(not ode_ready_to_be_solved))
    quit_system_button = st.sidebar.button(":gray[:material/close: Quitter le mode Système]", type="tertiary", use_container_width=True)

    # Handle quit system button click
    if quit_system_button:
        st.session_state.is_system = False
        st.session_state.system_equations = []
        st.session_state.system_funcs = []
        st.rerun()

    if solve_button:
        solve_system()


def solve_single_ode():
    """Solve a single ODE."""
    ode_ready_to_be_solved = st.session_state.ode_eq is not None and st.session_state.ode_parsed_successfully

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
        show_error("Entrez une EDO valide avant de résoudre.", "ode_ready_to_be_solved is False", "solve_single_ode")


def solve_system():
    """Solve a system of ODEs."""
    try:
        # Parse all equations in the system
        system_eqs = []
        for eq_str in st.session_state.system_equations:
            eq, _, error = parse_ode(eq_str)
            if error:
                show_error(f"Erreur dans l'équation: {eq_str}", error, "solve_system")
                return
            system_eqs.append(eq)

        # Build the function list
        func_list = st.session_state.system_funcs

        with st.spinner("Résolution du système..."):
            solution = sympy.solvers.ode.systems.dsolve_system(system_eqs, func_list)
            st.session_state.solution = solution

    except Exception as e:
        show_error(f"Erreur lors de la résolution du système", e, "solve_system")
        st.session_state.solution = f"Erreur: {e}"


def display_solution():
    """Display the solution and plot if available."""
    solution = st.session_state.solution

    if solution is not None:
        st.header(":material/lightbulb: Solution")

        if isinstance(solution, str):
            show_error(solution, "st.session_state.solution is str", "display_solution")

        elif solution is None or solution == []:
            st.warning("Aucune solution n'a été trouvée, l'équation est peut-être triviale (par exemple 0=0).")

        elif st.session_state.is_system:
            display_system_solution(solution)

        elif isinstance(solution, list):
            display_solutions(solution)

        else:
            display_solutions([solution])
    else:
        st.info("Entrez une EDO et cliquez sur \"Résoudre\" pour calculer une solution.")


def display_system_solution(solution):
    """Display solution for a system of ODEs."""
    multiple_solutions = len(solution) > 1

    if multiple_solutions:
        st.info(f"Plusieurs ({len(solution)}) solutions ont été trouvées pour le système")

    for i, sol_set in enumerate(solution):
        if multiple_solutions:
            st.subheader(f"Solution {i + 1}")

        if isinstance(sol_set, list):
            for j, sol in enumerate(sol_set):
                empty_col, latex_col, action_col = st.columns([1, 8, 1])

                try:
                    latex_col.latex(sympy.latex(sol))
                except Exception as e:
                    latex_col.warning(f"Échec du rendu LaTeX : {e}")
                    latex_col.text(str(sol))

                with action_col.popover(""):
                    if st.button("Copier LaTeX", type="tertiary", key=f"latex-copy-{i}-{j}"):
                        pyperclip.copy(sympy.latex(sol))
                    if st.button("Copier texte", type="tertiary", key=f"text-copy-{i}-{j}"):
                        pyperclip.copy(str(sol))


def display_solutions(solutions):
    multiple_solutions = len(solutions) > 1

    if multiple_solutions:
        st.info(f"Plusieurs ({len(solutions)}) solutions ont été trouvées")
        solution_to_graph = None
    else:
        solution_to_graph = solutions[0]

    for i, solution in enumerate(solutions):
        if multiple_solutions:
            st.subheader(f"Solution {i + 1}")

        empty_col, latex_col, action_col = st.columns([1, 8, 1], vertical_alignment="bottom")

        try:
            latex_col.latex(sympy.latex(solution))
        except Exception as e:
            latex_col.warning(f"Échec du rendu LaTeX : {e}")
            latex_col.text(sympy.latex(solution))  # Show raw LaTeX if rendering fails

        with action_col.popover(""):
            if st.button("Copier le LaTeX", type="tertiary", key=f"latex-copy-{solution}"):
                pyperclip.copy(sympy.latex(solutions))
            if st.button("Copier le texte", type="tertiary", key=f"text-copy-{solution}"):
                pyperclip.copy(f"f(x) = {solutions.rhs}")
            if multiple_solutions and st.button("Tracer", type="tertiary", key=f"graph-{solution}"):
                solution_to_graph = solution

    if solution_to_graph is not None:
        st.subheader("Graphe")
        sol_rhs = get_solution_rhs(solution_to_graph, f_x)
        fig, error = create_solution_plot(sol_rhs, x_sym)
        if fig:
            st.pyplot(fig)
        elif error:
            st.info(error)


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
