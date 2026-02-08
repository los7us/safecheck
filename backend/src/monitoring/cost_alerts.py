
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BudgetExceededException(Exception):
    pass

class CostMonitor:
    """Monitor and alert on costs"""
    
    def __init__(
        self,
        daily_budget_usd: float = 10.0,
        alert_threshold: float = 0.8  # 80% of budget
    ):
        self.daily_budget = daily_budget_usd
        self.alert_threshold = alert_threshold
        self.current_cost = 0.0
    
    def record_request_cost(self, cost: float):
        """Record cost and check budget"""
        self.current_cost += cost
        
        if self.current_cost >= self.daily_budget * self.alert_threshold:
            self._send_alert(
                f"Cost alert: ${self.current_cost:.2f} / ${self.daily_budget:.2f}"
            )
        
        if self.current_cost >= self.daily_budget:
            logger.error(f"Daily budget exceeded: ${self.current_cost:.2f}")
            # Potentially raise exception to block further requests?
            # raising here might be too aggressive without granular control
            pass 
    
    def _send_alert(self, message: str):
        """Send alert (email, Slack, etc.)"""
        logger.warning(f"COST_ALERT: {message}")
        # TODO: Implement actual alerting
