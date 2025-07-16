import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List

class TaskScheduler:
    """Simple task scheduler for the bot"""
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.running = False
        self.thread = None
    
    def add_periodic_task(self, func: Callable, interval_seconds: int, name: str = ""):
        """Add a periodic task that runs every interval_seconds"""
        task = {
            "func": func,
            "type": "periodic",
            "interval": interval_seconds,
            "last_run": None,
            "name": name or func.__name__
        }
        self.tasks.append(task)
    
    def add_daily_task(self, func: Callable, hour: int, minute: int = 0, name: str = ""):
        """Add a task that runs daily at specified time"""
        task = {
            "func": func,
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "last_run_date": None,
            "name": name or func.__name__
        }
        self.tasks.append(task)
    
    def add_hourly_task(self, func: Callable, hours: List[int], minute: int = 0, name: str = ""):
        """Add a task that runs at specific hours each day"""
        task = {
            "func": func,
            "type": "hourly",
            "hours": hours,
            "minute": minute,
            "last_runs": {},
            "name": name or func.__name__
        }
        self.tasks.append(task)
    
    def _should_run_periodic(self, task: Dict) -> bool:
        """Check if periodic task should run"""
        if task["last_run"] is None:
            return True
        
        elapsed = time.time() - task["last_run"]
        return elapsed >= task["interval"]
    
    def _should_run_daily(self, task: Dict) -> bool:
        """Check if daily task should run"""
        now = datetime.now()
        today = now.date()
        
        # Check if it's the right time
        if now.hour != task["hour"] or now.minute != task["minute"]:
            return False
        
        # Check if already run today
        return task["last_run_date"] != today
    
    def _should_run_hourly(self, task: Dict) -> bool:
        """Check if hourly task should run"""
        now = datetime.now()
        current_hour = now.hour
        
        # Check if it's the right time
        if current_hour not in task["hours"] or now.minute != task["minute"]:
            return False
        
        # Check if already run this hour today
        today_hour_key = f"{now.date()}-{current_hour}"
        return today_hour_key not in task["last_runs"]
    
    def _run_task(self, task: Dict):
        """Execute a task safely"""
        try:
            print(f"⚡ Running task: {task['name']}")
            task["func"]()
            
            # Update last run time
            now = datetime.now()
            if task["type"] == "periodic":
                task["last_run"] = time.time()
            elif task["type"] == "daily":
                task["last_run_date"] = now.date()
            elif task["type"] == "hourly":
                today_hour_key = f"{now.date()}-{now.hour}"
                task["last_runs"][today_hour_key] = now
                
                # Clean old entries (keep only last 7 days)
                cutoff_date = now.date() - timedelta(days=7)
                task["last_runs"] = {
                    k: v for k, v in task["last_runs"].items()
                    if v.date() >= cutoff_date
                }
                
        except Exception as e:
            print(f"❌ Error running task {task['name']}: {e}")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                for task in self.tasks:
                    should_run = False
                    
                    if task["type"] == "periodic":
                        should_run = self._should_run_periodic(task)
                    elif task["type"] == "daily":
                        should_run = self._should_run_daily(task)
                    elif task["type"] == "hourly":
                        should_run = self._should_run_hourly(task)
                    
                    if should_run:
                        self._run_task(task)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(10)
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print("⏰ Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("⏰ Task scheduler stopped")
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        now = datetime.now()
        status = {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "tasks": []
        }
        
        for task in self.tasks:
            task_info = {
                "name": task["name"],
                "type": task["type"]
            }
            
            if task["type"] == "periodic":
                if task["last_run"]:
                    last_run = datetime.fromtimestamp(task["last_run"])
                    next_run = last_run + timedelta(seconds=task["interval"])
                    task_info["last_run"] = last_run.strftime("%Y-%m-%d %H:%M:%S")
                    task_info["next_run"] = next_run.strftime("%Y-%m-%d %H:%M:%S")
                    task_info["interval"] = f"{task['interval']}s"
            elif task["type"] == "daily":
                task_info["time"] = f"{task['hour']:02d}:{task['minute']:02d}"
                task_info["last_run_date"] = str(task["last_run_date"]) if task["last_run_date"] else "Never"
            elif task["type"] == "hourly":
                task_info["hours"] = task["hours"]
                task_info["minute"] = task["minute"]
                task_info["runs_today"] = len([
                    k for k in task["last_runs"].keys()
                    if k.startswith(str(now.date()))
                ])
            
            status["tasks"].append(task_info)
        
        return status
