import os
import json
import pickle
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Configuration
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
STATE_FILE = os.path.join(os.path.dirname(__file__), 'state.json')
RESERVATIONS_FILE = os.path.join(os.path.dirname(__file__), 'reservations.json')
SLOTS_FILE = os.path.join(os.path.dirname(__file__), 'parking_slots.pkl')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

def load_json(filepath, default=None):
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return default if default is not None else {}

def save_json(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

def get_expected_slot_count():
    try:
        with open(SLOTS_FILE, 'rb') as f:
            return len(pickle.load(f))
    except Exception as e:
        print(f"Error loading {SLOTS_FILE}: {e}")
        return 12

def build_free_slots(count):
    return [{"id": i + 1, "status": "FREE"} for i in range(count)]

def get_normalized_slots():
    expected_count = get_expected_slot_count()
    ai_state = load_json(STATE_FILE, {"slots": []})
    slots = ai_state.get("slots", [])

    # If the saved detector state is stale after redrawing parking slots,
    # fall back to the current slot layout instead of showing old slot IDs.
    if len(slots) != expected_count:
        return build_free_slots(expected_count)

    return slots

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/slots', methods=['GET'])
def get_slots():
    # Load Reservations
    # reservations.json structure: {"reservations": [{"slot_id": 1, "name": "...", "plate": "...", "time": ...}]}
    res_data = load_json(RESERVATIONS_FILE, {"reservations": []})
    reservations = res_data.get("reservations", [])
    
    # Helper: Find reservation for a slot
    def get_reservation(slot_id):
        for r in reservations:
            if r['slot_id'] == slot_id:
                return r
        return None

    combined_slots = []
    slots_list = get_normalized_slots()

    for slot in slots_list:
        slot_id = slot['id']
        raw_status = slot['status'] # "OCCUPIED" or "FREE" (from AI)
        
        reservation = get_reservation(slot_id)
        
        # Determine Final Status
        # Priority: OCCUPIED (Real car) > RESERVED (Booked) > FREE
        final_status = "FREE"
        
        if raw_status == "OCCUPIED":
            final_status = "OCCUPIED"
        elif reservation:
            final_status = "RESERVED"
        
        combined_slots.append({
            "id": slot_id,
            "status": final_status,
            "raw_status": raw_status, # Debug info
            "reservation": reservation 
        })
        
    return jsonify({
        "timestamp": time.time(),
        "slots": combined_slots
    })

@app.route('/api/reserve', methods=['POST'])
def reserve_slot():
    try:
        data = request.json
        slot_id = int(data.get('slot_id'))
        name = data.get('name')
        plate = data.get('plate')
        
        if not all([slot_id, name, plate]):
            return jsonify({"error": "Missing fields"}), 400
            
        res_data = load_json(RESERVATIONS_FILE, {"reservations": []})
        reservations = res_data.get("reservations", [])
        
        # Check if already reserved
        for r in reservations:
            if r['slot_id'] == slot_id:
                return jsonify({"error": "Slot already reserved"}), 409
        
        # Check if physically occupied (Optional: Allow reservation even if occupied? Usually no.)
        # For this logic, we'll allow reservation unless the system explicitly blocks it, 
        # but the frontend sees it as RED if occupied.
        # Let's check AI state to prevent booking an occupied slot if desired.
        # ai_state = load_json(STATE_FILE, {"slots": []})
        # ... logic ...
        
        new_res = {
            "id": str(int(time.time() * 1000)), # Simple unique ID
            "slot_id": slot_id,
            "name": name,
            "plate": plate,
            "reserved_at": time.time()
        }
        
        reservations.append(new_res)
        res_data['reservations'] = reservations
        save_json(RESERVATIONS_FILE, res_data)
        
        return jsonify({"success": True, "reservation": new_res})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cancel', methods=['POST'])
def cancel_reservation():
    try:
        data = request.json
        slot_id = int(data.get('slot_id'))
        
        res_data = load_json(RESERVATIONS_FILE, {"reservations": []})
        reservations = res_data.get("reservations", [])
        
        initial_len = len(reservations)
        reservations = [r for r in reservations if r['slot_id'] != slot_id]
        
        if len(reservations) == initial_len:
             return jsonify({"error": "Reservation not found"}), 404
             
        res_data['reservations'] = reservations
        save_json(RESERVATIONS_FILE, res_data)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    res_data = load_json(RESERVATIONS_FILE, {"reservations": []})
    
    slots = get_normalized_slots()
    reservations = res_data.get("reservations", [])
    
    total_slots = len(slots)
    occupied_count = sum(1 for s in slots if s.get("status") == "OCCUPIED")
    reserved_count = len(reservations)
    # Note: A slot can be both reserved and occupied (customer arrived).
    # "Free" is roughly Total - Occupied (physically). 
    # Or strict definition: Total - (Occupied U Reserved).
    
    # Let's count strictly available for booking
    # Available = NOT Occupied AND NOT Reserved
    available_count = 0
    reserved_slot_ids = [r['slot_id'] for r in reservations]
    
    # If we have real slot data
    if slots:
        for s in slots:
            if s['status'] != "OCCUPIED" and s['id'] not in reserved_slot_ids:
                available_count += 1
    else:
        available_count = total_slots - reserved_count # Estimate if the detector has not run yet
    
    return jsonify({
        "total": total_slots,
        "occupied": occupied_count,
        "reserved": reserved_count,
        "available": available_count
    })

if __name__ == '__main__':
    print("Starting Flask Server...")
    print(f"Serving frontend from: {FRONTEND_DIR}")
    app.run(host='0.0.0.0', port=9000, debug=True)
