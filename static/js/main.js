// Config
const API_BASE_URL = window.location.origin;
let currentUser = null;
let authToken = null;
let currentFilter = null;
let transactionToDelete = null;
let swipeStartX = 0;
let swipeEndX = 0;
let currentSwipeId = null;

// Currency data
const currencies = {
    'IDR': { symbol: 'Rp', name: 'Rupiah Indonesia' },
    'USD': { symbol: '$', name: 'US Dollar' },
    'EUR': { symbol: '€', name: 'Euro' },
    'GBP': { symbol: '£', name: 'British Pound' },
    'JPY': { symbol: '¥', name: 'Japanese Yen' },
    'SGD': { symbol: 'S$', name: 'Singapore Dollar' },
    'THB': { symbol: '฿', name: 'Baht Thailand' },
    'KHR': { symbol: '៛', name: 'Riel Kamboja' }
};

// Helper untuk API calls
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}/api${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include' // Include cookies for session
        });
        
        if (response.status === 401) {
            // Token expired or invalid
            logout(true); // Silent logout
            throw new Error('Session expired. Please login again.');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ error: 'Network error' }));
            throw new Error(error.error || 'Request failed');
        }
        
        return response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', async function() {
    updateDate();
    await checkLoginStatus();
    setupSwipeListeners();
    setupEnterKeyListeners();
    setupFilterControls();
});

// Setup Enter key listeners for all forms
function setupEnterKeyListeners() {
    // Login form Enter key
    document.getElementById('loginPassword').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            login();
        }
    });
    
    document.getElementById('loginUsername').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            login();
        }
    });

    // Register form Enter key
    document.getElementById('registerPassword').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            register();
        }
    });

    // Transaction form Enter key
    document.getElementById('description').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTransaction();
        }
    });

    document.getElementById('amount').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTransaction();
        }
    });

    document.getElementById('proofDetails').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTransaction();
        }
    });
}

// Setup filter controls
function setupFilterControls() {
    const enableFilter = document.getElementById('enableFilter');
    const filterControls = document.getElementById('filterControls');
    
    enableFilter.addEventListener('change', function() {
        if (this.checked) {
            filterControls.style.display = 'flex';
            document.getElementById('filterDate').focus();
        } else {
            filterControls.style.display = 'none';
            clearFilter();
        }
    });
    
    // Initialize hidden
    filterControls.style.display = 'none';
}

// Setup swipe functionality
function setupSwipeListeners() {
    document.addEventListener('touchstart', handleTouchStart, false);
    document.addEventListener('touchmove', handleTouchMove, false);
    document.addEventListener('touchend', handleTouchEnd, false);
    
    // For mouse events (desktop testing)
    document.addEventListener('mousedown', handleMouseDown, false);
    document.addEventListener('mousemove', handleMouseMove, false);
    document.addEventListener('mouseup', handleMouseUp, false);
}

// Touch event handlers
function handleTouchStart(e) {
    const transactionItem = e.target.closest('.transaction-item');
    if (transactionItem && !e.target.closest('.proof-badge')) {
        swipeStartX = e.touches[0].clientX;
        currentSwipeId = transactionItem.id;
    }
}

function handleTouchMove(e) {
    if (!currentSwipeId) return;
    e.preventDefault();
}

function handleTouchEnd(e) {
    if (!currentSwipeId) return;
    
    const transactionItem = document.getElementById(currentSwipeId);
    if (transactionItem) {
        swipeEndX = e.changedTouches[0].clientX;
        const swipeDistance = swipeStartX - swipeEndX;
        
        // Reset all other transaction items
        document.querySelectorAll('.transaction-item.swiped').forEach(item => {
            if (item.id !== currentSwipeId) {
                item.classList.remove('swiped');
            }
        });
        
        // If swipe distance is enough, show delete button
        if (swipeDistance > 50) {
            transactionItem.classList.add('swiped');
        } else if (swipeDistance < -50) {
            transactionItem.classList.remove('swiped');
        }
    }
    
    currentSwipeId = null;
    swipeStartX = 0;
    swipeEndX = 0;
}

// Mouse event handlers (for desktop)
function handleMouseDown(e) {
    if (e.button !== 0) return; // Only left click
    
    const transactionItem = e.target.closest('.transaction-item');
    if (transactionItem && !e.target.closest('.proof-badge')) {
        swipeStartX = e.clientX;
        currentSwipeId = transactionItem.id;
        transactionItem.classList.add('dragging');
    }
}

function handleMouseMove(e) {
    if (!currentSwipeId) return;
    
    const transactionItem = document.getElementById(currentSwipeId);
    if (transactionItem) {
        swipeEndX = e.clientX;
        const swipeDistance = swipeStartX - swipeEndX;
        
        if (Math.abs(swipeDistance) > 50) {
            if (swipeDistance > 0) {
                transactionItem.classList.add('swiped');
            } else {
                transactionItem.classList.remove('swiped');
            }
        }
    }
}

function handleMouseUp(e) {
    if (!currentSwipeId) return;
    
    const transactionItem = document.getElementById(currentSwipeId);
    if (transactionItem) {
        transactionItem.classList.remove('dragging');
        
        // Reset all other transaction items
        document.querySelectorAll('.transaction-item.swiped').forEach(item => {
            if (item.id !== currentSwipeId) {
                item.classList.remove('swiped');
            }
        });
    }
    
    currentSwipeId = null;
    swipeStartX = 0;
    swipeEndX = 0;
}

// Notification system
function showNotification(type, title, message, duration = 5000) {
    const container = document.getElementById('notificationContainer');
    const notificationId = 'notification-' + Date.now();
    
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-times-circle',
        'info': 'fa-info-circle',
        'warning': 'fa-exclamation-triangle'
    };
    
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${icons[type]}"></i>
        </div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
        <button class="notification-close" onclick="removeNotification('${notificationId}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(notification);
    
    // Show notification with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            removeNotification(notificationId);
        }, duration);
    }
    
    return notificationId;
}

function removeNotification(id) {
    const notification = document.getElementById(id);
    if (notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

// Loading functions
function showLoading(message = 'Memproses...') {
    document.getElementById('loadingText').textContent = message;
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    setTimeout(() => {
        document.getElementById('loadingOverlay').classList.remove('active');
    }, 500);
}

function updateDate() {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    document.getElementById('transactionDate').value = today;
    document.getElementById('filterDate').value = today;
    document.getElementById('balanceDate').textContent = 
        now.toLocaleDateString('id-ID', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
}

// Authentication functions
async function login() {
    showLoading('Melakukan login...');
    
    try {
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        
        if (!username || !password) {
            throw new Error('Harap isi username dan password');
        }
        
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        // Save token and user data
        authToken = response.token;
        currentUser = response.user;
        
        // Save to localStorage for persistence
        localStorage.setItem('dh_finance_token', authToken);
        localStorage.setItem('dh_finance_user', JSON.stringify(currentUser));
        
        // Update UI
        showMainApp();
        await loadUserData();
        
        // Reset form
        document.getElementById('loginUsername').value = '';
        document.getElementById('loginPassword').value = '';
        
        showNotification('success', 'Login Berhasil', `Selamat datang kembali, ${username}!`);
        
    } catch (error) {
        showNotification('error', 'Login Gagal', error.message);
    } finally {
        hideLoading();
    }
}

async function register() {
    showLoading('Mendaftarkan akun...');
    
    try {
        const username = document.getElementById('registerUsername').value.trim();
        const email = document.getElementById('registerEmail').value.trim();
        const password = document.getElementById('registerPassword').value;
        
        if (!username || !password) {
            throw new Error('Harap isi username dan password');
        }
        
        const response = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        
        // Save token and user data
        authToken = response.token;
        currentUser = response.user;
        
        // Save to localStorage for persistence
        localStorage.setItem('dh_finance_token', authToken);
        localStorage.setItem('dh_finance_user', JSON.stringify(currentUser));
        
        // Update UI
        showMainApp();
        await loadUserData();
        
        showNotification('success', 'Pendaftaran Berhasil', 'Akun berhasil dibuat!');
        
        // Reset form
        document.getElementById('registerUsername').value = '';
        document.getElementById('registerEmail').value = '';
        document.getElementById('registerPassword').value = '';
        
    } catch (error) {
        showNotification('error', 'Pendaftaran Gagal', error.message);
    } finally {
        hideLoading();
    }
}

async function logout(silent = false) {
    if (!silent) {
        showLoading('Keluar dari sistem...');
    }
    
    try {
        // Clear token and user data
        authToken = null;
        currentUser = null;
        
        // Clear localStorage
        localStorage.removeItem('dh_finance_token');
        localStorage.removeItem('dh_finance_user');
        
        // Show auth section
        showAuthSection();
        
        if (!silent) {
            setTimeout(() => {
                hideLoading();
                showNotification('info', 'Logout Berhasil', 'Anda telah logout dari sistem');
            }, 500);
        }
    } catch (error) {
        console.error('Logout error:', error);
        if (!silent) {
            hideLoading();
        }
    }
}

async function checkLoginStatus() {
    showLoading('Memeriksa status login...');
    
    try {
        const savedToken = localStorage.getItem('dh_finance_token');
        const savedUser = localStorage.getItem('dh_finance_user');
        
        if (savedToken && savedUser) {
            // Try to restore session from localStorage
            authToken = savedToken;
            currentUser = JSON.parse(savedUser);
            
            // Verify token with server
            try {
                const response = await apiRequest('/auth/check');
                
                if (response.authenticated) {
                    // Token is valid, restore session
                    currentUser = response.user || currentUser;
                    
                    // Update localStorage with fresh user data
                    localStorage.setItem('dh_finance_user', JSON.stringify(currentUser));
                    
                    // Show main app
                    showMainApp();
                    await loadUserData();
                    hideLoading();
                    return;
                } else {
                    // Token is invalid, clear localStorage
                    localStorage.removeItem('dh_finance_token');
                    localStorage.removeItem('dh_finance_user');
                }
            } catch (error) {
                console.error('Token verification failed:', error);
                // Token invalid, clear storage
                localStorage.removeItem('dh_finance_token');
                localStorage.removeItem('dh_finance_user');
            }
        }
        
        // No valid session found, show auth section
        showAuthSection();
        hideLoading();
        
    } catch (error) {
        console.error('Error checking login status:', error);
        showAuthSection();
        hideLoading();
    }
}

function showAuthSection() {
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
    document.getElementById('currentUser').textContent = 'Belum Login';
    document.getElementById('footerUsername').textContent = '-';
    document.getElementById('footerTransactionCount').textContent = '0';
    
    // Clear any swipe states
    document.querySelectorAll('.transaction-item.swiped').forEach(item => {
        item.classList.remove('swiped');
    });
}

function showMainApp() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    document.getElementById('currentUser').textContent = currentUser ? currentUser.username : 'Belum Login';
}

// Transaction functions
function toggleProofField() {
    const hasProof = document.getElementById('hasProof').checked;
    const proofContainer = document.getElementById('proofContainer');
    const proofDetails = document.getElementById('proofDetails');
    
    if (hasProof) {
        proofContainer.classList.remove('hidden');
        proofDetails.required = true;
    } else {
        proofContainer.classList.add('hidden');
        proofDetails.required = false;
        proofDetails.value = '';
    }
}

function toggleFilterMode() {
    const enableFilter = document.getElementById('enableFilter').checked;
    const filterControls = document.getElementById('filterControls');
    
    if (enableFilter) {
        filterControls.style.display = 'flex';
    } else {
        filterControls.style.display = 'none';
        clearFilter();
    }
}

// Fungsi untuk membuka link bukti transfer di tab baru
function openProofLink(url) {
    if (!url || url === 'Tidak ada bukti transfer') {
        return;
    }
    
    // Validasi URL
    let validUrl = url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        validUrl = 'https://' + url;
    }
    
    // Buka langsung di tab baru tanpa alert
    window.open(validUrl, '_blank', 'noopener,noreferrer');
}

async function addTransaction() {
    if (!currentUser) return;
    
    showLoading('Menyimpan transaksi...');
    
    try {
        const type = document.getElementById('transactionType').value;
        const amount = parseFloat(document.getElementById('amount').value);
        const description = document.getElementById('description').value.trim();
        const date = document.getElementById('transactionDate').value;
        const hasProof = document.getElementById('hasProof').checked;
        let proofDetails = document.getElementById('proofDetails').value.trim();
        
        if (!amount || amount <= 0) {
            throw new Error('Harap masukkan nominal yang valid');
        }
        
        if (!date) {
            throw new Error('Harap pilih tanggal transaksi');
        }
        
        if (hasProof) {
            if (!proofDetails) {
                throw new Error('Harap isi link bukti transfer');
            }
            
            // Validasi format URL
            if (!proofDetails.startsWith('http://') && !proofDetails.startsWith('https://')) {
                proofDetails = 'https://' + proofDetails;
            }
            
            try {
                new URL(proofDetails);
            } catch (e) {
                throw new Error('Harap masukkan URL yang valid (contoh: https://prnt.sc/abc123)');
            }
        } else {
            proofDetails = 'Tidak ada bukti transfer';
        }
        
        // Kirim ke server
        await apiRequest('/transactions', {
            method: 'POST',
            body: JSON.stringify({
                type,
                amount,
                description: description || 'Tanpa keterangan',
                date,
                hasProof,
                proofDetails
            })
        });
        
        // Reset form
        document.getElementById('amount').value = '';
        document.getElementById('description').value = '';
        document.getElementById('hasProof').checked = false;
        document.getElementById('proofDetails').value = '';
        toggleProofField();
        
        // Reload data
        await loadUserData();
        
        const typeText = type === 'income' ? 'Uang Masuk' : 'Uang Keluar';
        showNotification('success', 'Transaksi Berhasil', 
            `${typeText} sebesar ${formatCurrency(amount, currencies[currentUser.currency || 'IDR'])} berhasil disimpan!`);
        
    } catch (error) {
        showNotification('error', 'Transaksi Gagal', error.message);
    } finally {
        hideLoading();
    }
}

async function deleteTransaction(transactionId) {
    if (!currentUser || !transactionId) return;
    
    showLoading('Menghapus transaksi...');
    
    try {
        await apiRequest(`/transactions/${transactionId}`, {
            method: 'DELETE'
        });
        
        await loadUserData();
        showNotification('success', 'Transaksi Dihapus', 'Transaksi berhasil dihapus');
        
    } catch (error) {
        showNotification('error', 'Gagal Menghapus', error.message);
    } finally {
        hideLoading();
    }
}

async function loadUserData() {
    if (!currentUser) return;
    
    try {
        // Update UI dengan user info
        document.getElementById('currentUser').textContent = currentUser.username;
        document.getElementById('footerUsername').textContent = currentUser.username;
        
        // Load transactions
        let endpoint = '/transactions';
        if (currentFilter) {
            endpoint += `?date=${currentFilter}`;
        }
        
        const transactions = await apiRequest(endpoint);
        
        // Load dashboard stats
        const stats = await apiRequest('/dashboard/stats');
        
        // Load user settings
        const settings = await apiRequest('/user/settings');
        currentUser.currency = settings.currency;
        
        updateDashboard(stats);
        renderTransactionList(transactions);
        updateFooterInfo(transactions);
        updateFilterStatus();
        updateCurrencySettings(settings.currency);
        
    } catch (error) {
        console.error('Error loading data:', error);
        if (error.message.includes('Session expired')) {
            showNotification('error', 'Sesi Berakhir', error.message);
        } else {
            showNotification('error', 'Gagal Memuat Data', error.message);
        }
    }
}

function updateDashboard(stats) {
    const currency = currencies[stats.currency || 'IDR'];
    
    document.getElementById('currentBalance').textContent = 
        formatCurrency(stats.balance, currency);
    document.getElementById('totalIncome').textContent = 
        formatCurrency(stats.totalIncome, currency);
    document.getElementById('totalExpense').textContent = 
        formatCurrency(stats.totalExpense, currency);
    document.getElementById('currencyLabel').textContent = stats.currency || 'IDR';
}

function renderTransactionList(transactions) {
    const container = document.getElementById('transactionList');
    
    if (!transactions || transactions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i class="fas fa-receipt"></i>
                </div>
                <h3 style="margin-bottom: 10px; color: #64748b;">Belum ada transaksi</h3>
                <p style="color: #94a3b8;">Tambahkan transaksi pertama Anda menggunakan form di sebelah kiri</p>
            </div>
        `;
        document.getElementById('transactionCountBadge').textContent = '0';
        return;
    }
    
    // Update transaction count badge
    document.getElementById('transactionCountBadge').textContent = transactions.length;
    
    const currency = currencies[currentUser.currency || 'IDR'];
    
    container.innerHTML = transactions.map(transaction => {
        const hasProof = transaction.hasProof && transaction.proofDetails !== 'Tidak ada bukti transfer';
        const proofClass = hasProof ? 'has-proof' : 'no-proof';
        const displayProof = hasProof ? 
            (transaction.proofDetails.length > 30 ? 
             transaction.proofDetails.substring(0, 30) + '...' : 
             transaction.proofDetails) : 
            transaction.proofDetails;
        
        // Buat elemen bukti transfer yang dapat diklik
        let proofElement = '';
        if (hasProof) {
            proofElement = `
                <a href="${transaction.proofDetails}" 
                   target="_blank"
                   onclick="openProofLink('${transaction.proofDetails}'); return false;"
                   class="proof-badge ${proofClass}"
                   title="Klik untuk membuka bukti transfer di tab baru">
                    <i class="fas ${hasProof ? 'fa-external-link-alt' : 'fa-times-circle'}"></i>
                    ${displayProof}
                </a>
            `;
        } else {
            proofElement = `
                <span class="proof-badge ${proofClass}">
                    <i class="fas ${hasProof ? 'fa-external-link-alt' : 'fa-times-circle'}"></i>
                    ${displayProof}
                </span>
            `;
        }
        
        return `
        <div class="transaction-item" id="transaction-${transaction.id}">
            <div class="transaction-content">
                <div style="font-weight: bold; margin-bottom: 8px; font-size: 18px;">
                    ${transaction.description}
                </div>
                <div style="font-size: 15px; color: #64748b; margin-bottom: 10px;">
                    <i class="far fa-calendar"></i> 
                    ${formatDate(transaction.date)}
                </div>
                <div style="margin-bottom: 10px;">
                    <span class="transaction-type type-${transaction.type}">
                        ${transaction.type === 'income' ? 'Uang Masuk' : 'Uang Keluar'}
                    </span>
                </div>
                <div>
                    ${proofElement}
                </div>
            </div>
            <div class="transaction-actions">
                <button class="delete-btn" onclick="deleteTransaction(${transaction.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="transaction-amount ${transaction.type === 'income' ? 'amount-income' : 'amount-expense'}">
                ${transaction.type === 'income' ? '+' : '-'} ${formatCurrency(transaction.amount, currency)}
            </div>
        </div>
        `;
    }).join('');
}

function updateFooterInfo(transactions) {
    document.getElementById('footerUsername').textContent = currentUser.username;
    document.getElementById('footerTransactionCount').textContent = transactions.length || 0;
}

// Filter functions
async function applyFilter() {
    if (!currentUser) return;
    
    showLoading('Menerapkan filter...');
    
    try {
        const filterDate = document.getElementById('filterDate').value;
        if (!filterDate) {
            showNotification('warning', 'Filter Gagal', 'Harap pilih tanggal untuk filter');
            hideLoading();
            return;
        }
        
        currentFilter = filterDate;
        await loadUserData();
        
        hideLoading();
        showNotification('info', 'Filter Diaktifkan', `Menampilkan transaksi pada tanggal ${formatDateForExport(filterDate)}`);
    } catch (error) {
        showNotification('error', 'Filter Gagal', error.message);
        hideLoading();
    }
}

async function clearFilter() {
    if (currentFilter) {
        showLoading('Reset filter...');
        
        currentFilter = null;
        document.getElementById('enableFilter').checked = false;
        document.getElementById('filterControls').style.display = 'none';
        await loadUserData();
        
        hideLoading();
        showNotification('info', 'Filter Dihapus', 'Menampilkan semua transaksi');
    }
}

function updateFilterStatus() {
    const filterStatus = document.getElementById('filterStatus');
    const filterStatusMini = document.getElementById('filterStatusMini');
    const filterMessage = document.getElementById('filterMessage');
    const filterMessageMini = document.getElementById('filterMessageMini');
    
    if (currentFilter) {
        filterStatus.classList.remove('hidden');
        filterStatus.classList.add('filter-active');
        filterMessage.textContent = `Menampilkan transaksi pada tanggal ${formatDateForExport(currentFilter)}`;
        
        filterStatusMini.style.display = 'flex';
        filterMessageMini.textContent = `Filter aktif: ${formatDateForExport(currentFilter)}`;
    } else {
        filterStatus.classList.add('hidden');
        filterStatus.classList.remove('filter-active');
        filterMessage.textContent = 'Menampilkan semua transaksi';
        
        filterStatusMini.style.display = 'none';
    }
}

// Export functions
async function exportToExcel() {
    if (!currentUser) return;
    
    showLoading('Mengekspor ke Excel...');
    
    try {
        let endpoint = '/export/excel';
        if (currentFilter) {
            endpoint += `?date=${currentFilter}`;
        }
        
        const response = await apiRequest(endpoint);
        
        if (!response.transactions || response.transactions.length === 0) {
            throw new Error('Tidak ada data transaksi untuk diekspor');
        }
        
        // Prepare data for Excel
        const excelData = response.transactions.map((transaction, index) => ({
            'No': index + 1,
            'Tanggal': transaction.Tanggal,
            'Jenis': transaction.Jenis,
            'Keterangan': transaction.Keterangan,
            'Jumlah': transaction.Jumlah,
            'Mata Uang': transaction['Mata Uang'],
            'Bukti Transfer': transaction['Bukti Transfer']
        }));
        
        // Create worksheet
        const ws = XLSX.utils.json_to_sheet(excelData);
        
        // Create workbook
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Transaksi");
        
        // Generate file name
        const filterSuffix = currentFilter ? `_filter_${currentFilter}` : '';
        const fileName = `dh_finance_${currentUser.username}${filterSuffix}_${new Date().toISOString().slice(0,10)}.xlsx`;
        
        // Save to file
        XLSX.writeFile(wb, fileName);
        
        hideLoading();
        showNotification('success', 'Ekspor Berhasil', `Data telah diekspor ke ${fileName}`);
        
    } catch (error) {
        showNotification('error', 'Ekspor Gagal', error.message);
        hideLoading();
    }
}

async function exportToWord() {
    if (!currentUser) return;
    
    showLoading('Mengekspor ke Word...');
    
    try {
        let endpoint = '/export/excel';
        if (currentFilter) {
            endpoint += `?date=${currentFilter}`;
        }
        
        const response = await apiRequest(endpoint);
        
        if (!response.transactions || response.transactions.length === 0) {
            throw new Error('Tidak ada data transaksi untuk diekspor');
        }
        
        const currency = currencies[currentUser.currency || 'IDR'];
        const summary = response.summary;
        
        // Create Word document content
        let wordContent = `
        <html xmlns:o='urn:schemas-microsoft-com:office:office' 
              xmlns:w='urn:schemas-microsoft-com:office:word' 
              xmlns='http://www.w3.org/TR/REC-html40'>
        <head>
            <meta charset='utf-8'>
            <title>Laporan Keuangan DH Finance</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #1e3a8a; border-bottom: 2px solid #1d4ed8; padding-bottom: 10px; }
                h2 { color: #1e3a8a; margin-top: 30px; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th { background-color: #dbeafe; color: #1e3a8a; padding: 12px; text-align: left; border: 1px solid #93c5fd; }
                td { padding: 10px; border: 1px solid #93c5fd; }
                .income { color: #10b981; }
                .expense { color: #ef4444; }
                .summary { background-color: #f8fafc; padding: 20px; border-radius: 10px; margin-top: 30px; }
                .footer { margin-top: 40px; font-size: 12px; color: #64748b; text-align: center; }
            </style>
        </head>
        <body>
            <h1>Laporan Keuangan DH Finance</h1>
            <p><strong>Pengguna:</strong> ${summary.user}</p>
            <p><strong>Tanggal Ekspor:</strong> ${new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
            <p><strong>Mata Uang:</strong> ${summary.currency} (${currency.symbol})</p>
            ${summary.filter_date ? `<p><strong>Filter Tanggal:</strong> ${formatDateForExport(summary.filter_date)}</p>` : ''}
            
            <h2>Ringkasan</h2>
            <div class="summary">
                <p><strong>Total Uang Masuk:</strong> <span class="income">${currency.symbol} ${formatNumber(summary.total_income)}</span></p>
                <p><strong>Total Uang Keluar:</strong> <span class="expense">${currency.symbol} ${formatNumber(summary.total_expense)}</span></p>
                <p><strong>Saldo Saat Ini:</strong> <strong>${currency.symbol} ${formatNumber(summary.balance)}</strong></p>
                <p><strong>Jumlah Transaksi:</strong> ${summary.transaction_count}</p>
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
                <tbody>
        `;
        
        // Add transaction rows
        response.transactions.forEach((transaction, index) => {
            const rowClass = transaction.Jenis === 'Uang Masuk' ? 'income' : 'expense';
            wordContent += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${transaction.Tanggal}</td>
                    <td>${transaction.Jenis}</td>
                    <td>${transaction.Keterangan}</td>
                    <td class="${rowClass}">${transaction.Jenis === 'Uang Masuk' ? '+' : '-'} ${currency.symbol} ${formatNumber(transaction.Jumlah)}</td>
                    <td>${transaction['Bukti Transfer']}</td>
                </tr>
            `;
        });
        
        wordContent += `
                </tbody>
            </table>
            
            <div class="footer">
                <p>&copy; ${new Date().getFullYear()} DH Finance - Aplikasi Manajemen Keuangan Pribadi</p>
                <p>Dokumen ini dibuat secara otomatis oleh sistem DH Finance</p>
            </div>
        </body>
        </html>
        `;
        
        // Create blob and download
        const blob = new Blob(['\ufeff', wordContent], {
            type: 'application/msword'
        });
        
        const filterSuffix = currentFilter ? `_filter_${currentFilter}` : '';
        const fileName = `dh_finance_${currentUser.username}${filterSuffix}_${new Date().toISOString().slice(0,10)}.doc`;
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        hideLoading();
        showNotification('success', 'Ekspor Berhasil', `Data telah diekspor ke ${fileName}`);
        
    } catch (error) {
        showNotification('error', 'Ekspor Gagal', error.message);
        hideLoading();
    }
}

// Currency functions
function updateCurrencySettings(userCurrency = null) {
    const container = document.getElementById('currencyGrid');
    if (!container) return;
    
    container.innerHTML = '';
    
    const currentUserCurrency = userCurrency || (currentUser?.currency || 'IDR');
    document.getElementById('currencyLabel').textContent = currentUserCurrency;
    
    Object.entries(currencies).forEach(([code, data]) => {
        const isActive = currentUserCurrency === code;
        const currencyItem = document.createElement('div');
        currencyItem.className = `currency-item ${isActive ? 'active' : ''}`;
        currencyItem.innerHTML = `
            <div style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">${data.symbol}</div>
            <div style="font-weight: 600; margin: 8px 0; font-size: 18px;">${code}</div>
            <div style="font-size: 15px; color: ${isActive ? '#1e3a8a' : '#64748b'};">
                ${data.name}
            </div>
        `;
        currencyItem.onclick = () => setCurrency(code);
        container.appendChild(currencyItem);
    });
}

async function setCurrency(currencyCode) {
    if (!currentUser) return;
    
    showLoading('Mengubah mata uang...');
    
    try {
        await apiRequest('/user/settings', {
            method: 'PUT',
            body: JSON.stringify({ currency: currencyCode })
        });
        
        // Update UI
        currentUser.currency = currencyCode;
        document.getElementById('currencyLabel').textContent = currencyCode;
        updateCurrencySettings(currencyCode);
        await loadUserData();
        
        // Add visual feedback
        const currencyItem = document.querySelector(`.currency-item.active`);
        if (currencyItem) {
            currencyItem.classList.add('selected');
            setTimeout(() => {
                currencyItem.classList.remove('selected');
            }, 500);
        }
        
        showNotification('success', 'Mata Uang Diubah', `Mata uang berhasil diubah ke ${currencyCode}`);
        
    } catch (error) {
        showNotification('error', 'Gagal Mengubah Mata Uang', error.message);
    } finally {
        hideLoading();
    }
}

// Utility functions
function formatCurrency(amount, currency) {
    return `${currency.symbol} ${formatNumber(amount)}`;
}

function formatNumber(number) {
    return number.toLocaleString('id-ID', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateForExport(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Handle browser refresh
window.addEventListener('beforeunload', function() {
    // Save current state
    if (currentUser && authToken) {
        localStorage.setItem('dh_finance_token', authToken);
        localStorage.setItem('dh_finance_user', JSON.stringify(currentUser));
    }
});