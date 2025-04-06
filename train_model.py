import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from config import DETECTION_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_training.log'),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starting model training...")

    try:
        # Load dataset
        df = pd.read_csv("baseline_data.csv")

        # Expected features
        feature_columns = [
            'cpu_usage',
            'memory_usage',
            'disk_io_read',
            'disk_io_write',
            'network_io_sent',
            'network_io_received',
            'log_count'
        ]

        # Check if all features exist
        if not all(col in df.columns for col in feature_columns):
            missing = [col for col in feature_columns if col not in df.columns]
            logging.error(f"Missing necessary feature columns: {missing}")
            return

        # Drop timestamp and other non-feature columns
        df = df[feature_columns]

        # Scale the features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)

        # Train Isolation Forest
        contamination = DETECTION_SETTINGS.get("contamination", 0.0001)
        logging.info(f"Training Isolation Forest with contamination={contamination}")

        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled)

        # Save model and scaler
        joblib.dump(model, "isolation_forest_model.pkl")
        joblib.dump(scaler, "feature_scaler.pkl")
        logging.info("Model and scaler saved successfully.")

    except Exception as e:
        logging.error(f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
