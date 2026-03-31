import logging
import json
from datetime import datetime
import time
from collections import defaultdict
import threading

class AlertSystem:
    def __init__(self, log_file="ids_alerts.log"):
        self.logger = logging.getLogger("IDS_Alerts")
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers if class is reinstantiated
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # Prevent propagation to root logger (stops duplicate console output)
            self.logger.propagate = False
        
        # For web interface - thread safe storage
        self.alerts_storage = None
        self.storage_lock = None  # Set this from app.py for thread safety
        
        # Cooldown tracking (10 seconds per IP)
        self.alert_cooldown = defaultdict(float)
        self.cooldown_time = 10.0

    def generate_alert(self, threat, packet_info):
        source_ip = packet_info.get('source_ip')
        current_time = time.time()
        
        # Skip if same IP alerted within cooldown period
        if current_time - self.alert_cooldown[source_ip] < self.cooldown_time:
            return
            
        self.alert_cooldown[source_ip] = current_time
        
        # Clean up threat details to make JSON serializable (convert FlagValue to str)
        clean_details = {}
        for key, value in threat.items():
            if key == 'features' and isinstance(value, dict):
                # Convert all feature values to strings if they're not basic types
                clean_features = {}
                for k, v in value.items():
                    if isinstance(v, (int, float, str, bool, type(None))):
                        clean_features[k] = v
                    else:
                        clean_features[k] = str(v)  # Convert FlagValue, bytes, etc to string
                clean_details[key] = clean_features
            else:
                clean_details[key] = value
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'threat_type': threat['type'],
            'source_ip': source_ip,
            'destination_ip': packet_info.get('destination_ip'),
            'confidence': threat.get('confidence', 0.0),
            'details': clean_details
        }
        
        # Log to file - use default=str to catch anything we missed
        alert_json = json.dumps(alert, default=str)
        if threat['confidence'] > 0.8:
            self.logger.critical(f"High confidence threat: {alert_json}")
        else:
            self.logger.warning(alert_json)
        
        # Store for web interface (thread-safe)
        if self.alerts_storage is not None:
            if self.storage_lock:
                with self.storage_lock:
                    self.alerts_storage.append(alert)
            else:
                self.alerts_storage.append(alert)