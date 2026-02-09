from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
import json
import sqlite3

# Initialize app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dh-finance-secret-2024')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_COOKIE_SECURE'] = False  # Set True for production with HTTPS
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Set True for production

# FIX: Gunakan path absolut untuk database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'finance.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    currency = db.Column(db.String(10), default='IDR')
    
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500))
    date = db.Column(db.String(20), nullable=False)
    has_proof = db.Column(db.Boolean, default=False)
    proof_details = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Auth Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username dan password wajib diisi'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password minimal 6 karakter'}), 400
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username sudah terdaftar'}), 400
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user
        new_user = User(
            username=username,
            email=email or f"{username}@dhfinance.app",
            password=hashed_password,
            last_login=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(new_user.id))
        
        return jsonify({
            'success': True,
            'message': 'Registrasi berhasil',
            'token': access_token,
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'currency': new_user.currency
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username dan password wajib diisi'}), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'Username atau password salah'}), 401
        
        # Check password
        if not bcrypt.check_password_hash(user.password, password):
            return jsonify({'error': 'Username atau password salah'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': 'Login berhasil',
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'currency': user.currency
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/check', methods=['GET'])
@jwt_required(optional=True)
def check_auth():
    current_user_id = get_jwt_identity()
    if current_user_id:
        try:
            user = User.query.get(int(current_user_id))
            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'currency': user.currency
                    }
                })
        except Exception as e:
            print(f"Error checking auth: {e}")
            return jsonify({'authenticated': False})
    
    return jsonify({'authenticated': False})

# Transaction Routes
@app.route('/api/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get filter parameters
        date_filter = request.args.get('date')
        
        # Query transactions
        query = Transaction.query.filter_by(user_id=current_user_id)
        
        if date_filter:
            query = query.filter_by(date=date_filter)
        
        transactions = query.order_by(Transaction.date.desc()).all()
        
        # Format response
        transactions_data = []
        for t in transactions:
            transactions_data.append({
                'id': t.id,
                'type': t.type,
                'amount': t.amount,
                'description': t.description,
                'date': t.date,
                'hasProof': t.has_proof,
                'proofDetails': t.proof_details,
                'createdAt': t.created_at.isoformat() if t.created_at else None
            })
        
        return jsonify(transactions_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
@jwt_required()
def add_transaction():
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'amount', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Field {field} diperlukan'}), 400
        
        # Create transaction
        new_transaction = Transaction(
            user_id=current_user_id,
            type=data['type'],
            amount=float(data['amount']),
            description=data.get('description', ''),
            date=data['date'],
            has_proof=data.get('hasProof', False),
            proof_details=data.get('proofDetails', '')
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transaksi berhasil disimpan',
            'transaction': {
                'id': new_transaction.id,
                'type': new_transaction.type,
                'amount': new_transaction.amount,
                'description': new_transaction.description,
                'date': new_transaction.date,
                'hasProof': new_transaction.has_proof,
                'proofDetails': new_transaction.proof_details
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # Find transaction
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user_id
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaksi tidak ditemukan'}), 404
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Transaksi berhasil dihapus'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# User Settings Routes
@app.route('/api/user/settings', methods=['GET'])
@jwt_required()
def get_settings():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User tidak ditemukan'}), 404
        
        return jsonify({
            'currency': user.currency
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User tidak ditemukan'}), 404
        
        data = request.get_json()
        
        if 'currency' in data:
            user.currency = data['currency']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pengaturan berhasil diperbarui',
            'settings': {
                'currency': user.currency
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Dashboard Stats
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    try:
        current_user_id = int(get_jwt_identity())
        
        # Query all transactions for this user
        transactions = Transaction.query.filter_by(user_id=current_user_id).all()
        
        # Calculate stats
        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')
        balance = total_income - total_expense
        
        # Get user currency
        user = User.query.get(current_user_id)
        
        return jsonify({
            'balance': balance,
            'totalIncome': total_income,
            'totalExpense': total_expense,
            'transactionCount': len(transactions),
            'currency': user.currency if user else 'IDR'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Export Routes
@app.route('/api/export/excel', methods=['GET'])
@jwt_required()
def export_excel():
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get filter parameters
        date_filter = request.args.get('date')
        
        # Query transactions
        query = Transaction.query.filter_by(user_id=current_user_id)
        
        if date_filter:
            query = query.filter_by(date=date_filter)
        
        transactions = query.order_by(Transaction.date.desc()).all()
        
        # Get user info
        user = User.query.get(current_user_id)
        
        # Format data for export
        export_data = []
        total_income = 0
        total_expense = 0
        
        for t in transactions:
            if t.type == 'income':
                total_income += t.amount
            else:
                total_expense += t.amount
            
            export_data.append({
                'Tanggal': t.date,
                'Jenis': 'Uang Masuk' if t.type == 'income' else 'Uang Keluar',
                'Keterangan': t.description,
                'Jumlah': t.amount,
                'Mata Uang': user.currency,
                'Bukti Transfer': t.proof_details if t.has_proof else 'Tidak ada'
            })
        
        # Prepare summary
        summary = {
            'user': user.username,
            'currency': user.currency,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense,
            'transaction_count': len(transactions),
            'export_date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'filter_date': date_filter
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'transactions': export_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database
def init_database():
    """Initialize database and create demo user"""
    try:
        print(f"📁 Database path: {DATABASE_PATH}")
        
        # Create database file if it doesn't exist
        if not os.path.exists(DATABASE_PATH):
            print("🔧 Creating new database...")
            # Create an empty SQLite database file
            conn = sqlite3.connect(DATABASE_PATH)
            conn.close()
        
        # Create tables
        with app.app_context():
            db.create_all()
            
            # Create demo user if not exists
            demo_user = User.query.filter_by(username='demo').first()
            if not demo_user:
                print("👤 Creating demo user...")
                demo_user = User(
                    username='demo',
                    email='demo@dhfinance.app',
                    password=bcrypt.generate_password_hash('demo123').decode('utf-8'),
                    currency='IDR',
                    last_login=datetime.utcnow()
                )
                db.session.add(demo_user)
                db.session.commit()
                print("✅ Demo user created successfully")
            else:
                print("✅ Demo user already exists")
                
            # Clear existing demo transactions and add fresh ones
            Transaction.query.filter_by(user_id=demo_user.id).delete()
            db.session.commit()
            
            # Add sample transactions for demo user
            today = datetime.now().strftime('%Y-%m-%d')
            sample_transactions = [
                Transaction(
                    user_id=demo_user.id,
                    type='income',
                    amount=1000000,
                    description='Gaji Bulanan',
                    date=today,
                    has_proof=True,
                    proof_details='https://prnt.sc/fk8Ctptkwt3'
                ),
                Transaction(
                    user_id=demo_user.id,
                    type='expense',
                    amount=125000,
                    description='Belanja Bulanan',
                    date=today,
                    has_proof=False,
                    proof_details='Tidak ada bukti transfer'
                ),
                Transaction(
                    user_id=demo_user.id,
                    type='income',
                    amount=500000,
                    description='Transfer dari Klien',
                    date=today,
                    has_proof=True,
                    proof_details='https://example.com/bukti-transfer.jpg'
                )
            ]
            
            db.session.add_all(sample_transactions)
            db.session.commit()
            print("✅ Database initialized successfully with demo data")
                
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()

# Initialize on startup
init_database()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)