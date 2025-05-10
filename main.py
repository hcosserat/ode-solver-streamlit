import streamlit as st

from ui import (
    setup_page,
    initialize_session_state,
    render_equation_input,
    render_system_input,
    render_solve_system_button,
    render_initial_conditions,
    render_solve_button,
    display_solution, show_intructions,
)


def main():
    setup_page()
    initialize_session_state()

    if st.session_state.is_system:
        render_system_input()
        render_solve_system_button()
    else:
        render_equation_input()
        render_solve_button()
        render_initial_conditions()

    display_solution()
    show_intructions()


if __name__ == "__main__":
    main()
