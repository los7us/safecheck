
import logging
import re
import sys
from typing import Optional

# Pre-compile regex for performance
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
API_KEY_PATTERN = re.compile(r'(api[_-]?key|token|secret)["\s:=]+([A-Za-z0-9_-]{20,})', re.IGNORECASE)

class SanitizingFilter(logging.Filter):
    """Remove PII and secrets from logs"""
    
    def filter(self, record):
        # Sanitize message
        record.msg = self._sanitize(str(record.msg))
        
        # Sanitize args
        if record.args:
            record.args = tuple(
                self._sanitize(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _sanitize(self, text: str) -> str:
        """Redact sensitive patterns"""
        text = EMAIL_PATTERN.sub('[EMAIL]', text)
        text = PHONE_PATTERN.sub('[PHONE]', text)
        # Use a lambda to preserve the key name but redact value
        text = API_KEY_PATTERN.sub(lambda m: f"{m.group(1)}=[REDACTED]", text)
        return text

def setup_logging(level=logging.INFO):
    """Configure secure logging"""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SanitizingFilter())
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(handler)
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").addFilter(SanitizingFilter())
    
    return logger
