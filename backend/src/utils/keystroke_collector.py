"""
 BioAuthAI - KEYSTROKE DATA COLLECTOR
Collects keystroke timing data during login and extracts 21 features
matching the DSL dataset format.
"""

import numpy as np
from datetime import datetime
import json


class KeystrokeCollector:
    """
    Collects keystroke timing data and extracts 21 features
    """
    
    def __init__(self):
        """Initialize keystroke collector"""
        self.key_events = []
        self.start_time = None
        self.end_time = None
    
    def add_keydown(self, key_code, timestamp_ms):
        """Record a key down event"""
        if self.start_time is None:
            self.start_time = timestamp_ms
        
        self.key_events.append({
            'type': 'keydown',
            'key': key_code,
            'time': timestamp_ms - self.start_time
        })
    
    def add_keyup(self, key_code, timestamp_ms):
        """Record a key up event"""
        if self.start_time is None:
            self.start_time = timestamp_ms
        
        self.key_events.append({
            'type': 'keyup',
            'key': key_code,
            'time': timestamp_ms - self.start_time
        })
        
        self.end_time = timestamp_ms
    
    def extract_dwell_times(self):
        """
        Extract dwell times (key hold duration)
        Dwell time = time between keydown and keyup for same key
        """
        dwell_times = []
        key_downs = {}
        
        for event in self.key_events:
            if event['type'] == 'keydown':
                key_downs[event['key']] = event['time']
            elif event['type'] == 'keyup' and event['key'] in key_downs:
                dwell = event['time'] - key_downs[event['key']]
                if dwell > 0:
                    dwell_times.append(dwell)
                del key_downs[event['key']]
        
        return dwell_times
    
    def extract_flight_times(self):
        """
        Extract flight times (time between keyup and next keydown)
        Flight time = time between releasing one key and pressing the next
        """
        flight_times = []
        key_ups = []
        
        for event in self.key_events:
            if event['type'] == 'keyup':
                key_ups.append(event['time'])
            elif event['type'] == 'keydown' and key_ups:
                last_keyup = key_ups[-1]
                flight = event['time'] - last_keyup
                if flight > 0:
                    flight_times.append(flight)
        
        return flight_times
    
    def extract_pause_patterns(self):
        """
        Extract pause patterns (longer gaps between key presses)
        Identifies natural pauses in typing (> 200ms)
        """
        pauses = []
        flight_times = self.extract_flight_times()
        
        # Pauses are flight times that are significantly longer than average
        if flight_times:
            avg_flight = np.mean(flight_times)
            for flight in flight_times:
                if flight > avg_flight * 2:  # Pause threshold
                    pauses.append(flight)
        
        return pauses
    
    def extract_typing_speed(self):
        """
        Calculate typing speed (characters per second)
        """
        if not self.key_events or self.start_time is None or self.end_time is None:
            return 0.0
        
        total_time_seconds = (self.end_time - self.start_time) / 1000.0
        if total_time_seconds <= 0:
            return 0.0
        
        # Count keydown events as "characters"
        key_count = sum(1 for e in self.key_events if e['type'] == 'keydown')
        typing_speed = key_count / total_time_seconds if total_time_seconds > 0 else 0.0
        
        return typing_speed
    
    def get_raw_keystroke_data(self):
        """
        Get raw keystroke data in the format expected by feature extractor
        """
        return {
            "dwell_times": self.extract_dwell_times(),
            "flight_times": self.extract_flight_times(),
            "pause_patterns": self.extract_pause_patterns(),
            "typing_speed": self.extract_typing_speed(),
            "key_count": sum(1 for e in self.key_events if e['type'] == 'keydown'),
            "total_time_ms": (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        }
    
    def is_valid(self):
        """Check if collected data is valid for feature extraction"""
        # Need at least 5 key presses
        key_count = sum(1 for e in self.key_events if e['type'] == 'keydown')
        return key_count >= 5
    
    def reset(self):
        """Reset collector for next session"""
        self.key_events = []
        self.start_time = None
        self.end_time = None


def extract_21_features(keystroke_data):
    """
    Extract 21 features from keystroke data
    Matches DSL dataset format exactly
    
    Features:
    - 8 Dwell Time stats (H.* from DSL)
    - 8 Flight Time stats (DD.* from DSL)
    - 5 Up-Down Time stats (UD.* from DSL)
    
    Input: dict with dwell_times, flight_times, pause_patterns, typing_speed
    Output: list of 21 float values
    """
    
    dwell = np.array(keystroke_data.get("dwell_times", []), dtype=np.float32)
    flight = np.array(keystroke_data.get("flight_times", []), dtype=np.float32)
    pause = np.array(keystroke_data.get("pause_patterns", []), dtype=np.float32)
    speed = float(keystroke_data.get("typing_speed", 0))
    
    features = []
    
    # ============ DWELL TIME FEATURES (8) ============
    # H.period, H.t, H.i, H.e, H.five, H.Shift.r, H.o (7 hold times + 1 count)
    if len(dwell) > 0:
        features.extend([
            float(np.mean(dwell)),                          # H.period (mean dwell)
            float(np.std(dwell)) if len(dwell) > 1 else 0.0,  # Variability
            float(np.median(dwell)),                        # Median dwell
            float(np.min(dwell)),                           # Min dwell
            float(np.max(dwell)),                           # Max dwell
            float(np.percentile(dwell, 25)),                # Q1 dwell
            float(np.percentile(dwell, 75)),                # Q3 dwell
            float(len(dwell))                               # Count
        ])
    else:
        features.extend([0.0] * 8)
    
    # ============ FLIGHT TIME FEATURES (8) ============
    # DD.period.t, DD.t.i, DD.i.e, DD.e.five, DD.five.Shift.r, DD.Shift.r.o, DD.o.a (7 flight times + 1 count)
    if len(flight) > 0:
        features.extend([
            float(np.mean(flight)),                         # DD.period.t (mean flight)
            float(np.std(flight)) if len(flight) > 1 else 0.0,  # Variability
            float(np.median(flight)),                       # Median flight
            float(np.min(flight)),                          # Min flight
            float(np.max(flight)),                          # Max flight
            float(np.percentile(flight, 25)),               # Q1 flight
            float(np.percentile(flight, 75)),               # Q3 flight
            float(len(flight))                              # Count
        ])
    else:
        features.extend([0.0] * 8)
    
    # ============ PAUSE/UP-DOWN TIME FEATURES (5) ============
    # UD.period.t, UD.t.i, UD.i.e, UD.e.five, UD.five.Shift.r (5 up-down times)
    if len(pause) > 0:
        features.extend([
            float(np.mean(pause)),                          # UD.period.t (mean pause)
            float(np.std(pause)) if len(pause) > 1 else 0.0,   # Variability
            float(np.median(pause)),                        # Median pause
            float(np.percentile(pause, 25)),                # Q1 pause
            float(np.percentile(pause, 75))                 # Q3 pause
        ])
    else:
        features.extend([0.0] * 5)
    
    # Ensure exactly 21 features
    assert len(features) == 21, f"Expected 21 features, got {len(features)}"
    
    return features


def create_keystroke_record_dict(keystroke_data, device_info=None):
    """
    Create a complete keystroke record dictionary ready for database storage
    """
    features = extract_21_features(keystroke_data)
    
    return {
        "keystroke_features": keystroke_data,
        "extracted_features": features,
        "device_info": device_info or {},
        "timestamp": datetime.utcnow().isoformat(),
        "feature_count": len(features),
        "key_count": keystroke_data.get("key_count", 0),
        "typing_speed": keystroke_data.get("typing_speed", 0)
    }
