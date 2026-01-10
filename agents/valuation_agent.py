"""
Technical Agent (formerly Valuation Agent)
Analyzes long-term price trends and stability using yfinance.
Focuses on 200-day moving averages, weekly RSI, and volatility for long-term investors.
"""

import sys
import json
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def analyze_stock(symbol):
    """
    Analyze a stock's technicals from a long-term investor perspective.
    Returns BUY/SELL signal with confidence score and reasoning.
    """
    try:
        # Fetch 1 year of historical data for long-term trends
        stock = yf.Ticker(symbol)
        # Fetch 2 years to be safe for 200 SMA
        hist = stock.history(period="2y")
        
        if hist.empty or len(hist) < 200:
            sys.stderr.write(f"Data fetch failed for {symbol}. Rows: {len(hist)}\n")
            if not hist.empty:
                sys.stderr.write(f"Start: {hist.index[0]}, End: {hist.index[-1]}\n")
            return {
                "success": False,
                "error": "Insufficient historical data (need 1 year+) for " + symbol
            }
        
        # Current data points
        current_price = hist['Close'].iloc[-1]
        
        # --- Indicators ---
        
        # 1. 200-day Simple Moving Average (Long-term trend)
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        
        # 2. 50-day Simple Moving Average (Medium-term trend)
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        
        # 3. Weekly RSI (Relative Strength Index) - Less noise than daily
        # Resample to weekly
        weekly_hist = hist['Close'].resample('W').last()
        delta = weekly_hist.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_weekly = 100 - (100 / (1 + rs)).iloc[-1]
        
        # 4. Volatility (Annualized Standard Deviation)
        daily_returns = hist['Close'].pct_change().dropna()
        annualized_volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # 5. 1-Year Return
        price_1y_ago = hist['Close'].iloc[-252] if len(hist) >= 252 else hist['Close'].iloc[0]
        return_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
        
        # --- Scoring Logic (Long-Term Investor) ---
        score = 50 # Start Neutral
        reasoning_parts = []
        
        # Trend Analysis (Golden Cross / Price vs 200 SMA)
        if current_price > sma_200:
            score += 20
            reasoning_parts.append("Price is in a long-term uptrend (above 200 DMA)")
            if sma_50 > sma_200:
                score += 5
                reasoning_parts.append("Bullish trend alignment (50 DMA > 200 DMA)")
        else:
            score -= 20
            reasoning_parts.append("Price is in a long-term downtrend (below 200 DMA)")
            
        # RSI Analysis (Weekly)
        if 40 <= rsi_weekly <= 70:
            score += 10
            reasoning_parts.append("Weekly RSI ({:.1f}) is in a healthy range".format(rsi_weekly))
        elif rsi_weekly > 70:
            score -= 5
            reasoning_parts.append("Weekly RSI ({:.1f}) indicates overbought conditions".format(rsi_weekly))
        elif rsi_weekly < 30:
            score += 5 # Contrarian buy for long term if trend is okay, or just oversold
            reasoning_parts.append("Weekly RSI ({:.1f}) indicates oversold territory (potential value)".format(rsi_weekly))
            
        # Volatility Analysis (Stability preference)
        if annualized_volatility < 20:
            score += 10
            reasoning_parts.append("Low volatility ({:.1f}%) suggests stability".format(annualized_volatility))
        elif annualized_volatility > 40:
            score -= 10
            reasoning_parts.append("High volatility ({:.1f}%) adds risk".format(annualized_volatility))
            
        # Performance context
        if return_1y > 0:
            reasoning_parts.append("Positive 1-year return of {:.1f}%".format(return_1y))
        else:
            reasoning_parts.append("Negative 1-year return of {:.1f}%".format(return_1y))

        # --- Final Signal ---
        
        # Long-term investors look for trend confirmation + stability
        signal = "BUY" if score >= 60 else "SELL" # Higher threshold for BUY
        confidence = min(100, max(0, int(score)))
        
        # Formatting reasoning
        reasoning = ". ".join(reasoning_parts) + "."
        
        return {
            "success": True,
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "score": score,
            "reasoning": reasoning,
            "metrics": {
                "current_price": round(current_price, 2),
                "sma_200": round(sma_200, 2),
                "sma_50": round(sma_50, 2),
                "rsi_weekly": round(rsi_weekly, 2),
                "volatility_1y": round(annualized_volatility, 2),
                "return_1y": round(return_1y, 2)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No symbol provided"}))
        sys.exit(1)
    
    symbol = sys.argv[1]
    result = analyze_stock(symbol)
    print(json.dumps(result))
