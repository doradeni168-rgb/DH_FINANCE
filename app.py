from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, Response
import json
import os
from datetime import datetime, timedelta
import csv
from io import StringIO, BytesIO
from flask_cors import CORS
import pathlib
import zipfile
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'dh_finance_secret_key_2024'
app_has_started = False

# Path untuk templates (sesuaikan dengan lokasi Anda)
TEMPLATE_PATH = r'C:\Users\DENI\Documents\Work\DH_FINANCE\templates'
# Jika ingin relatif ke project, gunakan:
# TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Path untuk data
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_PATH, exist_ok=True)

# File data path
USERS_FILE = os.path.join(DATA_PATH, 'users.json')
TRANSACTIONS_FILE = os.path.join(DATA_PATH, 'transactions.json')
SETTINGS_FILE = os.path.join(DATA_PATH, 'settings.json')
BACKUP_PATH = os.path.join(DATA_PATH, 'backups')
os.makedirs(BACKUP_PATH, exist_ok=True)

# Currency data (sama seperti di frontend)
CURRENCIES = {
    'IDR': {'symbol': 'Rp', 'name': 'Rupiah Indonesia'},
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
    'SGD': {'symbol': 'S$', 'name': 'Singapore Dollar'},
    'THB': {'symbol': '฿', 'name': 'Baht Thailand'},
    'KHR': {'symbol': '៛', 'name': 'Riel Kamboja'}
}

@app.before_request
def startup_tasks():
    global app_has_started
    if not app_has_started:
        initialize_data_files()
        app_has_started = True

CORS(app)

def initialize_data_files():
    """Initialize data files if they don't exist"""
    default_files = {
        USERS_FILE: {},
        TRANSACTIONS_FILE: {},
        SETTINGS_FILE: {}
    }
    
    for file_path, default_data in default_files.items():
        if not os.path.exists(file_path):
            print(f"Creating {file_path}...")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    # Initialize demo user data
    init_demo_data()

def init_demo_data():
    """Initialize demo user data"""
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        with open(TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
            transactions = json.load(f)
        
        demo_user = 'demo'
        
        # Create demo user if not exists
        if demo_user not in users:
            users[demo_user] = {
                'password': generate_password_hash('demo123'),
                'email': 'demo@dhfinance.com',
                'createdAt': datetime.now().isoformat(),
                'lastLogin': datetime.now().isoformat(),
                'fullname': 'Demo User'
            }
            print(f"Created demo user: {demo_user}")
        
        # Initialize settings for demo
        if demo_user not in settings:
            settings[demo_user] = {
                'currency': 'IDR'
            }
        
        # Add sample transactions if not exists or empty
        if demo_user not in transactions or len(transactions.get(demo_user, [])) == 0:
            sample_transactions = [
                {
                    'id': 1,
                    'type': 'income',
                    'amount': 1000000,
                    'description': 'Gaji Bulanan',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'hasProof': True,
                    'proofDetails': 'https://prnt.sc/fk8Ctptkwt3',
                    'createdAt': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'type': 'expense',
                    'amount': 125000,
                    'description': 'Belanja Bulanan',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'hasProof': False,
                    'proofDetails': 'Tidak ada bukti transfer',
                    'createdAt': datetime.now().isoformat()
                },
                {
                    'id': 3,
                    'type': 'income',
                    'amount': 500000,
                    'description': 'Transfer dari Klien',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'hasProof': True,
                    'proofDetails': 'https://example.com/bukti-transfer.jpg',
                    'createdAt': datetime.now().isoformat()
                }
            ]
            transactions[demo_user] = sample_transactions
            print(f"Created sample transactions for {demo_user}")
        
        # Save all data
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        with open(TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
            
        print("Demo data initialization complete!")
        
    except Exception as e:
        print(f"Error initializing demo data: {e}")

def load_data(file_path, default_data=None):
    """Load data from JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif default_data is not None:
            # Create file with default data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data
        else:
            return {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {file_path}: {e}")
        if default_data is not None:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data
        return {}

def save_data(file_path, data):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")
        return False

def format_currency(amount, currency_code='IDR'):
    """Format currency according to user preference"""
    currency = CURRENCIES.get(currency_code, CURRENCIES['IDR'])
    return f"{currency['symbol']} {format_number(amount)}"

def format_number(number):
    """Format number with Indonesian locale"""
    return f"{number:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def create_backup():
    """Create backup of all data"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_PATH, f'backup_{timestamp}.zip')
        
        with zipfile.ZipFile(backup_file, 'w') as backup_zip:
            for file_name in [USERS_FILE, TRANSACTIONS_FILE, SETTINGS_FILE]:
                if os.path.exists(file_name):
                    backup_zip.write(file_name, os.path.basename(file_name))
        
        return backup_file
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

# Initialize data
initialize_data_files()

@app.route('/')
def index():
    """Render halaman utama dari templates"""
    try:
        # Path ke index.html
        index_path = os.path.join(TEMPLATE_PATH, 'index.html')
        
        # Cek apakah file index.html ada
        if not os.path.exists(index_path):
            # Jika tidak ada, kembalikan HTML sederhana
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>DH Finance - Aplikasi Keuangan Pribadi</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%); }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 20px 60px rgba(30, 58, 138, 0.15); }
                    h1 { color: #1e3a8a; }
                    .error { color: #ef4444; background: #fecaca; padding: 15px; border-radius: 10px; margin: 20px 0; }
                    .info { background: #dbeafe; padding: 15px; border-radius: 10px; margin: 20px 0; }
                    .btn { background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; margin: 10px 5px; }
                    .btn:hover { background: #2563eb; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>DH Finance - Aplikasi Keuangan Pribadi</h1>
                    <div class="error">
                        <strong>File index.html tidak ditemukan!</strong>
                        <p>Silakan simpan file index.html di: <code>{}</code></p>
                    </div>
                    <div class="info">
                        <h3>API Server Berjalan dengan Baik!</h3>
                        <p>Backend API siap digunakan. Endpoint yang tersedia:</p>
                        <ul>
                            <li><strong>/api/login</strong> - Login user</li>
                            <li><strong>/api/register</strong> - Registrasi user baru</li>
                            <li><strong>/api/transactions</strong> - Kelola transaksi</li>
                            <li><strong>/api/settings</strong> - Pengaturan user</li>
                            <li><strong>/api/currencies</strong> - Data mata uang</li>
                            <li><strong>/api/export/excel</strong> - Ekspor ke Excel</li>
                            <li><strong>/api/export/word</strong> - Ekspor ke Word</li>
                            <li><strong>/api/backup</strong> - Backup data</li>
                            <li><strong>/api/restore</strong> - Restore data</li>
                        </ul>
                        <a href="/api/health" class="btn">Check Server Health</a>
                    </div>
                </div>
            </body>
            </html>
            '''.format(TEMPLATE_PATH)
        
        # Baca file HTML
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return html_content
        
    except Exception as e:
        return f'''
        <html>
        <head><title>DH Finance - Error</title></head>
        <body>
            <h1>Error Loading DH Finance</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        '''

# ================ AUTHENTICATION API ================

@app.route('/api/login', methods=['POST'])
def login():
    """API untuk login user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username dan password harus diisi'
            })
        
        users = load_data(USERS_FILE, {})
        
        if username in users and check_password_hash(users[username].get('password', ''), password):
            users[username]['lastLogin'] = datetime.now().isoformat()
            save_data(USERS_FILE, users)
            
            return jsonify({
                'success': True,
                'message': 'Login berhasil',
                'user': {
                    'username': username,
                    'email': users[username].get('email', ''),
                    'fullname': users[username].get('fullname', username),
                    'createdAt': users[username].get('createdAt', ''),
                    'lastLogin': users[username].get('lastLogin', '')
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Username atau password salah'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/register', methods=['POST'])
def register():
    """API untuk registrasi user baru"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username dan password harus diisi'
            })
        
        if len(username) < 3:
            return jsonify({
                'success': False,
                'message': 'Username minimal 3 karakter'
            })
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password minimal 6 karakter'
            })
        
        users = load_data(USERS_FILE, {})
        
        if username in users:
            return jsonify({
                'success': False,
                'message': 'Username sudah terdaftar'
            })
        
        users[username] = {
            'password': generate_password_hash(password),
            'email': email,
            'fullname': username,
            'createdAt': datetime.now().isoformat(),
            'lastLogin': datetime.now().isoformat()
        }
        
        save_data(USERS_FILE, users)
        
        # Initialize settings and transactions
        settings = load_data(SETTINGS_FILE, {})
        settings[username] = {'currency': 'IDR'}
        save_data(SETTINGS_FILE, settings)
        
        transactions = load_data(TRANSACTIONS_FILE, {})
        transactions[username] = []
        save_data(TRANSACTIONS_FILE, transactions)
        
        return jsonify({
            'success': True,
            'message': 'Pendaftaran berhasil! Silakan login dengan akun baru Anda.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/logout', methods=['POST'])
def logout():
    """API untuk logout user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if username:
            users = load_data(USERS_FILE, {})
            if username in users:
                users[username]['lastLogin'] = datetime.now().isoformat()
                save_data(USERS_FILE, users)
        
        return jsonify({
            'success': True,
            'message': 'Logout berhasil'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

# ================ TRANSACTIONS API ================

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """API untuk mendapatkan transaksi user"""
    try:
        username = request.args.get('username')
        filter_date = request.args.get('filterDate')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({
                'success': True,
                'transactions': [],
                'count': 0,
                'stats': {
                    'totalIncome': 0,
                    'totalExpense': 0,
                    'balance': 0
                }
            })
        
        user_transactions = transactions_data[username]
        
        # Apply filter if provided
        if filter_date:
            user_transactions = [
                t for t in user_transactions 
                if t.get('date') == filter_date
            ]
        
        # Calculate statistics
        total_income = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'income')
        total_expense = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'expense')
        balance = total_income - total_expense
        
        return jsonify({
            'success': True,
            'transactions': user_transactions,
            'count': len(user_transactions),
            'filtered': filter_date is not None,
            'stats': {
                'totalIncome': total_income,
                'totalExpense': total_expense,
                'balance': balance
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """API untuk menambah transaksi baru"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        
        if username not in transactions_data:
            transactions_data[username] = []
        
        # Generate new ID
        existing_ids = [t.get('id', 0) for t in transactions_data[username]]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        
        new_transaction = {
            'id': new_id,
            'type': data.get('type', 'expense'),
            'amount': float(data.get('amount', 0)),
            'description': data.get('description', 'Tanpa keterangan'),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'hasProof': data.get('hasProof', False),
            'proofDetails': data.get('proofDetails', 'Tidak ada bukti transfer'),
            'createdAt': datetime.now().isoformat()
        }
        
        # Validasi URL bukti transfer
        if new_transaction['hasProof'] and new_transaction['proofDetails'] != 'Tidak ada bukti transfer':
            if not (new_transaction['proofDetails'].startswith('http://') or 
                   new_transaction['proofDetails'].startswith('https://')):
                new_transaction['proofDetails'] = 'https://' + new_transaction['proofDetails']
        
        transactions_data[username].append(new_transaction)
        save_data(TRANSACTIONS_FILE, transactions_data)
        
        return jsonify({
            'success': True,
            'message': 'Transaksi berhasil disimpan!',
            'transaction': new_transaction
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """API untuk menghapus transaksi"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        # Find transaction
        transaction_to_delete = None
        for t in transactions_data[username]:
            if t.get('id') == transaction_id:
                transaction_to_delete = t
                break
        
        if not transaction_to_delete:
            return jsonify({
                'success': False,
                'message': 'Transaksi tidak ditemukan'
            })
        
        # Remove transaction
        transactions_data[username] = [
            t for t in transactions_data[username] 
            if t.get('id') != transaction_id
        ]
        
        save_data(TRANSACTIONS_FILE, transactions_data)
        
        return jsonify({
            'success': True,
            'message': 'Transaksi berhasil dihapus!',
            'deletedTransaction': transaction_to_delete
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

# ================ SETTINGS API ================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """API untuk mendapatkan pengaturan user"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in settings_data:
            settings_data[username] = {'currency': 'IDR'}
            save_data(SETTINGS_FILE, settings_data)
        
        return jsonify({
            'success': True,
            'settings': settings_data[username]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/settings/currency', methods=['POST'])
def update_currency():
    """API untuk mengupdate mata uang user"""
    try:
        data = request.get_json()
        username = data.get('username')
        currency = data.get('currency', 'IDR')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        if currency not in CURRENCIES:
            return jsonify({
                'success': False,
                'message': 'Mata uang tidak valid'
            })
        
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in settings_data:
            settings_data[username] = {}
        
        settings_data[username]['currency'] = currency
        save_data(SETTINGS_FILE, settings_data)
        
        return jsonify({
            'success': True,
            'message': 'Mata uang berhasil diupdate',
            'currency': currency,
            'currencyData': CURRENCIES[currency]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

# ================ CURRENCIES API ================

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """API untuk mendapatkan data mata uang"""
    try:
        return jsonify({
            'success': True,
            'currencies': CURRENCIES
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

# ================ EXPORT API ================

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    """Export transactions to Excel (CSV format)"""
    try:
        username = request.args.get('username')
        filter_date = request.args.get('filterDate')
        
        if not username:
            return jsonify({'success': False, 'message': 'Username required'})
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({'success': False, 'message': 'User not found'})
        
        user_transactions = transactions_data[username]
        if filter_date:
            user_transactions = [t for t in user_transactions if t.get('date') == filter_date]
        
        # Get user currency
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        currency_symbol = CURRENCIES.get(user_currency, CURRENCIES['IDR'])['symbol']
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['No', 'Tanggal', 'Jenis', 'Keterangan', 'Jumlah', 'Bukti Transfer', 'Dibuat Pada'])
        
        # Write data
        for idx, tx in enumerate(user_transactions, 1):
            tx_type = 'Uang Masuk' if tx.get('type') == 'income' else 'Uang Keluar'
            amount_display = f"{currency_symbol} {format_number(tx.get('amount', 0))}"
            
            writer.writerow([
                idx,
                tx.get('date', ''),
                tx_type,
                tx.get('description', ''),
                amount_display,
                tx.get('proofDetails', ''),
                tx.get('createdAt', '')[:19].replace('T', ' ')
            ])
        
        output.seek(0)
        mem = BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        
        # Create filename
        date_str = filter_date if filter_date else datetime.now().strftime('%Y-%m-%d')
        filename = f"dh_finance_transaksi_{username}_{date_str}.csv"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/export/word', methods=['GET'])
def export_word():
    """Export transactions to Word (HTML format that can be opened in Word)"""
    try:
        username = request.args.get('username')
        filter_date = request.args.get('filterDate')
        
        if not username:
            return jsonify({'success': False, 'message': 'Username required'})
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({'success': False, 'message': 'User not found'})
        
        user_transactions = transactions_data[username]
        if filter_date:
            user_transactions = [t for t in user_transactions if t.get('date') == filter_date]
        
        # Get user currency
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        currency_symbol = CURRENCIES.get(user_currency, CURRENCIES['IDR'])['symbol']
        
        # Calculate totals
        total_income = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'income')
        total_expense = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'expense')
        balance = total_income - total_expense
        
        # Create Word document (HTML format)
        word_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Laporan Keuangan DH Finance - {username}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #1e3a8a; border-bottom: 2px solid #1d4ed8; padding-bottom: 10px; }}
        h2 {{ color: #1e3a8a; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th {{ background-color: #dbeafe; color: #1e3a8a; padding: 12px; text-align: left; border: 1px solid #93c5fd; }}
        td {{ padding: 10px; border: 1px solid #93c5fd; }}
        .income {{ color: #10b981; }}
        .expense {{ color: #ef4444; }}
        .summary {{ background-color: #f8fafc; padding: 20px; border-radius: 10px; margin-top: 30px; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #64748b; text-align: center; }}
    </style>
</head>
<body>
    <h1>Laporan Keuangan DH Finance</h1>
    <p><strong>Pengguna:</strong> {username}</p>
    <p><strong>Tanggal Ekspor:</strong> {datetime.now().strftime('%d %B %Y, %H:%M')}</p>
    <p><strong>Mata Uang:</strong> {user_currency} ({currency_symbol})</p>
    {f'<p><strong>Filter Tanggal:</strong> {filter_date}</p>' if filter_date else ''}
    
    <div class="summary">
        <h2>Ringkasan Keuangan</h2>
        <p><strong>Total Uang Masuk:</strong> <span class="income">{currency_symbol} {format_number(total_income)}</span></p>
        <p><strong>Total Uang Keluar:</strong> <span class="expense">{currency_symbol} {format_number(total_expense)}</span></p>
        <p><strong>Saldo Saat Ini:</strong> <strong>{currency_symbol} {format_number(balance)}</strong></p>
        <p><strong>Jumlah Transaksi:</strong> {len(user_transactions)}</p>
    </div>
    
    <h2>Detail Transaksi</h2>
    <table>
        <thead>
            <tr>
                <th>No</th>
                <th>Tanggal</th>
                <th>Jenis</th>
                <th>Keterangan</th>
                <th>Jumlah</th>
                <th>Bukti Transfer</th>
            </tr>
        </thead>
        <tbody>"""
        
        # Add transaction rows
        for idx, tx in enumerate(user_transactions, 1):
            tx_type = 'Uang Masuk' if tx.get('type') == 'income' else 'Uang Keluar'
            amount_display = f"{'+' if tx.get('type') == 'income' else '-'} {currency_symbol} {format_number(tx.get('amount', 0))}"
            row_class = 'income' if tx.get('type') == 'income' else 'expense'
            
            word_content += f"""
            <tr>
                <td>{idx}</td>
                <td>{tx.get('date', '')}</td>
                <td>{tx_type}</td>
                <td>{tx.get('description', '')}</td>
                <td class="{row_class}">{amount_display}</td>
                <td>{tx.get('proofDetails', '')}</td>
            </tr>"""
        
        word_content += f"""
        </tbody>
    </table>
    
    <div class="footer">
        <p>&copy; {datetime.now().year} DH Finance - Aplikasi Manajemen Keuangan Pribadi</p>
        <p>Dokumen ini dibuat secara otomatis oleh sistem DH Finance</p>
    </div>
</body>
</html>"""
        
        # Create blob and download
        mem = BytesIO()
        mem.write(word_content.encode('utf-8'))
        mem.seek(0)
        
        # Create filename
        date_str = filter_date if filter_date else datetime.now().strftime('%Y-%m-%d')
        filename = f"dh_finance_transaksi_{username}_{date_str}.doc"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='application/msword'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ================ BACKUP & RESTORE API ================

@app.route('/api/backup', methods=['POST'])
def backup_data():
    """Create backup of all data"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        backup_file = create_backup()
        
        if backup_file:
            return jsonify({
                'success': True,
                'message': 'Backup berhasil dibuat',
                'backupFile': os.path.basename(backup_file),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Gagal membuat backup'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """List all available backups"""
    try:
        backups = []
        if os.path.exists(BACKUP_PATH):
            for file_name in os.listdir(BACKUP_PATH):
                if file_name.endswith('.zip'):
                    file_path = os.path.join(BACKUP_PATH, file_name)
                    file_stat = os.stat(file_path)
                    backups.append({
                        'name': file_name,
                        'size': file_stat.st_size,
                        'created': datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
        
        return jsonify({
            'success': True,
            'backups': sorted(backups, key=lambda x: x['modified'], reverse=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    """Download backup file"""
    try:
        # Security check
        if '..' in filename or filename.startswith('/'):
            return jsonify({
                'success': False,
                'message': 'Invalid filename'
            })
        
        backup_path = os.path.join(BACKUP_PATH, filename)
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'message': 'Backup file not found'
            })
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

# ================ STATISTICS API ================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API untuk mendapatkan statistik user"""
    try:
        username = request.args.get('username')
        filter_date = request.args.get('filterDate')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in transactions_data:
            user_currency = settings_data.get(username, {}).get('currency', 'IDR')
            return jsonify({
                'success': True,
                'stats': {
                    'totalIncome': 0,
                    'totalExpense': 0,
                    'balance': 0,
                    'transactionCount': 0,
                    'currency': user_currency,
                    'currencyData': CURRENCIES.get(user_currency, CURRENCIES['IDR'])
                }
            })
        
        user_transactions = transactions_data[username]
        
        # Apply filter if provided
        if filter_date:
            user_transactions = [
                t for t in user_transactions 
                if t.get('date') == filter_date
            ]
        
        total_income = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'income')
        total_expense = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'expense')
        balance = total_income - total_expense
        
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        
        return jsonify({
            'success': True,
            'stats': {
                'totalIncome': total_income,
                'totalExpense': total_expense,
                'balance': balance,
                'transactionCount': len(user_transactions),
                'currency': user_currency,
                'currencyData': CURRENCIES.get(user_currency, CURRENCIES['IDR'])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

# ================ HEALTH & INFO API ================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if template file exists
        index_path = os.path.join(TEMPLATE_PATH, 'index.html')
        template_exists = os.path.exists(index_path)
        
        # Load data stats
        users = load_data(USERS_FILE, {})
        transactions = load_data(TRANSACTIONS_FILE, {})
        
        total_transactions = 0
        for user_tx in transactions.values():
            total_transactions += len(user_tx)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'server_info': {
                'template_path': TEMPLATE_PATH,
                'template_exists': template_exists,
                'data_path': DATA_PATH,
                'backup_path': BACKUP_PATH
            },
            'data_stats': {
                'users_count': len(users),
                'total_transactions': total_transactions,
                'demo_user_exists': 'demo' in users
            },
            'api_endpoints': {
                'auth': ['/api/login', '/api/register', '/api/logout'],
                'transactions': ['/api/transactions', '/api/transactions/<id>'],
                'settings': ['/api/settings', '/api/settings/currency'],
                'currencies': ['/api/currencies'],
                'export': ['/api/export/excel', '/api/export/word'],
                'backup': ['/api/backup', '/api/backup/list', '/api/backup/download/<filename>'],
                'stats': ['/api/stats'],
                'health': ['/api/health']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        })

@app.route('/api/info', methods=['GET'])
def server_info():
    """Get server information"""
    try:
        import platform
        import sys
        
        return jsonify({
            'success': True,
            'info': {
                'python_version': sys.version,
                'platform': platform.platform(),
                'server_time': datetime.now().isoformat(),
                'template_path': TEMPLATE_PATH,
                'data_path': DATA_PATH,
                'users_file': USERS_FILE,
                'transactions_file': TRANSACTIONS_FILE,
                'settings_file': SETTINGS_FILE
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# ================ MAIN ================

if __name__ == "__main__":
    print("=" * 60)
    print("DH FINANCE - APLIKASI KEUANGAN PRIBADI")
    print("=" * 60)
    print(f"Template Path: {TEMPLATE_PATH}")
    print(f"Data Path: {DATA_PATH}")
    print(f"Backup Path: {BACKUP_PATH}")
    print(f"Server akan berjalan di http://localhost:10000")
    print("=" * 60)
    
    # Check if template file exists
    index_path = os.path.join(TEMPLATE_PATH, 'index.html')
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)