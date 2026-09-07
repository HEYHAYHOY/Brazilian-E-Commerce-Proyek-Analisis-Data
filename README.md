# Brazilian-E-Commerce-Proyek-Analisis-Data
gunakan pip install streamlit pada terminal
data saya langsung tarik dari kaggle

## Setup Environment - Anaconda
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt

## Setup Environment - Shell/Terminal
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt

## Run steamlit app
streamlit run streamlit_dashboard.py
