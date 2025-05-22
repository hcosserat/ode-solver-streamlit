import os
import threading
import webview


def start_streamlit():
    os.system("streamlit run main.py --server.headless true")


threading.Thread(target=start_streamlit, daemon=True).start()

webview.create_window("Solveur d'EDO", "http://localhost:8501", maximized=True)
webview.start()
