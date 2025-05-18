# Résolveur d'Équations Différentielles Ordinaires

Ce projet est une application Streamlit permettant de résoudre des équations différentielles ordinaires grâce à SymPy.

## Accès en ligne

L’application est disponible en ligne à l’adresse suivante :  
[ode-solver-pidr.streamlit.app](https://ode-solver-pidr.streamlit.app/)

Aucune installation n'est nécessaire pour utiliser la version en ligne.

## Exécution locale

### Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)

### Installation

1. Clonez ce dépôt
   ```bash
   git clone https://github.com/hcosserat/ode-solver-streamlit.git
   cd ode-solver-streamlit
   ```
2. Installez les dépendences
   ```bash
   pip install -r requirements.txt
   ```
3. Lancez l'application
   ```bash
   streamlit run main.py
   ```

### Fonctionnalités

Cette application permet de :

- Résoudre des équations différentielles ordinaires
- Visualiser les solutions graphiquement
- Calculer les dérivées d'ordre supérieur
- Exporter les équations vers GeoGebra 

Développé avec Streamlit, SymPy et Matplotlib dans le cadre du PIDR.
