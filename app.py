from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
import os
import re
import hashlib
import json
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# File paths
DATA_DIR = os.path.join(os.getcwd(), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.txt')
ADMIN_FILE = os.path.join(DATA_DIR, 'admin.txt')
USERS_DATA_DIR = os.path.join(DATA_DIR, 'users')
APPOINTMENTS_FILE = os.path.join(DATA_DIR, 'appointments.json')
DOCTORS_FILE = os.path.join(DATA_DIR, 'doctors.json')
ROOMS_FILE = os.path.join(DATA_DIR, 'rooms.json')
REMINDER_PROFILES_FILE = os.path.join(DATA_DIR, 'reminder_profiles.json')
BILLS_FILE = os.path.join(DATA_DIR, 'bills.json')
PRESCRIPTIONS_FILE = os.path.join(DATA_DIR, 'prescriptions.json')
MEDICINE_INVENTORY_FILE = os.path.join(DATA_DIR, 'medicine_inventory.json')

# Initialize directories and files
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USERS_DATA_DIR, exist_ok=True)

# Initialize default data
for file in [DOCTORS_FILE, ROOMS_FILE, APPOINTMENTS_FILE, REMINDER_PROFILES_FILE, BILLS_FILE, PRESCRIPTIONS_FILE, MEDICINE_INVENTORY_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            if file == DOCTORS_FILE:
                json.dump(["Dr. Smith", "Dr. Johnson"], f)
            elif file == ROOMS_FILE:
                json.dump(["Room 101", "Room 102"], f)
            elif file == BILLS_FILE:
                json.dump([
                    {
                        "id": "1001",
                        "patient": "john_doe",
                        "date": "2023-01-15",
                        "due_date": "2023-02-15",
                        "items": [
                            {"description": "Consultation", "amount": 150.00},
                            {"description": "Lab Test", "amount": 75.50}
                        ],
                        "total": 225.50,
                        "status": "paid"
                    }
                ], f)
            elif file == MEDICINE_INVENTORY_FILE:
                json.dump([
                    {"id": 1, "name": "Paracetamol", "price": 5.99, "stock": 100},
                    {"id": 2, "name": "Ibuprofen", "price": 8.50, "stock": 75},
                    {"id": 3, "name": "Amoxicillin", "price": 12.99, "stock": 50}
                ], f)
            else:
                json.dump([], f)

# Template filters
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)

@app.template_filter('currencyformat')
def currencyformat(value):
    return f"${value:,.2f}"

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, user_details):
    username = username.strip()
    user_dir = os.path.join(USERS_DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    
    with open(USERS_FILE, 'a') as f:
        f.write(f"{username}:{hash_password(password)}\n")
    
    details_file = os.path.join(user_dir, 'user_details.json')
    with open(details_file, 'w') as f:
        json.dump(user_details, f)

def verify_user(username, password):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split(':', 1)
            if len(parts) == 2 and parts[0] == username and parts[1] == hash_password(password):
                return True
    return False

def get_all_users():
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for line in f:
                users.append(line.split(':', 1)[0].strip())
    return users

def verify_admin(password):
    if not os.path.exists(ADMIN_FILE):
        return False
    with open(ADMIN_FILE, 'r') as f:
        return f.read().strip() == hash_password(password)

def get_reminder_profiles():
    try:
        with open(REMINDER_PROFILES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_reminder_profiles(profiles):
    with open(REMINDER_PROFILES_FILE, 'w') as f:
        json.dump(profiles, f)

def get_user_preferences(username):
    prefs_file = os.path.join(USERS_DATA_DIR, username, 'preferences.json')
    try:
        with open(prefs_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'default_reminder_profile': None}

def save_user_preferences(username, preferences):
    prefs_file = os.path.join(USERS_DATA_DIR, username, 'preferences.json')
    with open(prefs_file, 'w') as f:
        json.dump(preferences, f)

def save_appointment(appointment):
    appointments = get_all_appointments()
    appointments.append(appointment)
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(appointments, f)

def get_all_appointments():
    try:
        with open(APPOINTMENTS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def get_user_appointments(username):
    return [appt for appt in get_all_appointments() if appt.get('patient') == username]

def get_doctors():
    try:
        with open(DOCTORS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def get_rooms():
    try:
        with open(ROOMS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def create_recurring_appointments(base_appt, frequency, count):
    appointments = []
    current_date = datetime.fromisoformat(base_appt['datetime'])
    for i in range(count):
        new_date = current_date + timedelta(days=7 if frequency == 'weekly' else 1)
        new_appt = base_appt.copy()
        new_appt['datetime'] = new_date.isoformat()
        new_appt['date'] = new_date.date().isoformat()
        new_appt['time'] = new_date.time().strftime('%H:%M')
        new_appt['id'] = f"{base_appt['id']}-{i+1}"
        appointments.append(new_appt)
        current_date = new_date
    return appointments

# Billing and Prescription Helper Functions
def get_bills():
    try:
        with open(BILLS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_bill(bill):
    bills = get_bills()
    bills.append(bill)
    with open(BILLS_FILE, 'w') as f:
        json.dump(bills, f, indent=4)

def get_user_bills(username):
    return [bill for bill in get_bills() if bill['patient'] == username]

def generate_bill_id():
    bills = get_bills()
    if not bills:
        return "1000"
    last_id = max(int(bill['id']) for bill in bills)
    return str(last_id + 1)

def get_prescriptions():
    try:
        with open(PRESCRIPTIONS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_prescription(prescription):
    prescriptions = get_prescriptions()
    prescriptions.append(prescription)
    with open(PRESCRIPTIONS_FILE, 'w') as f:
        json.dump(prescriptions, f, indent=4)

def get_medicine_inventory():
    try:
        with open(MEDICINE_INVENTORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_medicine_inventory(medicine_id, quantity):
    medicines = get_medicine_inventory()
    for med in medicines:
        if med['id'] == medicine_id:
            med['stock'] -= quantity
            break
    with open(MEDICINE_INVENTORY_FILE, 'w') as f:
        json.dump(medicines, f, indent=4)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user', methods=['GET', 'POST'])
def user():
    if request.method == 'POST':
        if 'new_user' in request.form:
            return redirect(url_for('register'))
        elif 'existing_user' in request.form:
            return redirect(url_for('login'))
    return render_template('user.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if verify_admin(password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin password', 'danger')
    return render_template('admin.html')

from datetime import datetime
import re
from werkzeug.security import generate_password_hash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Validate all required fields
            required_fields = {
                'first_name': 'First name',
                'surname': 'Last name',
                'phone': 'Phone number',
                'email': 'Email address',
                'dob': 'Date of birth',
                'username': 'Username',
                'password': 'Password'
            }
            
            # Check for missing or empty fields
            for field, name in required_fields.items():
                if field not in request.form or not request.form[field].strip():
                    flash(f'{name} is required', 'danger')
                    return render_template('register.html', form_data=request.form)

            # Calculate age from dob
            try:
                dob = datetime.strptime(request.form['dob'], '%Y-%m-%d')
                today = datetime.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except ValueError:
                flash('Invalid date format (use YYYY-MM-DD)', 'danger')
                return render_template('register.html', form_data=request.form)

            # Validate username format
            username = request.form['username'].strip()
            if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
                flash('Username must be 4-20 characters (letters, numbers, _)', 'danger')
                return render_template('register.html', form_data=request.form)

            # Validate password strength
            password = request.form['password']
            if len(password) < 8:
                flash('Password must be at least 8 characters', 'danger')
                return render_template('register.html', form_data=request.form)

            # Check if username exists (replace with your actual database check)
            if user_exists(username):  # You need to implement this function
                flash('Username already exists', 'danger')
                return render_template('register.html', form_data=request.form)

            # Prepare user data
            user_details = {
                'first_name': request.form['first_name'].strip(),
                'surname': request.form['surname'].strip(),
                'phone': request.form['phone'].strip(),
                'email': request.form['email'].strip().lower(),
                'dob': request.form['dob'],
                'age': age,
                'blood_type': request.form.get('blood_type', ''),
                'username': username,
                'password_hash': generate_password_hash(password)
            }

            # Save to database (replace with your actual save function)
            if save_user(user_details):  # You need to implement this function
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'danger')

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('register.html', form_data=request.form if request.method == 'POST' else None)

# Helper functions (you need to implement these according to your database)
def user_exists(username):
    """Check if username exists in database"""
    # Example for MongoDB:
    # return db.users.find_one({'username': username}) is not None
    return False  # Replace with actual implementation

def save_user(user_data):
    """Save user to database"""
    # Example for MongoDB:
    # result = db.users.insert_one(user_data)
    # return result.inserted_id is not None
    return True  # Replace with actual implementation

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if verify_user(username, password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/user/dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    user_dir = os.path.join(USERS_DATA_DIR, username)
    files = os.listdir(user_dir) if os.path.exists(user_dir) else []
    
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                try:
                    os.makedirs(user_dir, exist_ok=True)
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(user_dir, filename))
                    flash('File uploaded successfully', 'success')
                except Exception as e:
                    flash(f'File upload failed: {str(e)}', 'danger')
            return redirect(url_for('user_dashboard'))
        
        elif 'doctor' in request.form:
            try:
                dt_str = request.form['date']
                dt = datetime.fromisoformat(dt_str)
            except (ValueError, KeyError):
                flash('Invalid date/time format', 'danger')
                return redirect(url_for('user_dashboard'))
            
            appointment = {
                'id': hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:8],
                'patient': username,
                'doctor': request.form['doctor'],
                'room': request.form['room'],
                'datetime': dt.isoformat(),
                'date': dt.date().isoformat(),
                'time': dt.time().strftime('%H:%M'),
                'duration': request.form.get('duration', '30'),
                'reason': request.form.get('reason', ''),
                'status': 'Scheduled',
                'reminder_profile': request.form.get('reminder_profile', ''),
                'follow_up': {
                    'needed': request.form.get('needs_follow_up', 'no') == 'yes',
                    'date': request.form.get('follow_up_date', ''),
                    'reminder_profile': request.form.get('follow_up_reminder_profile', '')
                }
            }
            
            if request.form.get('recurring', 'no') != 'no':
                freq, count = request.form['recurring'].split('-')
                recurring_appts = create_recurring_appointments(appointment, freq, int(count))
                for appt in recurring_appts:
                    save_appointment(appt)
                flash(f'{len(recurring_appts)} recurring appointments created', 'success')
            else:
                save_appointment(appointment)
                flash('Appointment created successfully', 'success')
            
            return redirect(url_for('user_dashboard'))
    
    appointments = get_user_appointments(username)
    return render_template('user_dashboard.html',
                         files=files,
                         appointments=appointments,
                         doctors=get_doctors(),
                         rooms=get_rooms(),
                         reminder_profiles=get_reminder_profiles(),
                         bills=get_user_bills(username))

@app.route('/admin/dashboard')
# Here the password for admin is 'admin123'.
def admin_dashboard():
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin'))
    
    users = get_all_users()
    user_files = {}
    for user in users:
        user_dir = os.path.join(USERS_DATA_DIR, user)
        if os.path.exists(user_dir):
            files = os.listdir(user_dir)
            user_files[user] = files
    
    return render_template('admin_dashboard.html',
                         users=user_files,
                         appointments=get_all_appointments(),
                         doctors=get_doctors(),
                         rooms=get_rooms(),
                         bills=get_bills())

@app.route('/admin/manage', methods=['GET', 'POST'])
def admin_manage():
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        if 'doctor' in request.form:
            doctors = get_doctors()
            doctors.append(request.form['doctor'])
            with open(DOCTORS_FILE, 'w') as f:
                json.dump(doctors, f)
            flash('Doctor added successfully', 'success')
        elif 'room' in request.form:
            rooms = get_rooms()
            rooms.append(request.form['room'])
            with open(ROOMS_FILE, 'w') as f:
                json.dump(rooms, f)
            flash('Room added successfully', 'success')
    
    return render_template('admin_manage.html',
                         doctors=get_doctors(),
                         rooms=get_rooms())

@app.route('/set-default-profile/<profile_id>', methods=['POST'])
def set_default_profile(profile_id):
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    preferences = get_user_preferences(username)
    preferences['default_reminder_profile'] = profile_id
    save_user_preferences(username, preferences)
    flash('Default reminder profile set', 'success')
    return redirect(url_for('manage_reminder_profiles'))

@app.route('/reminder-profiles', methods=['GET', 'POST'])
def manage_reminder_profiles():
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    
    if request.method == 'POST':
        if 'delete' in request.form:
            profile_id = request.form['delete']
            profiles = [p for p in get_reminder_profiles() if p['id'] != profile_id]
            save_reminder_profiles(profiles)
            flash('Reminder profile deleted', 'success')
            return redirect(url_for('manage_reminder_profiles'))
        
        elif 'set_default' in request.form:
            profile_id = request.form['set_default']
            preferences = get_user_preferences(username)
            preferences['default_reminder_profile'] = profile_id
            save_user_preferences(username, preferences)
            flash('Default reminder profile set', 'success')
            return redirect(url_for('manage_reminder_profiles'))
        
        else:
            profiles = get_reminder_profiles()
            new_profile = {
                'id': hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:8],
                'name': request.form['profile_name'],
                'reminders': []
            }
            
            times = request.form.getlist('reminder_time[]')
            types = request.form.getlist('reminder_type[]')
            messages = request.form.getlist('custom_message[]')
            
            for t, ty, m in zip(times, types, messages):
                if t:
                    new_profile['reminders'].append({
                        'time': int(t),
                        'type': ty,
                        'message': m
                    })
            
            profiles.append(new_profile)
            save_reminder_profiles(profiles)
            flash('Reminder profile created', 'success')
            return redirect(url_for('manage_reminder_profiles'))
    
    preferences = get_user_preferences(username)
    return render_template('reminder_profiles.html',
                         reminder_profiles=get_reminder_profiles(),
                         default_profile=preferences.get('default_reminder_profile'))

# Billing and Prescription Routes
@app.route('/doctor/prescribe', methods=['GET', 'POST'])
def prescribe_medicine():
    if 'username' not in session or not session.get('admin'):
        flash('Doctor access required', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        patient = request.form['patient']
        medicines = []
        total = 0
        
        medicine_ids = request.form.getlist('medicine_id[]')
        quantities = request.form.getlist('quantity[]')
        instructions = request.form.getlist('instructions[]')
        
        inventory = get_medicine_inventory()
        
        for med_id, qty, instr in zip(medicine_ids, quantities, instructions):
            if not qty or int(qty) <= 0:
                continue
                
            med = next((m for m in inventory if m['id'] == int(med_id)), None)
            if med:
                item_total = med['price'] * int(qty)
                medicines.append({
                    'medicine_id': med['id'],
                    'name': med['name'],
                    'quantity': int(qty),
                    'price': med['price'],
                    'instructions': instr,
                    'subtotal': item_total
                })
                total += item_total
        
        if medicines:
            prescription = {
                'id': len(get_prescriptions()) + 1,
                'doctor': session['username'],
                'patient': patient,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'medicines': medicines,
                'total': total,
                'paid': False,
                'notes': request.form.get('notes', '')
            }
            
            save_prescription(prescription)
            
            # Create a bill automatically
            bill = {
                'id': generate_bill_id(),
                'patient': patient,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'due_date': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                'items': [{
                    'description': f"Prescription #{prescription['id']}",
                    'amount': total
                }],
                'total': total,
                'status': 'unpaid',
                'prescription_id': prescription['id']
            }
            save_bill(bill)
            
            flash('Prescription created and bill generated', 'success')
            return redirect(url_for('view_prescription', prescription_id=prescription['id']))
    
    patients = get_all_users()
    medicines = get_medicine_inventory()
    return render_template('prescribe.html', patients=patients, medicines=medicines)

@app.route('/prescription/<int:prescription_id>')
def view_prescription(prescription_id):
    prescription = next((p for p in get_prescriptions() if p['id'] == prescription_id), None)
    if not prescription:
        flash('Prescription not found', 'danger')
        return redirect(url_for('home'))
    
    # Check authorization
    if (session.get('username') not in [prescription['patient'], prescription['doctor']] 
        and not session.get('admin')):
        flash('Not authorized to view this prescription', 'danger')
        return redirect(url_for('home'))
    
    return render_template('view_prescription.html', 
                         prescription=prescription,
                         is_doctor=session.get('username') == prescription['doctor'])

@app.route('/patient/prescriptions')
def patient_prescriptions():
    if 'username' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
    
    prescriptions = [p for p in get_prescriptions() if p['patient'] == session['username']]
    return render_template('patient_prescriptions.html', prescriptions=prescriptions)

@app.route('/pay/prescription/<int:prescription_id>', methods=['POST'])
def pay_prescription(prescription_id):
    if 'username' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
    
    prescriptions = get_prescriptions()
    bills = get_bills()
    
    for pres in prescriptions:
        if pres['id'] == prescription_id and pres['patient'] == session['username']:
            pres['paid'] = True
            # Update corresponding bill
            for bill in bills:
                if bill.get('prescription_id') == prescription_id:
                    bill['status'] = 'paid'
                    bill['payment_date'] = datetime.now().strftime('%Y-%m-%d')
                    break
            
            # Save changes
            with open(PRESCRIPTIONS_FILE, 'w') as f:
                json.dump(prescriptions, f, indent=4)
            with open(BILLS_FILE, 'w') as f:
                json.dump(bills, f, indent=4)
            
            flash('Payment successful!', 'success')
            return redirect(url_for('patient_prescriptions'))
    
    flash('Prescription not found', 'danger')
    return redirect(url_for('patient_prescriptions'))

@app.route('/user/bills')
def view_bills():
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    bills = get_user_bills(username)
    return render_template('bills.html', bills=bills)

@app.route('/bill/<bill_id>')
def view_bill(bill_id):
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    bill = next((b for b in get_bills() if b['id'] == bill_id), None)
    if not bill:
        flash('Bill not found', 'danger')
        return redirect(url_for('view_bills'))
    
    if session.get('admin') or bill['patient'] == session['username']:
        return render_template('bill_detail.html', bill=bill)
    
    flash('Unauthorized access', 'danger')
    return redirect(url_for('view_bills'))

@app.route('/admin/bills', methods=['GET', 'POST'])
def manage_bills():
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        if 'delete' in request.form:
            bill_id = request.form['delete']
            bills = [b for b in get_bills() if b['id'] != bill_id]
            with open(BILLS_FILE, 'w') as f:
                json.dump(bills, f, indent=4)
            flash('Bill deleted successfully', 'success')
            return redirect(url_for('manage_bills'))
        
        new_bill = {
            'id': generate_bill_id(),
            'patient': request.form['username'],
            'date': date.today().isoformat(),
            'items': [],
            'total': 0,
            'status': 'unpaid',
            'due_date': request.form['due_date']
        }
        
        item_names = request.form.getlist('item_name[]')
        item_prices = request.form.getlist('item_price[]')
        
        for name, price in zip(item_names, item_prices):
            if name and price:
                new_bill['items'].append({
                    'description': name,
                    'amount': float(price)
                })
                new_bill['total'] += float(price)
        
        save_bill(new_bill)
        flash('Bill created successfully', 'success')
        return redirect(url_for('manage_bills'))
    
    return render_template('admin_bills.html',
                         bills=get_bills(),
                         users=get_all_users())

@app.route('/pay/<bill_id>', methods=['POST'])
def pay_bill(bill_id):
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    bills = get_bills()
    for bill in bills:
        if bill['id'] == bill_id and bill['patient'] == session['username']:
            bill['status'] = 'paid'
            bill['payment_date'] = date.today().isoformat()
            with open(BILLS_FILE, 'w') as f:
                json.dump(bills, f, indent=4)
            flash('Payment successful!', 'success')
            return redirect(url_for('view_bills'))
    
    flash('Bill not found', 'danger')
    return redirect(url_for('view_bills'))

@app.route('/admin/file/<username>/<filename>')
def admin_view_file(username, filename):
    if 'admin' not in session:
        flash('Admin access required', 'danger')
        return redirect(url_for('admin'))
    
    file_path = os.path.join(USERS_DATA_DIR, username, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash('File not found', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete-file/<filename>', methods=['POST'])
def delete_file(filename):
    if 'username' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    file_path = os.path.join(USERS_DATA_DIR, username, secure_filename(filename))
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            flash('File deleted successfully', 'success')
        return redirect(url_for('user_dashboard'))
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'w') as f:
            f.write(hash_password('admin123'))
    app.run(host='0.0.0.0', port=5000, debug=True)