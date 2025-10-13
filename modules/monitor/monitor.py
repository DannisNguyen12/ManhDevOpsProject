import boto3
import requests
import time
import logging
import os
import json
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

class WebsiteMonitor:
    def __init__(self):
        self.websites_table = dynamodb.Table(os.environ['WEBSITES_TABLE'])
        self.cloudwatch = cloudwatch
        self.max_crawl_depth = int(os.environ.get('MAX_CRAWL_DEPTH', '2'))
        self.max_pages_per_site = int(os.environ.get('MAX_PAGES_PER_SITE', '10'))

    def get_websites(self) -> List[Dict]:
        """Get all websites to monitor"""
        try:
            response = self.websites_table.scan()
            websites = response.get('Items', [])

            # Filter for enabled websites
            enabled_websites = []
            for website in websites:
                if website.get('enabled', True):  # Default to enabled
                    enabled_websites.append(website)

            logger.info(f"Retrieved {len(enabled_websites)} websites to monitor")
            return enabled_websites
        except Exception as e:
            logger.error(f"Failed to retrieve websites: {str(e)}")
            return []

    def crawl_website(self, website: Dict) -> Dict:
        """Crawl website and extract links/content"""
        start_time = time.time()
        url = website['url']
        website_id = website['id']
        website_name = website.get('name', website_id)

        crawled_pages = []
        visited_urls = set()
        urls_to_visit = [url]

        logger.info(f"Starting crawl of {url} with max depth {self.max_crawl_depth}")

        try:
            while urls_to_visit and len(crawled_pages) < self.max_pages_per_site:
                current_url = urls_to_visit.pop(0)

                if current_url in visited_urls:
                    continue

                if not self._is_same_domain(url, current_url):
                    continue

                visited_urls.add(current_url)

                page_start_time = time.time()
                response = requests.get(current_url, timeout=30, allow_redirects=True)
                page_response_time = time.time() - page_start_time

                if response.status_code != 200:
                    continue

                # Parse HTML content
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    absolute_url = urljoin(current_url, href)
                    if self._is_valid_url(absolute_url) and self._is_same_domain(url, absolute_url):
                        links.append(absolute_url)

                # Extract page info
                title = soup.title.string if soup.title else "No Title"
                word_count = len(re.findall(r'\b\w+\b', soup.get_text()))

                page_info = {
                    'url': current_url,
                    'title': title,
                    'word_count': word_count,
                    'links_found': len(links),
                    'response_time': round(page_response_time * 1000, 2),
                    'status_code': response.status_code,
                    'crawled_at': str(int(time.time()))
                }

                crawled_pages.append(page_info)

                # Add new links to visit queue (breadth-first)
                if len(visited_urls) < self.max_crawl_depth * 5:  # Limit based on depth
                    for link in links:
                        if link not in visited_urls and link not in urls_to_visit:
                            urls_to_visit.append(link)

            total_crawl_time = time.time() - start_time

            # Send operational metrics
            self._send_operational_metrics(website_id, website_name, total_crawl_time, len(crawled_pages))

            result = {
                'website_id': website_id,
                'website_name': website_name,
                'base_url': url,
                'total_pages_crawled': len(crawled_pages),
                'total_crawl_time': round(total_crawl_time, 2),
                'pages': crawled_pages,
                'timestamp': str(int(time.time()))
            }

            logger.info(f"Successfully crawled {url}: {len(crawled_pages)} pages in {total_crawl_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Failed to crawl {url}: {str(e)}")
            total_crawl_time = time.time() - start_time
            self._send_operational_metrics(website_id, website_name, total_crawl_time, 0)

            return {
                'website_id': website_id,
                'website_name': website_name,
                'base_url': url,
                'total_pages_crawled': 0,
                'total_crawl_time': round(total_crawl_time, 2),
                'error': str(e),
                'timestamp': str(int(time.time()))
            }

    def check_website(self, website: Dict) -> Optional[Dict]:
        """Check website availability and latency (legacy method)"""
        url = website['url']
        website_id = website['id']
        website_name = website.get('name', website_id)

        try:
            logger.info(f"Monitoring {url}")

            # Make HTTP request
            start_time = time.time()
            response = requests.get(url, timeout=30, allow_redirects=True)
            response_time = time.time() - start_time

            # Calculate metrics
            availability = 1 if 200 <= response.status_code < 400 else 0
            latency_ms = round(response_time * 1000, 2)

            # Send metrics to CloudWatch
            self._send_metrics_to_cloudwatch(website_id, website_name, availability, latency_ms, response.status_code)

            result = {
                'website_id': website_id,
                'website_name': website_name,
                'url': url,
                'status_code': response.status_code,
                'response_time': latency_ms,
                'availability': availability,
                'timestamp': str(int(time.time()))
            }

            logger.info(f"Successfully monitored {url}: {response.status_code} in {latency_ms}ms")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to monitor {url}: {str(e)}")

            # Send failure metrics to CloudWatch
            self._send_metrics_to_cloudwatch(website_id, website_name, 0, 0, 0)

            return {
                'website_id': website_id,
                'website_name': website_name,
                'url': url,
                'status_code': 0,
                'response_time': 0,
                'availability': 0,
                'error': str(e),
                'timestamp': str(int(time.time()))
            }

    def _is_same_domain(self, base_url: str, target_url: str) -> bool:
        """Check if two URLs belong to the same domain"""
        try:
            base_domain = urlparse(base_url).netloc
            target_domain = urlparse(target_url).netloc
            return base_domain == target_domain
        except:
            return False

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not a fragment/anchor"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc) and not url.startswith('#')
        except:
            return False

    def _send_operational_metrics(self, website_id: str, website_name: str, crawl_time: float, pages_crawled: int):
        """Send operational health metrics to CloudWatch"""
        try:
            import psutil
            memory_usage = psutil.virtual_memory().percent

            metrics_data = [
                {
                    'MetricName': 'CrawlTime',
                    'Dimensions': [
                        {'Name': 'WebsiteId', 'Value': website_id},
                        {'Name': 'WebsiteName', 'Value': website_name}
                    ],
                    'Value': crawl_time,
                    'Unit': 'Seconds'
                },
                {
                    'MetricName': 'PagesCrawled',
                    'Dimensions': [
                        {'Name': 'WebsiteId', 'Value': website_id},
                        {'Name': 'WebsiteName', 'Value': website_name}
                    ],
                    'Value': pages_crawled,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'MemoryUsage',
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': 'WebCrawler'}
                    ],
                    'Value': memory_usage,
                    'Unit': 'Percent'
                }
            ]

            cloudwatch.put_metric_data(
                Namespace='WebCrawler/Operational',
                MetricData=metrics_data
            )

        except Exception as e:
            logger.error(f"Failed to send operational metrics: {str(e)}")

    def create_website_alarms(self, website: Dict):
        """Create CloudWatch alarms for a specific website if they don't exist"""
        website_id = website['id']
        website_name = website.get('name', website_id)

        try:
            # Check if alarms already exist for this website
            existing_alarms = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f"{website_name}-"
            )

            if existing_alarms['MetricAlarms']:
                logger.info(f"Alarms already exist for {website_name}")
                return

            # Create availability alarm for this website
            self.cloudwatch.put_metric_alarm(
                AlarmName=f"{website_name}-Availability",
                AlarmDescription=f"Alert when {website_name} availability drops below 95%",
                ActionsEnabled=True,
                AlarmActions=[os.environ.get('ALARM_SNS_TOPIC_ARN', '')],
                MetricName='Availability',
                Namespace='WebsiteMonitoring',
                Statistic='Average',
                Dimensions=[
                    {'Name': 'WebsiteId', 'Value': website_id},
                    {'Name': 'WebsiteName', 'Value': website_name}
                ],
                Period=300,  # 5 minutes
                EvaluationPeriods=3,
                DatapointsToAlarm=2,
                Threshold=0.95,
                ComparisonOperator='LessThanThreshold'
            )

            # Create latency alarm for this website
            self.cloudwatch.put_metric_alarm(
                AlarmName=f"{website_name}-Latency",
                AlarmDescription=f"Alert when {website_name} latency exceeds 2000ms",
                ActionsEnabled=True,
                AlarmActions=[os.environ.get('ALARM_SNS_TOPIC_ARN', '')],
                MetricName='Latency',
                Namespace='WebsiteMonitoring',
                Statistic='Average',
                Dimensions=[
                    {'Name': 'WebsiteId', 'Value': website_id},
                    {'Name': 'WebsiteName', 'Value': website_name}
                ],
                Period=300,  # 5 minutes
                EvaluationPeriods=2,
                DatapointsToAlarm=1,
                Threshold=2000,
                ComparisonOperator='GreaterThanThreshold'
            )

            logger.info(f"Created CloudWatch alarms for {website_name}")

        except Exception as e:
            logger.error(f"Failed to create alarms for {website_name}: {str(e)}")

def lambda_handler(event, context):
    """Main Lambda handler for website monitoring and crawling"""
    logger.info("Starting website monitoring and crawling execution")

    monitor = WebsiteMonitor()
    websites = monitor.get_websites()

    if not websites:
        logger.warning("No websites found to monitor")
        return {
            'statusCode': 200,
            'body': '{"message": "No websites to monitor"}'
        }

    crawl_results = []
    monitor_results = []

    for website in websites:
        # Create CloudWatch alarms for this website if they don't exist
        monitor.create_website_alarms(website)

        # Perform crawling
        crawl_result = monitor.crawl_website(website)
        if crawl_result:
            crawl_results.append(crawl_result)

        # Also perform basic availability check
        monitor_result = monitor.check_website(website)
        if monitor_result:
            monitor_results.append(monitor_result)

    logger.info(f"Successfully crawled {len(crawl_results)} websites and monitored {len(monitor_results)} websites")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully processed {len(crawl_results)} websites',
            'crawl_results_count': len(crawl_results),
            'monitor_results_count': len(monitor_results),
            'timestamp': str(int(time.time()))
        })
    }