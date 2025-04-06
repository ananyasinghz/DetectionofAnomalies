import psutil
import pandas as pd
import time
import logging
import platform
import subprocess
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)

def get_system_data():
    """Get system logs and top processes with improved error handling"""
    try:
        if platform.system() == "Windows":
            cmd = '''wevtutil qe System /q:"*[System[(Level=1 or Level=2)]]" /c:5 /rd:true /f:text'''
            logs = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, encoding='utf-8', errors='ignore').splitlines()
        elif platform.system() == "Linux":
            cmd = "journalctl -p crit..err -n 5 --no-pager --utc"
            logs = subprocess.check_output(cmd, shell=True, encoding='utf-8').splitlines()
        else:
            logs = ["Unsupported OS"]
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': round(proc.info['cpu_percent'], 1),
                    'memory': round(proc.info['memory_percent'], 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'logs': logs[:5],
            'top_cpu': sorted(processes, key=lambda x: x['cpu'], reverse=True)[:3],
            'top_mem': sorted(processes, key=lambda x: x['memory'], reverse=True)[:3]
        }
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e.output}")
        return {'logs': ["Error: Log retrieval failed"], 'top_cpu': [], 'top_mem': []}
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {'logs': ["Error: Data collection failed"], 'top_cpu': [], 'top_mem': []}

def collect_metrics():
    """Collect all system metrics with process data"""
    system_data = get_system_data()
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_io_read': psutil.disk_io_counters().read_count,
        'disk_io_write': psutil.disk_io_counters().write_count,
        'network_io_sent': psutil.net_io_counters().bytes_sent,
        'network_io_received': psutil.net_io_counters().bytes_recv,
        'log_count': len(system_data['logs']),
        'log_samples': json.dumps({
            'system_logs': system_data['logs'],
            'top_processes': {
                'cpu': system_data['top_cpu'],
                'memory': system_data['top_mem']
            }
        }, ensure_ascii=False)
    }

def main():
    logging.info("Collecting 1000 samples with process data...")
    data = []
    
    try:
        for i in range(1000):
            metrics = collect_metrics()
            data.append(metrics)
            
            sample = json.loads(metrics['log_samples'])
            logging.info(
                f"Sample {i+1}: "
                f"CPU={metrics['cpu_usage']}% | "
                f"Top Process: {sample['top_processes']['cpu'][0]['name'] if sample['top_processes']['cpu'] else 'None'}"
            )
            
            time.sleep(1)
            
        df = pd.DataFrame(data)
        df.to_csv("baseline_data.csv", index=False, encoding='utf-8-sig')
        logging.info("Data collection complete with process info")
        
    except Exception as e:
        logging.error(f"Collection failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
