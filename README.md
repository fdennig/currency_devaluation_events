# FX Risk Research

This repository contains the computations and code for the FX risk policy paper.

## Structure
- `notebooks/consolidated_currency_analysis.ipynb`: Main Jupyter notebook with explanations + computations
- `source/data_analysis_functions.py`: Core functions, loaded into notebook
- `data/`: Input datasets
- `requirements.txt`: Python dependencies

## Getting Started
```bash
# create and activate virtual env (recommended)
python -m venv .venv
source .venv/bin/activate   # on mac/linux
.venv\Scripts\activate      # on windows

# install deps
pip install -r requirements.txt

# start notebook
jupyter notebook notebooks/consolidated_currency_analysis.ipynb
```


