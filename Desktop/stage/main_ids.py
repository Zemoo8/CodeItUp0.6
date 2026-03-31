from scapy.all import IP, TCP
import queue
import time
from packet_capture import PacketCapture
from traffic_analyzer import TrafficAnalyzer
from detection_engine import DetectionEngine
from alert_system import AlertSystem
from port_blocker import PortBlocker

class IntrusionDetectionSystem:
    def __init__(self, interface="eth0"):
        self.packet_capture = PacketCapture()
        self.traffic_analyzer = TrafficAnalyzer()
        self.detection_engine = DetectionEngine()
        self.alert_system = AlertSystem()
        self.port_blocker = PortBlocker(auto_unblock_seconds=300)  # 5 min blocks
        
        self.interface = interface
        self.training_start_time = None
        self.training_duration = 300  # 5 minutes initial training
        
    def start(self):
        print(f"🚀 Starting IDS on {self.interface}")
        print("📚 TRAINING PHASE: Learning normal traffic for 5 minutes...")
        print("   (Blocking disabled during training)")
        
        self.training_start_time = time.time()
        self.packet_capture.start_capture(self.interface)
        
        packets_processed = 0
        
        try:
            while True:
                try:
                    packet = self.packet_capture.packet_queue.get(timeout=1)
                    features = self.traffic_analyzer.analyze_packet(packet)
                    
                    if not features:
                        continue
                    
                    packets_processed += 1
                    
                    # Training phase
                    if self.detection_engine.training_mode:
                        self.detection_engine.collect_training_sample(features)
                        elapsed = time.time() - self.training_start_time
                        
                        # Auto-finalize training after 5 mins or 1000 packets
                        if elapsed > self.training_duration or len(self.detection_engine.training_buffer) >= 1000:
                            print("\n🎓 Finalizing training...")
                            if self.detection_engine.finalize_training():
                                print("🛡️ PROTECTION ACTIVE: Blocking enabled!")
                            else:
                                print("⚠️ Training failed, continuing in detection-only mode")
                        else:
                            if packets_processed % 100 == 0:
                                progress = min(100, (elapsed/self.training_duration)*100)
                                print(f"   Training... {progress:.1f}% ({len(self.detection_engine.training_buffer)} samples)")
                        continue
                    
                    # Active detection phase
                    threats = self.detection_engine.detect_threats(features)
                    
                    for threat in threats:
                        packet_info = {
                            'source_ip': packet[IP].src,
                            'destination_ip': packet[IP].dst,
                            'source_port': packet[TCP].sport,
                            'destination_port': packet[TCP].dport,
                            'raw_packet': bytes(packet[TCP].payload)[:50].hex()  # First 50 bytes
                        }
                        
                        # Generate alert
                        self.alert_system.generate_alert(threat, packet_info)
                        
                        # Block if required
                        if threat.get('action') == 'block':
                            self.port_blocker.block_port(
                                packet[IP].src, 
                                packet[TCP].dport,
                                f"{threat['type']}: {threat.get('rule', 'anomaly')}"
                            )
                        
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    raise
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping IDS...")
            self.port_blocker.flush_all()  # Cleanup iptables
            self.packet_capture.stop()
            print("✅ IDS Stopped, all blocks cleared")