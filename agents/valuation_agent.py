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
        
        # 6. Volume Analysis
        avg_volume_50 = hist['Volume'].rolling(window=50).mean().iloc[-1]
        recent_volume = hist['Volume'].iloc[-5:].mean()  # Last 5 days avg
        volume_ratio = recent_volume / avg_volume_50 if avg_volume_50 > 0 else 1
        
        # Check if recent up-days have higher volume (accumulation)
        recent_data = hist.tail(20)
        up_days = recent_data[recent_data['Close'] > recent_data['Open']]
        down_days = recent_data[recent_data['Close'] <= recent_data['Open']]
        avg_up_volume = up_days['Volume'].mean() if len(up_days) > 0 else 0
        avg_down_volume = down_days['Volume'].mean() if len(down_days) > 0 else 0
        accumulation = avg_up_volume > avg_down_volume * 1.2  # 20% more volume on up days
        
        # 7. Max Drawdown (1 Year)
        rolling_max = hist['Close'].rolling(window=252, min_periods=1).max()
        drawdown = (hist['Close'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()  # Most negative value
        
        # 8. MACD (Moving Average Convergence Divergence)
        ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        macd_current = macd_histogram.iloc[-1]
        macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]
        
        # --- Scoring Logic (Long-Term Investor) ---
        score = 50 # Start Neutral
        scoring_log = []
        scoring_log.append({"metric": "Starting Base", "points": 50, "desc": "Neutral starting position"})
        
        reasoning_parts = []
        
        # Trend Analysis (Golden Cross / Price vs 200 SMA)
        if current_price > sma_200:
            score += 20
            scoring_log.append({"metric": "Long-term Trend", "points": 20, "desc": "Price above 200 DMA"})
            reasoning_parts.append("Price is in a long-term uptrend (above 200 DMA)")
            if sma_50 > sma_200:
                score += 5
                scoring_log.append({"metric": "Trend Alignment", "points": 5, "desc": "50 DMA > 200 DMA (Bullish)"})
                reasoning_parts.append("Bullish trend alignment (50 DMA > 200 DMA)")
        else:
            score -= 20
            scoring_log.append({"metric": "Long-term Trend", "points": -20, "desc": "Price below 200 DMA"})
            reasoning_parts.append("Price is in a long-term downtrend (below 200 DMA)")
            
        # RSI Analysis (Weekly)
        if 40 <= rsi_weekly <= 70:
            score += 10
            scoring_log.append({"metric": "Momentum (RSI)", "points": 10, "desc": f"Healthy Weekly RSI ({rsi_weekly:.1f})"})
            reasoning_parts.append("Weekly RSI ({:.1f}) is in a healthy range".format(rsi_weekly))
        elif rsi_weekly > 70:
            score -= 5
            scoring_log.append({"metric": "Momentum (RSI)", "points": -5, "desc": f"Overbought Weekly RSI ({rsi_weekly:.1f})"})
            reasoning_parts.append("Weekly RSI ({:.1f}) indicates overbought conditions".format(rsi_weekly))
        elif rsi_weekly < 30:
            score += 5 # Contrarian buy for long term if trend is okay, or just oversold
            scoring_log.append({"metric": "Momentum (RSI)", "points": 5, "desc": f"Oversold Weekly RSI ({rsi_weekly:.1f})"})
            reasoning_parts.append("Weekly RSI ({:.1f}) indicates oversold territory (potential value)".format(rsi_weekly))
            
        # Volatility Analysis (Stability preference)
        if annualized_volatility < 20:
            score += 10
            scoring_log.append({"metric": "Volatility", "points": 10, "desc": f"Low Volatility ({annualized_volatility:.1f}%)"})
            reasoning_parts.append("Low volatility ({:.1f}%) suggests stability".format(annualized_volatility))
        elif annualized_volatility > 40:
            score -= 10
            scoring_log.append({"metric": "Volatility", "points": -10, "desc": f"High Volatility ({annualized_volatility:.1f}%)"})
            reasoning_parts.append("High volatility ({:.1f}%) adds risk".format(annualized_volatility))
            
        # Performance context
        if return_1y > 0:
            reasoning_parts.append("Positive 1-year return of {:.1f}%".format(return_1y))
        else:
            reasoning_parts.append("Negative 1-year return of {:.1f}%".format(return_1y))
        
        # Volume Analysis
        if volume_ratio > 1.5:
            score += 5
            scoring_log.append({"metric": "Volume", "points": 5, "desc": f"High recent volume ({volume_ratio:.1f}x avg)"})
            reasoning_parts.append("Increased trading interest (volume {:.1f}x average)".format(volume_ratio))
        if accumulation:
            score += 5
            scoring_log.append({"metric": "Accumulation", "points": 5, "desc": "Higher volume on up days"})
            reasoning_parts.append("Signs of institutional accumulation")
        
        # Max Drawdown Analysis
        if max_drawdown > -15:
            score += 5
            scoring_log.append({"metric": "Max Drawdown", "points": 5, "desc": f"Low drawdown ({max_drawdown:.1f}%)"})
            reasoning_parts.append("Low max drawdown ({:.1f}%) shows resilience".format(max_drawdown))
        elif max_drawdown < -40:
            score -= 5
            scoring_log.append({"metric": "Max Drawdown", "points": -5, "desc": f"High drawdown ({max_drawdown:.1f}%)"})
            reasoning_parts.append("Significant drawdown ({:.1f}%) indicates risk".format(max_drawdown))
        
        # MACD Analysis
        if macd_bullish:
            score += 5
            scoring_log.append({"metric": "MACD", "points": 5, "desc": "MACD above signal (Bullish)"})
            reasoning_parts.append("MACD shows bullish momentum")
        else:
            score -= 3
            scoring_log.append({"metric": "MACD", "points": -3, "desc": "MACD below signal (Bearish)"})
            reasoning_parts.append("MACD shows weakening momentum")

        # --- Final Signal ---
        
        # Normalize score to 0-100 range
        score = min(100, max(0, score))
        
        # Long-term investors look for trend confirmation + stability
        signal = "BUY" if score >= 60 else "SELL"
        confidence = score
        
        # Formatting reasoning
        reasoning = ". ".join(reasoning_parts) + "."
        
        return {
            "success": True,
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "score": score,
            "scoring_log": scoring_log,
            "reasoning": reasoning,
            "metrics": {
                "current_price": round(current_price, 2),
                "sma_200": round(sma_200, 2),
                "sma_50": round(sma_50, 2),
                "rsi_weekly": round(rsi_weekly, 2),
                "volatility_1y": round(annualized_volatility, 2),
                "return_1y": round(return_1y, 2),
                "volume_ratio": round(volume_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "macd_signal": "Bullish" if macd_bullish else "Bearish"
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
