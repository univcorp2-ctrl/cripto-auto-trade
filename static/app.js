let chart;
const $ = (id) => document.getElementById(id);
const pct = (v) => `${(v * 100).toFixed(2)}%`;
const num = (v) => Number(v).toFixed(2);

async function init(){
  try{
    const health = await fetch('/api/health').then(r=>r.json());
    $('healthDot').className = 'dot ok'; $('healthText').textContent = health.service;
  }catch(e){$('healthDot').className='dot bad';$('healthText').textContent='offline'}
  const data = await fetch('/api/strategies').then(r=>r.json());
  $('strategy').innerHTML = data.strategies.map(s=>`<option value="${s.name}">${s.label} - ${s.style}</option>`).join('');
  $('runBacktest').onclick = () => run('/api/backtest', 'Backtest');
  $('runForward').onclick = () => runForward();
  $('runRealtime').onclick = () => run('/api/realtime', 'Realtime');
  $('runCompare').onclick = () => runCompare();
  await runCompare();
  await run('/api/backtest', 'Backtest');
}
function query(){
  const p = new URLSearchParams({strategy:$('strategy').value,data_source:$('dataSource').value,exchange:$('exchange').value,symbol:$('symbol').value,timeframe:$('timeframe').value,limit:'350'});
  if($('dataSource').value === 'live') p.set('live','true');
  return p;
}
async function run(path, label){
  $('chartSubtitle').textContent = 'Loading...';
  try{
    const result = await fetch(`${path}?${query()}`).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()});
    renderResult(result, label);
  }catch(e){renderError(e)}
}
async function runForward(){
  $('chartSubtitle').textContent = 'Forward testing...';
  try{
    const result = await fetch(`/api/forward-test?${query()}`).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()});
    renderResult(result.forward, `Forward: ${result.verdict}`);
    $('latestJson').textContent = JSON.stringify(result, null, 2);
  }catch(e){renderError(e)}
}
async function runCompare(){
  try{
    const result = await fetch(`/api/compare?${query()}`).then(r=>r.json());
    renderTable(result.backtest.map(r=>({strategy:r.strategy,total_return:r.total_return,max_drawdown:r.max_drawdown,trade_count:r.trade_count,verdict:r.total_return>0?'positive':'watch'})));
  }catch(e){renderError(e)}
}
function renderResult(result, label){
  $('totalReturn').textContent = pct(result.total_return || 0);
  $('drawdown').textContent = pct(result.max_drawdown || 0);
  $('sharpe').textContent = num(result.sharpe_like || 0);
  $('trades').textContent = result.trade_count ?? 0;
  $('latestSignal').textContent = result.latest_signal?.action || '-';
  $('latestJson').textContent = JSON.stringify(result.latest_signal || result, null, 2);
  $('chartSubtitle').textContent = `${label} / ${result.strategy || $('strategy').value}`;
  drawChart(result.equity_curve || []);
}
function drawChart(points){
  const ctx = $('equityChart');
  if(chart) chart.destroy();
  chart = new Chart(ctx, {type:'line', data:{labels:points.map(p=>String(p.timestamp).slice(0,10)), datasets:[{label:'Equity', data:points.map(p=>p.equity), borderColor:'#56f39a', backgroundColor:'rgba(86,243,154,.12)', fill:true, tension:.25, pointRadius:0}]}, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{labels:{color:'#e9f8ff'}}}, scales:{x:{ticks:{color:'#9eb8c7'},grid:{color:'rgba(255,255,255,.05)'}},y:{ticks:{color:'#9eb8c7'},grid:{color:'rgba(255,255,255,.06)'}}}}});
}
function renderTable(rows){
  $('comparison').querySelector('tbody').innerHTML = rows.map(r=>`<tr><td>${r.strategy}</td><td class="${r.total_return>=0?'positive':'negative'}">${pct(r.total_return)}</td><td>${pct(r.max_drawdown)}</td><td>${r.trade_count}</td><td>${r.verdict}</td></tr>`).join('');
}
function renderError(e){
  $('chartSubtitle').textContent = 'Error';
  $('latestJson').textContent = String(e.stack || e);
}
init();
