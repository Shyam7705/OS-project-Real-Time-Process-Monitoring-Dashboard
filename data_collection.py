import psutil
import time
from threading import Thread

class ProcessDataCollector:
    def __init__(self):
        self.last_cpu_update = 0
        self.cpu_data_cache = {}
        self.processes = []
        self.is_collecting = False

    def get_process_data(self):
        if self.is_collecting:
            return self.processes

        self.is_collecting = True
        thread = Thread(target=self._collect_data)
        thread.daemon = True
        thread.start()
        return self.processes

    def _collect_data(self):
        processes = []
        current_time = time.time()
        update_cpu = (current_time - self.last_cpu_update) >= 5

        for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info', 'create_time']):
            try:
                pid = proc.info['pid']
                process_info = {
                    'pid': pid,
                    'name': proc.info['name'] or 'Unknown',
                    'state': proc.info['status'],
                    'cpu_percent': 0.0,
                    'memory_mb': proc.info['memory_info'].rss / (1024 * 1024),
                    'start_time': proc.info['create_time']
                }
                if update_cpu:
                    process_info['cpu_percent'] = proc.cpu_percent(interval=None)
                    self.cpu_data_cache[pid] = process_info['cpu_percent']
                else:
                    process_info['cpu_percent'] = self.cpu_data_cache.get(pid, 0.0)
                processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        self.processes = processes
        if update_cpu:
            self.last_cpu_update = current_time
        self.is_collecting = False