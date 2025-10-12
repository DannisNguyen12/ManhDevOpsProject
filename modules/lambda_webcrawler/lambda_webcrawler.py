import boto3
import requests
from bs4 import BeautifulSoup
import time
import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

class WebCrawler:
    def __init__(self):
        self.targets_table = dynamodb.Table(os.environ['TARGETS_TABLE'])
        self.results_table = dynamodb.Table(os.environ['CRAWL_RESULTS_TABLE'])
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WebCrawler/1.0 (+https://github.com/your-repo)'
        })

    def get_crawl_targets(self) -> List[Dict]:
        """Get all crawl targets from DynamoDB"""
        try:
            response = self.targets_table.scan()
            targets = response.get('Items', [])

            # Filter for targets that have crawling enabled
            crawl_targets = []
            for target in targets:
                if target.get('crawl_enabled', True):  # Default to enabled
                    crawl_targets.append(target)

            logger.info(f"Retrieved {len(crawl_targets)} crawl targets")
            return crawl_targets
        except Exception as e:
            logger.error(f"Failed to retrieve crawl targets: {str(e)}")
            return []

    def crawl_website(self, target: Dict) -> Optional[Dict]:
        """Crawl a single website and extract content"""
        url = target['url']
        crawl_timestamp = str(int(time.time()))

        try:
            logger.info(f"Crawling {url}")

            # Make HTTP request
            start_time = time.time()
            response = self.session.get(url, timeout=30)
            response_time = time.time() - start_time

            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract basic information
            crawl_result = {
                'target_id': target['id'],
                'crawl_timestamp': crawl_timestamp,
                'url': url,
                'status_code': response.status_code,
                'response_time': round(response_time * 1000, 2),  # milliseconds
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.content),
                'title': self.extract_title(soup),
                'meta_description': self.extract_meta_description(soup),
                'headings': self.extract_headings(soup),
                'links': self.extract_links(soup, url),
                'images': self.extract_images(soup, url),
                'text_content': self.extract_text_content(soup),
                'crawl_depth': target.get('crawl_depth', 1),
                'selectors': target.get('selectors', {}),
                'custom_data': self.extract_custom_data(soup, target.get('selectors', {})),
                'ttl': int(time.time()) + (30 * 24 * 60 * 60)  # 30 days TTL
            }

            # Store in DynamoDB
            self.results_table.put_item(Item=crawl_result)

            logger.info(f"Successfully crawled {url} in {response_time:.2f}s")
            return crawl_result

        except Exception as e:
            logger.error(f"Failed to crawl {url}: {str(e)}")

            # Store error result
            error_result = {
                'target_id': target['id'],
                'crawl_timestamp': crawl_timestamp,
                'url': url,
                'status_code': 0,
                'error': str(e),
                'ttl': int(time.time()) + (30 * 24 * 60 * 60)
            }
            self.results_table.put_item(Item=error_result)
            return error_result

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.text.strip() if title_tag else ""

    def extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '') if meta_desc else ""

    def extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract headings by level"""
        headings = {}
        for level in range(1, 7):
            heading_tags = soup.find_all(f'h{level}')
            headings[f'h{level}'] = [h.text.strip() for h in heading_tags]
        return headings

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from the page"""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)
            links.append({
                'text': a_tag.text.strip(),
                'url': absolute_url,
                'internal': self.is_internal_link(absolute_url, base_url)
            })
        return links[:100]  # Limit to first 100 links

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all images from the page"""
        images = []
        for img_tag in soup.find_all('img', src=True):
            src = img_tag['src']
            absolute_url = urljoin(base_url, src)
            images.append({
                'src': absolute_url,
                'alt': img_tag.get('alt', ''),
                'title': img_tag.get('title', '')
            })
        return images[:50]  # Limit to first 50 images

    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:10000]  # Limit to 10k characters

    def extract_custom_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, str]:
        """Extract custom data using CSS selectors"""
        custom_data = {}
        for key, selector in selectors.items():
            try:
                element = soup.select_one(selector)
                if element:
                    custom_data[key] = element.text.strip()
                else:
                    custom_data[key] = ""
            except Exception as e:
                logger.warning(f"Failed to extract data for selector {selector}: {str(e)}")
                custom_data[key] = ""
        return custom_data

    def is_internal_link(self, url: str, base_url: str) -> bool:
        """Check if a link is internal to the domain"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            return parsed_url.netloc == parsed_base.netloc
        except:
            return False

def lambda_handler(event, context):
    """Main Lambda handler"""
    logger.info(f"Starting web crawler execution")

    crawler = WebCrawler()
    targets = crawler.get_crawl_targets()

    if not targets:
        logger.warning("No crawl targets found")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No crawl targets found'})
        }

    results = []
    for target in targets:
        result = crawler.crawl_website(target)
        if result:
            results.append(result)

    logger.info(f"Crawled {len(results)} websites successfully")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully crawled {len(results)} websites',
            'results_count': len(results)
        })
    }