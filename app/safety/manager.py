"""Safety manager orchestrating all safety features."""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.safety.config import SafetyConfig, SafetyMode
from app.safety.models import AccountReputation, GroupRiskAssessment, FloodWaitRecord
from app.safety.rate_limiter import RateLimiter
from app.safety.account_warmup import AccountWarmupManager
from app.safety.content_variation import ContentVariationEngine
from app.safety.group_filter import GroupFilter


class SafetyManager:
    """Orchestrates all safety features."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.rate_limiter = RateLimiter(session)
        self.warmup_manager = AccountWarmupManager(session)
        self.content_variation = ContentVariationEngine()
        self.group_filter = GroupFilter(session)
    
    async def get_or_create_reputation(self, user_id: int) -> AccountReputation:
        """Get or create account reputation record."""
        result = await self.session.execute(
            select(AccountReputation).where(AccountReputation.user_id == user_id)
        )
        rep = result.scalar_one_or_none()
        
        if not rep:
            rep = AccountReputation(user_id=user_id)
            self.session.add(rep)
            await self.session.flush()
        
        return rep
    
    async def check_can_send_to_group(
        self,
        user_id: int,
        community_id: int,
        safety_config: SafetyConfig | None = None
    ) -> tuple[bool, str | None]:
        """Check if user can send to this group.
        
        Returns: (can_send, reason_if_blocked)
        """
        rep = await self.get_or_create_reputation(user_id)
        
        # Check if account is restricted
        if rep.is_restricted:
            if rep.restriction_until and datetime.utcnow() < rep.restriction_until:
                return False, f"Account restricted until {rep.restriction_until}"
            else:
                # Restriction expired
                rep.is_restricted = False
                rep.restriction_reason = None
                rep.restriction_until = None
                await self.session.flush()
        
        # Check rate limits
        if safety_config:
            can_send, reason = await self.rate_limiter.check_limit(
                user_id, safety_config
            )
            if not can_send:
                return False, reason
        
        # Check account warmup
        if safety_config and safety_config.warmup_enabled:
            can_send, reason = await self.warmup_manager.can_send(
                user_id, community_id, safety_config
            )
            if not can_send:
                return False, reason
        
        # Check group risk
        can_send, reason = await self.group_filter.can_send_to_group(
            user_id, community_id
        )
        if not can_send:
            return False, reason
        
        return True, None
    
    async def record_send_success(self, user_id: int, community_id: int):
        """Record successful message send."""
        rep = await self.get_or_create_reputation(user_id)
        rep.total_messages_sent += 1
        rep.total_groups_targeted += 1
        rep.last_activity = datetime.utcnow()
        
        # Update reputation score positively
        rep.reputation_score = min(100, rep.reputation_score + 0.5)
        
        await self.session.flush()
        await self.rate_limiter.record_send(user_id)
    
    async def record_send_error(self, user_id: int, error_type: str, details: str):
        """Record message send error."""
        rep = await self.get_or_create_reputation(user_id)
        rep.error_count += 1
        rep.last_activity = datetime.utcnow()
        
        # Decrease reputation score
        rep.reputation_score = max(0, rep.reputation_score - 1.0)
        
        await self.session.flush()
    
    async def record_flood_wait(self, user_id: int, wait_seconds: int, community_id: int | None = None):
        """Record Telegram flood wait incident."""
        rep = await self.get_or_create_reputation(user_id)
        rep.flood_wait_count += 1
        
        # Significantly decrease reputation
        rep.reputation_score = max(0, rep.reputation_score - 5.0)
        
        # If too many flood waits, restrict account
        if rep.flood_wait_count > 3:
            rep.is_restricted = True
            rep.restriction_reason = "Too many flood wait incidents"
            rep.restriction_until = datetime.utcnow() + timedelta(hours=1)
        
        record = FloodWaitRecord(
            user_id=user_id,
            community_id=community_id,
            wait_seconds=wait_seconds,
        )
        self.session.add(record)
        await self.session.flush()
    
    async def get_next_send_delay_ms(self, user_id: int, safety_config: SafetyConfig) -> int:
        """Get delay before next send in milliseconds."""
        return await self.rate_limiter.get_next_delay_ms(user_id, safety_config)
    
    async def get_safety_config_for_user(self, user_id: int) -> SafetyConfig:
        """Get appropriate safety config for user."""
        rep = await self.get_or_create_reputation(user_id)
        config = SafetyConfig.from_mode(rep.safety_mode)
        
        # Adjust based on reputation score
        if rep.reputation_score < 30:
            # Bad reputation: force safe mode
            config = SafetyConfig.from_mode(SafetyMode.SAFE)
        
        return config
    
    async def set_safety_mode(self, user_id: int, mode: SafetyMode):
        """Set safety mode for user."""
        rep = await self.get_or_create_reputation(user_id)
        rep.safety_mode = mode
        await self.session.flush()
