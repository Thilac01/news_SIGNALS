import requests
import random
import time
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

PROXY_CONFIG_FILE = "data/proxy_config.json"
PROXY_LOG_FILE = "data/proxy_rotation.log"

# Reliable GitHub lists for free HTTP/HTTPS proxies
GITHUB_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

class ProxyManager:
    def __init__(self):
        self.config = self.load_config()
        self.current_proxy = None
        self.last_rotation = None
        self.rotation_count = 0
        self.proxy_pool = []
        self.last_pool_refresh = None
        
        # Initial pool load if enabled
        if self.config.get("enabled"):
            try:
                self.refresh_proxy_pool()
            except Exception as e:
                logger.error(f"Failed to initialize proxy pool: {e}")
        
    def load_config(self):
        """Load proxy configuration from file"""
        if not os.path.exists(PROXY_CONFIG_FILE):
            default_config = {
                "enabled": False,
                "rotation_interval_hours": 1,
                "auto_switch_on_block": True,
                "auto_switch_on_403": True,
                "auto_switch_on_429": True,
                "auto_switch_on_503": True,
                "auto_switch_on_captcha": True,
                "use_random_user_agents": True,
                "request_delay_min": 1,
                "request_delay_max": 3
            }
            self.save_config(default_config)
            return default_config
        
        try:
            with open(PROXY_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading proxy config: {e}")
            return {}
    
    def save_config(self, config):
        """Save proxy configuration to file"""
        try:
            os.makedirs(os.path.dirname(PROXY_CONFIG_FILE), exist_ok=True)
            with open(PROXY_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving proxy config: {e}")
    
    def log_rotation(self, reason, proxy=None):
        """Log proxy rotation event"""
        try:
            os.makedirs(os.path.dirname(PROXY_LOG_FILE), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            proxy_str = proxy if proxy else "None"
            log_entry = f"[{timestamp}] {reason} | Proxy: {proxy_str}\n"
            
            with open(PROXY_LOG_FILE, 'a') as f:
                f.write(log_entry)
            
            logger.info(f"Proxy rotation: {reason}")
        except Exception as e:
            logger.error(f"Error logging proxy rotation: {e}")

    def refresh_proxy_pool(self):
        """Fetch fresh proxies from GitHub repositories"""
        new_proxies = set()
        logger.info("Refreshing proxy pool from GitHub sources...")
        
        for url in GITHUB_PROXY_SOURCES:
            try:
                logger.info(f"Fetching proxies from: {url}")
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    count = 0
                    for line in lines:
                        line = line.strip()
                        # Basic validation for IP:Port format
                        if line and ':' in line and not line.startswith('<'):
                            new_proxies.add(line)
                            count += 1
                    logger.info(f"Fetched {count} proxies from {url}")
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                
        if new_proxies:
            self.proxy_pool = list(new_proxies)
            self.last_pool_refresh = datetime.now()
            logger.info(f"Proxy pool refreshed. Total unique proxies: {len(self.proxy_pool)}")
            self.log_rotation(f"Refreshed proxy pool with {len(self.proxy_pool)} proxies")
        else:
            logger.error("Failed to fetch any proxies from GitHub sources")
            self.log_rotation("Failed to refresh proxy pool")
    
    def get_new_proxy(self):
        """Get a random proxy from the pool"""
        if not self.config.get("enabled"):
            return None
            
        # Refresh pool if empty or old (e.g., older than 6 hours)
        if not self.proxy_pool or (self.last_pool_refresh and datetime.now() - self.last_pool_refresh > timedelta(hours=6)):
            self.refresh_proxy_pool()
            
        if not self.proxy_pool:
            logger.warning("No proxies available in pool")
            return None
            
        # Pick a random proxy
        proxy = random.choice(self.proxy_pool)
        
        # Format for requests (handling ip:port)
        if not proxy.startswith("http"):
             formatted_proxy = f"http://{proxy}"
        else:
             formatted_proxy = proxy
             
        self.current_proxy = formatted_proxy
        self.last_rotation = datetime.now()
        self.rotation_count += 1
        
        self.log_rotation("Rotated to new proxy from GitHub pool", formatted_proxy)
        return formatted_proxy
    
    def should_rotate(self):
        """Check if proxy should be rotated based on time"""
        if not self.config.get("enabled"):
            return False
        
        if not self.last_rotation:
            return True
        
        interval_hours = self.config.get("rotation_interval_hours", 1)
        time_since_rotation = datetime.now() - self.last_rotation
        
        return time_since_rotation >= timedelta(hours=interval_hours)
    
    def rotate_if_needed(self):
        """Rotate proxy if time interval has passed"""
        if self.should_rotate():
            self.get_new_proxy()
            self.log_rotation("Scheduled rotation (time interval)")
    
    def get_random_user_agent(self):
        """Get a random user agent"""
        if self.config.get("use_random_user_agents", True):
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]
    
    def get_request_delay(self):
        """Get random delay between min and max"""
        min_delay = self.config.get("request_delay_min", 1)
        max_delay = self.config.get("request_delay_max", 3)
        return random.uniform(min_delay, max_delay)
    
    def make_request(self, url, method="GET", **kwargs):
        """Make HTTP request with proxy and retry logic"""
        if not self.config.get("enabled"):
            # If proxies disabled, make normal request
            return requests.request(method, url, **kwargs)
        
        # Rotate if needed
        self.rotate_if_needed()
        
        # Get current proxy
        if not self.current_proxy:
            self.current_proxy = self.get_new_proxy()
        
        # Setup request parameters
        # Use simple HTTP/HTTPS proxy dict (most of these lists are HTTP proxies)
        proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
        
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = self.get_random_user_agent()
        kwargs["headers"] = headers
        
        # Add delay
        time.sleep(self.get_request_delay())
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Need to verify if the proxy works by handling ProxyError or ConnectTimeout
                response = requests.request(method, url, proxies=proxies, **kwargs)
                
                # Check for errors that should trigger rotation
                if response.status_code == 403 and self.config.get("auto_switch_on_403"):
                    self.log_rotation(f"HTTP 403 detected on attempt {attempt + 1}")
                    self.current_proxy = self.get_new_proxy()
                    proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
                    continue
                
                if response.status_code == 429 and self.config.get("auto_switch_on_429"):
                    self.log_rotation(f"HTTP 429 (rate limit) detected on attempt {attempt + 1}")
                    self.current_proxy = self.get_new_proxy()
                    proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
                    time.sleep(5) 
                    continue
                
                if response.status_code == 503 and self.config.get("auto_switch_on_503"):
                    self.log_rotation(f"HTTP 503 detected on attempt {attempt + 1}")
                    self.current_proxy = self.get_new_proxy()
                    proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
                    continue
                
                if self.config.get("auto_switch_on_captcha"):
                    if "captcha" in response.text.lower() or "recaptcha" in response.text.lower():
                        self.log_rotation(f"CAPTCHA detected on attempt {attempt + 1}")
                        self.current_proxy = self.get_new_proxy()
                        proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
                        continue
                
                return response
                
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                # If proxy fails, rotate immediately and retry
                self.log_rotation(f"Proxy failed on attempt {attempt + 1}: {str(e)}")
                if self.config.get("auto_switch_on_block"):
                    self.current_proxy = self.get_new_proxy()
                    proxies = {"http": self.current_proxy, "https": self.current_proxy} if self.current_proxy else None
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
        
        raise Exception("Max retries exceeded")

    def get_status(self):
        """Get current proxy status"""
        return {
            "enabled": self.config.get("enabled", False),
            "current_proxy": self.current_proxy,
            "last_rotation": self.last_rotation.isoformat() if self.last_rotation else None,
            "rotation_count": self.rotation_count,
            "pool_size": len(self.proxy_pool),
            "next_rotation": (self.last_rotation + timedelta(hours=self.config.get("rotation_interval_hours", 1))).isoformat() if self.last_rotation else None
        }
    
    def get_recent_logs(self, lines=50):
        """Get recent proxy rotation logs"""
        if not os.path.exists(PROXY_LOG_FILE):
            return []
        
        try:
            with open(PROXY_LOG_FILE, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception as e:
            logger.error(f"Error reading proxy logs: {e}")
            return []

proxy_manager = ProxyManager()
