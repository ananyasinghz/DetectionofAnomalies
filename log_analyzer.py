import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import re
import os

def parse_log_file(log_file):
    """Parse the anomaly detection log file into a structured DataFrame."""
    if not os.path.exists(log_file):
        print(f"Error: Log file {log_file} not found")
        return None
        
    data = []
    pattern = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - '
        r'(?P<level>\w+) - '
        r'(?P<message>.*)'
    )
    
    try:
        with open(log_file, 'r') as f:
            current_entry = None
            for line in f:
                line = line.rstrip()
                match = pattern.match(line)
                if match:
                    entry = match.groupdict()
                    # If this line starts an anomaly block, record it separately.
                    if "ANOMALY:" in entry['message']:
                        # Save the previous anomaly entry if any
                        if current_entry:
                            data.append(current_entry)
                        current_entry = entry
                        current_entry['detail_lines'] = []
                    else:
                        # If we're in the middle of an anomaly block, append the details.
                        if current_entry is not None:
                            current_entry['detail_lines'].append(line)
                        else:
                            data.append(entry)
                else:
                    # If the line doesn't match the pattern, assume it's part of the details.
                    if current_entry is not None:
                        current_entry['detail_lines'].append(line)
            # Append the last anomaly entry if exists
            if current_entry:
                data.append(current_entry)
    except Exception as e:
        print(f"Error parsing log file: {str(e)}")
        return None
    
    # Process detail lines for anomaly entries to extract metrics.
    for entry in data:
        if 'detail_lines' in entry and entry['detail_lines']:
            for detail in entry['detail_lines']:
                if detail.startswith("CPU:"):
                    try:
                        entry['cpu_usage'] = float(detail.split("CPU:")[1].strip().replace('%',''))
                    except:
                        pass
                elif detail.startswith("RAM:"):
                    try:
                        entry['memory_usage'] = float(detail.split("RAM:")[1].strip().replace('%',''))
                    except:
                        pass
                elif detail.startswith("Log Count:"):
                    try:
                        entry['log_count'] = int(detail.split("Log Count:")[1].strip())
                    except:
                        pass
                elif detail.startswith("Top Processes:"):
                    idx = entry['detail_lines'].index(detail)
                    entry['top_processes'] = "\n".join(entry['detail_lines'][idx+1:]).strip()
                    break
    return pd.DataFrame(data)

def analyze_processes(df_anomalies):
    """Analyze which processes most frequently appear in anomaly reports."""
    if df_anomalies.empty or 'top_processes' not in df_anomalies.columns:
        print("No process data found in anomalies.")
        return

    process_stats = {}
    for _, row in df_anomalies.iterrows():
        proc_text = row.get('top_processes', '')
        if isinstance(proc_text, str):
            for line in proc_text.splitlines():
                proc_name = line.strip().split()[0]  # assume the first word is the process name
                if proc_name:
                    process_stats[proc_name] = process_stats.get(proc_name, 0) + 1

    print("\n=== Top Anomaly Processes ===")
    sorted_procs = sorted(process_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for proc, count in sorted_procs:
        print(f"  {proc}: {count} times")

def analyze_logs():
    """Analyze and visualize log data."""
    print("\n=== Log Analysis Started ===")
    
    # Use anomalies.log (this is the file your anomaly detector creates)
    df = parse_log_file('anomalies.log')
    if df is None or df.empty:
        print("No data found in anomalies.log")
        return
        
    # Filter anomaly entries (those whose message contains "ANOMALY:")
    df_anomalies = df[df['message'].str.contains("ANOMALY:")]
    
    # Convert timestamp to datetime
    try:
        df['datetime'] = pd.to_datetime(df['timestamp'])
    except Exception as e:
        print(f"Timestamp conversion error: {e}")
        return
    if not df_anomalies.empty:
        try:
            df_anomalies['datetime'] = pd.to_datetime(df_anomalies['timestamp'])
        except Exception as e:
            print(f"Timestamp conversion error in anomalies: {e}")
    
    # Basic statistics
    print("\n=== Basic Statistics ===")
    total_entries = len(df)
    anomaly_count = len(df_anomalies)
    print(f"Total log entries: {total_entries}")
    print(f"Total anomalies detected: {anomaly_count}")
    if total_entries > 0:
        print(f"Anomaly rate: {anomaly_count/total_entries*100:.2f}%")
    
    # Process analysis
    analyze_processes(df_anomalies)
    
    # Create multiple time-series plots
    plt.figure(figsize=(14, 10))
    
    # Plot 1: CPU Usage Over Time
    plt.subplot(2, 2, 1)
    if 'cpu_usage' in df.columns:
        plt.plot(df['datetime'], df['cpu_usage'], 'b-', label='Normal', alpha=0.7)
        if not df_anomalies.empty and 'cpu_usage' in df_anomalies.columns:
            plt.plot(df_anomalies['datetime'], df_anomalies['cpu_usage'], 'ro', label='Anomaly')
        plt.title('CPU Usage Over Time')
        plt.ylabel('Percentage')
        plt.legend()
    else:
        plt.title('CPU Usage Data Not Available')
    
    # Plot 2: Memory Usage Over Time
    plt.subplot(2, 2, 2)
    if 'memory_usage' in df.columns:
        plt.plot(df['datetime'], df['memory_usage'], 'b-', label='Normal', alpha=0.7)
        if not df_anomalies.empty and 'memory_usage' in df_anomalies.columns:
            plt.plot(df_anomalies['datetime'], df_anomalies['memory_usage'], 'ro', label='Anomaly')
        plt.title('Memory Usage Over Time')
        plt.ylabel('Percentage')
        plt.legend()
    else:
        plt.title('Memory Usage Data Not Available')
    
    # Plot 3: Disk I/O Over Time
    plt.subplot(2, 2, 3)
    if 'disk_io' in df.columns:
        plt.plot(df['datetime'], df['disk_io'], 'b-', label='Normal', alpha=0.7)
        if not df_anomalies.empty and 'disk_io' in df_anomalies.columns:
            plt.plot(df_anomalies['datetime'], df_anomalies['disk_io'], 'ro', label='Anomaly')
        plt.title('Disk I/O Over Time')
        plt.ylabel('Read Count')
        plt.legend()
    else:
        plt.title('Disk I/O Data Not Available')
    
    # Plot 4: Network I/O Over Time
    plt.subplot(2, 2, 4)
    if 'network_io' in df.columns:
        plt.plot(df['datetime'], df['network_io'], 'b-', label='Normal', alpha=0.7)
        if not df_anomalies.empty and 'network_io' in df_anomalies.columns:
            plt.plot(df_anomalies['datetime'], df_anomalies['network_io'], 'ro', label='Anomaly')
        plt.title('Network I/O Over Time')
        plt.ylabel('Bytes Sent')
        plt.legend()
    else:
        plt.title('Network I/O Data Not Available')
    
    plt.tight_layout()
    plt.savefig('anomaly_analysis.png')
    print("\nAnalysis complete. Visualization saved as 'anomaly_analysis.png'")

if __name__ == "__main__":
    analyze_logs()
