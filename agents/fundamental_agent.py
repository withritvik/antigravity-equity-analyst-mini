"""
Fundamental Agent - Analyzes financial health for long-term investing
Focuses on Quality (ROE), Value (P/E), Safety (D/E), and Growth
"""

import sys
import json
import yfinance as yf

def analyze_fundamentals(symbol):
    """
    Analyze a stock's fundamental metrics from a long-term investor perspective.
    Returns BUY/SELL signal with confidence score and reasoning
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info or 'symbol' not in info:
            return {
                "success": False,
                "error": "Unable to fetch fundamental data for " + symbol
            }
        
        # Extract key metrics with fallbacks
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        debt_to_equity = info.get('debtToEquity')
        roe = info.get('returnOnEquity')
        profit_margins = info.get('profitMargins')
        revenue_growth = info.get('revenueGrowth')
        earnings_growth = info.get('earningsGrowth')
        free_cashflow = info.get('freeCashflow')
        market_cap = info.get('marketCap')
        
        score = 50  # Start neutral
        reasoning_parts = []
        metrics_found = {}
        
        # --- QUALITY CHECK (ROE & Margins) ---
        # Long-term investors want companies that efficiently generate profits
        if roe is not None:
            roe_pct = roe * 100
            metrics_found['ROE'] = "{:.1f}%".format(roe_pct)
            if roe_pct > 15:
                score += 15
                reasoning_parts.append("High Quality: Strong ROE of {:.1f}% (>15%)".format(roe_pct))
            elif roe_pct < 8:
                score -= 10
                reasoning_parts.append("Low Quality: Weak ROE of {:.1f}%".format(roe_pct))
            else:
                reasoning_parts.append("Moderate ROE of {:.1f}%".format(roe_pct))
                
        if profit_margins is not None:
            margin_pct = profit_margins * 100
            metrics_found['Net Margin'] = "{:.1f}%".format(margin_pct)
            if margin_pct > 15:
                score += 10
                reasoning_parts.append("High net profit margins ({:.1f}%)".format(margin_pct))
            elif margin_pct < 5:
                score -= 10
                reasoning_parts.append("Thin profit margins ({:.1f}%)".format(margin_pct))

        # --- SAFETY CHECK (Debt) ---
        # Long-term investors avoid excessive debt
        if debt_to_equity is not None:
            # yfinance returns D/E as percentage (e.g. 50 is 0.5) or ratio depending on version
            # Usually it's a ratio like 0.5 or 1.2
            # Let's assume ratio. If it's > 100, treat as %, otherwise ratio
            de_ratio = debt_to_equity
            if de_ratio > 10: # Likely percentage, convert to ratio
                de_ratio = de_ratio / 100
                
            metrics_found['D/E'] = round(de_ratio, 2)
            
            if de_ratio < 0.5:
                score += 10
                reasoning_parts.append("Safety: Conservative debt levels (D/E: {:.2f})".format(de_ratio))
            elif de_ratio > 1.5:
                score -= 15
                reasoning_parts.append("Risk: High leverage (D/E: {:.2f})".format(de_ratio))
            else:
                reasoning_parts.append("Manageable debt (D/E: {:.2f})".format(de_ratio))

        # --- VALUE CHECK (P/E) ---
        # Don't overpay for quality
        if pe_ratio is not None:
            metrics_found['P/E'] = round(pe_ratio, 2)
            if pe_ratio < 0:
                score -= 20
                reasoning_parts.append("Risk: Company is currently loss-making")
            elif pe_ratio < 15:
                score += 10
                reasoning_parts.append("Value: Attractive valuation (P/E {:.1f})".format(pe_ratio))
            elif pe_ratio > 50:
                score -= 10
                reasoning_parts.append("Expensive: High valuation premium (P/E {:.1f})".format(pe_ratio))
            else:
                reasoning_parts.append("Fair valuation (P/E {:.1f})".format(pe_ratio))

        # --- GROWTH CHECK ---
        # Future value comes from growth
        if revenue_growth is not None:
            growth_pct = revenue_growth * 100
            metrics_found['Rev Growth'] = "{:.1f}%".format(growth_pct)
            if growth_pct > 10:
                score += 10
                reasoning_parts.append("Growth: Strong revenue expansion ({:.1f}%)".format(growth_pct))
            elif growth_pct < 0:
                score -= 10
                reasoning_parts.append("concern: Shrinking revenue ({:.1f}%)".format(growth_pct))

        # --- Final Signal ---
        
        # Long-term investing requires higher conviction
        signal = "BUY" if score >= 60 else "SELL"
        confidence = min(100, max(0, int(score)))
        
        if not reasoning_parts:
            reasoning_parts.append("Insufficient data for fundamental analysis")
        
        reasoning = ". ".join(reasoning_parts) + "."
        
        return {
            "success": True,
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "score": score,
            "reasoning": reasoning,
            "metrics": metrics_found,
            "company_info": {
                "name": info.get('longName') or info.get('shortName'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "market_cap": market_cap,
                "current_price": info.get('currentPrice') or info.get('regularMarketPrice')
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
    result = analyze_fundamentals(symbol)
    print(json.dumps(result))
