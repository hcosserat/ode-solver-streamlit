import streamlit


def show_error(msg, error, function):
    streamlit.error(msg)
    print(f"{function} | {msg} : {error}")
