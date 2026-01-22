from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import json
import os
from datetime import datetime
import csv
from io import StringIO, BytesIO
from flask_cors import CORS

app = Flask(__name__, template_folder='.', static_folder='static')
app_has_started = False

@app.before_request
def startup_tasks():
    global app_has_started
    if not app_has_started:
        initialize_data_files()
        app_has_started = True

CORS(app)

os.makedirs('data', exist_ok=True)
os.makedirs('static', exist_ok=True)

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

initialize_data_files()

users = load_data(USERS_FILE, {})
transactions = load_data(TRANSACTIONS_FILE, {})
settings = load_data(SETTINGS_FILE, {})

@app.route('/')
def index():
    """Render halaman utama"""
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
            .btn {{ background: #3b82f6; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; margin: 10px 5px; }}
            .btn:hover {{ background: #2563eb; }}
        </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ DH Finance - Aplikasi Keuangan Pribadi</h1>
                <div class="error">
                    <strong>Error:</strong> {str(e)}
                </div>
                <div class="info">
                    <h3>File index.html tidak ditemukan</h3>
                    <p>Pastikan file <code>index.html</code> berada di folder yang sama dengan <code>app.py</code></p>
                    <p>Atau download file HTML yang sudah diperbarui:</p>
                    <a href="/api/download-html" class="btn">Download index.html</a>
                    <a href="/api/health" class="btn">Check Server Health</a>
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
                        <li><code>GET /api/stats?username=USERNAME</code> - Get statistik</li>
                        <li><code>GET /api/currencies</code> - Get daftar mata uang</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/api/download-html', methods=['GET'])
def download_html():
    """Download HTML file template"""
    html_content = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DH Finance - Aplikasi Keuangan Pribadi</title>
    <!-- CSS and JS akan dimuat dari server -->
</head>
<body>
    <div id="app">
        Loading DH Finance...
    </div>
    <script>
        // Aplikasi akan dimuat secara dinamis
        fetch('/')
            .then(response => response.text())
            .then(html => {
                document.body.innerHTML = html;
                // Load scripts dynamically
                const scripts = document.querySelectorAll('script');
                scripts.forEach(script => {
                    if (script.src) {
                        const newScript = document.createElement('script');
                        newScript.src = script.src;
                        document.head.appendChild(newScript);
                    }
                });
            })
            .catch(error => {
                document.getElementById('app').innerHTML = 
                    '<div style="padding: 40px; text-align: center; color: #ef4444;">' +
                    '<h2>Error loading application</h2>' +
                    '<p>' + error.message + '</p>' +
                    '<a href="/api/health">Check server status</a>' +
                    '</div>';
            });
    </script>
</body>
</html>"""
    
    mem = BytesIO()
    mem.write(html_content.encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        as_attachment=True,
        download_name='index.html',
        mimetype='text/html'
    )

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
        
        users = load_data(USERS_FILE, {})
        
        if username in users and users[username].get('password') == password:
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
            'password': password,
            'email': email,
            'createdAt': datetime.now().isoformat(),
            'lastLogin': datetime.now().isoformat()
        }
        
        settings_data = load_data(SETTINGS_FILE, {})
        if username not in settings_data:
            settings_data[username] = {
                'currency': 'IDR'
            }
        
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        if username not in transactions_data:
            transactions_data[username] = []
        
        save_data(USERS_FILE, users)
        save_data(SETTINGS_FILE, settings_data)
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
    """API untuk mendapatkan transaksi user dengan filter"""
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
            transactions_data[username] = []
            save_data(TRANSACTIONS_FILE, transactions_data)
            return jsonify({
                'success': True,
                'transactions': [],
                'count': 0,
                'filtered': False
            })
        
        user_transactions = transactions_data[username]
        
        # Apply filter if provided
        if filter_date:
            filtered_transactions = [
                t for t in user_transactions 
                if t.get('date') == filter_date
            ]
            return jsonify({
                'success': True,
                'transactions': filtered_transactions,
                'count': len(filtered_transactions),
                'filtered': True,
                'filterDate': filter_date
            })
        
        return jsonify({
            'success': True,
            'transactions': user_transactions,
            'count': len(user_transactions),
            'filtered': False
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
        
        # Validate proof URL if provided
        has_proof = data.get('hasProof', False)
        proof_details = data.get('proofDetails', '')
        
        if has_proof and proof_details:
            if not proof_details.startswith('http://') and not proof_details.startswith('https://'):
                proof_details = 'https://' + proof_details
        elif not has_proof:
            proof_details = 'Tidak ada bukti transfer'
        
        new_transaction = {
            'id': new_id,
            'type': data.get('type', 'expense'),
            'amount': float(data.get('amount', 0)),
            'description': data.get('description', 'Tanpa keterangan'),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'hasProof': has_proof,
            'proofDetails': proof_details,
            'createdAt': datetime.now().isoformat()
        }
        
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
        
        # Find the transaction
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
        
        # Remove the transaction
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
            'message': 'Mata uang berhasil diupdate',
            'currency': currency
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/currencies', methods=['GET'])
def get_currencies():
    """API untuk mendapatkan daftar mata uang yang tersedia"""
    currencies = {
        'IDR': {'symbol': 'Rp', 'name': 'Rupiah Indonesia'},
        'USD': {'symbol': '$', 'name': 'US Dollar'},
        'EUR': {'symbol': '€', 'name': 'Euro'},
        'GBP': {'symbol': '£', 'name': 'British Pound'},
        'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
        'SGD': {'symbol': 'S$', 'name': 'Singapore Dollar'},
        'THB': {'symbol': '฿', 'name': 'Baht Thailand'},
        'KHR': {'symbol': '៛', 'name': 'Riel Kamboja'}
    }
    
    return jsonify({
        'success': True,
        'currencies': currencies
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API untuk mendapatkan statistik user dengan filter"""
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
            return jsonify({
                'success': True,
                'stats': {
                    'totalIncome': 0,
                    'totalExpense': 0,
                    'balance': 0,
                    'transactionCount': 0,
                    'currency': settings_data.get(username, {}).get('currency', 'IDR'),
                    'filtered': False
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
                'filtered': filter_date is not None,
                'filterDate': filter_date
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    """API untuk ekspor data ke Excel dengan filter"""
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
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        user_transactions = transactions_data[username]
        
        # Apply filter if provided
        if filter_date:
            user_transactions = [
                t for t in user_transactions 
                if t.get('date') == filter_date
            ]
        
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['No', 'Tanggal', 'Jenis', 'Keterangan', 'Jumlah', 'Mata Uang', 'Bukti Transfer', 'Dibuat Pada'])
        
        for i, transaction in enumerate(user_transactions, 1):
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
        
        output.seek(0)
        mem = BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        
        # Create filename with filter info if applicable
        filter_suffix = f"_filter_{filter_date}" if filter_date else ""
        filename = f"dh_finance_{username}{filter_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
    """API untuk ekspor data ke Word (HTML format) dengan filter"""
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
            return jsonify({
                'success': False,
                'message': 'User tidak ditemukan'
            })
        
        user_transactions = transactions_data[username]
        
        # Apply filter if provided
        if filter_date:
            user_transactions = [
                t for t in user_transactions 
                if t.get('date') == filter_date
            ]
        
        user_currency = settings_data.get(username, {}).get('currency', 'IDR')
        
        total_income = sum(
            t.get('amount', 0) 
            for t in user_transactions 
            if t.get('type') == 'income'
        )
        total_expense = sum(
            t.get('amount', 0) 
            for t in user_transactions 
            if t.get('type') == 'expense'
        )
        balance = total_income - total_expense
        
        def format_currency(amount):
            return f"{amount:,.2f}"
        
        # Currency symbols mapping
        currency_symbols = {
            'IDR': 'Rp',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'SGD': 'S$',
            'THB': '฿',
            'KHR': '៛'
        }
        
        symbol = currency_symbols.get(user_currency, user_currency)
        
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
                .filter-info {{ background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Laporan Keuangan DH Finance</h1>
            <p><strong>Pengguna:</strong> {username}</p>
            <p><strong>Tanggal Ekspor:</strong> {datetime.now().strftime('%d %B %Y %H:%M:%S')}</p>
            <p><strong>Mata Uang:</strong> {user_currency} ({symbol})</p>
        """
        
        # Add filter info if applicable
        if filter_date:
            html_content += f"""
            <div class="filter-info">
                <strong>Filter Tanggal:</strong> {filter_date}
            </div>
            """
        
        html_content += f"""
            <div class="summary">
                <p><strong>Total Uang Masuk:</strong> <span class="income">{symbol} {format_currency(total_income)}</span></p>
                <p><strong>Total Uang Keluar:</strong> <span class="expense">{symbol} {format_currency(total_expense)}</span></p>
                <p><strong>Saldo Saat Ini:</strong> <strong>{symbol} {format_currency(balance)}</strong></p>
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
                        <th>Dibuat Pada</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add transaction rows
        for i, transaction in enumerate(user_transactions, 1):
            row_class = 'income' if transaction.get('type') == 'income' else 'expense'
            amount_sign = '+' if transaction.get('type') == 'income' else '-'
            amount_formatted = format_currency(transaction.get('amount', 0))
            
            # Format date for display
            trans_date = transaction.get('date', '')
            try:
                if trans_date:
                    date_obj = datetime.strptime(trans_date, '%Y-%m-%d')
                    trans_date = date_obj.strftime('%d %B %Y')
            except:
                pass
            
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{trans_date}</td>
                        <td>{'Uang Masuk' if transaction.get('type') == 'income' else 'Uang Keluar'}</td>
                        <td>{transaction.get('description', '')}</td>
                        <td class="{row_class}">{amount_sign} {symbol} {amount_formatted}</td>
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
        
        mem = BytesIO()
        mem.write(html_content.encode('utf-8'))
        mem.seek(0)
        
        # Create filename with filter info if applicable
        filter_suffix = f"_filter_{filter_date}" if filter_date else ""
        filename = f"dh_finance_{username}{filter_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.doc"
        
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

@app.route('/api/backup', methods=['GET'])
def backup_data():
    """API untuk backup semua data"""
    try:
        users_data = load_data(USERS_FILE, {})
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        settings_data = load_data(SETTINGS_FILE, {})
        
        backup = {
            'timestamp': datetime.now().isoformat(),
            'users': users_data,
            'transactions': transactions_data,
            'settings': settings_data
        }
        
        mem = BytesIO()
        mem.write(json.dumps(backup, indent=2, ensure_ascii=False).encode('utf-8'))
        mem.seek(0)
        
        filename = f"dh_finance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/restore', methods=['POST'])
def restore_data():
    """API untuk restore data dari backup"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang diupload'
            })
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang dipilih'
            })
        
        if not file.filename.endswith('.json'):
            return jsonify({
                'success': False,
                'message': 'File harus berupa JSON'
            })
        
        backup_data = json.loads(file.read().decode('utf-8'))
        
        # Validate backup structure
        required_keys = ['users', 'transactions', 'settings']
        for key in required_keys:
            if key not in backup_data:
                return jsonify({
                    'success': False,
                    'message': f'Data backup tidak valid: {key} tidak ditemukan'
                })
        
        # Save backup data
        save_data(USERS_FILE, backup_data['users'])
        save_data(TRANSACTIONS_FILE, backup_data['transactions'])
        save_data(SETTINGS_FILE, backup_data['settings'])
        
        return jsonify({
            'success': True,
            'message': 'Data berhasil direstore dari backup'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        users_count = len(load_data(USERS_FILE, {}))
        transactions_data = load_data(TRANSACTIONS_FILE, {})
        total_transactions = sum(len(t) for t in transactions_data.values())
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'data_files': {
                'users': os.path.exists(USERS_FILE),
                'transactions': os.path.exists(TRANSACTIONS_FILE),
                'settings': os.path.exists(SETTINGS_FILE)
            },
            'statistics': {
                'users_count': users_count,
                'total_transactions': total_transactions,
                'demo_user_exists': 'demo' in load_data(USERS_FILE, {})
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        })

@app.route('/api/notification-test', methods=['GET'])
def notification_test():
    """Endpoint untuk testing notifications"""
    return jsonify({
        'success': True,
        'notifications': [
            {
                'type': 'success',
                'title': 'Test Success',
                'message': 'This is a test success notification'
            },
            {
                'type': 'error',
                'title': 'Test Error',
                'message': 'This is a test error notification'
            },
            {
                'type': 'info',
                'title': 'Test Info',
                'message': 'This is a test info notification'
            },
            {
                'type': 'warning',
                'title': 'Test Warning',
                'message': 'This is a test warning notification'
            }
        ]
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({
        'success': False,
        'message': 'Endpoint tidak ditemukan',
        'error': str(e)
    }), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        'success': False,
        'message': 'Terjadi kesalahan internal server',
        'error': str(e)
    }), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)