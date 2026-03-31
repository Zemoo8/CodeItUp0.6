from scapy.all import IP, TCP
from main_ids import IntrusionDetectionSystem

def test_ids():
    # Create test packets to simulate various scenarios
    test_packets = [
        # Normal traffic
        IP(src="192.168.1.1", dst="192.168.1.2") / TCP(sport=1234, dport=80, flags="A"),
        IP(src="192.168.1.3", dst="192.168.1.4") / TCP(sport=1235, dport=443, flags="P"),

        # SYN flood simulation
        IP(src="10.0.0.1", dst="192.168.1.2") / TCP(sport=5678, dport=80, flags="S"),
        IP(src="10.0.0.2", dst="192.168.1.2") / TCP(sport=5679, dport=80, flags="S"),
        IP(src="10.0.0.3", dst="192.168.1.2") / TCP(sport=5680, dport=80, flags="S"),

        # Port scan simulation
        IP(src="192.168.1.100", dst="192.168.1.2") / TCP(sport=4321, dport=22, flags="S"),
        IP(src="192.168.1.100", dst="192.168.1.2") / TCP(sport=4321, dport=23, flags="S"),
        IP(src="192.168.1.100", dst="192.168.1.2") / TCP(sport=4321, dport=25, flags="S"),
    ]

    ids = IntrusionDetectionSystem()

    # ========== ADD THIS: Train anomaly detector ==========
    print("Training anomaly detector with dummy normal traffic...")
    dummy_training_data = [
        [500, 10.0, 5000.0],  # [packet_size, packet_rate, byte_rate]
        [600, 12.0, 6000.0],
        [450, 8.0, 4500.0],
        [700, 15.0, 7000.0],
        [550, 11.0, 5500.0],
        [480, 9.0, 4800.0],
        [650, 13.0, 6500.0],
        [520, 10.5, 5200.0],
        [580, 12.5, 5800.0],
        [470, 8.5, 4700.0],
    ]
    ids.detection_engine.train_anomaly_detector(dummy_training_data)
    print("Training complete!\n")
    # ======================================================

    # Simulate packet processing and threat detection
    print("Starting IDS Test...")
    for i, packet in enumerate(test_packets, 1):
        print(f"\nProcessing packet {i}: {packet.summary()}")

        # Analyze the packet
        features = ids.traffic_analyzer.analyze_packet(packet)

        if features:
            # Detect threats based on features
            threats = ids.detection_engine.detect_threats(features)

            if threats:
                print(f"Detected threats: {threats}")
            else:
                print("No threats detected.")
        else:
            print("Packet does not contain IP/TCP layers or is ignored.")

    print("\nIDS Test Completed.")

if __name__ == "__main__":
    test_ids()