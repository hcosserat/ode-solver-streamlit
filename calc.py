import re

import sympy
from sympy import Function, Derivative, Eq, dsolve, symbols, S
from sympy import gamma as Gamma, zeta as Zeta, beta as Beta
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Setup for parsing expressions
transformations = standard_transformations + (implicit_multiplication_application,)
local_dict = {
    'x': symbols("x"),
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
local_dict.update({letter: Function(letter) for letter in "fghopqrstuvw"})
local_dict.update({str(s): s for s in symbols('gamma zeta beta omega mu rho sigma F0 Omega')})

# x is the independent variable
x_sym = local_dict["x"]
# f is the function f(x)
f_func_name = local_dict["f"]
f_x = f_func_name(x_sym)


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
    - f'(x), g'(x), h'(x), etc. to Derivative(f(x), (x, n))
    - f^(n)(x), g^(n)(x), etc. to Derivative(f(x), (x, n))
    - F(f, x) = G(f, x) to Eq(F(f, x), G(f, x))
    - a^b to a**b
    """
    # Handle f'(x), g'(x), etc. notation for any single letter function except x
    pattern1 = r"([a-wyzA-Z])('+)\(x\)"

    def replacement1(match):
        func_name = match.group(1)
        derivative_order = len(match.group(2))
        return f"Derivative({func_name}(x), (x, {derivative_order}))"

    # Handle f^(n)(x), g^(n)(x), etc. notation for any single letter function except x
    pattern2 = r"([a-wyzA-Z])\^?\((\d+)\)\(x\)"

    def replacement2(match):
        func_name = match.group(1)
        derivative_order = int(match.group(2))
        return f"Derivative({func_name}(x), (x, {derivative_order}))"

    processed_string = re.sub(pattern1, replacement1, ode_string)
    processed_string = re.sub(pattern2, replacement2, processed_string)

    # Handle natural equality notation
    if len(sides := processed_string.split("=")) == 2:
        processed_string = f"Eq({sides[0]}, {sides[1]})"

    # Handle exponentiation
    processed_string = processed_string.replace("^", "**")

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
    except ValueError as e:
        return None, f"Une erreur est survenue durant la résolution ({e})"
    except Exception as e:
        return None, f"Une erreur imprévue est survenue durant la résolution ({e})"


def compute_nth_derivative(eq, n):
    lhs = eq.lhs
    rhs = eq.rhs
    return Eq(sympy.diff(lhs, (x_sym, n)), sympy.diff(rhs, (x_sym, n)))
