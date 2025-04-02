import logging
import os
import tempfile
import requests
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dataclasses import dataclass

logger = logging.getLogger('govwatcher-archive.crawlers.webpage')

@dataclass
class CrawlResult:
    """Result of a webpage crawl"""
    success: bool
    warc_path: str = None
    screenshot_path: str = None
    html_path: str = None
    text_path: str = None
    pdf_path: str = None
    content_hash: str = None
    status_code: int = None
    size_bytes: int = None
    error: str = None
    metadata: dict = None

class WebpageCrawler:
    """Crawls webpages and captures content"""
    
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.CRAWLER_USER_AGENT
        })
    
    def crawl(self, domain):
        """Crawl a domain and return results"""
        url = f"https://{domain}"
        logger.info(f"Crawling {url}")
        
        result = CrawlResult(success=False)
        result.metadata = {
            'url': url,
            'timestamp': time.time(),
            'domain': domain
        }
        
        try:
            # Fetch the page
            response = self.session.get(url, timeout=self.config.CRAWL_TIMEOUT)
            result.status_code = response.status_code
            result.metadata['final_url'] = response.url
            
            # Check if successful
            if response.status_code != 200:
                result.error = f"HTTP status code: {response.status_code}"
                return result
            
            # Store HTML content
            html_content = response.text
            
            # Store content in temp files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save HTML
                html_file = os.path.join(temp_dir, 'content.html')
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Extract text
                soup = BeautifulSoup(html_content, 'html.parser')
                text_content = soup.get_text(separator='\n', strip=True)
                text_file = os.path.join(temp_dir, 'content.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                # Take screenshot if enabled
                screenshot_file = None
                if self.config.ENABLE_SCREENSHOTS:
                    screenshot_file = self._take_screenshot(url, temp_dir)
                    result.metadata['screenshot_taken'] = bool(screenshot_file)
                
                # Generate PDF if enabled
                pdf_file = None
                if self.config.ENABLE_PDF:
                    pdf_file = self._generate_pdf(url, temp_dir)
                    result.metadata['pdf_generated'] = bool(pdf_file)
                
                # Generate WARC
                warc_file = self._generate_warc(url, response, temp_dir)
                
                # These would be stored by the storage manager when saving a snapshot
                result.html_path = html_file
                result.text_path = text_file
                result.screenshot_path = screenshot_file
                result.pdf_path = pdf_file
                result.warc_path = warc_file
                
                # Calculate hash from HTML content
                import hashlib
                hasher = hashlib.sha256()
                hasher.update(html_content.encode('utf-8'))
                result.content_hash = hasher.hexdigest()
                
                # Set size (approximate)
                result.size_bytes = len(html_content)
                
                # Mark as successful
                result.success = True
            
            return result
            
        except requests.RequestException as e:
            result.error = f"Request error: {str(e)}"
            logger.error(f"Error crawling {url}: {str(e)}")
            return result
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
            logger.exception(f"Unexpected error crawling {url}: {str(e)}")
            return result
    
    def _take_screenshot(self, url, temp_dir):
        """Take a screenshot of the webpage"""
        screenshot_file = os.path.join(temp_dir, 'screenshot.png')
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={self.config.CRAWLER_USER_AGENT}')
            
            browser = webdriver.Chrome(options=options)
            browser.set_window_size(1280, 1024)
            
            browser.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Take screenshot
            browser.save_screenshot(screenshot_file)
            browser.quit()
            
            return screenshot_file
        except Exception as e:
            logger.exception(f"Error taking screenshot of {url}: {str(e)}")
            return None
    
    def _generate_pdf(self, url, temp_dir):
        """Generate a PDF of the webpage"""
        pdf_file = os.path.join(temp_dir, 'content.pdf')
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={self.config.CRAWLER_USER_AGENT}')
            options.add_argument('--print-to-pdf=' + pdf_file)
            
            browser = webdriver.Chrome(options=options)
            browser.get(url)
            time.sleep(3)  # Wait for page to load
            browser.quit()
            
            return pdf_file
        except Exception as e:
            logger.exception(f"Error generating PDF of {url}: {str(e)}")
            return None
    
    def _generate_warc(self, url, response, temp_dir):
        """Generate a WARC file for the webpage"""
        try:
            # Simple placeholder implementation - in a real system you'd use
            # a dedicated WARC tool like warcio
            warc_file = os.path.join(temp_dir, 'original.warc')
            
            with open(warc_file, 'w', encoding='utf-8') as f:
                f.write(f"WARC/1.0\r\n")
                f.write(f"WARC-Type: response\r\n")
                f.write(f"WARC-Target-URI: {url}\r\n")
                f.write(f"WARC-Date: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}\r\n")
                f.write(f"WARC-Record-ID: <urn:uuid:{os.urandom(16).hex()}>\r\n")
                f.write(f"Content-Type: application/http; msgtype=response\r\n")
                f.write(f"Content-Length: {len(response.content)}\r\n")
                f.write(f"\r\n")
                f.write(f"HTTP/1.1 {response.status_code} {response.reason}\r\n")
                for key, value in response.headers.items():
                    f.write(f"{key}: {value}\r\n")
                f.write(f"\r\n")
                f.write(response.text)
            
            return warc_file
        except Exception as e:
            logger.exception(f"Error generating WARC for {url}: {str(e)}")
            return None
