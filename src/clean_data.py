import pandas as pd
import numpy as np

print("Loading raw data...")
df = pd.read_csv("data/raw/dengue_raw.csv")

# 1. Fix corrupted city values
city_map = {'CCC': 'Chattogram', 'DNCC': 'Dhaka North', 'DSCC': 'Dhaka South', 'GCC': 'Gazipur', 'NCC': 'Narayanganj'}
for prefix, city_name in city_map.items():
    df.loc[df['city'].str.startswith(prefix, na=False), 'city'] = city_name

# 2. Drop constant columns
cols_to_drop = ['population_density_sqkm', 'water_logging_risk_index', 'sanitation_score']
df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

# 3. Parse dates & sort
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['city', 'ward_id', 'date']).reset_index(drop=True)

# 4. FEATURE ENGINEERING (Crucial for the Model)
print("Engineering features...")
# 2-week and 4-week rainfall lags per ward
df['rain_lag_2w'] = df.groupby('ward_id')['rainfall_mm'].shift(2)
df['rain_lag_4w'] = df.groupby('ward_id')['rainfall_mm'].shift(4)

# Rolling averages
df['temp_rolling_4w'] = df.groupby('ward_id')['avg_temp_c'].transform(lambda x: x.rolling(4).mean())
df['humidity_rolling_4w'] = df.groupby('ward_id')['relative_humidity_pct'].transform(lambda x: x.rolling(4).mean())

# Lagged dengue cases
df['dengue_lag_1w'] = df.groupby('ward_id')['dengue_cases'].shift(1)

# Time features
df['month'] = df['date'].dt.month
df['week'] = df['date'].dt.isocalendar().week.astype(int)

# Drop rows with NaN (from the lags)
df = df.dropna().reset_index(drop=True)

# 5. Save
df.to_csv("data/processed/dengue_clean.csv", index=False)
print(f"✅ Clean data with engineered features saved! Shape: {df.shape}")