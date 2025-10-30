from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta
import config

class BudgetManager:
    def __init__(self):
        self.budgets = {}  # user_id -> budget config
        
    def set_budget(self, user_id: str, monthly_limit: Decimal, 
                   alert_thresholds: List[float] = None):
        """Set budget for user"""
        if alert_thresholds is None:
            alert_thresholds = config.ALERT_THRESHOLDS
            
        self.budgets[user_id] = {
            "monthly_limit": monthly_limit,
            "current_spend": Decimal("0"),
            "alert_thresholds": alert_thresholds,
            "alerts_sent": set(),
            "last_reset": datetime.now()
        }
        
    def check_budget(self, user_id: str, cost: Decimal) -> bool:
        """Check if request is within budget"""
        if user_id not in self.budgets:
            self.set_budget(user_id, Decimal(str(config.DEFAULT_MONTHLY_BUDGET)))
        
        budget = self.budgets[user_id]
        projected_spend = budget["current_spend"] + cost
        
        return projected_spend <= budget["monthly_limit"]
    
    def record_spend(self, user_id: str, cost: Decimal):
        """Record spending and check alerts"""
        if user_id not in self.budgets:
            self.set_budget(user_id, Decimal(str(config.DEFAULT_MONTHLY_BUDGET)))
        
        budget = self.budgets[user_id]
        budget["current_spend"] += cost
        
        # Check alert thresholds
        spend_percentage = float(budget["current_spend"] / budget["monthly_limit"])
        
        for threshold in budget["alert_thresholds"]:
            if spend_percentage >= threshold and threshold not in budget["alerts_sent"]:
                self._send_alert(user_id, threshold, budget["current_spend"], budget["monthly_limit"])
                budget["alerts_sent"].add(threshold)
    
    def _send_alert(self, user_id: str, threshold: float, current: Decimal, limit: Decimal):
        """Send budget alert (simplified for MVP)"""
        print(f"⚠️  BUDGET ALERT [{user_id}]: {threshold*100}% of budget used (${current} / ${limit})")
        # TODO: Implement email/webhook alerts
    
    def get_remaining_budget(self, user_id: str) -> Decimal:
        """Get remaining budget"""
        if user_id not in self.budgets:
            return Decimal(str(config.DEFAULT_MONTHLY_BUDGET))
        
        budget = self.budgets[user_id]
        return budget["monthly_limit"] - budget["current_spend"]
