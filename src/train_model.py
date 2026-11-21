import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

print("Loading clean data...")
df = pd.read_csv("data/processed/dengue_clean.csv")
df['date'] = pd.to_datetime(df['date'])

# Features (Must match exactly what is in the CSV now)
features = [
    'rainfall_mm', 'avg_temp_c', 'relative_humidity_pct', 
    'rain_lag_2w', 'rain_lag_4w', 'temp_rolling_4w', 'humidity_rolling_4w',
    'dengue_lag_1w', 'month', 'week'
]

# Chronological Split
train_df = df[df['date'] < '2025-01-01']
test_df = df[df['date'] >= '2025-01-01']

X_train, y_train = train_df[features], train_df['dengue_cases']
X_test, y_test = test_df[features], test_df['dengue_cases']

print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")

# Train LightGBM
print("Training LightGBM...")
model = lgb.LGBMRegressor(
    objective='poisson',
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31,
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))

print(f"✅ Validation MAE: {mae:.2f}")
print(f"✅ Validation RMSE: {rmse:.2f}")

# Save
joblib.dump(model, 'models/dengue_model.pkl')
with open("models/validation_metrics.txt", "w") as f:
    f.write(f"MAE: {mae:.2f}\nRMSE: {rmse:.2f}\n")
print("Model and metrics saved.")
print(f"✅ Training pipeline complete. Model serialized to models/dengue_model.pkl")
print(f"📊 Final Metrics -> MAE: {mae:.2f}, RMSE: {rmse:.2f}")
print("\n📊 Analyzing Feature Importance...")
importance = model.feature_importances_
feature_importance = pd.DataFrame({
    'Feature': features,
    'Importance': importance
}).sort_values(by='Importance', ascending=False)

# Save the feature importance to a file for the architecture report
feature_importance.to_csv("models/feature_importance.csv", index=False)
print("✅ Feature importance saved to models/feature_importance.csv")
print(f"Top Predictor: {feature_importance.iloc[0]['Feature']}")
