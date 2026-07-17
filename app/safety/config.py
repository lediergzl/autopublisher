"""Safety configuration and presets."""

from enum import Enum
from pydantic import BaseModel


class SafetyMode(str, Enum):
    """Publishing safety modes."""
    SAFE = "safe"        # Conservative: 20 groups/hour, 1-3 min delay
    NORMAL = "normal"    # Balanced: 50 groups/hour, 30-60 sec delay
    FAST = "fast"        # Aggressive: 100 groups/hour, 10-30 sec delay


class SafetyConfig(BaseModel):
    """Safety configuration for a user."""
    
    mode: SafetyMode = SafetyMode.NORMAL
    
    # Rate limiting (groups per hour)
    max_groups_per_hour: int
    
    # Delay between sends (milliseconds)
    min_delay_ms: int
    max_delay_ms: int
    
    # Account warmup
    warmup_enabled: bool = True
    warmup_day_1_limit: int = 10
    warmup_day_7_limit: int = 30
    
    # Content variation
    enable_content_variation: bool = True
    
    # Flood wait handling
    max_retries: int = 3
    initial_retry_delay_seconds: int = 60
    
    # Timeout per message send
    message_timeout_seconds: int = 30
    
    @classmethod
    def from_mode(cls, mode: SafetyMode) -> "SafetyConfig":
        """Create config from preset mode."""
        presets = {
            SafetyMode.SAFE: {
                "mode": SafetyMode.SAFE,
                "max_groups_per_hour": 20,
                "min_delay_ms": 60000,
                "max_delay_ms": 180000,
                "warmup_enabled": True,
                "warmup_day_1_limit": 5,
                "warmup_day_7_limit": 20,
                "enable_content_variation": True,
            },
            SafetyMode.NORMAL: {
                "mode": SafetyMode.NORMAL,
                "max_groups_per_hour": 50,
                "min_delay_ms": 30000,
                "max_delay_ms": 60000,
                "warmup_enabled": True,
                "warmup_day_1_limit": 10,
                "warmup_day_7_limit": 30,
                "enable_content_variation": True,
            },
            SafetyMode.FAST: {
                "mode": SafetyMode.FAST,
                "max_groups_per_hour": 100,
                "min_delay_ms": 10000,
                "max_delay_ms": 30000,
                "warmup_enabled": True,
                "warmup_day_1_limit": 15,
                "warmup_day_7_limit": 50,
                "enable_content_variation": True,
            },
        }
        return cls(**presets[mode])
