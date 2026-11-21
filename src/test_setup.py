import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import lightgbm as lgb
import statsmodels.api as sm
import optuna
import shap
import sklearn

print("✅ Packages installed successfully!")

# Read the raw data
df = pd.read_csv("data/raw/dengue_raw.csv")

print("\n📊 Data loaded!")
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print("\nNumber of unique cities:", df['city'].nunique())
print("Cities:", df['city'].unique())
print("\nNumber of unique wards:", df['ward_id'].nunique())
print("\nDate range:", df['date'].min(), "to", df['date'].max())