// ================================================
// BANKGUARD ANALYTICS — MAIN APPLICATION LOGIC
// ================================================

// ---- Currency Conversion ----
const USD_TO_INR = 84;       // 1 USD = ₹84
const LAKH  = 100000;        // 1 Lakh  = 1,00,000
const CRORE = 10000000;      // 1 Crore = 1,00,00,000

/** Format a raw INR value nicely */
function fmtINR(inr, short = false) {
  if (inr >= CRORE)       return '₹' + (inr / CRORE).toFixed(1) + ' Cr';
  if (inr >= LAKH)        return '₹' + (inr / LAKH).toFixed(1) + ' L';
  return '₹' + Math.round(inr).toLocaleString('en-IN');
}
/** Format chart-axis value (amounts stored as K-INR) */
function axisKINR(v) {
  if (v >= 10000)  return '₹' + (v / 10000).toFixed(0) + ' Cr';   // eg 84000K = 840Cr
  if (v >= 1000)   return '₹' + (v / 1000).toFixed(1) + ' kCr';
  return '₹' + v + 'K';
}

// ---- Chart.js Global Defaults ----
Chart.defaults.color = '#8892b0';
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
Chart.defaults.font.family = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

// ---- Real Dataset Statistics (monetary values in K-INR = K$ × 84) ----
const DATA = {
  txTypeCounts: { Deposit: 15218, Withdrawal: 14864, Transfer: 14904, Payment: 5014 },
  // K-INR totals (original K$ × 84)
  txTypeAmountsINR: {
    Deposit:    Math.round(37981288  * USD_TO_INR / 1000),   // K₹
    Withdrawal: Math.round(37146059  * USD_TO_INR / 1000),
    Transfer:   Math.round(37534177  * USD_TO_INR / 1000),
    Payment:    Math.round(12533074  * USD_TO_INR / 1000),
  },

  months2023: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
  // Monthly 2023 — now in K-INR (original K$ × 84)
  deposits2023:    [705.2,707.4,766.9,687.3,779.4,774.0,652.2,721.8,692.8,689.4,799.1,740.9].map(v=>Math.round(v*84)),
  withdrawals2023: [819.5,680.9,644.2,697.9,724.1,767.5,784.6,688.2,700.3,857.6,708.3,761.3].map(v=>Math.round(v*84)),
  transfers2023:   [731.0,680.3,769.6,698.4,750.1,788.2,695.3,760.2,712.5,742.3,770.1,735.7].map(v=>Math.round(v*84)),
  payments2023:    [240.4,235.1,249.0,230.0,242.5,255.3,220.1,248.7,232.1,236.8,262.3,189.1].map(v=>Math.round(v*84)),

  years: ['2023', '2024', '2025', '2026'],
  // Yearly in K-INR
  yearlyAmounts: {
    Deposit:    [8716,903,97,243].map(v=>Math.round(v*84)),
    Withdrawal: [8834,965,156,241].map(v=>Math.round(v*84)),
    Transfer:   [8733,933,145,250].map(v=>Math.round(v*84)),
    Payment:    [2837,329,54,86].map(v=>Math.round(v*84)),
  },
  yearlyCounts: {
    Deposit:    [3491, 375, 40, 96],
    Withdrawal: [3522, 394, 55, 99],
    Transfer:   [3456, 354, 55, 96],
    Payment:    [1175, 126, 17, 34],
  },

  customerTypes:  ['Individual', 'Small Business', 'Large Enterprise'],
  customerCounts: [353, 356, 402],

  accountStatuses:     ['Active', 'Inactive', 'Closed'],
  accountStatusCounts: [1337, 253, 77],

  accountTypes:      ['Checking', 'Savings', 'Payroll', 'Business', 'Youth'],
  accountTypeCounts: [315, 335, 313, 365, 339],
  accountTypeActive:   [254, 269, 248, 296, 270],
  accountTypeInactive: [45,  47,  53,  54,  54],
  accountTypeClosed:   [16,  19,  12,  15,  15],

  // Balance buckets (INR labels)
  balanceBuckets: ['<₹4L', '₹4–17L', '₹17–42L', '₹42–84L'],
  balanceCounts:  [102, 249, 497, 819],

  loanStatuses:     ['Active', 'Paid Off', 'Overdue'],
  loanStatusCounts: [242, 57, 34],

  irBands:  ['2–4%', '4–6%', '6–8%', '8–10%', '10–12%', '12–14%', '14–16%'],
  irCounts: [25, 51, 55, 69, 60, 52, 21],

  // Loan amount buckets in INR
  loanAmtBuckets: ['<₹8L', '₹8–21L', '₹21–42L', '₹42–63L', '₹63L+'],
  loanAmtCounts:  [26, 48, 88, 78, 93],

  // Branch volumes in K-INR
  topBranches:     ['Br 47','Br 39','Br 25','Br 46','Br 50','Br 15','Br 27','Br 12','Br 8','Br 33'],
  topBranchAmts:   [2708,2654,2625,2621,2617,2590,2571,2548,2530,2510].map(v=>Math.round(v*84)),
  topBranchCounts: [1054,1031,1025,1051,1071,1044,1042,1020,1012,1008],
};

// ---- Colour palette ----
const P = {
  indigo: '#6366f1', purple: '#8b5cf6', green:  '#10b981',
  amber:  '#f59e0b', red:    '#ef4444', blue:   '#3b82f6',
  cyan:   '#06b6d4', rose:   '#f43f5e',
};

// ---- Shared tooltip ----
const TOOLTIP = {
  backgroundColor: '#131520', titleColor: '#e8eaf6', bodyColor: '#8892b0',
  borderColor: 'rgba(99,102,241,0.35)', borderWidth: 1, cornerRadius: 8, padding: 12,
};

// ---- Scale helper ----
function gridScale(extra = {}) {
  return { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color:'#8892b0', font:{size:11} }, ...extra };
}

// ---- Bar dataset helper ----
function barDs(label, data, colors, extra = {}) {
  return { label, data, backgroundColor: colors, borderRadius:6, borderSkipped:false, ...extra };
}

// ================================================
// CHART REGISTRY — lazy init per section
// ================================================
const charts = {};
function getOrCreate(id, buildFn) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  charts[id] = buildFn(canvas);
  return charts[id];
}

// ================================================
// SECTION NAVIGATION
// ================================================
const sectionInited = {};
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  const sec = document.getElementById('section-' + name);
  const nav = document.getElementById('nav-' + name);
  if (!sec || !nav) return;
  sec.classList.add('active');
  nav.classList.add('active');
  document.getElementById('breadcrumb').textContent = {
    dashboard:'Dashboard', transactions:'Transactions', loans:'Loan Risk',
    accounts:'Accounts', fraud:'Fraud Monitor', roadmap:'Project Roadmap'
  }[name] || name;

  if (!sectionInited[name]) {
    sectionInited[name] = true;
    const inits = {
      dashboard: initDashboardCharts, transactions: initTransactionCharts,
      loans: initLoanCharts, accounts: initAccountCharts, fraud: initFraudCharts,
    };
    if (inits[name]) inits[name]();
  } else {
    requestAnimationFrame(() => Object.values(charts).forEach(c => { try { c.resize(); } catch(_){} }));
  }
}

// ================================================
// SIDEBAR TOGGLE
// ================================================
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }

// ================================================
// THEME TOGGLE
// ================================================
function toggleTheme() {
  const html = document.documentElement;
  const isNowLight = !html.dataset.theme;
  html.dataset.theme = isNowLight ? 'light' : '';
  document.getElementById('themeIcon').innerHTML = isNowLight
    ? '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
    : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
}

// ================================================
// ANIMATED COUNTER (₹ Crore format for money)
// ================================================
function animateCounter(el, target, isMoney = false) {
  const duration = 1800;
  const start = performance.now();
  const update = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(eased * target);
    if (isMoney) {
      // target is USD value; convert to INR then display as Crore
      const inr = current * USD_TO_INR;
      el.textContent = inr >= CRORE
        ? '₹' + (inr / CRORE).toFixed(1) + ' Cr'
        : '₹' + inr.toLocaleString('en-IN');
    } else {
      el.textContent = current.toLocaleString('en-IN');
    }
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

function initCounters() {
  document.querySelectorAll('.kpi-value').forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    if (!isNaN(target)) animateCounter(el, target, el.classList.contains('money'));
  });
}

// ================================================
// SPARKLINES
// ================================================
function createSparkline(canvasId, data, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas, {
    type: 'line',
    data: { labels: data.map((_,i)=>i), datasets:[{
      data, borderColor:color, borderWidth:2, fill:true,
      backgroundColor:color+'30', tension:0.4, pointRadius:0
    }]},
    options: { responsive:false, animation:false,
      plugins:{legend:{display:false},tooltip:{enabled:false}},
      scales:{x:{display:false},y:{display:false}} }
  });
}
function initSparklines() {
  [
    ['spark1',[850,900,920,880,960,1010,1080,1111],P.indigo],
    ['spark2',[1400,1450,1480,1510,1530,1600,1650,1667],P.green],
    ['spark3',[65,70,72,75,78,80,81,82],P.amber],
    ['spark4',[28,31,29,30,32,33,34,34],P.red],
    ['spark5',[42000,44000,46000,47000,48000,49000,49500,50000],P.blue],
    ['spark6',[290,298,305,310,315,320,330,333],P.purple],
  ].forEach(([id,data,color])=>createSparkline(id,data,color));
}

// ================================================
// DASHBOARD CHARTS
// ================================================
function initDashboardCharts() {
  // Line — monthly 2023 (K-INR)
  getOrCreate('transactionChart', canvas => new Chart(canvas, {
    type:'line',
    data:{
      labels:DATA.months2023,
      datasets:[
        {label:'Deposits',   data:DATA.deposits2023,    borderColor:P.indigo, backgroundColor:P.indigo+'22', borderWidth:2.5,tension:0.4,fill:true,pointRadius:3,pointHoverRadius:6},
        {label:'Withdrawals',data:DATA.withdrawals2023, borderColor:P.red,   backgroundColor:P.red+'18',    borderWidth:2.5,tension:0.4,fill:true,pointRadius:3,pointHoverRadius:6},
        {label:'Transfers',  data:DATA.transfers2023,   borderColor:P.green,  backgroundColor:P.green+'18',  borderWidth:2.5,tension:0.4,fill:true,pointRadius:3,pointHoverRadius:6},
        {label:'Payments',   data:DATA.payments2023,    borderColor:P.amber,  backgroundColor:P.amber+'18',  borderWidth:2.5,tension:0.4,fill:true,pointRadius:3,pointHoverRadius:6},
      ]
    },
    options:{
      responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,mode:'index',intersect:false,
        callbacks:{label:ctx=>`${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN')}K`}}},
      scales:{x:gridScale(),y:gridScale({ticks:{color:'#8892b0',font:{size:11},callback:v=>axisKINR(v)}})}
    }
  }));

  // Doughnut — transaction type share
  getOrCreate('typeDonutChart', canvas => new Chart(canvas, {
    type:'doughnut',
    data:{labels:Object.keys(DATA.txTypeCounts),datasets:[{
      data:Object.values(DATA.txTypeCounts),
      backgroundColor:[P.indigo,P.red,P.green,P.amber],borderWidth:0,hoverOffset:10
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'65%',animation:{duration:900},
      plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:10,padding:12,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP}}
  }));

  // Doughnut — customer types
  getOrCreate('customerTypeChart', canvas => new Chart(canvas, {
    type:'doughnut',
    data:{labels:DATA.customerTypes,datasets:[{
      data:DATA.customerCounts,backgroundColor:[P.indigo,P.purple,P.blue],borderWidth:0,hoverOffset:10
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',animation:{duration:900},
      plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:10,padding:10,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP}}
  }));

  // Bar — balance distribution
  getOrCreate('balanceDistChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.balanceBuckets,datasets:[barDs('Accounts',DATA.balanceCounts,[P.blue,P.indigo,P.purple,P.green])]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,callbacks:{label:ctx=>ctx.parsed.y+' accounts'}}},
      scales:{x:gridScale(),y:gridScale({beginAtZero:true})}}
  }));

  // Doughnut — account status
  getOrCreate('accountStatusChart', canvas => new Chart(canvas, {
    type:'doughnut',
    data:{labels:DATA.accountStatuses,datasets:[{
      data:DATA.accountStatusCounts,backgroundColor:[P.green,P.amber,P.red],borderWidth:0,hoverOffset:10
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',animation:{duration:900},
      plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:10,padding:10,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP}}
  }));
}

// ================================================
// TRANSACTION SECTION CHARTS + TABLE
// ================================================
const txTypes = ['Deposit','Withdrawal','Transfer','Payment'];

// Generate fake transactions with amounts in INR
const fakeTransactions = Array.from({length:200}, () => {
  const typeIdx = Math.floor(Math.random()*4);
  const month   = String(Math.floor(Math.random()*12)+1).padStart(2,'0');
  const day     = String(Math.floor(Math.random()*28)+1).padStart(2,'0');
  const hour    = String(Math.floor(Math.random()*24)).padStart(2,'0');
  // Amount in INR: ₹8,400 – ₹8,00,000 (was $100–$9,600 × 84)
  const amtINR  = Math.round((Math.random()*9500+100) * USD_TO_INR);
  return {
    id:     3000000 + Math.floor(Math.random()*50000),
    origin: 200000  + Math.floor(Math.random()*1667),
    dest:   200000  + Math.floor(Math.random()*1667),
    type:   txTypes[typeIdx],
    amount: amtINR,
    date:   `2023-${month}-${day} ${hour}:00`,
    branch: Math.floor(Math.random()*50)+1,
  };
});

let filteredTransactions = [...fakeTransactions];
let currentPage = 1;
const ROWS_PER_PAGE = 10;

function initTransactionCharts() {
  buildYearlyChart('amount');

  // Horizontal bar — top branches (K-INR)
  getOrCreate('branchChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{
      labels:DATA.topBranches,
      datasets:[barDs('Volume',DATA.topBranchAmts,
        [P.indigo,P.purple,P.blue,P.cyan,P.green,P.amber,P.red,P.rose,P.indigo,P.purple]
      )]
    },
    options:{
      indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,callbacks:{
        label:ctx=>'₹'+ctx.parsed.x.toLocaleString('en-IN')+'K'
      }}},
      scales:{
        x:gridScale({ticks:{color:'#8892b0',font:{size:11},callback:v=>axisKINR(v)}}),
        y:gridScale({ticks:{color:'#8892b0',font:{size:10}}})
      }
    }
  }));

  renderTransactionTable();
}

let yearlyChartMode = 'amount';
function buildYearlyChart(mode) {
  yearlyChartMode = mode;
  const srcData = mode==='amount' ? DATA.yearlyAmounts : DATA.yearlyCounts;
  const colors  = [P.indigo, P.red, P.green, P.amber];
  const datasets = Object.entries(srcData).map(([key,vals],i)=>({
    label:key, data:vals, backgroundColor:colors[i],
    borderRadius:6, borderSkipped:false, barPercentage:0.75, categoryPercentage:0.8,
  }));

  getOrCreate('yearlyChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.years,datasets},
    options:{
      responsive:true,maintainAspectRatio:false,animation:{duration:800},
      plugins:{
        legend:{display:true,position:'top',align:'end',labels:{boxWidth:10,font:{size:11},color:'#8892b0'}},
        tooltip:{...TOOLTIP,callbacks:{label:ctx=>
          mode==='amount'
            ? `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString('en-IN')}K`
            : `${ctx.dataset.label}: ${ctx.parsed.y} txns`
        }}
      },
      scales:{
        x:gridScale(),
        y:gridScale({ticks:{color:'#8892b0',font:{size:11},callback:v=>mode==='amount'?axisKINR(v):v}})
      }
    }
  }));
}

function updateYearChart(mode, btn) {
  document.querySelectorAll('.ctrl-btn').forEach(b=>b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  buildYearlyChart(mode);
}

// ---- Transaction Table ----
function renderTransactionTable() {
  const tbody = document.getElementById('txTableBody');
  if (!tbody) return;
  const start      = (currentPage-1)*ROWS_PER_PAGE;
  const pageData   = filteredTransactions.slice(start, start+ROWS_PER_PAGE);
  const totalPages = Math.ceil(filteredTransactions.length/ROWS_PER_PAGE);
  document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
  document.getElementById('prevPage').disabled = currentPage===1;
  document.getElementById('nextPage').disabled = currentPage===totalPages;

  const badge = {Deposit:'badge-deposit',Withdrawal:'badge-withdrawal',Transfer:'badge-transfer',Payment:'badge-payment'};
  tbody.innerHTML = pageData.map(tx=>`
    <tr>
      <td>#${tx.id}</td>
      <td>${tx.origin}</td>
      <td>${tx.dest}</td>
      <td><span class="tx-type-badge ${badge[tx.type]}">${tx.type}</span></td>
      <td>₹${tx.amount.toLocaleString('en-IN')}</td>
      <td>${tx.date}</td>
      <td>Branch ${tx.branch}</td>
    </tr>
  `).join('');
}

function filterTransactions() {
  const filter = document.getElementById('txTypeFilter').value;
  filteredTransactions = filter==='all' ? [...fakeTransactions] : fakeTransactions.filter(t=>t.type===filter);
  currentPage = 1;
  renderTransactionTable();
}
function changePage(delta) {
  const totalPages = Math.ceil(filteredTransactions.length/ROWS_PER_PAGE);
  currentPage = Math.max(1, Math.min(totalPages, currentPage+delta));
  renderTransactionTable();
}

// ================================================
// LOAN CHARTS
// ================================================
function initLoanCharts() {
  getOrCreate('loanStatusChart', canvas => new Chart(canvas, {
    type:'doughnut',
    data:{labels:DATA.loanStatuses,datasets:[{
      data:DATA.loanStatusCounts,backgroundColor:[P.green,P.indigo,P.red],borderWidth:0,hoverOffset:10
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',animation:{duration:900},
      plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:10,padding:10,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP}}
  }));

  getOrCreate('interestRateChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.irBands,datasets:[barDs('Loans',DATA.irCounts,
      DATA.irBands.map((_,i)=>`hsla(${220+i*15},75%,62%,0.9)`)
    )]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,callbacks:{label:ctx=>ctx.parsed.y+' loans'}}},
      scales:{x:gridScale(),y:gridScale({beginAtZero:true})}}
  }));

  getOrCreate('loanAmtChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.loanAmtBuckets,datasets:[barDs('Loans',DATA.loanAmtCounts,
      [P.blue,P.indigo,P.purple,P.green,P.amber]
    )]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,callbacks:{label:ctx=>ctx.parsed.y+' loans'}}},
      scales:{x:gridScale(),y:gridScale({beginAtZero:true})}}
  }));
}

// ================================================
// ACCOUNT CHARTS
// ================================================
function initAccountCharts() {
  getOrCreate('accountTypeStatusChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.accountTypes,datasets:[
      {label:'Active',  data:DATA.accountTypeActive,  backgroundColor:P.green+'cc',borderRadius:5,borderSkipped:false,barPercentage:0.75},
      {label:'Inactive',data:DATA.accountTypeInactive,backgroundColor:P.amber+'cc',borderRadius:5,borderSkipped:false,barPercentage:0.75},
      {label:'Closed',  data:DATA.accountTypeClosed,  backgroundColor:P.red+'cc',  borderRadius:5,borderSkipped:false,barPercentage:0.75},
    ]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:true,position:'top',align:'end',labels:{boxWidth:10,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP},
      scales:{x:gridScale(),y:gridScale({beginAtZero:true})}}
  }));

  getOrCreate('accountTypeDonut', canvas => new Chart(canvas, {
    type:'doughnut',
    data:{labels:DATA.accountTypes,datasets:[{
      data:DATA.accountTypeCounts,backgroundColor:[P.indigo,P.green,P.amber,P.red,P.purple],borderWidth:0,hoverOffset:10
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'58%',animation:{duration:900},
      plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:10,padding:10,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP}}
  }));

  getOrCreate('balanceBarChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.balanceBuckets,datasets:[barDs('Accounts',DATA.balanceCounts,[P.blue,P.indigo,P.purple,P.green])]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,callbacks:{label:ctx=>ctx.parsed.y+' accounts'}}},
      scales:{x:gridScale(),y:gridScale({beginAtZero:true})}}
  }));
}

// ================================================
// FRAUD CHARTS
// ================================================
function initFraudCharts() {
  getOrCreate('fraudRiskChart', canvas => new Chart(canvas, {
    type:'doughnut',
    data:{labels:['Low Risk (Active)','Medium Risk (Paid Off)','High Risk (Overdue)'],datasets:[{
      data:[242,57,34],backgroundColor:[P.green,P.amber,P.red],borderWidth:0,hoverOffset:10
    }]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',animation:{duration:900},
      plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:10,padding:8,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP}}
  }));

  getOrCreate('anomalyChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:['Missing Values','Typos','Duplicates','Format Issues','Date Issues','Future Dates','Bad IDs'],
      datasets:[barDs('% of Records',[2.0,1.0,1.0,1.0,1.0,1.0,1.0],
        [P.red,P.amber,P.amber,P.indigo,P.indigo,P.purple,P.purple]
      )]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:false},tooltip:{...TOOLTIP,callbacks:{label:ctx=>ctx.parsed.y+'% of data'}}},
      scales:{
        x:gridScale({ticks:{color:'#8892b0',font:{size:10},maxRotation:30}}),
        y:{...gridScale(),max:2.8,ticks:{color:'#8892b0',font:{size:11},callback:v=>v+'%'}}
      }}
  }));

  getOrCreate('riskByTypeChart', canvas => new Chart(canvas, {
    type:'bar',
    data:{labels:DATA.accountTypes,datasets:[
      {label:'Overdue Loans',data:[7,6,8,7,6],backgroundColor:P.red+'cc',  borderRadius:5,borderSkipped:false},
      {label:'Active Loans', data:[50,48,47,52,45],backgroundColor:P.green+'cc',borderRadius:5,borderSkipped:false},
    ]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:900},
      plugins:{legend:{display:true,position:'top',align:'end',labels:{boxWidth:10,font:{size:11},color:'#8892b0'}},tooltip:TOOLTIP},
      scales:{x:gridScale(),y:gridScale({beginAtZero:true})}}
  }));
}

// ================================================
// FRAUD RISK SCORER (thresholds in INR)
// ================================================
// INR thresholds: ₹42L (Very High), ₹17L (High), ₹4.2L (Moderate)
const THR_VERY_HIGH = 4200000;  // ₹42 Lakh
const THR_HIGH      = 1700000;  // ₹17 Lakh
const THR_MODERATE  =  420000;  // ₹4.2 Lakh

function calcFraudScore() {
  const amount     = parseFloat(document.getElementById('txAmount').value) || 0;
  const loanBal    = parseFloat(document.getElementById('loanBalance').value) || 0;
  const type       = document.getElementById('txType').value;
  const hour       = parseInt(document.getElementById('txHour').value,10)  || 12;
  const freq       = parseInt(document.getElementById('txFreq').value,10)  || 0;
  const loanStatus = document.getElementById('loanStatus').value;
  if (!amount && !freq) return;

  let score = 0;
  const factors = [];

  // Loan Balance checks
  if (loanBal > 0) {
    if (amount > loanBal) { 
      score += 35; 
      factors.push({text:'Txn > Loan Balance', cls:'risk'}); 
    } else if (amount > loanBal * 0.8) { 
      score += 20; 
      factors.push({text:'High % of Loan Balance', cls:'warn'}); 
    }
  }

  if (amount > THR_VERY_HIGH)    { score+=30; factors.push({text:'Very High Amount (>₹42L)',cls:'risk'}); }
  else if (amount > THR_HIGH)    { score+=20; factors.push({text:'High Amount (>₹17L)',     cls:'warn'}); }
  else if (amount > THR_MODERATE){ score+=10; factors.push({text:'Moderate Amount (>₹4.2L)',cls:''}); }

  if (hour>=0&&hour<=5)  { score+=25; factors.push({text:'Late Night Txn',   cls:'risk'}); }
  else if (hour>=22)     { score+=15; factors.push({text:'Late Evening Txn', cls:'warn'}); }

  if (type==='withdrawal')  { score+=15; factors.push({text:'Withdrawal Type',cls:'warn'}); }
  else if (type==='transfer'){ score+=10; factors.push({text:'Transfer Type', cls:''}); }

  if (freq>20)      { score+=25; factors.push({text:'High Txn Frequency',   cls:'risk'}); }
  else if (freq>10) { score+=15; factors.push({text:'Elevated Frequency',   cls:'warn'}); }
  else if (freq>5)  { score+=5;  factors.push({text:'Normal Frequency',cls:''}); }

  if (loanStatus==='overdue')  { score+=20; factors.push({text:'Overdue Loan',    cls:'risk'}); }
  else if (loanStatus==='none'){ score+=5;  factors.push({text:'No Loan Record',  cls:''}); }

  score = Math.min(score, 100);

  const arc = document.getElementById('scoreArc');
  if (arc) arc.style.strokeDashoffset = 314 - (314*score/100);
  document.getElementById('scoreNum').textContent = score;

  const level  = score<25?0:score<50?1:score<75?2:3;
  const icons  = ['✅','⚠️','🚨','🔴'];
  const texts  = ['Low Risk — Transaction appears normal','Moderate Risk — Flagged for review',
                  'High Risk — Manual review required','Critical Risk — Block & investigate immediately'];
  const clrs   = ['#10b981','#f59e0b','#ef4444','#dc2626'];
  const ve = document.getElementById('scoreVerdict');
  ve.querySelector('.verdict-icon').textContent = icons[level];
  ve.querySelector('.verdict-text').textContent = texts[level];
  ve.querySelector('.verdict-text').style.color = clrs[level];
  document.getElementById('verdictFactors').innerHTML =
    factors.map(f=>`<span class="factor-chip ${f.cls}">${f.text}</span>`).join('');
}

// ================================================
// BACKGROUND PARTICLES
// ================================================

// ================================================
// BACKGROUND PARTICLES
// ================================================
function initParticles() {
  const container = document.getElementById('bgParticles');
  if (!container) return;
  const colors = [P.indigo,P.purple,P.green,P.blue,P.amber];
  for (let i=0;i<18;i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const size = Math.random()*4+2;
    Object.assign(p.style,{
      width:size+'px', height:size+'px', left:Math.random()*100+'%',
      background:colors[Math.floor(Math.random()*colors.length)],
      animationDuration:(12+Math.random()*20)+'s',
      animationDelay:(-Math.random()*20)+'s',
    });
    container.appendChild(p);
  }
}

// ================================================
// SEARCH
// ================================================
function initSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;
  const sectionMap = {
    dashboard:    ['dashboard','overview','kpi','executive','summary'],
    transactions: ['transaction','transfer','deposit','withdrawal','payment','branch','volume'],
    loans:        ['loan','credit','risk','interest','default','model','xgboost','forest'],
    accounts:     ['account','balance','savings','checking','business','youth','payroll'],
    fraud:        ['fraud','anomaly','detection','score','suspicious','monitor'],
    roadmap:      ['roadmap','future','phase','vision','upcoming','evolution','cloud','kafka'],
  };
  input.addEventListener('input', function() {
    const q = this.value.toLowerCase().trim();
    if (!q) return;
    for (const [section, keywords] of Object.entries(sectionMap)) {
      if (keywords.some(k=>k.includes(q)||q.includes(k))) { showSection(section); break; }
    }
  });
  document.addEventListener('keydown', e=>{
    if ((e.ctrlKey||e.metaKey)&&e.key==='k') { e.preventDefault(); input.focus(); }
  });
}

// ================================================
// METRIC BAR ANIMATION (Loan section)
// ================================================
function animateMetricBars() {
  document.querySelectorAll('.metric-fill').forEach(el => {
    const target = el.style.width;
    el.style.width = '0%';
    el.style.transition = 'width 1.4s cubic-bezier(0.4,0,0.2,1) 0.3s';
    requestAnimationFrame(()=>requestAnimationFrame(()=>{ el.style.width = target; }));
  });
}

// ================================================
// ENTRY POINT
// ================================================
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initCounters();
  initSparklines();
  initSearch();

  // Boot dashboard (default active section)
  sectionInited['dashboard'] = true;
  initDashboardCharts();

  // Trigger metric bar animation when Loans section first becomes visible
  document.querySelectorAll('.metric-fill').forEach(el=>el.style.width='0%');
  const loanObserver = new IntersectionObserver(entries=>{
    entries.forEach(e=>{ if(e.isIntersecting){ animateMetricBars(); loanObserver.disconnect(); } });
  },{threshold:0.2});
  const loanSection = document.getElementById('section-loans');
  if (loanSection) loanObserver.observe(loanSection);

  // Initialize Loan Predictor default data
  if(document.getElementById('loanIntent')) updateIntentData();
});

// ================================================
// LOAN ELIGIBILITY PREDICTOR
// ================================================
const intentData = {
  Personal: { rate: 12.5, docs: 'ID Proof, Income Proof, Bank Statements (last 3 months)' },
  Education: { rate: 8.5, docs: 'Admission Letter, Fee Structure, ID Proof, Co-applicant Income Proof' },
  Medical: { rate: 10.0, docs: 'Hospital Estimate/Bills, ID Proof, Income Proof' },
  Venture: { rate: 14.0, docs: 'Business Plan, Registration Docs, P&L Statement, ID Proof' },
  HomeImprovement: { rate: 9.5, docs: 'Property Papers, Contractor Estimate, ID Proof, Income Proof' },
  DebtConsolidation: { rate: 11.0, docs: 'Existing Loan Statements, Foreclosure Letters, Income Proof' }
};

function updateIntentData() {
  const intent = document.getElementById('loanIntent').value;
  const data = intentData[intent] || intentData['Personal'];
  document.getElementById('loanInterest').value = data.rate;
  
  const docsList = data.docs.split(', ').map(d => `<li>✅ ${d}</li>`).join('');
  document.getElementById('requiredDocsText').innerHTML = `<ul style="list-style:none; padding:0; margin:4px 0 0 0; display:flex; flex-direction:column; gap:4px;">${docsList}</ul>`;
}

async function predictLoanRisk() {
  const age = parseInt(document.getElementById('loanAge').value, 10) || 28;
  const income = parseFloat(document.getElementById('loanIncome').value) || 0;
  const homeOwnership = document.getElementById('homeOwnership').value;
  const employment = parseFloat(document.getElementById('employmentYrs').value) || 0;
  const principal = parseFloat(document.getElementById('loanPrincipal').value) || 0;
  const interest = parseFloat(document.getElementById('loanInterest').value) || 12.5;
  const intent = document.getElementById('loanIntent').value;
  const creditHist = parseFloat(document.getElementById('creditHistory').value) || 0;

  if (!principal || !income) return;

  // Map requested UI fields to Backend Model Features
  const intentToAccType = { 'Personal':1, 'Education':2, 'Medical':1, 'Venture':4, 'HomeImprovement':3, 'DebtConsolidation':1 };
  
  const reqBody = {
    principal_amount_inr: principal,
    interest_rate: interest / 100, // percentage to decimal
    loan_to_balance_ratio: Math.min(principal / income, 2.0), // heuristic mapped
    txn_frequency_90d: Math.round(5 + employment * 2), // proxy based on employment
    avg_txn_amount_inr: (income / 12) * 0.2, // heuristic based on income
    account_type_id: intentToAccType[intent] || 1,
    loan_duration_days: 1095 // proxy 3 years
  };

  const resDiv = document.getElementById('loanResult');
  resDiv.style.display = 'flex';
  document.getElementById('loanVerdictText').textContent = 'Calculating...';
  document.getElementById('loanVerdictFactors').innerHTML = '';
  
  // Set initial fraud box scanning state
  const fraudBox = document.getElementById('applicationFraudBox');
  fraudBox.style.background = 'rgba(239,68,68,0.05)';
  fraudBox.style.borderColor = 'rgba(239,68,68,0.2)';
  document.getElementById('fraudCheckIcon').textContent = '🕵️';
  document.getElementById('fraudCheckStatus').textContent = 'Scanning...';
  document.getElementById('fraudCheckStatus').style.color = 'var(--text-primary)';
  document.getElementById('fraudCheckDesc').textContent = 'Analyzing application anomalies';

  try {
    // Try hitting the Flask API
    const response = await fetch('http://127.0.0.1:5000/api/predict/loan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody)
    });
    
    if (response.ok) {
      const data = await response.json();
      displayLoanResult(data.default_percentage, data.risk_class, data.model_used);
      evaluateApplicationFraud(age, income, employment, principal, creditHist);
      return;
    }
  } catch (e) {
    console.log("API offline, falling back to heuristic model");
  }

  // Fallback heuristic if API is unavailable
  let prob = 5; // base 5% probability
  if (principal / income > 0.8) prob += 20;
  else if (principal / income > 0.5) prob += 10;
  
  if (interest > 12) prob += 25;
  else if (interest > 8) prob += 15;
  
  if (employment < 2) prob += 15;
  
  if (principal > 2000000) prob += 10;

  prob = Math.min(prob, 95);
  
  let riskClass = 'LOW';
  if (prob >= 75) riskClass = 'CRITICAL';
  else if (prob >= 50) riskClass = 'HIGH';
  else if (prob >= 25) riskClass = 'MODERATE';
  
  setTimeout(() => {
    displayLoanResult(prob, riskClass, 'Heuristic Fallback');
    evaluateApplicationFraud(age, income, employment, principal, creditHist);
  }, 600);
}

function evaluateApplicationFraud(age, income, employment, principal, creditHist) {
  let fraudScore = 0;
  let anomaly = '';
  let flag = 'CLEAN';

  if (age < 22 && income > 1500000) {
    fraudScore += 40; anomaly = 'Age/Income mismatch anomaly'; flag = 'SUSPICIOUS';
  } else if (creditHist === 0 && principal > 1000000) {
    fraudScore += 35; anomaly = 'High amount with no credit history'; flag = 'SUSPICIOUS';
  } else if (principal > income * 8) {
    fraudScore += 50; anomaly = 'Principal exceeds 8x annual income'; flag = 'HIGH RISK';
  } else if (employment > 0 && age - employment < 16) {
    fraudScore += 60; anomaly = 'Impossible employment duration for age'; flag = 'HIGH RISK';
  }

  const box = document.getElementById('applicationFraudBox');
  const icon = document.getElementById('fraudCheckIcon');
  const status = document.getElementById('fraudCheckStatus');
  const desc = document.getElementById('fraudCheckDesc');

  if (fraudScore === 0) {
    box.style.background = 'rgba(16,185,129,0.05)';
    box.style.borderColor = 'rgba(16,185,129,0.2)';
    icon.textContent = '✅';
    status.textContent = 'Verified & Clean';
    status.style.color = '#10b981';
    desc.textContent = 'No fraud anomalies detected';
  } else if (flag === 'SUSPICIOUS') {
    box.style.background = 'rgba(245,158,11,0.05)';
    box.style.borderColor = 'rgba(245,158,11,0.2)';
    icon.textContent = '⚠️';
    status.textContent = 'Suspicious Profile';
    status.style.color = '#f59e0b';
    desc.textContent = anomaly;
  } else {
    box.style.background = 'rgba(239,68,68,0.05)';
    box.style.borderColor = 'rgba(239,68,68,0.2)';
    icon.textContent = '🚨';
    status.textContent = 'Fraud Alert';
    status.style.color = '#ef4444';
    desc.textContent = anomaly;
    
    // Auto-override default risk visually if high fraud risk
    setTimeout(() => {
      document.getElementById('loanVerdictText').textContent = 'Rejected (Fraud Prevention)';
      document.getElementById('loanVerdictText').style.color = '#ef4444';
      document.getElementById('loanVerdictIcon').textContent = '🚫';
    }, 100);
  }
}

function displayLoanResult(prob, riskClass, modelName) {
  const arc = document.getElementById('loanScoreArc');
  if (arc) arc.style.strokeDashoffset = 314 - (314 * prob / 100);
  document.getElementById('loanScoreNum').textContent = Math.round(prob);

  const icons = { 'LOW': '✅', 'MODERATE': '⚠️', 'HIGH': '🚨', 'CRITICAL': '🔴' };
  const texts = {
    'LOW': 'Low Default Risk — Eligible for Loan',
    'MODERATE': 'Moderate Risk — Further Review Required',
    'HIGH': 'High Risk — Likely to Default',
    'CRITICAL': 'Critical Risk — Application Denied'
  };
  const clrs = { 'LOW': '#10b981', 'MODERATE': '#f59e0b', 'HIGH': '#ef4444', 'CRITICAL': '#dc2626' };

  const iconEl = document.getElementById('loanVerdictIcon');
  const textEl = document.getElementById('loanVerdictText');
  
  iconEl.textContent = icons[riskClass] || '❓';
  textEl.textContent = texts[riskClass] || 'Unknown Risk';
  textEl.style.color = clrs[riskClass] || '#e8eaf6';

  let factorsHTML = `<span class="factor-chip" style="background:rgba(99,102,241,0.1); color:var(--accent-indigo); border: 1px solid rgba(99,102,241,0.2);">Model: ${modelName || 'XGBoost'}</span>`;
  
  if (prob > 50) {
     factorsHTML += `<span class="factor-chip risk" style="background:rgba(239,68,68,0.1); color:#ef4444; border: 1px solid rgba(239,68,68,0.2);">High Probability</span>`;
  } else {
     factorsHTML += `<span class="factor-chip" style="background:rgba(16,185,129,0.1); color:#10b981; border: 1px solid rgba(16,185,129,0.2);">Safe Range</span>`;
  }

  document.getElementById('loanVerdictFactors').innerHTML = factorsHTML;
}
