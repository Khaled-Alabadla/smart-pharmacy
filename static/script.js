const API_BASE = '/';

// DOM Elements
const inventoryBody = document.getElementById('inventory-body');
const salesList = document.getElementById('sales-list');
const totalItemsEl = document.getElementById('total-items');
const expiredCountEl = document.getElementById('expired-count');
const totalSalesEl = document.getElementById('total-sales');
const dateDisplay = document.getElementById('date-display');

const saleModal = document.getElementById('sale-modal');
const addModal = document.getElementById('add-modal');

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    updateDate();
    setInterval(updateDate, 60000);
});

function updateDate() {
    const now = new Date();
    dateDisplay.innerText = now.toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
}

async function loadData() {
    try {
        const [inventory, history] = await Promise.all([
            fetch('/inventory').then(r => r.json()),
            fetch('/sales_history').then(r => r.json())
        ]);

        renderInventory(inventory);
        renderSales(history);
        updateStats(inventory, history);
    } catch (err) {
        console.error('Failed to load data:', err);
    }
}

function renderInventory(items) {
    inventoryBody.innerHTML = '';
    items.forEach(item => {
        const tr = document.createElement('tr');
        if (item.is_expired) tr.classList.add('expired-row');

        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>${item.quantity}</td>
            <td>$${item.base_price.toFixed(2)}</td>
            <td>$${item.final_price.toFixed(2)}</td>
            <td class="${item.is_expired ? 'danger-text' : ''}">${item.expiry_date}</td>
            <td>${item.requires_prescription ? '<span class="prescription-tag">Requires RX</span>' : 'OTC'}</td>
            <td>
                <button onclick="openSaleModal('${item.name}', ${item.requires_prescription})" class="sell-btn">Sell</button>
            </td>
        `;
        inventoryBody.appendChild(tr);
    });
}

function renderSales(history) {
    salesList.innerHTML = '';
    history.slice().reverse().forEach(sale => {
        const div = document.createElement('div');
        div.className = 'sale-item';
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between;">
                <strong>${sale.medicine} (x${sale.quantity})</strong>
                <span>$${sale.total_price.toFixed(2)}</span>
            </div>
            <div class="meta">Sold to ${sale.customer} on ${sale.date}</div>
        `;
        salesList.appendChild(div);
    });
}

function updateStats(inventory, history) {
    totalItemsEl.innerText = inventory.reduce((acc, item) => acc + item.quantity, 0);
    expiredCountEl.innerText = inventory.filter(i => i.is_expired).length;
    totalSalesEl.innerText = history.length;
}

// Modals Logic
function openSaleModal(name, requiresRX) {
    document.getElementById('sale-name').value = name;
    document.getElementById('m-sale-name').innerText = name;
    document.getElementById('prescription-check').classList.toggle('hidden', !requiresRX);
    saleModal.style.display = 'flex';
}

document.getElementById('add-med-modal-btn').onclick = () => addModal.style.display = 'flex';

document.querySelectorAll('.close-modal').forEach(btn => {
    btn.onclick = () => {
        saleModal.style.display = 'none';
        addModal.style.display = 'none';
    };
});

// Form Submissions
document.getElementById('sale-form').onsubmit = async (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('sale-name').value,
        quantity: parseInt(document.getElementById('sale-qty').value),
        customer_name: document.getElementById('cust-name').value,
        customer_phone: document.getElementById('cust-phone').value,
        prescription_confirmed: document.getElementById('pres-confirmed').checked
    };

    const res = await fetch('/sell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    const result = await res.json();
    if (res.ok) {
        alert(`Sale successful! Customer debt: $${result.customer_debt.toFixed(2)}`);
        saleModal.style.display = 'none';
        loadData();
        e.target.reset();
    } else {
        alert(result.detail);
    }
};

document.getElementById('add-form').onsubmit = async (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('add-name').value,
        base_price: parseFloat(document.getElementById('add-price').value),
        quantity: parseInt(document.getElementById('add-qty').value),
        expiry_date: document.getElementById('add-expiry').value,
        requires_prescription: document.getElementById('add-pres').checked
    };

    const res = await fetch('/add_medicine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        addModal.style.display = 'none';
        loadData();
        e.target.reset();
    } else {
        alert('Error adding medicine');
    }
};

document.getElementById('refresh-btn').onclick = loadData;
