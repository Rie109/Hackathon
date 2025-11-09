
"""
Smart Trash Bin Monitoring System - EXTENDED v2.2
Backend for Mobile Expense Tracker App Integration + IoT Features
Compatible with all Expense Tracker features
"""

import asyncio
import json
import datetime
import websockets
import time
import socket
import math
import csv
import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
import sys

# Try to ensure Windows console can print UTF-8 (emojis) to avoid logging errors
try:
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")
except Exception:
	pass

# ============ LOGGING ============
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s [%(levelname)-8s] %(name)s - %(message)s',
	handlers=[
		logging.StreamHandler(),
		logging.FileHandler('trash_bin_extended.log')
	]
)
logger = logging.getLogger(__name__)

# ============ IP DISCOVERY ============
class IPDiscovery:
	@staticmethod
	def get_local_ip() -> str:
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			ip = s.getsockname()[0]
			s.close()
			return ip
		except:
			return "127.0.0.1"

	@staticmethod
	def get_hostname() -> str:
		try:
			return socket.gethostname()
		except:
			return "raspberrypi"

# ============ mDNS DISCOVERY ============
class MDNSBroadcaster:
	def __init__(self):
		try:
			from zeroconf import ServiceInfo, Zeroconf
			local_ip = IPDiscovery.get_local_ip()
			hostname = IPDiscovery.get_hostname()
            
			self.service_info = ServiceInfo(
				"_trashbin._tcp.local.",
				f"Smart Trash Bin._trashbin._tcp.local.",
				addresses=[socket.inet_aton(local_ip)],
				port=8765,
				properties={
					'bin_id': 'trash_bin_01',
					'version': '2.2',
					'hostname': hostname,
					'features': 'trash_monitoring,expense_tracking,iot'
				}
			)
            
			self.zeroconf = Zeroconf()
			self.zeroconf.register_service(self.service_info)
			logger.info(f"✓ mDNS Broadcaster running at {local_ip}:8765")
		except:
			logger.warning("mDNS not available")
			self.zeroconf = None

	def cleanup(self):
		if self.zeroconf:
			try:
				self.zeroconf.unregister_service(self.service_info)
				self.zeroconf.close()
			except:
				pass

# ============ CONFIGURATION ============
@dataclass
class Config:
	# Server
	PORT: int = 8765
	HOST: str = "0.0.0.0"
    
	# Trash Bin
	BIN_ID: str = "trash_bin_01"
	BIN_LOCATION: str = "Default Location"
	BIN_HEIGHT_CM: int = 100
	BIN_RADIUS_CM: int = 30
	MAX_CAPACITY_LITERS: float = None
    
	# Alerts
	ALERT_HIGH: int = 80
	ALERT_MEDIUM: int = 60
    
	# Sensor
	SENSOR_READ_INTERVAL: int = 5
	REPORT_INTERVAL: int = 10
    
	# Logging
	ENABLE_LOGGING: bool = True
	LOG_FILE: str = "trash_bin_data.csv"
    
	# Expense Tracking (NEW)
	ENABLE_EXPENSE_TRACKING: bool = True
	EXPENSE_DB_FILE: str = "expenses.json"
    
	# mDNS
	ENABLE_MDNS: bool = True
    
	def __post_init__(self):
		if self.MAX_CAPACITY_LITERS is None:
			self.MAX_CAPACITY_LITERS = math.pi * (self.BIN_RADIUS_CM ** 2) * self.BIN_HEIGHT_CM / 1000

config = Config()

# ...existing code continues unchanged...
