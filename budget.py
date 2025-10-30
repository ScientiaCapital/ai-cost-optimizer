from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta
import os
import logging
import httpx
import config

# Configure logging for budget alerts
logger = logging.getLogger(__name__)

# File logger for budget alerts
budget_logger = logging.getLogger("budget_alerts")
budget_handler = logging.FileHandler("budget_alerts.log")
budget_handler.setFormatter(logging.Formatter(
    '%(asctime)s - [BUDGET_ALERT] - user=%(user)s threshold=%(threshold)s%% spent=$%(current)s/$%(limit)s'
))
budget_logger.addHandler(budget_handler)
budget_logger.setLevel(logging.WARNING)

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
    
    async def record_spend(self, user_id: str, cost: Decimal):
        """Record spending and check alerts"""
        if user_id not in self.budgets:
            self.set_budget(user_id, Decimal(str(config.DEFAULT_MONTHLY_BUDGET)))

        budget = self.budgets[user_id]
        budget["current_spend"] += cost

        # Check alert thresholds
        spend_percentage = float(budget["current_spend"] / budget["monthly_limit"])

        for threshold in budget["alert_thresholds"]:
            if spend_percentage >= threshold and threshold not in budget["alerts_sent"]:
                await self._send_alert(user_id, threshold, budget["current_spend"], budget["monthly_limit"])
                budget["alerts_sent"].add(threshold)
    
    async def _send_alert(self, user_id: str, threshold: float, current: Decimal, limit: Decimal):
        """
        Send budget alert via all configured channels.

        Channels:
        - Console logging (always)
        - File logging (always)
        - Email (if configured)
        - Webhook (if configured)
        """
        threshold_pct = threshold * 100
        message = f"Budget Alert: {threshold_pct}% of ${limit} used (${current} spent)"

        # 1. Console logging (always)
        logger.warning(f"⚠️  BUDGET ALERT [{user_id}]: {message}")

        # 2. File logging with structured format (always)
        budget_logger.warning(
            message,
            extra={
                "user": user_id,
                "threshold": f"{threshold_pct:.0f}",
                "current": str(current),
                "limit": str(limit)
            }
        )

        # 3. Email alerts (if configured)
        await self._send_email_alert(user_id, threshold_pct, current, limit)

        # 4. Webhook alerts (if configured)
        await self._send_webhook_alert(user_id, threshold_pct, current, limit)

    async def _send_email_alert(self, user_id: str, threshold_pct: float,
                                current: Decimal, limit: Decimal):
        """Send email alert using SendGrid or SMTP."""
        if not os.getenv("ALERT_EMAIL_ENABLED", "").lower() == "true":
            return

        email_to = os.getenv("ALERT_EMAIL_TO")
        if not email_to:
            logger.warning("ALERT_EMAIL_ENABLED=true but ALERT_EMAIL_TO not set")
            return

        try:
            sendgrid_key = os.getenv("SENDGRID_API_KEY")
            if sendgrid_key:
                await self._send_via_sendgrid(email_to, user_id, threshold_pct, current, limit)
            else:
                logger.info("Email alerts configured but no SendGrid API key. Email not sent.")
                logger.info("Hint: Set SENDGRID_API_KEY or implement SMTP configuration")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_via_sendgrid(self, to_email: str, user_id: str,
                                 threshold_pct: float, current: Decimal, limit: Decimal):
        """Send email via SendGrid API."""
        api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("ALERT_EMAIL_FROM", "alerts@ai-cost-optimizer.com")

        subject = f"🚨 Budget Alert: {threshold_pct:.0f}% Used"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #f39c12;">⚠️ Budget Alert</h2>
            <p>User <strong>{user_id}</strong> has reached <strong>{threshold_pct:.0f}%</strong> of their budget threshold.</p>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Current Spend:</strong> ${current}</p>
                <p style="margin: 5px 0;"><strong>Monthly Limit:</strong> ${limit}</p>
                <p style="margin: 5px 0;"><strong>Remaining:</strong> ${limit - current}</p>
            </div>
            <p style="color: #777; font-size: 12px;">
                This is an automated alert from AI Cost Optimizer.<br>
                Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
            </p>
        </body>
        </html>
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": from_email},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_content}]
                },
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Email alert sent successfully to {to_email}")

    async def _send_webhook_alert(self, user_id: str, threshold_pct: float,
                                  current: Decimal, limit: Decimal):
        """Send webhook alert (Slack, Discord, custom endpoint)."""
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if not webhook_url:
            return

        try:
            payload = {
                "user_id": user_id,
                "threshold": threshold_pct,
                "current_spend": str(current),
                "monthly_limit": str(limit),
                "remaining": str(limit - current),
                "timestamp": datetime.now().isoformat(),
                "alert_type": "budget_threshold",
                "message": f"Budget alert: {threshold_pct:.0f}% of ${limit} used"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook alert sent successfully to {webhook_url[:50]}...")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def get_remaining_budget(self, user_id: str) -> Decimal:
        """Get remaining budget"""
        if user_id not in self.budgets:
            return Decimal(str(config.DEFAULT_MONTHLY_BUDGET))
        
        budget = self.budgets[user_id]
        return budget["monthly_limit"] - budget["current_spend"]
