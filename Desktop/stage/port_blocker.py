import subprocess
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict

class PortBlocker:
    def __init__(self, auto_unblock_seconds=300):
        self.blocked_entries = {}  # {(ip, port): unblock_time}
        self.auto_unblock = auto_unblock_seconds
        self.lock = threading.Lock()
        self.whitelist = {'127.0.0.1', '192.168.1.1'}  # Add your VM gateway here
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def block_port(self, ip, port, reason="Anomaly detected"):
        """Block specific IP:Port combination"""
        if ip in self.whitelist:
            return False
            
        key = (ip, port)
        
        with self.lock:
            if key in self.blocked_entries:
                # Extend block time
                self.blocked_entries[key]['unblock_time'] = datetime.now() + timedelta(seconds=self.auto_unblock)
                return True
            
            # Add iptables rule
            try:
                cmd = f"iptables -A INPUT -s {ip} -p tcp --dport {port} -j DROP"
                subprocess.run(cmd.split(), check=True, capture_output=True)
                
                self.blocked_entries[key] = {
                    'ip': ip,
                    'port': port,
                    'blocked_at': datetime.now(),
                    'unblock_time': datetime.now() + timedelta(seconds=self.auto_unblock),
                    'reason': reason
                }
                print(f"🚫 BLOCKED {ip}:{port} - {reason}")
                return True
            except Exception as e:
                print(f"Failed to block {ip}:{port}: {e}")
                return False
    
    def unblock_port(self, ip, port):
        """Manually unblock a port"""
        key = (ip, port)
        with self.lock:
            if key in self.blocked_entries:
                try:
                    cmd = f"iptables -D INPUT -s {ip} -p tcp --dport {port} -j DROP"
                    subprocess.run(cmd.split(), check=True, capture_output=True)
                    del self.blocked_entries[key]
                    return True
                except Exception as e:
                    print(f"Failed to unblock: {e}")
        return False
    
    def _cleanup_loop(self):
        """Auto-unblock expired entries"""
        while True:
            time.sleep(10)
            now = datetime.now()
            with self.lock:
                expired = [k for k, v in self.blocked_entries.items() if v['unblock_time'] < now]
                for key in expired:
                    ip, port = key
                    self.unblock_port(ip, port)
                    print(f"✅ Auto-unblocked {ip}:{port}")
    
    def get_blocked_list(self):
        """Return list of currently blocked ports"""
        with self.lock:
            return list(self.blocked_entries.values())
    
    def flush_all(self):
        """Clear all blocks (use with caution)"""
        with self.lock:
            for ip, port in list(self.blocked_entries.keys()):
                self.unblock_port(ip, port)