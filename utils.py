import psutil
import win32evtlog
import time

def get_system_metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk_io = psutil.disk_io_counters()
    net_io = psutil.net_io_counters()

    processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                "name": proc.info['name'],
                "cpu": proc.info['cpu_percent'],
                "memory": proc.info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU usage
    top_cpu = sorted(processes, key=lambda x: x["cpu"], reverse=True)[:3]

    # Read latest system logs (Windows-specific)
    logs = []
    try:
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        for event in events[:3]:
            logs.append({
                "Log Name": "System",
                "Source": event.SourceName,
                "Event ID": event.EventID
            })
    except Exception:
        logs.append("Failed to fetch system logs.")

    return {
        "cpu_usage": cpu,
        "memory_usage": memory,
        "disk_io_read": disk_io.read_bytes,
        "disk_io_write": disk_io.write_bytes,
        "network_io_sent": net_io.bytes_sent,
        "network_io_received": net_io.bytes_recv,
        "log_count": len(logs),
        "top_processes": {
            "cpu": top_cpu
        },
        "system_logs": logs
    }
