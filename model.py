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
        # Fetch data from Supabase
        response = supabase.table(table_name).select("*").execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Ensure all required columns exist
            required_columns = feature_columns + target_columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing columns in {table_name}: {missing_columns}")
            
            return df
        else:
            raise ValueError(f"No data found in table {table_name}")
            
    except Exception as e:
        print(f"Error fetching data from {table_name}: {str(e)}")
        raise

def train_svm_model(feature_columns, target_column, data=None, table_name=None, filter_condition=None):
    """
    Versi fleksibel yang bisa terima:
    - DataFrame langsung (data)
    - Atau query dari Supabase (table_name + filter_condition)
    """
    try:
        # Get data
        if data is not None:
            df = data
        elif table_name is not None:
            df = fetch_data(table_name, feature_columns, [target_column])
        else:
            raise ValueError("Either data or table_name must be provided")
        
        # Prepare features and target
        X = df[feature_columns].values
        y = df[target_column].values
        
        # Pipeline model
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('svr', SVR(kernel='linear', C=250, epsilon=0.01))
        ])
        
        model.fit(X, y)
        
        # Evaluasi
        y_pred = model.predict(X)
        
        mae = mean_absolute_error(y, y_pred)
        mape = mean_absolute_percentage_error(y, y_pred) * 100
        r2 = r2_score(y, y_pred)
        
        return model, mae, mape, r2
        
    except Exception as e:
        print(f"Error in train_svm_model: {str(e)}")
        raise

def predict_population(years, model):
    """
    Predict population for given years using trained model
    """
    try:
        # Ensure years is 2D array
        if len(years.shape) == 1:
            years = np.array(years).reshape(-1, 1)
        
        # Get predictions
        predictions = model.predict(years)
        
        return np.round(predictions, 2)
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        raise