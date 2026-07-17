"""Content variation engine to avoid spam patterns."""

import random
from typing import Optional


class ContentVariationEngine:
    """Generates variations of content to avoid exact duplicates."""
    
    # Emoji variations
    EMOJI_PACKS = {
        "fire": ["🔥", "⚡", "💥", "✨", "🌟"],
        "sale": ["💰", "💵", "🏷️", "💳", "🛒"],
        "phone": ["📱", "☎️", "📲", "💬"],
        "check": ["✓", "✅", "☑️", "👍"],
    }
    
    # Text variations
    VARIATIONS = {
        "available": ["disponible", "en venta", "oferta", "stock disponible"],
        "buy": ["compra", "obtén", "adquiere", "consigue"],
        "contact": ["contacta", "comunícate", "envía DM", "escribe aquí"],
        "limited": ["oferta limitada", "stock limitado", "últimas unidades", "promoción limitada"],
    }
    
    def vary_content(self, content: str, variation_intensity: float = 0.5) -> str:
        """Apply variations to content.
        
        variation_intensity: 0.0-1.0, higher = more changes
        """
        if not isinstance(variation_intensity, (int, float)) or not 0 <= variation_intensity <= 1:
            variation_intensity = 0.5
        
        # Randomly decide if we change emojis
        if random.random() < variation_intensity * 0.5:
            content = self._vary_emojis(content)
        
        # Randomly decide if we rephrase
        if random.random() < variation_intensity * 0.3:
            content = self._rephrase_phrases(content)
        
        return content
    
    def _vary_emojis(self, text: str) -> str:
        """Replace emojis with similar ones."""
        for emoji_type, emojis in self.EMOJI_PACKS.items():
            for emoji in emojis[1:]:
                if emoji in text:
                    replacement = random.choice(emojis)
                    text = text.replace(emoji, replacement, 1)
        
        return text
    
    def _rephrase_phrases(self, text: str) -> str:
        """Replace common phrases with variations."""
        for key, variations in self.VARIATIONS.items():
            for variation in variations:
                if variation.lower() in text.lower():
                    replacement = random.choice(variations)
                    import re
                    pattern = re.compile(re.escape(variation), re.IGNORECASE)
                    text = pattern.sub(replacement, text, count=1)
                    break
        
        return text
    
    def get_variation_factor(self, times_used: int) -> float:
        """Get variation intensity based on how many times content was used.
        
        More uses = higher variation.
        """
        if times_used == 0:
            return 0.0
        elif times_used <= 2:
            return min(0.3, times_used * 0.15)
        elif times_used <= 5:
            return 0.5
        else:
            return min(0.9, 0.7 + (times_used - 5) * 0.05)
