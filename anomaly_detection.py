import json
import logging
import joblib
import pandas as pd
from datetime import datetime
from utils import get_system_metrics
from config import DETECTION_SETTINGS
import time
import colorama

colorama.init()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("anomaly_detection.log"),
        logging.StreamHandler()
    ]
)

def format_processes(process_list):
    lines = []
    for i, proc in enumerate(process_list, start=1):
        if proc.get("name", "").lower() == "system idle process":
            continue  # 🧹 Skip idle process
        name = proc.get("name", "Unknown")
        cpu = proc.get("cpu", 0.0)
        mem = proc.get("memory", 0.0)
        lines.append(f"  {i}. {name} ({cpu}% CPU, {mem}% RAM)")
    return "\n".join(lines) if lines else "  No relevant processes."

def main():
    try:
        model = joblib.load("isolation_forest_model.pkl")
        scaler = joblib.load("feature_scaler.pkl")
        logging.info("Model loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load model or scaler: {e}")
        return

    logging.info("Starting real-time monitoring with colored output...")

    try:
        while True:
            metrics = get_system_metrics()

            # Prepare features as a DataFrame with proper column names
            input_df = pd.DataFrame([{
                "cpu_usage": metrics["cpu_usage"],
                "memory_usage": metrics["memory_usage"],
                "disk_io_read": metrics["disk_io_read"],
                "disk_io_write": metrics["disk_io_write"],
                "network_io_sent": metrics["network_io_sent"],
                "network_io_received": metrics["network_io_received"],
                "log_count": metrics["log_count"]
            }])

            scaled_features = scaler.transform(input_df)
            prediction = model.predict(scaled_features)[0]

            is_anomaly = prediction == -1

            now = datetime.now().strftime("%H:%M:%S")
            if is_anomaly:
                print(f"{now} - \033[91m🚨 ANOMALY\033[0m - CPU: {metrics['cpu_usage']}% | RAM: {metrics['memory_usage']}% | "
                      f"Disk Read: {metrics['disk_io_read']} | Disk Write: {metrics['disk_io_write']} | "
                      f"Net Sent: {metrics['network_io_sent']} | Net Received: {metrics['network_io_received']} | LOGS: {metrics['log_count']}")

                print("\033[93m▼ SYSTEM DETAILS ▼\033[0m")
                print("\033[93m[TOP PROCESSES]\033[0m")
                print(format_processes(metrics.get("top_processes", {}).get("cpu", [])))
                print("\033[93m[RECENT LOGS]\033[0m")
                for log in metrics.get("system_logs", []):
                    print(f"  - {log}")
                print("-" * 40)

                # Log anomaly in plain format
                logging.warning("ANOMALY:\n"
                                f"CPU: {metrics['cpu_usage']}%\n"
                                f"RAM: {metrics['memory_usage']}%\n"
                                f"Disk IO Read: {metrics['disk_io_read']}\n"
                                f"Disk IO Write: {metrics['disk_io_write']}\n"
                                f"Network IO Sent: {metrics['network_io_sent']}\n"
                                f"Network IO Received: {metrics['network_io_received']}\n"
                                f"Log Count: {metrics['log_count']}\n"
                                f"Top Processes:\n{format_processes(metrics.get('top_processes', {}).get('cpu', []))}")

            time.sleep(DETECTION_SETTINGS.get("monitor_interval_seconds", 3))

    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

if __name__ == "__main__":
    main()
