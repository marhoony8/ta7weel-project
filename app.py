from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from sqlalchemy import text 


app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'ta7weel.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    national_id = db.Column(db.String(20), unique=True)
    full_name_en = db.Column(db.String(100))
    password = db.Column(db.String(80))
    dob = db.Column(db.String(20), default="1990-01-01")
    phone = db.Column(db.String(20), default="00000000")
    email = db.Column(db.String(100), default="example@mail.com")
    is_admin = db.Column(db.Boolean, default=False)
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    color = db.Column(db.String(30))
    year = db.Column(db.Integer)
    vin = db.Column(db.String(50)) 
    violations = db.Column(db.Float, default=0.0) 
    is_insured = db.Column(db.Boolean, default=False) 
    is_registered = db.Column(db.Boolean, default=True) 
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class TransferRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_plate = db.Column(db.String(20))
    from_id = db.Column(db.String(20)) 
    to_id = db.Column(db.String(20))   
    status = db.Column(db.String(20), default="Pending")


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(national_id=data['national_id'], password=data['password']).first()
    if user:
        return jsonify({
            "national_id": user.national_id, 
            "full_name": user.full_name_en or "User",
            "full_name_en": user.full_name_en or "User",
            "dob": user.dob,
            "phone": user.phone,
            "email": user.email,
            "is_admin": user.is_admin
        }), 200
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/admin/get_all_users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([{
        "national_id": u.national_id, 
        "full_name": u.full_name_en or "No Name",
        "full_name_en": u.full_name_en or "No Name",
        "dob": u.dob,
        "phone": u.phone or "N/A",
        "email": u.email or "N/A"
    } for u in users])

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    data = request.json
    try:
        new_user = User(
            national_id=data['national_id'],
            full_name_en=data.get('full_name_en', ''),
            password=data['password'],
            dob=data.get('dob', '1990-01-01'),
            phone=data.get('phone', '00000000'),
            email=data.get('email', 'example@mail.com'),
            is_admin=data.get('is_admin', False)
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User Created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/admin/update_user', methods=['POST'])
def update_user():
    data = request.json
    user = User.query.filter_by(national_id=data['national_id']).first()
    if user:
        user.full_name_en = data.get('full_name_en', user.full_name_en)
        user.dob = data.get('dob', user.dob)
        user.phone = data.get('phone', user.phone)
        user.email = data.get('email', user.email)
        if data.get('password'): user.password = data['password']
        db.session.commit()
        return jsonify({"message": "Updated Successfully"}), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/admin/delete_user/<nid>', methods=['DELETE'])
def delete_user(nid):
    user = User.query.filter_by(national_id=nid).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/admin/get_all_vehicles', methods=['GET'])
def get_all_vehicles():
    vehicles = Vehicle.query.all()
    res = []
    for v in vehicles:
        owner = User.query.get(v.owner_id)
        res.append({
            "plate": v.plate_number,
            "brand": v.brand,
            "model": v.model,
            "color": v.color,
            "year": v.year,
            "vin": v.vin,
            "violations": v.violations,
            "is_insured": v.is_insured,
            "is_registered": v.is_registered,
            "owner_national_id": owner.national_id if owner else "No Owner"
        })
    return jsonify(res)

@app.route('/admin/add_vehicle', methods=['POST'])
def add_vehicle():
    data = request.json
    owner = User.query.filter_by(national_id=data['owner_national_id']).first()
    if not owner:
        return jsonify({"error": "Owner (National ID) not found"}), 404
    try:
        new_v = Vehicle(
            plate_number=data['plate'],
            brand=data['brand'],
            owner_id=owner.id,
            model=data.get('model', 'Unknown'),
            color=data.get('color', 'White'),
            year=data.get('year', 2024),
            vin=data.get('vin', 'N/A'),
            violations=data.get('violations', 0.0),
            is_insured=data.get('is_insured', False),
            is_registered=data.get('is_registered', True)
        )
        db.session.add(new_v)
        db.session.commit()
        return jsonify({"message": "Vehicle Added"}), 201
    except:
        return jsonify({"error": "Plate number already exists"}), 400

@app.route('/admin/update_vehicle', methods=['POST'])
def update_vehicle():
    data = request.json
    v = Vehicle.query.filter_by(plate_number=data['plate']).first()
    if not v:
        return jsonify({"error": "Vehicle not found"}), 404
    v.brand = data.get('brand', v.brand)
    v.model = data.get('model', v.model)
    v.color = data.get('color', v.color)
    v.vin = data.get('vin', v.vin)
    v.year = data.get('year', v.year)
    v.violations = data.get('violations', v.violations)
    v.is_insured = data.get('is_insured', v.is_insured)
    v.is_registered = data.get('is_registered', v.is_registered)
    if 'owner_national_id' in data:
        new_owner = User.query.filter_by(national_id=data['owner_national_id']).first()
        if new_owner:
            v.owner_id = new_owner.id
    db.session.commit()
    return jsonify({"message": "Vehicle Updated Successfully"}), 200

@app.route('/admin/delete_vehicle/<plate>', methods=['DELETE'])
def delete_vehicle(plate):
    v = Vehicle.query.filter_by(plate_number=plate).first()
    if v:
        db.session.delete(v)
        db.session.commit()
        return jsonify({"message": "Vehicle Deleted"}), 200
    return jsonify({"error": "Vehicle not found"}), 404

@app.route('/my_vehicles/<nid>', methods=['GET'])
def my_vehicles(nid):
    user = User.query.filter_by(national_id=nid).first()
    if not user: return jsonify([]), 404
    return jsonify([{
        "plate": v.plate_number,
        "brand": v.brand,
        "model": v.model,
        "color": v.color,
        "year": v.year,
        "vin": v.vin,
        "violations": v.violations,
        "is_insured": v.is_insured,
        "is_registered": v.is_registered
    } for v in user.vehicles])

@app.route('/send_transfer', methods=['POST'])
def send_transfer():
    data = request.json
    receiver = User.query.filter_by(national_id=data['to_id']).first()
    if not receiver:
        return jsonify({"error": "Receiver ID not found"}), 400
    new_req = TransferRequest(
        vehicle_plate=data['plate'],
        from_id=data['from_id'],
        to_id=data['to_id']
    )
    db.session.add(new_req)
    db.session.commit()
    return jsonify({"message": "Request Sent"}), 201

@app.route('/get_requests/<nid>', methods=['GET'])
def get_requests(nid):
    reqs = TransferRequest.query.filter_by(to_id=nid, status="Pending").all()
    return jsonify([{
        "id": r.id,
        "plate": r.vehicle_plate,
        "sender": r.from_id
    } for r in reqs])


@app.route('/respond_request', methods=['POST'])
def respond_request():
    data = request.json
    req = TransferRequest.query.get(data['request_id'])
    if not req: return jsonify({"error": "Not found"}), 404
    
    if data['action'] == "accept":
        vehicle = Vehicle.query.filter_by(plate_number=req.vehicle_plate).first()
        new_owner = User.query.filter_by(national_id=req.to_id).first()
        
        if vehicle and new_owner:
      
            reasons = []
            if vehicle.violations > 0:
                reasons.append(f"يوجد مخالفات مرورية بقيمة {vehicle.violations} ريال")
            if not vehicle.is_insured:
                reasons.append("المركبة غير مؤمنة")
            if not vehicle.is_registered:
                reasons.append("استمارة المركبة غير صالحة (غير مسجلة)")
            
            
            if reasons:
                return jsonify({
                    "error": "تعذر إتمام نقل الملكية",
                    "reasons": reasons
                }), 400
            
         
            vehicle.owner_id = new_owner.id
            req.status = "Accepted"
            db.session.commit()
            return jsonify({"message": "تم نقل الملكية بنجاح"}), 200
    else:
        req.status = "Rejected"
        db.session.commit()
        return jsonify({"message": "تم رفض الطلب"}), 200

    return jsonify({"error": "Unknown error"}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    
        try:
          
            with db.engine.connect() as conn:
       
                existing_columns = [col['name'] for col in db.inspect(db.engine).get_columns('vehicle')]
                
                if 'is_insured' not in existing_columns:
                    conn.execute(text("ALTER TABLE vehicle ADD COLUMN is_insured BOOLEAN DEFAULT 0"))
                    print("--- Column 'is_insured' added successfully ---")
                
                if 'is_registered' not in existing_columns:
                    conn.execute(text("ALTER TABLE vehicle ADD COLUMN is_registered BOOLEAN DEFAULT 1"))
                    print("--- Column 'is_registered' added successfully ---")
                
                conn.commit()
        except Exception as e:
            print(f"Note: Database update check skipped or already updated: {e}")
        

        if not User.query.filter_by(national_id="999").first():
            admin = User(national_id="999", full_name_en="System Admin", password="admin", is_admin=True)
            db.session.add(admin)
            db.session.commit()
            
    print("--- Server is running with all Admin privileges ---")
    app.run(debug=True, host='0.0.0.0', port=5000)