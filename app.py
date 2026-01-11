# -*- coding: utf-8 -*-
"""
Mini Analyst - Minimal Stock Analysis App
Lightweight Python-only backend for constrained environments (512MB RAM, 0.1 CPU)
Uses separate agent files called via subprocess, same architecture as main Analyst.
"""

import sys
import os

# Ensure the root directory is in the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'agents'))

from orchestration_agent import DebateSimulator
from data.tickers import NIFTY_50, SP_500

from flask import Flask, render_template_string, request, jsonify
import subprocess
import json
import yfinance as yf

app = Flask(__name__)

# Path to agent scripts
AGENTS_DIR = os.path.join(os.path.dirname(__file__), 'agents')

# ============== Agent Runner ==============

def run_agent(script_name, symbol):
    """Run a Python agent script and return JSON result"""
    script_path = os.path.join(AGENTS_DIR, script_name)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path, symbol],
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
    
    # Fetch Extra Data (History for Chart)
    history = []
    news = []
    try:
        ticker = yf.Ticker(symbol)
        # 1y history for chart
        hist = ticker.history(period="1y")
        if not hist.empty:
            history = [{"date": d.strftime('%Y-%m-%d'), "price": round(p, 2)} 
                      for d, p in zip(hist.index, hist['Close'])]
        
        # Fetch news (top 3) - yfinance uses nested 'content' structure
        if ticker.news:
            for n in ticker.news[:3]:
                content = n.get('content', {})
                news.append({
                    "title": content.get('title', ''),
                    "link": content.get('clickThroughUrl', {}).get('url', '#'),
                    "publisher": content.get('provider', {}).get('displayName', ''),
                    "time": content.get('pubDate', '')
                })
    except Exception as e:
        print(f"Extra data fetch failed: {e}")

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
        "fundamental": fund,
        "history": history,
        "news": news
    }

# ============== HTML Template ==============

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini Analyst</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: monospace; 
            background: #000; 
            color: #fff; 
            height: 100vh; /* Changed from min-height to fix layout */
            display: flex;
            flex-direction: column;
            /* Removed centering and padding to push to edges */
            font-size: 18px;
            margin: 0;
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
        /* Layout */
        body { 
            padding-top: 60px; 
            margin: 0;
            overflow: hidden; /* Main scroll handled by containers */
            height: 100vh;
        }
        
        .main-layout {
            display: flex;
            height: calc(100vh - 60px); 
            overflow: hidden;
            width: 100%; /* Explicitly set full width */
        }
        
        .sidebar {
            width: 250px;
            background: #0a0a0a;
            border-right: 1px solid #333;
            border-left: 1px solid #333;
            overflow-y: auto;
            padding: 10px 0;
            flex-shrink: 0;
        }
        
        .sidebar h4 {
            text-align: center;
            color: #888;
            margin: 10px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.9em;
        }

        .stock-item {
            padding: 8px 15px;
            color: #ccc;
            cursor: pointer;
            border-bottom: 1px solid #222;
            font-family: monospace;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .stock-item:hover {
            background: #222;
            color: #fff;
        }
        
        .content-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
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

        /* Chart Container */
        .chart-container {
            width: 100%;
            height: 300px;
            margin: 20px 0;
            background: #0a0a0a;
            border: 1px solid #333;
            padding: 10px;
        }
        
        /* News Items */
        .news-section {
            margin: 20px 0;
            padding: 15px;
            background: #0a0a0a;
            border: 1px solid #333;
        }
        .news-item {
            border-bottom: 1px solid #333;
            padding: 10px 0;
        }
        .news-item:last-child { border-bottom: none; }
        .news-item a { color: #0cf; text-decoration: none; font-size: 1em; }
        .news-item a:hover { text-decoration: underline; }
        .news-meta { color: #666; font-size: 0.8em; margin-top: 5px; }
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
            <span class="index-name">SENSEX</span>
            <span id="sensex-value" class="index-value">--</span>
            <span id="sensex-change" class="index-change">--</span>
        </div>
        <div class="index-item">
            <span class="index-name">DOW JONES</span>
            <span id="dow-value" class="index-value">--</span>
            <span id="dow-change" class="index-change">--</span>
        </div>
        <div class="index-item">
            <span class="index-name">S&P 500</span>
            <span id="sp500-value" class="index-value">--</span>
            <span id="sp500-change" class="index-change">--</span>
        </div>
        <div class="index-item">
            <span class="index-name">SSE COMP</span>
            <span id="sse-value" class="index-value">--</span>
            <span id="sse-change" class="index-change">--</span>
        </div>
    </div>
    
    <div class="main-layout">
        <!-- Left Sidebar: NIFTY 500 -->
        <div class="sidebar" style="border-right: 1px solid #333; border-left: none;">
            <h4>NIFTY 500</h4>
            {% for ticker, name in nifty %}
            <div class="stock-item" onclick="analyzeStock('{{ ticker }}')">
                <span style="font-weight:bold; color:#e0e0e0;">{{ ticker }}</span><br>
                <span style="font-size:0.8em; color:#888;">{{ name }}</span>
            </div>
            {% endfor %}
        </div>

        <!-- Main Content -->
        <div class="content-area">
            <div class="container" style="margin-top:0;">
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
            </div>
            
            <div class="footer">
                <p>PM - Ritvik Pandey | Engineer - Google AntiGravity</p>
            </div>
        </div>

        <!-- Right Sidebar: S&P 500 -->
        <div class="sidebar" style="border-left: 1px solid #333; border-right: none;">
            <h4>S&P 500</h4>
            {% for ticker, name in sp500 %}
            <div class="stock-item" onclick="analyzeStock('{{ ticker }}')">
                <span style="font-weight:bold; color:#e0e0e0;">{{ ticker }}</span><br>
                <span style="font-size:0.8em; color:#888;">{{ name }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        // Fetch index data on load
        function fetchIndices() {
            fetch('/indices')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    var indices = ['nifty', 'sensex', 'dow', 'sp500', 'sse'];
                    indices.forEach(function(idx) {
                        if (data[idx]) {
                            var valElem = document.getElementById(idx + '-value');
                            var changeElem = document.getElementById(idx + '-change');
                            if (valElem && changeElem) {
                                valElem.textContent = data[idx].value.toLocaleString();
                                changeElem.textContent = (data[idx].change >= 0 ? '+' : '') + data[idx].change.toFixed(2) + '%';
                                changeElem.className = 'index-change ' + (data[idx].change >= 0 ? 'up' : 'down');
                            }
                        }
                    });
                })
                .catch(function(e) { console.log('Index fetch error:', e); });
        }
        fetchIndices();
        setInterval(fetchIndices, 5000); // Refresh every 5 seconds
        
        document.getElementById('ticker').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeStock();
        });
        
        function analyzeStock(symbol) {
            var ticker = symbol ? symbol : document.getElementById('ticker').value.trim().toUpperCase();
            if (symbol) document.getElementById('ticker').value = symbol; // Update input box
            if (!ticker) { alert('Please enter a ticker symbol'); return; }
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerHTML = '<p class="loading" style="text-align:center;">Analyzing ' + ticker + '...</p>';
            
            fetch('/analyze?symbol=' + encodeURIComponent(ticker))
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        var html = '<h3 style="text-align:center; margin-bottom:5px;">' + data.company + '</h3>';
                        html += '<p style="text-align:center;color:#888; margin-top:0;">' + data.symbol + '</p>';
                        
                        // Price Display
                        var price = data.technical.metrics.current_price;
                        var currency = data.symbol.includes('.NS') ? '₹' : '$';
                        html += '<h2 style="text-align:center; color:#fff; margin: 10px 0;">' + currency + price + '</h2>';
                        
                        // Chart Container
                        html += '<div class="chart-container"><canvas id="stockChart"></canvas></div>';
                        
                        html += '<p class="signal ' + data.signal.toLowerCase() + '">' + data.signal + ' (' + data.score + '/100)</p>';
                        
                        // News Section
                        if (data.news && data.news.length > 0) {
                            html += '<h4>Latest Headlines</h4>';
                            html += '<div class="news-section">';
                            data.news.forEach(function(n) {
                                var date = n.time ? new Date(n.time) : new Date();
                                var dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                                html += '<div class="news-item">';
                                html += '<a href="' + n.link + '" target="_blank">' + n.title + '</a>';
                                html += '<div class="news-meta">' + n.publisher + ' • ' + dateStr + '</div>';
                                html += '</div>';
                            });
                            html += '</div>';
                        }
                        
                        // Debate Transcript
                        html += '<h4>Analyst Debate (5 Rounds)</h4>';
                        html += '<div class="debate-container">';
                        
                        data.transcript.forEach(function(entry) {
                            var speakerClass = '';
                            if (entry.speaker.includes('Fundamental')) speakerClass = 'speaker-fund';
                            else if (entry.speaker.includes('Technical')) speakerClass = 'speaker-tech';
                            else speakerClass = 'speaker-orch';
                            
                            html += '<div class="dialogue-box ' + speakerClass + '">';
                            html += '<span class="speaker-name">' + entry.speaker + '</span>';
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
                            var techMetrics = data.technical.metrics || {};
                            var techCategories = {
                                'Price & Trend': {
                                    'current_price': {v: techMetrics.current_price, tip: 'Current market price of the stock'},
                                    'sma_200': {v: techMetrics.sma_200, tip: '200-day moving average - long-term trend indicator'},
                                    'sma_50': {v: techMetrics.sma_50, tip: '50-day moving average - medium-term trend indicator'}
                                },
                                'Momentum': {
                                    'rsi_weekly': {v: techMetrics.rsi_weekly, tip: 'Weekly RSI - overbought >70, oversold <30'},
                                    'macd_signal': {v: techMetrics.macd_signal, tip: 'MACD momentum direction - Bullish or Bearish'}
                                },
                                'Risk & Volatility': {
                                    'volatility_1y': {v: techMetrics.volatility_1y, tip: 'Annualized volatility - lower is more stable'},
                                    'max_drawdown': {v: techMetrics.max_drawdown, tip: 'Worst peak-to-trough decline in 1 year'},
                                    'return_1y': {v: techMetrics.return_1y, tip: '1-year total return percentage'}
                                },
                                'Volume': {
                                    'volume_ratio': {v: techMetrics.volume_ratio, tip: 'Recent volume vs 50-day average - >1.5 is high interest'}
                                }
                            };
                            for (var cat in techCategories) {
                                html += '<h5 style="color:#666; margin:10px 0 5px; font-size:0.85em;">' + cat + '</h5>';
                                html += '<table>';
                                for (var k in techCategories[cat]) {
                                    var item = techCategories[cat][k];
                                    if (item.v !== undefined && item.v !== null) {
                                        html += '<tr title="' + item.tip + '" style="cursor:help;"><td>' + k.replace(/_/g, ' ') + '</td><td>' + item.v + '</td></tr>';
                                    }
                                }
                                html += '</table>';
                            }
                        }
                        html += '</div>';
                        
                        // Fundamental Table
                        html += '<div style="flex:1; min-width:250px;">';
                        html += '<h4>Fundamental Data</h4>';
                        if (data.fundamental.success) {
                            var fundMetrics = data.fundamental.metrics || {};
                            var fundCategories = {
                                'Quality': {
                                    'ROE': {v: fundMetrics['ROE'], tip: 'Return on Equity - measures profitability vs shareholder equity'},
                                    'Net Margin': {v: fundMetrics['Net Margin'], tip: 'Net profit as % of revenue'}
                                },
                                'Valuation': {
                                    'P/E': {v: fundMetrics['P/E'], tip: 'Price-to-Earnings ratio - lower may indicate value'},
                                    'Target Price': {v: fundMetrics['Target Price'], tip: 'Average analyst price target'},
                                    'Upside': {v: fundMetrics['Upside'], tip: 'Potential upside to analyst target price'}
                                },
                                'Safety': {
                                    'D/E': {v: fundMetrics['D/E'], tip: 'Debt-to-Equity ratio - lower is safer'},
                                    'Beta': {v: fundMetrics['Beta'], tip: 'Market sensitivity - <1 is less volatile than market'}
                                },
                                'Growth': {
                                    'Rev Growth': {v: fundMetrics['Rev Growth'], tip: 'Year-over-year revenue growth'}
                                },
                                'Dividends': {
                                    'Div Yield': {v: fundMetrics['Div Yield'], tip: 'Annual dividend as % of stock price'},
                                    'Payout Ratio': {v: fundMetrics['Payout Ratio'], tip: '% of earnings paid as dividends - 20-60% is sustainable'}
                                },
                                'Analyst Ratings': {
                                    'Strong Buy': {v: fundMetrics['Strong Buy'], tip: 'Number of analysts with Strong Buy rating'},
                                    'Buy': {v: fundMetrics['Buy'], tip: 'Number of analysts with Buy rating'},
                                    'Hold': {v: fundMetrics['Hold'], tip: 'Number of analysts with Hold rating'},
                                    'Sell': {v: fundMetrics['Sell'], tip: 'Number of analysts with Sell rating'},
                                    'Bullish %': {v: fundMetrics['Bullish %'], tip: 'Percentage of analysts that are bullish'}
                                },
                                'Insider Activity': {
                                    'Insider Buys': {v: fundMetrics['Insider Buys'], tip: 'Recent insider purchase transactions'},
                                    'Insider Sells': {v: fundMetrics['Insider Sells'], tip: 'Recent insider sale transactions'},
                                    'Inst. Ownership': {v: fundMetrics['Inst. Ownership'], tip: '% of shares held by institutions'}
                                },
                                'Position': {
                                    '52W Range': {v: fundMetrics['52W Range'], tip: 'Current price position within 52-week range'}
                                }
                            };
                            for (var cat in fundCategories) {
                                var hasData = false;
                                for (var k in fundCategories[cat]) {
                                    if (fundCategories[cat][k].v !== undefined && fundCategories[cat][k].v !== null) hasData = true;
                                }
                                if (hasData) {
                                    html += '<h5 style="color:#666; margin:10px 0 5px; font-size:0.85em;">' + cat + '</h5>';
                                    html += '<table>';
                                    for (var k in fundCategories[cat]) {
                                        var item = fundCategories[cat][k];
                                        if (item.v !== undefined && item.v !== null) {
                                            html += '<tr title="' + item.tip + '" style="cursor:help;"><td>' + k + '</td><td>' + item.v + '</td></tr>';
                                        }
                                    }
                                    html += '</table>';
                                }
                            }
                        }
                        html += '</div>';
                        
                        html += '</div>'; // End data tables div
                        
                        // Scoring Breakdown Section
                        html += '<h4 style="margin-top:30px; border-top:1px solid #333; padding-top:20px;">Scoring Breakdown</h4>';
                        html += '<div style="display:flex; gap:20px; flex-wrap:wrap;">';
                        
                        // Technical Scoring
                        html += '<div style="flex:1; min-width:250px;">';
                        html += '<h5 style="color:#888;">Technical Score (' + (data.technical.score || 0) + ')</h5>';
                        if (data.technical.scoring_log) {
                            html += '<table style="font-size:0.85em; color:#ccc;">';
                            data.technical.scoring_log.forEach(function(item) {
                                var color = item.points > 0 ? '#0f0' : (item.points < 0 ? '#f00' : '#888');
                                var sign = item.points > 0 ? '+' : '';
                                html += '<tr><td>' + item.desc + '</td><td style="color:' + color + '; text-align:right;">' + sign + item.points + '</td></tr>';
                            });
                            html += '</table>';
                        }
                        html += '</div>';

                        // Fundamental Scoring
                        html += '<div style="flex:1; min-width:250px;">';
                        html += '<h5 style="color:#888;">Fundamental Score (' + (data.fundamental.score || 0) + ')</h5>';
                        if (data.fundamental.scoring_log) {
                            html += '<table style="font-size:0.85em; color:#ccc;">';
                            data.fundamental.scoring_log.forEach(function(item) {
                                var color = item.points > 0 ? '#0f0' : (item.points < 0 ? '#f00' : '#888');
                                var sign = item.points > 0 ? '+' : '';
                                html += '<tr><td>' + item.desc + '</td><td style="color:' + color + '; text-align:right;">' + sign + item.points + '</td></tr>';
                            });
                            html += '</table>';
                        }
                        html += '</div>';
                        
                        html += '</div>'; // End scoring div
                        
                        document.getElementById('result').innerHTML = html;
                        
                        // Render Chart
                        if (data.history && data.history.length > 0) {
                            renderChart(data.history, data.symbol);
                        }
                    } else {
                        document.getElementById('result').innerHTML = '<p class="error" style="text-align:center;">Error: ' + data.error + '</p>';
                    }
                })
                .catch(function(e) {
                    document.getElementById('result').innerHTML = '<p class="error" style="text-align:center;">Error: ' + e.message + '</p>';
                });
        }
        
        var myChart = null;
        function renderChart(history, symbol) {
            var ctx = document.getElementById('stockChart').getContext('2d');
            if (myChart) myChart.destroy();
            
            var prices = history.map(h => h.price);
            var dates = history.map(h => h.date);
            // Green if up, Red if down
            var color = prices[prices.length-1] >= prices[0] ? '#0f0' : '#f00';
            
            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: symbol + ' Price',
                        data: prices,
                        borderColor: color,
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { 
                            display: true,
                            title: {
                                display: false,
                                text: 'Date',
                                color: '#666'
                            },
                            ticks: {
                                color: '#aaa',
                                maxTicksLimit: 12,
                                callback: function(val, index) {
                                    var label = this.getLabelForValue(val);
                                    var date = new Date(label);
                                    var month = date.toLocaleDateString('en-US', { month: 'short' });
                                    var year = date.getFullYear().toString().slice(-2);
                                    return month + " '" + year;
                                }
                            }
                        },
                        y: { 
                            display: true,
                            grid: { color: '#333' },
                            title: {
                                display: true,
                                text: 'Price (' + (symbol.includes('.NS') ? 'INR' : 'USD') + ')',
                                color: '#666'
                            }
                        }
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

# ============== Routes ==============

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, nifty=NIFTY_50, sp500=SP_500)

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
    """Fetch real-time values for global indices"""
    # Mapping: Key -> (YFinance Ticker, Display Name)
    indices_map = {
        'nifty': ('^NSEI', 'Nifty 50'),
        'sensex': ('^BSESN', 'Sensex'),
        'sp500': ('^GSPC', 'S&P 500'),
        'dow': ('^DJI', 'Dow Jones'),
        'sse': ('000001.SS', 'SSE Composite')
    }
    
    result = {}
    
    for key, (ticker, _) in indices_map.items():
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period='2d')
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                result[key] = {'value': round(current, 2), 'change': round(change, 2)}
        except:
            result[key] = {'value': 0, 'change': 0}
            
    return jsonify(result)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
