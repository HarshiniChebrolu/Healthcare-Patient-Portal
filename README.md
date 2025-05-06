# Healthcare Patient Portal

The **Healthcare Patient Portal** is a Python-based application designed to manage healthcare operations such as patient records, doctor details, appointments, billing, medicine inventory, and more — all in a simplified text/JSON-based backend system. It provides a console interface for efficient and accessible healthcare data management.

## 🩺 Features

- Admin login with credentials stored securely
- Manage doctors, patients, rooms, and appointments
- Prescription and billing generation
- Medicine inventory tracking
- Reminder profiles for patients
- File-based storage using `.json` and `.txt` formats

## 📁 Project Structure

```
Patient-Management/
│
├── app.py                         # Main application logic
├── data/
│   ├── admin.txt                  # Admin credentials
│   ├── users.txt                  # Patient/user info
│   ├── doctors.json               # Doctor data
│   ├── appointments.json          # Appointment bookings
│   ├── prescriptions.json         # Medical prescriptions
│   ├── bills.json                 # Billing information
│   ├── rooms.json                 # Hospital room allocation
│   ├── reminder_profiles.json     # Medication reminders
│   ├── medicine_inventory.json    # Available medicines
```

## 🚀 Getting Started

### Prerequisites

- Python 3.6+
- No external libraries needed (uses standard Python libraries)

### Running the Application

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/healthcare-patient-portal.git
   cd healthcare-patient-portal/Patient-Management
   ```

2. Run the app:
   ```bash
   python app.py
   ```

### Sample Admin Login

> Check `data/admin.txt` for credentials (e.g., `admin,admin123`)

## 📌 Future Enhancements

- GUI with Tkinter or web-based interface (Flask/Django)
- SQLite or MySQL database integration
- Authentication improvements
- Patient reports and analytics



## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to fork and submit a pull request!

---

Made with ❤️ for learning and healthcare simulation.
