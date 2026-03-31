from flask import Flask, render_template, jsonify, request
from main_ids import IntrusionDetectionSystem
from scapy.all import IP, TCP
import threading
import time

app = Flask(__name__, template_folder='templates')

# Shared storage
alerts_list = []
alerts_lock = threading.Lock()
blocked_ports_cache = []
training_status = {"active": True, "progress": 0, "samples": 0}

# Initialize IDS
ids = IntrusionDetectionSystem(interface="enp0s3")  # Change to your VM interface
ids.alert_system.alerts_storage = alerts_list
ids.alert_system.storage_lock = alerts_lock

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        'training': ids.detection_engine.training_mode,
        'training_progress': min(100, (time.time() - ids.training_start_time)/ids.training_duration * 100) if ids.detection_engine.training_mode else 100,
        'samples_collected': len(ids.detection_engine.training_buffer),
        'protection_active': not ids.detection_engine.training_mode and ids.detection_engine.is_trained
    })

@app.route('/api/alerts')
def get_alerts():
    with alerts_lock:
        alerts_copy = list(alerts_list[-100:])
    return jsonify({
        'alerts': alerts_copy,
        'blocked_ports': ids.port_blocker.get_blocked_list()
    })

@app.route('/api/stats')
def get_stats():
    with alerts_lock:
        total = len(alerts_list)
        sig = len([a for a in alerts_list if a['threat_type'] == 'signature'])
        anom = len([a for a in alerts_list if a['threat_type'] == 'anomaly'])
        blocked = len(ids.port_blocker.get_blocked_list())
    
    return jsonify({
        'total_alerts': total,
        'signature_alerts': sig,
        'anomaly_alerts': anom,
        'blocked_ports_count': blocked,
        'training_mode': ids.detection_engine.training_mode
    })

@app.route('/api/clear', methods=['POST'])
def clear_alerts():
    """Clear all alerts from the dashboard"""
    with alerts_lock:
        alerts_list.clear()
    return jsonify({'status': 'Alerts cleared', 'count': 0})

@app.route('/api/unblock', methods=['POST'])
def unblock_port():
    data = request.json
    success = ids.port_blocker.unblock_port(data['ip'], data['port'])
    return jsonify({'success': success})

@app.route('/api/flush-blocks', methods=['POST'])
def flush_blocks():
    """Unblock all currently blocked ports"""
    ids.port_blocker.flush_all()
    return jsonify({'status': 'All blocks cleared', 'count': 0})

@app.route('/run-test')
def run_test():
    """Inject test malicious packets"""
    if ids.detection_engine.training_mode:
        return jsonify({'error': 'Cannot test during training phase'}), 400
    
    # Force training completion for testing
    if not ids.detection_engine.is_trained:
        ids.detection_engine.finalize_training()
    
    test_packets = [
        IP(src="10.0.0.1", dst="192.168.1.2") / TCP(sport=5678, dport=80, flags="S"),
        IP(src="10.0.0.2", dst="192.168.1.2") / TCP(sport=5679, dport=80, flags="S"),
        IP(src="10.0.0.3", dst="192.168.1.2") / TCP(sport=5680, dport=80, flags="S"),
    ]
    
    for packet in test_packets:
        features = ids.traffic_analyzer.analyze_packet(packet)
        if features:
            threats = ids.detection_engine.detect_threats(features)
            for threat in threats:
                packet_info = {
                    'source_ip': packet[IP].src,
                    'destination_ip': packet[IP].dst,
                    'source_port': packet[TCP].sport,
                    'destination_port': packet[TCP].dport,
                    'raw_packet': 'SYN Flood Test'
                }
                ids.alert_system.generate_alert(threat, packet_info)
                if threat.get('action') == 'block':
                    ids.port_blocker.block_port(packet[IP].src, packet[TCP].dport, "Test Block")
    
    return jsonify({'status': 'Test attack injected! Check blocked ports.'})

def run_ids():
    ids.start()

if __name__ == '__main__':
    ids_thread = threading.Thread(target=run_ids, daemon=True)
    ids_thread.start()
    
    print("🌐 Dashboard: http://0.0.0.0:5000")
    print("⚠️  Run as root/sudo for iptables blocking to work!")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)