"""
Simple in-memory rate limiter for concurrent video analyses.

Prevents system overload by limiting the number of concurrent analyses.
"""
import asyncio
import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Maximum concurrent analyses allowed
MAX_CONCURRENT_ANALYSES = 3

# Track currently running analyses
_active_analyses: Dict[str, datetime] = {}


def can_start_analysis(video_id: str) -> bool:
    """
    Check if a new analysis can be started.
    
    Returns:
        True if under limit, False if limit exceeded
    """
    # Clean up stale entries (analyses that have been running > 30 minutes)
    cutoff_time = datetime.now() - timedelta(minutes=30)
    stale_keys = [
        vid for vid, start_time in _active_analyses.items()
        if start_time < cutoff_time
    ]
    for key in stale_keys:
        _active_analyses.pop(key, None)
        logger.warning(f"Removed stale analysis tracking for {key}")
    
    # Check if we're under the limit
    if len(_active_analyses) >= MAX_CONCURRENT_ANALYSES:
        logger.warning(
            f"Rate limit exceeded: {len(_active_analyses)}/{MAX_CONCURRENT_ANALYSES} "
            f"concurrent analyses active"
        )
        return False
    
    return True


def start_analysis(video_id: str) -> None:
    """Mark an analysis as started."""
    _active_analyses[video_id] = datetime.now()
    logger.info(f"Analysis started for {video_id} ({len(_active_analyses)}/{MAX_CONCURRENT_ANALYSES} active)")


def finish_analysis(video_id: str) -> None:
    """Mark an analysis as finished."""
    _active_analyses.pop(video_id, None)
    logger.info(f"Analysis finished for {video_id} ({len(_active_analyses)}/{MAX_CONCURRENT_ANALYSES} active)")


def get_active_count() -> int:
    """Get number of currently active analyses."""
    return len(_active_analyses)

