from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import json
import os
from datetime import datetime
import csv
from io import StringIO, BytesIO
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Enable CORS for all routes

# Buat folder untuk penyimpanan data jika belum ada
os.makedirs('data', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# File data path
USERS_FILE = 'data/users.json'
TRANSACTIONS_FILE = 'data/transactions.json'
SETTINGS_FILE = 'data/settings.json'

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
                'password': 'demo123',
                'email': 'demo@dhfinance.com',
                'createdAt': datetime.now().isoformat(),
                'lastLogin': datetime.now().isoformat()
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
        # Return empty data and try to recreate file
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

# Initialize data files when app starts
initialize_data_files()

# Load initial data
users = load_data(USERS_FILE, {})
transactions = load_data(TRANSACTIONS_FILE, {})
settings = load_data(SETTINGS_FILE, {})

@app.route('/')
def index():
    """Render halaman utama dari templates/index.html"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"""
        <html>
        <head><title>DH Finance - Error</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%); }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 20px 60px rgba(30, 58, 138, 0.15); }}
            h1 {{ color: #1e3a8a; }}
            .error {{ color: #ef4444; background: #fecaca; padding: 15px; border-radius: 10px; margin: 20px 0; }}
            .info {{ background: #dbeafe; padding: 15px; border-radius: 10px; margin: 20px 0; }}
        </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ DH Finance - Aplikasi Keuangan Pribadi</h1>
                <div class="error">
                    <strong>Error:</strong> {str(e)}
                </div>
                <div class="info">
                    <p>File <code>index.html</code> tidak ditemukan di folder <code>templates/</code>.</p>
                    <p>Pastikan struktur folder Anda seperti ini:</p>
                    <pre>
DH_FINANCE/
├── app.py
├── templates/
│   └── index.html
├── data/
│   ├── users.json
│   ├── transactions.json
│   └── settings.json
└── static/
                    </pre>
                </div>
                <div class="info">
                    <p>Server API berjalan dengan baik. Endpoint yang tersedia:</p>
                    <ul>
                        <li><code>POST /api/login</code> - Login user</li>
                        <li><code>POST /api/register</code> - Registrasi user baru</li>
                        <li><code>GET /api/transactions?username=USERNAME</code> - Get transaksi</li>
                        <li><code>POST /api/transactions</code> - Tambah transaksi baru</li>
                        <li><code>DELETE /api/transactions/ID?username=USERNAME</code> - Hapus transaksi</li>
                        <li><code>GET /api/export/excel?username=USERNAME</code> - Ekspor ke Excel</li>
                        <li><code>GET /api/export/word?username=USERNAME</code> - Ekspor ke Word</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files from static folder"""
    return send_from_directory('static', path)

# API Endpoints
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
        
        # Reload users data
        users = load_data(USERS_FILE, {})
        
        # Cek user
        if username in users and users[username].get('password') == password:
            # Update last login
            users[username]['lastLogin'] = datetime.now().isoformat()
            save_data(USERS_FILE, users)
            
            return jsonify({
                'success': True,
                'message': 'Login berhasil',
                'user': {
                    'username': username,
                    'email': users[username].get('email', ''),
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
        
        # Validasi
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
        
        # Reload data
        users = load_data(USERS_FILE, {})
        
        if username in users:
            return jsonify({
                'success': False,
                'message': 'Username sudah terdaftar'
            })
        
        # Create new user
        users[username] = {
            'password': password,
            'email': email,
            'createdAt': datetime.now().isoformat(),
            'lastLogin': datetime.now().isoformat()
        }
        
        # Initialize user settings
        settings = load_data(SETTINGS_FILE, {})
        if username not in settings:
            settings[username] = {
                'currency': 'IDR'
            }
        
        # Initialize empty transactions
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        if username not in transactions_data:
            transactions_data[username] = []
        
        # Save data
        save_data(USERS_FILE, users)
        save_data(SETTINGS_FILE, settings)
        save_data(TRANSACTIONS_FILE, transactions_data)
        
        return jsonify({
            'success': True,
            'message': 'Pendaftaran berhasil! Silakan login dengan akun baru Anda.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """API untuk mendapatkan transaksi user"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        
        if username not in transactions_data:
            transactions_data[username] = []
            save_data(TRANSACTIONS_FILE, transactions_data)
            
        return jsonify({
            'success': True,
            'transactions': transactions_data[username],
            'count': len(transactions_data[username])
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
        
        # Load current transactions
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        
        # Initialize if not exists
        if username not in transactions_data:
            transactions_data[username] = []
        
        # Get the highest ID
        existing_ids = [t.get('id', 0) for t in transactions_data[username]]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        
        # Create new transaction
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
        
        # Add transaction
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
        
        # Load current transactions
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        # Find and remove transaction
        initial_length = len(transactions_data[username])
        transactions_data[username] = [
            t for t in transactions_data[username] 
            if t.get('id') != transaction_id
        ]
        
        if len(transactions_data[username]) < initial_length:
            save_data(TRANSACTIONS_FILE, transactions_data)
            return jsonify({
                'success': True,
                'message': 'Transaksi berhasil dihapus!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Transaksi tidak ditemukan'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

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
        
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in settings_data:
            settings_data[username] = {}
        
        settings_data[username]['currency'] = currency
        save_data(SETTINGS_FILE, settings_data)
        
        return jsonify({
            'success': True,
            'message': 'Mata uang berhasil diupdate'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    """API untuk ekspor data ke Excel"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        # Load data
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        # Get user settings
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        
        # Create CSV data
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['No', 'Tanggal', 'Jenis', 'Keterangan', 'Jumlah', 'Mata Uang', 'Bukti Transfer', 'Dibuat Pada'])
        
        # Write data
        for i, transaction in enumerate(transactions_data[username], 1):
            writer.writerow([
                i,
                transaction.get('date', ''),
                'Uang Masuk' if transaction.get('type') == 'income' else 'Uang Keluar',
                transaction.get('description', ''),
                f"{transaction.get('amount', 0):.2f}",
                user_currency,
                transaction.get('proofDetails', ''),
                transaction.get('createdAt', '')
            ])
        
        # Create response
        output.seek(0)
        mem = BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))  # utf-8-sig for Excel compatibility
        mem.seek(0)
        
        filename = f"dh_finance_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/export/word', methods=['GET'])
def export_word():
    """API untuk ekspor data ke Word (HTML format)"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        # Load data
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        # Get user settings
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        
        # Calculate totals
        total_income = sum(
            t.get('amount', 0) 
            for t in transactions_data[username] 
            if t.get('type') == 'income'
        )
        total_expense = sum(
            t.get('amount', 0) 
            for t in transactions_data[username] 
            if t.get('type') == 'expense'
        )
        balance = total_income - total_expense
        
        # Format currency
        def format_currency(amount):
            return f"{amount:,.2f}"
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Laporan Keuangan DH Finance</title>
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
            <p><strong>Tanggal Ekspor:</strong> {datetime.now().strftime('%d %B %Y %H:%M:%S')}</p>
            <p><strong>Mata Uang:</strong> {user_currency}</p>
            
            <div class="summary">
                <p><strong>Total Uang Masuk:</strong> <span class="income">{format_currency(total_income)} {user_currency}</span></p>
                <p><strong>Total Uang Keluar:</strong> <span class="expense">{format_currency(total_expense)} {user_currency}</span></p>
                <p><strong>Saldo Saat Ini:</strong> <strong>{format_currency(balance)} {user_currency}</strong></p>
                <p><strong>Jumlah Transaksi:</strong> {len(transactions_data[username])}</p>
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
                        <th>Dibuat Pada</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add transaction rows
        for i, transaction in enumerate(transactions_data[username], 1):
            row_class = 'income' if transaction.get('type') == 'income' else 'expense'
            amount_sign = '+' if transaction.get('type') == 'income' else '-'
            amount_formatted = format_currency(transaction.get('amount', 0))
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{transaction.get('date', '')}</td>
                        <td>{'Uang Masuk' if transaction.get('type') == 'income' else 'Uang Keluar'}</td>
                        <td>{transaction.get('description', '')}</td>
                        <td class="{row_class}">{amount_sign} {amount_formatted} {user_currency}</td>
                        <td>{transaction.get('proofDetails', '')}</td>
                        <td>{transaction.get('createdAt', '')}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
            
            <div class="footer">
                <p>&copy; """ + str(datetime.now().year) + """ DH Finance - Aplikasi Manajemen Keuangan Pribadi</p>
                <p>Dokumen ini dibuat secara otomatis oleh sistem DH Finance</p>
            </div>
        </body>
        </html>
        """
        
        # Create response
        mem = BytesIO()
        mem.write(html_content.encode('utf-8'))
        mem.seek(0)
        
        filename = f"dh_finance_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.doc"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='application/msword'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API untuk mendapatkan statistik user"""
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username tidak ditemukan'
            })
        
        # Load data
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        if username not in transactions_data:
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        # Calculate stats
        user_transactions = transactions_data[username]
        total_income = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'income')
        total_expense = sum(t.get('amount', 0) for t in user_transactions if t.get('type') == 'expense')
        balance = total_income - total_expense
        
        # Get currency
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        
        return jsonify({
            'success': True,
            'stats': {
                'totalIncome': total_income,
                'totalExpense': total_expense,
                'balance': balance,
                'transactionCount': len(user_transactions),
                'currency': user_currency
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/init-demo', methods=['POST'])
def init_demo():
    """API untuk inisialisasi data demo"""
    try:
        initialize_data_files()
        
        return jsonify({
            'success': True,
            'message': 'Data demo berhasil diinisialisasi'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_files': {
            'users': os.path.exists(USERS_FILE),
            'transactions': os.path.exists(TRANSACTIONS_FILE),
            'settings': os.path.exists(SETTINGS_FILE)
        }
    })

if __name__ == '__main__':
    # Initialize data files
    initialize_data_files()
    
    print("=" * 50)
    print("DH Finance Application")
    print("=" * 50)
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Template Folder: {app.template_folder}")
    print(f"Static Folder: {app.static_folder}")
    print("=" * 50)
    
    # Check if index.html exists in templates folder
    template_path = os.path.join('templates', 'index.html')
    if os.path.exists(template_path):
        print(f"✓ Found index.html in templates folder")
    else:
        print(f"✗ index.html NOT found in templates folder")
        print(f"  Looking for: {os.path.abspath(template_path)}")
        print("  Please make sure your HTML file is in the templates folder")
    
    print("=" * 50)
    print("Server running at: http://localhost:5000")
    print("Demo account: demo / demo123")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)