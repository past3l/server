import asyncio
import websockets
import json
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from collections import defaultdict
import time

class TrafficServer:
    def __init__(self):
        self.clients = set()
        self.setup_directories()
        self.ip_loggers = {}  # Her IP için ayrı logger
        self.total_packets = 0
        self.start_time = time.time()

    def setup_directories(self):
        # Ana dizinler
        self.base_dir = "/var/log/traffic-analyzer"
        self.main_log_dir = f"{self.base_dir}/main_logs"
        self.ip_log_dir = f"{self.base_dir}/ip_logs"
        
        # Dizinleri oluştur
        for dir_path in [self.base_dir, self.main_log_dir, self.ip_log_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Ana log dosyası
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.main_log_file = f"{self.main_log_dir}/traffic_{self.current_date}.log"
        
        # Ana logger'ı kur
        self.setup_main_logger()

    def setup_main_logger(self):
        # Ana logger
        self.main_logger = logging.getLogger('MainTrafficLogger')
        self.main_logger.setLevel(logging.INFO)

        # Dosya handler'ı (10MB'lık dosyalar, 30 dosya sakla)
        file_handler = RotatingFileHandler(
            self.main_log_file, 
            maxBytes=10*1024*1024,
            backupCount=30
        )
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        self.main_logger.addHandler(file_handler)
        self.main_logger.addHandler(console_handler)

    def get_ip_logger(self, ip):
        if ip not in self.ip_loggers:
            # IP için özel logger oluştur
            logger = logging.getLogger(f'IP_{ip}')
            logger.setLevel(logging.INFO)
            
            # IP'ye özel dizin oluştur
            ip_dir = f"{self.ip_log_dir}/{ip}"
            os.makedirs(ip_dir, exist_ok=True)
            
            # IP'ye özel log dosyası
            log_file = f"{ip_dir}/traffic_{self.current_date}.log"
            
            # Handler'ı ayarla
            handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=30
            )
            
            formatter = logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
            self.ip_loggers[ip] = logger
        
        return self.ip_loggers[ip]

    def print_packet(self, data):
        os.system('clear')
        print(f"=== Ağ Trafiği Analizi ===")
        print(f"Sunucu IP: 194.135.82.193")
        print(f"Toplam Paket: {self.total_packets}")
        print(f"Zaman: {data['timestamp']}")
        print(f"Protokol: {data['protocol']}")
        print(f"Kaynak: {data['source_ip']}")
        print(f"Hedef: {data['dest_ip']}")
        
        if data['ports']:
            print(f"Kaynak Port: {data['ports'].get('source_port')}")
            print(f"Hedef Port: {data['ports'].get('dest_port')}")
        
        print(f"Boyut: {data['size']} bytes")
        print(f"Veri İçeriği: {data['data']}")
        print("-" * 80)
        print(f"\nLog Dosyası: {self.main_log_file}")
        print("Ctrl+C ile programı sonlandırabilirsiniz.")

    def log_traffic(self, data):
        # Ana logga kaydet
        self.main_logger.info(json.dumps(data))
        
        # Kaynak IP için logla
        source_ip = data['source_ip']
        source_logger = self.get_ip_logger(source_ip)
        source_logger.info(
            f"GIDEN -> {data['dest_ip']} | "
            f"Protocol: {data['protocol']} | "
            f"Size: {data['size']} bytes | "
            f"Ports: {data['ports']} | "
            f"Veri: {data['data']}"
        )
        
        # Hedef IP için logla
        dest_ip = data['dest_ip']
        dest_logger = self.get_ip_logger(dest_ip)
        dest_logger.info(
            f"GELEN <- {source_ip} | "
            f"Protocol: {data['protocol']} | "
            f"Size: {data['size']} bytes | "
            f"Ports: {data['ports']} | "
            f"Veri: {data['data']}"
        )

    async def handle_client(self, websocket):
        client_ip = websocket.remote_address[0]
        self.main_logger.info(f"New connection from {client_ip}")
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.total_packets += 1
                    
                    # Verileri logla
                    self.log_traffic(data)
                    
                    # Ekranı güncelle
                    self.print_packet(data)
                    
                except json.JSONDecodeError:
                    self.main_logger.error(f"Invalid JSON data: {message}")
        except websockets.exceptions.ConnectionClosed:
            self.main_logger.info(f"Connection closed: {client_ip}")
        finally:
            self.clients.remove(websocket)

    async def start_server(self, host='0.0.0.0', port=8765):
        try:
            self.main_logger.info(f"Starting server on {host}:{port}")
            
            server = await websockets.serve(
                self.handle_client,
                host,
                port,
                ping_interval=None
            )
            
            self.main_logger.info("Server started successfully")
            print(f"Log dosyası: {self.main_log_file}")
            await asyncio.Future()  # Sonsuza kadar çalış
            
        except Exception as e:
            self.main_logger.error(f"Server error: {e}")

if __name__ == "__main__":
    server = TrafficServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        server.main_logger.info("Server shutting down...")
    except Exception as e:
        server.main_logger.error(f"Critical error: {e}")
