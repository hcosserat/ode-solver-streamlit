import sympy
from sympy import Function, Derivative, Eq, dsolve, symbols, S
from sympy import gamma as Gamma, zeta as Zeta, beta as Beta
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

# --- SymPy Setup ---
# x is the independent variable
x_sym = symbols('x')
# f is the function f(x)
f_func_name = Function('f')
f_x = f_func_name(x_sym)

# Setup for parsing expressions
transformations = standard_transformations + (implicit_multiplication_application,)
local_dict = {
    'f': f_func_name,
    'x': x_sym,
    'Eq': Eq,
    'Derivative': Derivative,
    'sin': sympy.sin,
    'cos': sympy.cos,
    'exp': sympy.exp,
    'ln': sympy.ln,
    'log': sympy.log,
    'sqrt': sympy.sqrt,
    'pi': sympy.pi,
    'E': sympy.E,
    'S': S,
    "Gamma": Gamma,
    "Zeta": Zeta,
    "Beta": Beta,
}

local_dict.update({str(s): s for s in symbols('gamma zeta beta lambda omega mu rho sigma F0 Omega')})


def get_ode_order(equation, func):
    """Determines the order of the ODE with respect to func."""
    if equation is None:
        return 0

    max_order = 0
    # Check both sides of the equation if it's an Eq object
    if isinstance(equation, Eq):
        expr_to_check = [equation.lhs, equation.rhs]
    else:
        expr_to_check = [equation]

    for expr in expr_to_check:
        for atom in expr.atoms(Derivative):
            if atom.expr == func:
                current_order = 0
                for var_info in atom.args[1:]:
                    if isinstance(var_info, sympy.core.containers.Tuple):
                        diff_var, order = var_info
                        if diff_var == x_sym:
                            current_order += order
                    else:
                        diff_var = var_info
                        if diff_var == x_sym:
                            current_order += 1

                max_order = max(max_order, current_order)

    return max_order


def get_solution_rhs(solution, func):
    """Extracts the RHS of the solution if it's an Eq, otherwise returns the solution."""
    if isinstance(solution, Eq) and solution.lhs == func:
        return solution.rhs
    elif isinstance(solution, list) and solution:
        if isinstance(solution[0], Eq) and solution[0].lhs == func:
            return solution[0].rhs
    return None


def prepare_ode_input(ode_string: str):
    """
    Preprocesses ODE input by converting:
    - f'(x), f''(x), etc. to Derivative(f(x), (x, n))
    - f^(n)(x) to Derivative(f(x), (x, n))
    - F(f, x) = G(f, x) to Eq(F(f, x), G(f, x))
    """
    # Handle f'(x), f''(x) notation
    pattern1 = r"f('+)\(x\)"

    def replacement1(match):
        derivative_order = len(match.group(1))
        return f"Derivative(f(x), (x, {derivative_order}))"

    # Handle f^(n)(x) notation
    pattern2 = r"f\^?\((\d+)\)\(x\)"

    def replacement2(match):
        derivative_order = int(match.group(1))
        return f"Derivative(f(x), (x, {derivative_order}))"

    processed_string = re.sub(pattern1, replacement1, ode_string)
    processed_string = re.sub(pattern2, replacement2, processed_string)

    # Handle natural equality notation
    if len(sides := processed_string.split("=")) == 2:
        processed_string = f"Eq({sides[0]}, {sides[1]})"

    return processed_string


def parse_ode(ode_string):
    """Parse an ODE string into a sympy equation."""
    if not ode_string:
        return None, None, "Équation vide"

    ode_string = prepare_ode_input(ode_string)

    try:
        parsed_ode = parse_expr(ode_string, local_dict=local_dict, transformations=transformations)

        if not isinstance(parsed_ode, Eq):
            # If user just entered an expression, assume it's LHS = 0
            ode_eq = Eq(parsed_ode, 0)
        else:
            ode_eq = parsed_ode

        ode_order = get_ode_order(ode_eq, f_x)
        return ode_eq, ode_order, ""
    except Exception as e:
        return None, 0, f"Erreur de parsing, verifiez la syntaxe ({e})."


def solve_ode(ode_eq, ics_dict=None):
    """Solve the ODE with optional initial conditions."""
    try:
        if ics_dict:
            solution = dsolve(ode_eq, f_x, ics=ics_dict)
        else:
            solution = dsolve(ode_eq, f_x)
        return solution, ""
    except NotImplementedError:
        return None, "L'équation n'est pas supportée par l'application pour le moment."
    except Exception as e:
        return None, f"Une erreur est survenue durant la résolution : {e}"
