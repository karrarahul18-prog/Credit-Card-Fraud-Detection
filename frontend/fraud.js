

const FLASK_URL = 'http://127.0.0.1:5000';   // change if Flask runs elsewhere

// ── On page load: fetch dropdown options from Flask ───────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const res  = await fetch(FLASK_URL + '/options');
    const data = await res.json();

    // Populate merchant dropdown
    const merchantSel = document.getElementById('merchant');
    merchantSel.innerHTML = '';
    data.merchants.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m; opt.textContent = m;
      merchantSel.appendChild(opt);
    });

    // Populate city dropdown
    const citySel = document.getElementById('city');
    citySel.innerHTML = '';
    data.cities.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c; opt.textContent = c;
      citySel.appendChild(opt);
    });
  } catch (e) {
    console.warn('Could not load options from Flask — using defaults already in HTML.');
  }

  // Update history count badge in nav
  updateHistoryBadge();
});


// ── Form submit ───────────────────────────────────────────────────────────────
const form       = document.getElementById('fraudForm');
const analyzeBtn = document.getElementById('analyzeBtn');
const spinner    = document.getElementById('spinner');
const btnText    = document.getElementById('btnText');

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  // Show loading state
  analyzeBtn.disabled   = true;
  if (spinner)  spinner.style.display  = 'block';
  if (btnText)  btnText.textContent    = 'Analyzing...';

  // Collect form values
  const payload = {
    transaction_amount:     parseFloat(document.getElementById('transaction_amount').value),
    avg_transaction_amount: parseFloat(document.getElementById('avg_amount').value),
    transaction_hour:       parseInt(document.getElementById('txn_hour').value),
    day_of_week:            parseInt(document.getElementById('day_of_week').value),
    merchant_category:      document.getElementById('merchant').value,
    city:                   document.getElementById('city').value,
    distance_from_home_km:  parseFloat(document.getElementById('distance').value),
    transactions_last_24h:  parseInt(document.getElementById('txn_24h').value),
    is_international:       document.getElementById('is_international').checked ? 1 : 0,
    is_online:              document.getElementById('is_online').checked       ? 1 : 0,
    card_present:           document.getElementById('card_present').checked    ? 1 : 0,
  };

  try {
    // POST to Flask /predict  (Flask also saves to history.json automatically)
    const response = await fetch(FLASK_URL + '/predict', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });

    const result = await response.json();

    if (result.success) {
      showResult(result);
      updateHistoryBadge();   // refresh badge after saving
    } else {
      alert('Error: ' + result.error);
    }
  } catch (err) {
    alert('Cannot connect to Flask server.\nMake sure you ran: python app.py');
    console.error(err);
  }

  // Reset button
  analyzeBtn.disabled   = false;
  if (spinner) spinner.style.display = 'none';
  if (btnText) btnText.textContent   = '🔍 Analyze Transaction';
});


// ── Show result panel ─────────────────────────────────────────────────────────
function showResult(r) {
  const placeholder = document.getElementById('resultPlaceholder');
  const content     = document.getElementById('resultContent');
  if (placeholder) placeholder.classList.add('hidden');
  if (content)     content.classList.remove('hidden');

  const isFraud = r.is_fraud;

  // Verdict icon & title
  const verdictIcon  = document.getElementById('verdictIcon');
  const verdictTitle = document.getElementById('verdictTitle');
  const verdictSub   = document.getElementById('verdictSub');
  const riskBadge    = document.getElementById('riskBadge');

  if (verdictIcon)  verdictIcon.textContent  = isFraud ? '🚨' : '✅';
  if (verdictTitle) {
    verdictTitle.textContent = isFraud ? 'FRAUD DETECTED!' : 'Transaction is Safe';
    verdictTitle.className   = 'verdict-title ' + (isFraud ? 'fraud' : 'safe');
  }
  if (verdictSub) {
    verdictSub.textContent = isFraud
      ? 'This transaction is flagged as potentially fraudulent. Contact your bank immediately.'
      : 'This transaction appears normal based on your spending patterns.';
  }

  // Risk badge
  if (riskBadge) {
    const riskLevel = r.risk_level.split(' ')[0];
    riskBadge.innerHTML = `<span class="risk-badge risk-${riskLevel}">● ${r.risk_level}</span>`;
  }

  // Probability bar
  const prob    = r.fraud_probability;
  const probBar = document.getElementById('probBar');
  const probVal = document.getElementById('probValue');
  if (probBar) {
    probBar.className  = 'prob-bar-fill ' + (isFraud ? 'fraud-fill' : 'safe-fill');
    probBar.style.width = '0%';
    setTimeout(() => { probBar.style.width = prob + '%'; }, 80);
  }
  if (probVal) probVal.textContent = prob + '%';

  // Stats boxes
  const statFraud = document.getElementById('statFraud');
  const statSafe  = document.getElementById('statSafe');
  const statRisk  = document.getElementById('statRisk');
  if (statFraud) statFraud.textContent = r.fraud_probability + '%';
  if (statSafe)  statSafe.textContent  = r.normal_probability + '%';
  if (statRisk) {
    const riskLevel = r.risk_level.split(' ')[0];
    statRisk.textContent  = riskLevel;
    statRisk.style.color  =
      riskLevel === 'HIGH'   ? 'var(--danger)'  :
      riskLevel === 'MEDIUM' ? 'var(--warning)' : 'var(--success)';
  }

  // Detection reasons
  const reasonsList = document.getElementById('reasonsList');
  if (reasonsList) {
    reasonsList.innerHTML = '';
    const items = (r.reasons && r.reasons.length)
      ? r.reasons
      : ['✅ No suspicious patterns found in this transaction.'];

    items.forEach(reason => {
      const div       = document.createElement('div');
      div.className   = 'reason-item ' + (isFraud ? 'fraud-reason' : 'safe-reason');
      div.textContent = reason;
      reasonsList.appendChild(div);
    });
  }

  // Scroll to result on mobile
  if (window.innerWidth < 800) {
    const rc = document.getElementById('resultCard');
    if (rc) rc.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}


// ── History badge: shows count of saved transactions in nav ───────────────────
async function updateHistoryBadge() {
  try {
    const res  = await fetch(FLASK_URL + '/api/history');
    const data = await res.json();
    const badge = document.getElementById('historyBadge');
    if (badge && data.total > 0) {
      badge.textContent = data.total;
      badge.style.display = 'inline';
    }
  } catch (e) {
    // silently ignore — badge is optional
  }
}