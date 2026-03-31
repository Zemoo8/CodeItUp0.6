from collections import defaultdict
from scapy.all import IP, TCP

class TrafficAnalyzer:
    def __init__(self):
        self.connections = defaultdict(list)
        self.flow_stats = defaultdict(lambda: {
            'packet_count': 0,
            'byte_count': 0,
            'start_time': None,
            'last_time': None
        })

    def analyze_packet(self, packet):
        if IP in packet and TCP in packet:
            ip_src = packet[IP].src
            ip_dst = packet[IP].dst
            port_src = packet[TCP].sport
            port_dst = packet[TCP].dport

            flow_key = (ip_src, ip_dst, port_src, port_dst)

            # Update flow statistics
            stats = self.flow_stats[flow_key]
            stats['packet_count'] += 1
            stats['byte_count'] += len(packet)
            current_time = packet.time

            if not stats['start_time']:
                stats['start_time'] = current_time
            stats['last_time'] = current_time

            return self.extract_features(packet, stats)

    def extract_features(self, packet, stats):
        time_diff = stats['last_time'] - stats['start_time']
        
        # Fix: Prevent division by zero on sub-millisecond packets
        if time_diff < 0.001:
            packet_rate = stats['packet_count'] / 0.001  # Assume 1ms minimum
            byte_rate = stats['byte_count'] / 0.001
        else:
            packet_rate = stats['packet_count'] / time_diff
            byte_rate = stats['byte_count'] / time_diff

        return {
            'packet_size': len(packet),
            'flow_duration': time_diff,
            'packet_rate': packet_rate,
            'byte_rate': byte_rate,
            'tcp_flags': packet[TCP].flags,
            'window_size': packet[TCP].window
            }