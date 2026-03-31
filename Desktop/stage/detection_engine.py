from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os
from collections import deque

class DetectionEngine:
    def __init__(self, model_path="models/ids_model.pkl"):
        self.model_path = model_path
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.05,  # Lower = less sensitive
            random_state=42,
            n_estimators=100
        )
        self.signature_rules = self.load_signature_rules()
        self.is_trained = False
        self.training_buffer = deque(maxlen=1000)  # Store last 1000 packets for training
        self.training_mode = True  # Start in training mode
        
        # Try load existing model
        if os.path.exists(model_path):
            self.load_model()
    
    def collect_training_sample(self, features):
        """Add packet to training buffer"""
        if self.training_mode and len(self.training_buffer) < 1000:
            self.training_buffer.append([
                features['packet_size'],
                features['packet_rate'],
                features['byte_rate'],
                features.get('window_size', 0)
            ])
            return True
        return False
    
    def finalize_training(self):
        """Convert buffer to trained model"""
        if len(self.training_buffer) < 50:
            print("⚠️ Not enough data to train (need 50+ packets)")
            return False
        
        data = np.array(list(self.training_buffer))
        self.scaler.fit(data)
        scaled_data = self.scaler.transform(data)
        self.anomaly_detector.fit(scaled_data)
        self.is_trained = True
        self.training_mode = False
        self.save_model()
        print(f"✅ Model trained on {len(data)} normal packets")
        return True
    
    def save_model(self):
        """Persist model to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({
            'scaler': self.scaler,
            'model': self.anomaly_detector,
            'is_trained': self.is_trained
        }, self.model_path)
    
    def load_model(self):
        """Load model from disk"""
        try:
            data = joblib.load(self.model_path)
            self.scaler = data['scaler']
            self.anomaly_detector = data['model']
            self.is_trained = data['is_trained']
            self.training_mode = False
            print("✅ Loaded pre-trained model")
        except Exception as e:
            print(f"Failed to load model: {e}")
    
    def load_signature_rules(self):
        # ... existing signature rules ...
        return {
            'syn_flood': {
                'severity': 'high',
                'action': 'block',  # New: define action
                'condition': lambda f: (f['tcp_flags'] == 2 and f['packet_rate'] > 100)
            },
            'port_scan': {
                'severity': 'medium',
                'action': 'alert',
                'condition': lambda f: (f['packet_size'] < 100 and f['packet_rate'] > 50)
            },
            'xmas_scan': {
                'severity': 'high', 
                'action': 'block',
                'condition': lambda f: f['tcp_flags'] == 41
            }
        }
    
    def detect_threats(self, features):
        threats = []
        
        # Signature detection
        for rule_name, rule in self.signature_rules.items():
            try:
                if rule['condition'](features):
                    threats.append({
                        'type': 'signature',
                        'rule': rule_name,
                        'severity': rule.get('severity', 'medium'),
                        'action': rule.get('action', 'alert'),  # block or alert
                        'confidence': 1.0,
                        'features': features  # Include raw features for display
                    })
            except:
                continue
        
        # Anomaly detection (only if trained)
        if self.is_trained and not self.training_mode:
            try:
                vector = np.array([[features['packet_size'], features['packet_rate'], 
                                  features['byte_rate'], features.get('window_size', 0)]])
                scaled = self.scaler.transform(vector)
                score = self.anomaly_detector.score_samples(scaled)[0]
                
                if score < -0.6:  # Anomaly threshold
                    threats.append({
                        'type': 'anomaly',
                        'score': float(score),
                        'severity': 'high' if score < -0.8 else 'medium',
                        'action': 'block' if score < -0.8 else 'alert',
                        'confidence': min(1.0, abs(score)),
                        'features': features
                    })
            except Exception as e:
                pass
        
        return threats