import numpy as np
import pandas as pd
from supabase import create_client, Client
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline
import os
from dotenv import load_dotenv

load_dotenv()

# Koneksi Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data(table_name, feature_columns, target_columns):
    try:
        target_columns_str = ','.join(target_columns)
        response = supabase.table(table_name).select(
            ','.join(feature_columns) + "," + target_columns_str
        ).execute()
        df = pd.DataFrame(response.data)
        df = df.sort_values(by=feature_columns[0])
        return df
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        raise

def enforce_monotonic_increase(predictions):
    """Memastikan nilai prediksi selalu naik"""
    adjusted = np.array(predictions.copy())
    for i in range(1, len(adjusted)):
        if adjusted[i] < adjusted[i-1]:
            # Jika turun, naikkan minimal 1% dari nilai sebelumnya
            adjusted[i] = adjusted[i-1] * 1.01
    return adjusted

def train_svm_model(feature_columns, target_column, data=None, table_name=None, filter_condition=None):
    """
    Versi fleksibel yang bisa terima:
    - DataFrame langsung (data)
    - Atau query dari Supabase (table_name + filter_condition)
    """
    try:
        # Jika data tidak diberikan, ambil dari Supabase
        if data is None:
            if table_name is None:
                raise ValueError("Harap berikan data atau table_name")
                
            query = supabase.table(table_name).select(','.join(feature_columns + [target_column]))
            
            if filter_condition:
                for col, val in filter_condition.items():
                    query = query.filter(col, val)
                    
            response = query.execute()
            df = pd.DataFrame(response.data)
        else:
            df = data
            
        # Pastikan data terurut
        df = df.sort_values(feature_columns[0])
        
        # Persiapan data training
        X = df[feature_columns].values.reshape(-1, 1)
        y = df[target_column].values
        
        # Pipeline model
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('svr', SVR(kernel='rbf', C=1000, epsilon=0.01, gamma=0.1))
        ])
        
        model.fit(X, y)
        
        # Evaluasi
        y_pred = model.predict(X)
        y_pred_adjusted = enforce_monotonic_increase(y_pred)
        
        mae = mean_absolute_error(y, y_pred_adjusted)
        mape = mean_absolute_percentage_error(y, y_pred_adjusted) * 100
        r2 = r2_score(y, y_pred_adjusted)
        
        return model, mae, mape, r2
        
    except Exception as e:
        print(f"Error in model training: {str(e)}")
        raise

def predict_population(years, model):
    try:
        if isinstance(years, (int, float)):
            years = np.array([[years]])
        elif isinstance(years, (list, np.ndarray)):
            years = np.array(years).reshape(-1, 1)
            
        # Dapatkan prediksi dasar
        raw_predictions = model.predict(years)
        
        # Sesuaikan untuk memastikan tren naik
        adjusted_predictions = enforce_monotonic_increase(raw_predictions)
        
        return np.round(adjusted_predictions, 2)
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        raise