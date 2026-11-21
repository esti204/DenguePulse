# System Architecture & Design Choices

## 1. Data Flow
1. **Data Ingestion:** The raw dataset (`dengue_raw.csv`) is loaded locally.
2. **Cleaning Pipeline (`src/clean_data.py`):** Fixes corrupted city names, drops constant columns, and parses datetime objects.
3. **Feature Engineering (`src/train_model.py`):** Computes multi-week grouped lags (2-week and 4-week rainfall lags) per `ward_id`, along with rolling averages for temperature and humidity. 
4. **Model Training:** A LightGBM Regressor is trained on a chronological split (Train: pre-2025, Test: 2025) using a Poisson objective (optimal for count data like dengue cases).
5. **Serialization:** The trained model is saved as `models/dengue_model.pkl` using `joblib`.
6. **Frontend (`app.py`):** A Streamlit Web Dashboard loads the serialized model and cleaned data to provide interactive outbreak risk predictions to the user.

## 2. Design Choices & Justification
- **Chronological Validation Split:** Because this is time-series data, a random train/test split would cause data leakage (using future data to predict the past). We strictly split the data chronologically (Training on data before 2025, testing on 2025 data) to ensure real-world forecasting reliability.
- **LightGBM with Poisson Objective:** Dengue cases are non-negative count data. Standard regression (MSE) can predict negative cases, which is impossible. The Poisson objective handles zero-inflated, count-based distributions perfectly.
- **Grouped Multi-Week Lags:** The brief mandated computing 2–4 week rainfall lags grouped by `ward_id`. We engineered `rain_lag_2w` and `rain_lag_4w` to capture the biological lag between mosquito breeding (due to rain) and the onset of human dengue symptoms.

## 3. Efficiency (Computational & Token)
- **Local Inference:** The model is serialized to a `.pkl` file. This allows the Streamlit dashboard to perform predictions locally in less than 1 second, requiring zero API calls or token costs during inference.
- **Data Caching:** The Streamlit dashboard uses `@st.cache_resource` to load the model and data into memory exactly once, ensuring fast UI interactions.

## 4. Resilience
- **Graceful Handling:** If the serialized model file is missing, the dashboard will catch the error and display a user-friendly warning rather than crashing.
- ## 5. Future Enhancements (Phase 2)
- Implement a PostgreSQL database for real-time doctor schedule updates.
- Integrate SMS alerts for high-risk outbreak wards.
