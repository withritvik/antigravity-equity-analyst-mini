import json
import sys

class DebateSimulator:
    def __init__(self, fund_data, tech_data, symbol):
        self.fund = fund_data
        self.tech = tech_data
        self.symbol = symbol
        self.fund_score = self.fund.get('score', 50)
        self.tech_score = self.tech.get('score', 50)
        self.transcript = []

    def generate_dialogue(self, speaker, tone, message):
        return {
            "speaker": speaker,
            "tone": tone,
            "message": message
        }

    def run_debate(self):
        # --- Round 1: Opening Statements ---
        
        # Fundamental Opening
        fund_reasoning = self.fund.get('reasoning', 'Fundamentals are strong.')
        if self.fund_score >= 60:
            fund_msg = f"This company is a powerhouse. {fund_reasoning}"
            fund_tone = "confident"
        elif self.fund_score <= 40:
            fund_msg = f"I cannot recommend this. {fund_reasoning}"
            fund_tone = "skeptical"
        else:
            fund_msg = f"It's a mixed bag. {fund_reasoning}"
            fund_tone = "neutral"
        self.transcript.append(self.generate_dialogue("Fundamental Agent", fund_tone, fund_msg))

        # Technical Opening
        tech_reasoning = self.tech.get('reasoning', 'Technical trend is bullish.')
        if self.tech_score >= 60:
            tech_msg = f"The charts agree. {tech_reasoning}"
            tech_tone = "excited"
        elif self.tech_score <= 40:
            tech_msg = f"Price action is dangerous. {tech_reasoning}"
            tech_tone = "cautious"
        else:
            tech_msg = f"Price is chopping sideways. {tech_reasoning}"
            tech_tone = "bored"
        self.transcript.append(self.generate_dialogue("Technical Agent", tech_tone, tech_msg))

        # --- Round 2: The Attack (Cross-Exam) ---
        
        # Fund attacks Tech
        fund_metrics = self.fund.get('metrics', {})
        tech_metrics = self.tech.get('metrics', {})
        
        if self.tech_score > self.fund_score:
            self.transcript.append(self.generate_dialogue("Fundamental Agent", "aggressive", 
                "You're chasing lines on a chart! Look at the valuation. Ideally we want value, not just momentum."))
        elif 'RSI' in tech_metrics and float(str(tech_metrics['RSI']).replace('%','')) > 70:
             self.transcript.append(self.generate_dialogue("Fundamental Agent", "warning", 
                "RSI is overbought. You're buying the top!"))
        else:
             self.transcript.append(self.generate_dialogue("Fundamental Agent", "critical", 
                "Technical patterns can fail. Show me the cash flow backing this move."))

        # Tech attacks Fund
        if self.fund_score > self.tech_score:
            self.transcript.append(self.generate_dialogue("Technical Agent", "defensive", 
                "Valuation takes years to play out. The trend is NOW. Don't fight the tape!"))
        elif 'P/E' in fund_metrics and float(str(fund_metrics['P/E'])) > 50:
             self.transcript.append(self.generate_dialogue("Technical Agent", "mocking", 
                "With that P/E? Good luck waiting for earnings to catch up. The market votes with price."))
        else:
             self.transcript.append(self.generate_dialogue("Technical Agent", "dismissive", 
                "Fundamentals are lagging indicators. By the time they look good, the move is over."))

        # --- Round 3: The Defense ---
        
        self.transcript.append(self.generate_dialogue("Fundamental Agent", "calm", 
            f"Quality wins in the end. My score of {self.fund_score} reflects business reality."))
        
        self.transcript.append(self.generate_dialogue("Technical Agent", "firm", 
            f"Price is reality. My score of {self.tech_score} reflects supply and demand."))

        # --- Round 4: Risk Assessment (Consensus on Downside) ---
        
        self.transcript.append(self.generate_dialogue("Moderator", "neutral", 
            "Agents, what is the biggest risk here?"))
            
        risk_msg = "Market volatility"
        if self.fund_score < 40: risk_msg = "Bankruptcy or earnings miss"
        elif self.tech_score < 40: risk_msg = "Trend breakdown"
        elif self.fund_score > 80 and self.tech_score > 80: risk_msg = "Overvaluation pullbacks"
        
        self.transcript.append(self.generate_dialogue("Joint Statement", "serious", 
            f"Agreed. The main risk is {risk_msg}."))

        # --- Round 5: Closing & Vote ---
        
        final_score = (self.fund_score * 0.6) + (self.tech_score * 0.4)
        decision = "HOLD"
        if final_score >= 65: decision = "BUY"
        elif final_score <= 35: decision = "SELL"
        
        final_tone = "triumphant" if decision == "BUY" else "stern"
        
        conclusion = ""
        if decision == "BUY":
            conclusion = f"We recommend a BUY. Final Weighted Score: {round(final_score, 1)}."
        elif decision == "SELL":
            conclusion = f"We recommend a SELL. Final Weighted Score: {round(final_score, 1)}."
        else:
            conclusion = f"We recommend holding for now. Score: {round(final_score, 1)}."

        self.transcript.append(self.generate_dialogue("Orchestrator", final_tone, conclusion))
        
        return {
            "transcript": self.transcript,
            "final_score": round(final_score, 1),
            "final_signal": decision
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Insufficient arguments"}))
        sys.exit(1)
        
    try:
        # Expecting JSON strings as arguments for simplicity in this specific architecture
        # In app.py we will likely import the class, but if run as script:
        fund_data = json.loads(sys.argv[1])
        tech_data = json.loads(sys.argv[2])
        symbol = sys.argv[3] if len(sys.argv) > 3 else "UNKNOWN"
        
        simulator = DebateSimulator(fund_data, tech_data, symbol)
        result = simulator.run_debate()
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
