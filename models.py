import re
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class Match:
    platform: str            # e.g., "VPL", "VPG", "LPM"
    home_team: str
    away_team: str
    match_time: datetime     # Timezone-aware or UTC datetime
    competition: str = "Pro Clubs League"
    match_url: str = ""
    status: str = "Upcoming"
    home_logo: str = ""
    away_logo: str = ""
    league_logo: str = ""
    
    @property
    def unix_timestamp(self) -> int:
        """Returns unix timestamp integer for Discord dynamic timestamps."""
        if self.match_time.tzinfo is None:
            dt = self.match_time.replace(tzinfo=timezone.utc)
        else:
            dt = self.match_time
        return int(dt.timestamp())

    @property
    def discord_formatted_time(self) -> str:
        """Returns Discord formatted dynamic timestamp string."""
        ts = self.unix_timestamp
        return f"<t:{ts}:F> (<t:{ts}:R>)"

    @property
    def discord_time_short(self) -> str:
        """Returns Discord formatted short time + relative timestamp string."""
        ts = self.unix_timestamp
        return f"<t:{ts}:t> (<t:{ts}:R>)"

    def is_opponent(self, club_name: str) -> str:
        """Returns the opponent team relative to club_name."""
        norm_club = re.sub(r'\W+', '', club_name.lower())
        norm_home = re.sub(r'\W+', '', self.home_team.lower())
        norm_away = re.sub(r'\W+', '', self.away_team.lower())
        
        if norm_club in norm_home:
            return self.away_team
        elif norm_club in norm_away:
            return self.home_team
        return f"{self.home_team} vs {self.away_team}"

    def deduplication_key(self, club_name: str = "") -> str:
        """Generates a key for deduplicating matches."""
        norm_home = re.sub(r'\W+', '', self.home_team.lower())
        norm_away = re.sub(r'\W+', '', self.away_team.lower())
        teams = tuple(sorted([norm_home, norm_away]))
        
        # Round time to nearest 30-minute bucket to merge slight scraper time drift
        ts_bucket = round(self.unix_timestamp / 1800) * 1800
        return f"{teams[0]}_{teams[1]}_{ts_bucket}"

def deduplicate_and_sort_matches(matches: List[Match], club_name: str = "") -> List[Match]:
    """
    Deduplicates matches based on team pairs and match time buckets,
    then sorts all matches in exact chronological order (earliest first).
    """
    seen_keys = set()
    unique_matches: List[Match] = []
    
    for match in matches:
        key = match.deduplication_key(club_name)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_matches.append(match)
            
    # Sort strictly in chronological order by match_time
    unique_matches.sort(key=lambda m: m.unix_timestamp)
    return unique_matches

def get_matchday_window(dt: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Returns (start_monday_00_00, end_wednesday_23_59) for the relevant matchday week.
    - On Mon, Tue, Wed: returns current week's Monday 00:00 to Wednesday 23:59.
    - On Thu, Fri, Sat, Sun: returns next week's Monday 00:00 to Wednesday 23:59.
    """
    MYT = timezone(timedelta(hours=8))
    if dt is None:
        dt = datetime.now(MYT)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=MYT)
        
    weekday = dt.weekday()  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    if weekday <= 2:  # Mon, Tue, Wed
        start_monday = (dt - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # Thu, Fri, Sat, Sun
        days_until_next_mon = 7 - weekday
        start_monday = (dt + timedelta(days=days_until_next_mon)).replace(hour=0, minute=0, second=0, microsecond=0)
        
    end_wednesday = (start_monday + timedelta(days=2)).replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_monday, end_wednesday

def filter_weekly_matchday_fixtures(matches: List[Match], target_dt: Optional[datetime] = None) -> List[Match]:
    """
    Filters matches for the Monday-Wednesday matchday window:
    - On Mon/Tue/Wed: returns current week's Monday-Wednesday fixtures.
    - On Thu/Fri/Sat/Sun: returns next week's Monday-Wednesday fixtures.
    """
    MYT = timezone(timedelta(hours=8))
    start_win, end_win = get_matchday_window(target_dt)
    
    filtered: List[Match] = []
    for m in matches:
        m_dt = m.match_time if m.match_time.tzinfo else m.match_time.replace(tzinfo=MYT)
        if start_win <= m_dt <= end_win:
            filtered.append(m)
            
    return filtered

def filter_upcoming_matches(matches: List[Match], days: Optional[int] = None) -> List[Match]:
    """Backwards-compatible helper calling filter_weekly_matchday_fixtures."""
    return filter_weekly_matchday_fixtures(matches)
