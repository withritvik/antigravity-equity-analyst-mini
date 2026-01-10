"""
Mini Analyst - Minimal Stock Analysis App
Lightweight Python-only backend for constrained environments (512MB RAM, 0.1 CPU)
Uses separate agent files called via subprocess, same architecture as main Analyst.
"""

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))
from orchestration_agent import DebateSimulator

app = Flask(__name__)

# Path to agent scripts
AGENTS_DIR = os.path.join(os.path.dirname(__file__), 'agents')

# ============== Agent Runner ==============

def run_agent(script_name, symbol):
    """Run a Python agent script and return JSON result"""
    script_path = os.path.join(AGENTS_DIR, script_name)
    
    try:
        result = subprocess.run(
            ['python3', script_path, symbol],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "Agent failed"
            }
        
        # Find JSON in output (last line starting with {)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('{'):
                return json.loads(line)
        
        return {"success": False, "error": "No JSON output from agent"}
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Agent timed out"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": "Invalid JSON: " + str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def full_analysis(symbol):
    """Run agents and orchestrate debate"""
    # Run technical (valuation) agent
    tech = run_agent('valuation_agent.py', symbol)
    
    # Run fundamental agent
    fund = run_agent('fundamental_agent.py', symbol)
    
    if not tech.get('success') and not fund.get('success'):
        return {
            "success": False, 
            "error": "Analysis failed. Tech: " + tech.get('error', 'Unknown') + 
                     " | Fund: " + fund.get('error', 'Unknown')
        }
    
    # Run Orchestration / Debate
    simulator = DebateSimulator(fund, tech, symbol)
    debate_result = simulator.run_debate()
    
    # Get company name
    company = fund.get('company_info', {}).get('name') or symbol
    if isinstance(company, dict):
        company = symbol
    
    return {
        "success": True,
        "symbol": symbol,
        "company": company,
        "signal": debate_result['final_signal'],
        "score": debate_result['final_score'],
        "transcript": debate_result['transcript'],
        "technical": tech,
        "fundamental": fund
    }

# ============== HTML Template ==============

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini Analyst</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: monospace; 
            background: #000; 
            color: #fff; 
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 30px;
            font-size: 18px;
        }
        .container {
            text-align: center;
            max-width: 800px;
            width: 100%;
        }
        h1 { 
            font-size: 3em;
            margin-bottom: 15px;
        }
        .subtitle {
            color: #888;
            font-size: 1.2em;
            margin-bottom: 50px;
        }
        .search-box {
            margin-bottom: 20px;
        }
        input { 
            background: #111; 
            border: 2px solid #444; 
            color: #fff; 
            padding: 20px 25px; 
            width: 100%;
            max-width: 400px;
            font-family: monospace;
            font-size: 1.4em;
            text-align: center;
            text-transform: uppercase;
        }
        input::placeholder {
            text-transform: none;
        }
        button { 
            background: #fff; 
            color: #000; 
            border: none; 
            padding: 18px 60px; 
            cursor: pointer;
            font-family: monospace;
            font-weight: bold;
            font-size: 1.3em;
            margin-top: 15px;
        }
        button:hover { background: #ccc; }
        button:disabled { background: #666; cursor: wait; }
        .hint {
            color: #0f0;
            font-size: 1em;
            margin-top: 25px;
            line-height: 1.6;
        }
        .result { 
            margin-top: 40px; 
            padding: 25px; 
            border: 1px solid #444;
            background: #111;
            text-align: left;
            width: 100%;
            font-size: 1em;
        }
        .buy { color: #0f0; }
        .sell { color: #f00; }
        .loading { color: #ff0; }
        .signal {
            font-size: 2em;
            text-align: center;
            margin: 15px 0;
        }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        td { padding: 5px; border-bottom: 1px solid #333; }
        td:first-child { color: #888; }
        td:last-child { text-align: right; }
        .error { color: #f66; }
        h3, h4 { margin-top: 15px; margin-bottom: 10px; }
        .index-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #111;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: center;
            gap: 60px;
            padding: 12px 20px;
            font-size: 1em;
            z-index: 100;
        }
        .index-item {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .index-name { color: #888; }
        .index-value { color: #fff; font-weight: bold; }
        .index-change.up { color: #0f0; }
        .index-change.down { color: #f00; }
        .footer {
            margin-top: 50px;
            color: #444;
            font-size: 0.8em;
            text-align: center;
            width: 100%;
        }
        body { padding-top: 60px; }
        
        /* Debate Styles */
        .debate-container {
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            max-height: 500px;
            overflow-y: auto;
        }
        .dialogue-box {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 6px;
            position: relative;
        }
        .speaker-fund {
            background: #1a2a1a;
            border-left: 4px solid #0f0;
            margin-right: 20%;
        }
        .speaker-tech {
            background: #2a1a1a;
            border-left: 4px solid #f00;
            margin-left: 20%;
        }
        .speaker-orch {
            background: #1a1a2a;
            border-left: 4px solid #00f;
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
        }
        .speaker-name {
            font-size: 0.8em;
            color: #888;
            margin-bottom: 4px;
            display: block;
            text-transform: uppercase;
        }
        .dialogue-text {
            color: #e0e0e0;
        }
        .tone-tag {
            font-size: 0.7em;
            color: #666;
            margin-left: 10px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="index-bar">
        <div class="index-item">
            <span class="index-name">NIFTY 50</span>
            <span id="nifty-value" class="index-value">--</span>
            <span id="nifty-change" class="index-change">--</span>
        </div>
        <div class="index-item">
            <span class="index-name">S&P 500</span>
            <span id="sp500-value" class="index-value">--</span>
            <span id="sp500-change" class="index-change">--</span>
        </div>
    </div>
    
    <div class="container">
        <h1>MINI ANALYST</h1>
        <p class="subtitle">Minimal Stock Analysis</p>
        
        <div class="search-box">
            <input type="text" id="ticker" placeholder="Enter ticker symbol">
        </div>
        
        <button onclick="analyzeStock()">ANALYZE</button>
        
        <p class="hint">
            Enter ticker symbol (e.g., AAPL, MSFT)<br>
            For NSE stocks, add .NS suffix (e.g., RELIANCE.NS, TCS.NS)
        </p>
        
        <div id="result" class="result" style="display:none;"></div>

        <div class="footer">
            <p>PM - Ritvik Pandey</p>
            <p>Engineer - Google AntiGravity</p>
        </div>
    </div>
    
    <script>
        // Fetch index data on load
        function fetchIndices() {
            fetch('/indices')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.nifty) {
                        document.getElementById('nifty-value').textContent = data.nifty.value.toLocaleString();
                        var niftyChange = document.getElementById('nifty-change');
                        niftyChange.textContent = (data.nifty.change >= 0 ? '+' : '') + data.nifty.change.toFixed(2) + '%';
                        niftyChange.className = 'index-change ' + (data.nifty.change >= 0 ? 'up' : 'down');
                    }
                    if (data.sp500) {
                        document.getElementById('sp500-value').textContent = data.sp500.value.toLocaleString();
                        var sp500Change = document.getElementById('sp500-change');
                        sp500Change.textContent = (data.sp500.change >= 0 ? '+' : '') + data.sp500.change.toFixed(2) + '%';
                        sp500Change.className = 'index-change ' + (data.sp500.change >= 0 ? 'up' : 'down');
                    }
                })
                .catch(function(e) { console.log('Index fetch error:', e); });
        }
        fetchIndices();
        setInterval(fetchIndices, 5000); // Refresh every 5 seconds
        
        document.getElementById('ticker').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeStock();
        });
        
        function analyzeStock() {
            var ticker = document.getElementById('ticker').value.trim().toUpperCase();
            if (!ticker) { alert('Please enter a ticker symbol'); return; }
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerHTML = '<p class="loading" style="text-align:center;">Analyzing ' + ticker + '...</p>';
            
            fetch('/analyze?symbol=' + encodeURIComponent(ticker))
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        var html = '<h3 style="text-align:center;">' + data.company + '</h3>';
                        html += '<p style="text-align:center;color:#888;">' + data.symbol + '</p>';
                        html += '<p class="signal ' + data.signal.toLowerCase() + '">' + data.signal + ' (' + data.score + '/100)</p>';
                        
                        // Debate Transcript
                        html += '<h4>Analyst Debate (5 Rounds)</h4>';
                        html += '<div class="debate-container">';
                        
                        data.transcript.forEach(function(entry) {
                            var speakerClass = '';
                            if (entry.speaker.includes('Fundamental')) speakerClass = 'speaker-fund';
                            else if (entry.speaker.includes('Technical')) speakerClass = 'speaker-tech';
                            else speakerClass = 'speaker-orch';
                            
                            html += '<div class="dialogue-box ' + speakerClass + '">';
                            html += '<span class="speaker-name">' + entry.speaker;
                            html += '<span class="tone-tag">(' + entry.tone + ')</span></span>';
                            html += '<p class="dialogue-text">' + entry.message + '</p>';
                            html += '</div>';
                        });
                        
                        html += '</div>';
                        
                        // Data Tables
                        html += '<div style="display:flex; gap:20px; flex-wrap:wrap;">';
                        
                        // Technical Table
                        html += '<div style="flex:1; min-width:250px;">';
                        html += '<h4>Technical Data</h4>';
                        if (data.technical.success) {
                            html += '<table>';
                            var techMetrics = data.technical.metrics || {};
                            for (var k in techMetrics) {
                                html += '<tr><td>' + k + '</td><td>' + techMetrics[k] + '</td></tr>';
                            }
                            html += '</table>';
                        }
                        html += '</div>';
                        
                        // Fundamental Table
                        html += '<div style="flex:1; min-width:250px;">';
                        html += '<h4>Fundamental Data</h4>';
                        if (data.fundamental.success) {
                            html += '<table>';
                            var fundMetrics = data.fundamental.metrics || {};
                            for (var k in fundMetrics) {
                                html += '<tr><td>' + k + '</td><td>' + fundMetrics[k] + '</td></tr>';
                            }
                            html += '</table>';
                        }
                        html += '</div>';
                        
                        html += '</div>'; // End data tables div
                        
                        document.getElementById('result').innerHTML = html;
                    } else {
                        document.getElementById('result').innerHTML = '<p class="error" style="text-align:center;">Error: ' + data.error + '</p>';
                    }
                })
                .catch(function(e) {
                    document.getElementById('result').innerHTML = '<p class="error" style="text-align:center;">Error: ' + e.message + '</p>';
                });
        }
    </script>
</body>
</html>
"""

# ============== Routes ==============

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze')
def analyze_route():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({"success": False, "error": "No symbol provided"})
    return jsonify(full_analysis(symbol))

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/indices')
def get_indices():
    """Fetch real-time NIFTY50 and S&P500 index values"""
    result = {}
    
    try:
        # NIFTY 50
        nifty = yf.Ticker('^NSEI')
        nifty_hist = nifty.history(period='2d')
        if len(nifty_hist) >= 2:
            current = nifty_hist['Close'].iloc[-1]
            prev = nifty_hist['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            result['nifty'] = {'value': round(current, 2), 'change': round(change, 2)}
    except:
        pass
    
    try:
        # S&P 500
        sp500 = yf.Ticker('^GSPC')
        sp500_hist = sp500.history(period='2d')
        if len(sp500_hist) >= 2:
            current = sp500_hist['Close'].iloc[-1]
            prev = sp500_hist['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            result['sp500'] = {'value': round(current, 2), 'change': round(change, 2)}
    except:
        pass
    
    return jsonify(result)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
