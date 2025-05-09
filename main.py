from ui import (
    setup_page,
    initialize_session_state,
    render_equation_input,
    render_initial_conditions,
    render_solve_button,
    display_solution
)


def main():
    # Setup the page
    setup_page()

    # Initialize session state
    initialize_session_state()

    # Render equation input
    render_equation_input()

    # Render initial conditions
    render_initial_conditions()

    # Render solve button
    render_solve_button()

    # Display solution
    display_solution()


if __name__ == "__main__":
    main()
