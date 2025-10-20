import pytest
import os
import json
from modules.monitor.monitor import WebsiteMonitor


def test_monitor_initialization():
    """Test monitor can be initialized"""
    os.environ['WEBSITES_TABLE'] = 'test-table'
    monitor = WebsiteMonitor()
    assert monitor is not None
