# Scrapy settings for news_scraper project
BOT_NAME = 'news_scraper'

# Scrapy settings for user agent and robot.txt rules
USER_AGENT = 'news_scraper (+http://www.yourdomain.com)'  # Set a custom user-agent
ROBOTSTXT_OBEY = False  # Respect robots.txt

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests (default: 0)
DOWNLOAD_DELAY = 2  # Delay between requests in seconds

# The download timeout (in seconds)
DOWNLOAD_TIMEOUT = 60

# Enable or disable extensions
EXTENSIONS = {
   'scrapy.extensions.telnet.TelnetConsole': None,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy_selenium.SeleniumMiddleware': 800,
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Enable or disable the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable or disable pipelines
ITEM_PIPELINES = {
   'news_scraper.pipelines.NewsScraperPipeline': 1,
}

# Enable logging (you can adjust this to get different log levels)
LOG_LEVEL = 'INFO'

# Configure the output format (You can choose between JSON, CSV, etc.)
FEED_FORMAT = 'json'
FEED_URI = 'output.json'  # Set the output file name
