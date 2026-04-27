import logging
from googleapiclient.discovery import build
from core.youtube_fleet import youtube_fleet

logger = logging.getLogger("YouTubeAnalytics")

class YouTubeAnalytics:
    """
    Pulls data from YouTube Studio to feed into Andrew's Strategic LLM Loop.
    """
    def __init__(self):
        # Reuses the same OAuth manager as the Fleet Uploader
        self.fleet = youtube_fleet

    def fetch_channel_performance(self, account_identifier: str) -> dict:
        """
        Fetches views, estimated minutes watched, and average view duration 
        for the last 30 days.
        """
        creds = self.fleet._get_credentials(account_identifier)
        if not creds:
            logger.error(f"Cannot fetch analytics. No valid credentials for {account_identifier}.")
            return {"status": "error", "message": "auth_missing"}

        try:
            # Requires 'https://www.googleapis.com/auth/yt-analytics.readonly' scope
            youtube_analytics = build('youtubeAnalytics', 'v2', credentials=creds)
            
            # 30 day lookback
            import datetime
            end_date = datetime.date.today().strftime('%Y-%m-%d')
            start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
            
            request = youtube_analytics.reports().query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration",
                dimensions="day",
                sort="day"
            )
            response = request.execute()
            
            # Simple aggregation for the LLM
            total_views = 0
            total_minutes = 0
            days_data = response.get('rows', [])
            
            for row in days_data:
                total_views += int(row[1])
                total_minutes += float(row[2])
                
            avg_duration = 0
            if total_views > 0:
                avg_duration = (total_minutes / total_views) * 60 # in seconds
                
            logger.info(f"Analytics pulled for {account_identifier}. Views: {total_views}")
            
            return {
                "status": "success",
                "account": account_identifier,
                "period": "Last 30 Days",
                "total_views": total_views,
                "average_view_duration_seconds": round(avg_duration, 2),
                "insight": "High drop-off detected" if avg_duration < 45 else "Retention is healthy"
            }

        except Exception as e:
            logger.error(f"YouTube Analytics API Error: {e}")
            return {"status": "error", "message": str(e)}

youtube_analytics = YouTubeAnalytics()
