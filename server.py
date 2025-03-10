import asyncio
import websockets
import json
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
import prettytable
from collections import defaultdict
import time

class TrafficServer:
    def __init__(self):
        self.clients = set()
        self.setup_directories()
        self.setup_logging()
        self.total_packets = 0
        self.stats = {
            'protocols': defaultdict(int),
            'sources': defaultdict(int),
            'destinations': defaultdict(int),
            'ports': defaultdict(int)
        }
        self.start_time = time.time()

    def setup_directories(self):
        # Ana dizinler
        self.base_dir = "/var/log/traffic-analyzer"
        self.log_dir = f"{self.base_dir}/logs"
        self.stats_dir = f"{self.base_dir}/stats"
        
        # Dizinleri oluştur
        for dir_path in [self.base_dir, self.log_dir, self.stats_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Log dosyası yolları
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.log_file = f"{self.log_dir}/traffic_{self.current_date}.log"
        self.stats_file = f"{self.stats_dir}/stats_{self.current_date}.log"

    def setup_logging(self):
        # Ana logger
        self.logger = logging.getLogger('TrafficAnalyzer')
        self.logger.setLevel(logging.INFO)

        # Dosya handler'ı (10MB'lık dosyalar, 30 dosya sakla)
        file_handler = RotatingFileHandler(
            self.log_file, 
            maxBytes=10*1024*1024,  # 10MB
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
        
        # Handler'ları ekle
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def update_stats(self, data):
        # İstatistikleri güncelle
        self.stats['protocols'][data['protocol']] += 1
        self.stats['sources'][data['source_ip']] += 1
        self.stats['destinations'][data['dest_ip']] += 1
        if data['ports']:
            self.stats['ports'][data['ports'].get('source_port', 0)] += 1
            self.stats['ports'][data['ports'].get('dest_port', 0)] += 1

    def create_stats_table(self):
        # İstatistik tabloları oluştur
        tables = {}
        
        for stat_type in ['protocols', 'sources', 'destinations', 'ports']:
            table = prettytable.PrettyTable()
            table.field_names = [stat_type.title(), "Count"]
            
            # En çok kullanılan 10 öğeyi göster
            sorted_items = sorted(
                self.stats[stat_type].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            for item, count in sorted_items:
                table.add_row([item, count])
            
            tables[stat_type] = table

        return tables

    def print_status(self, data):
        os.system('clear')
        uptime = time.time() - self.start_time
        
        print("=" * 50)
        print(f"TRAFFIC ANALYZER STATUS")
        print("=" * 50)
        print(f"Uptime: {int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s")
        print(f"Total Packets: {self.total_packets}")
        print(f"Current Log: {self.log_file}")
        print("=" * 50)
        
        # Son paket bilgisi
        print("\nLAST PACKET:")
        print(f"Time: {data['timestamp']}")
        print(f"Protocol: {data['protocol']}")
        print(f"Source: {data['source_ip']} -> Destination: {data['dest_ip']}")
        if data['ports']:
            print(f"Ports: {data['ports']}")
        print(f"Size: {data['size']} bytes")
        print("=" * 50)
        
        # İstatistik tablolarını göster
        tables = self.create_stats_table()
        for name, table in tables.items():
            print(f"\n{name.upper()} STATISTICS:")
            print(table)

    async def handle_client(self, websocket):
        client_ip = websocket.remote_address[0]
        self.logger.info(f"New connection from {client_ip}")
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.total_packets += 1
                    self.update_stats(data)
                    
                    # Log the data
                    self.logger.info(json.dumps(data))
                    
                    # Update display
                    self.print_status(data)
                    
                    # Her 1000 pakette bir istatistikleri kaydet
                    if self.total_packets % 1000 == 0:
                        self.save_stats()
                        
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON data: {message}")
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Connection closed: {client_ip}")
        finally:
            self.clients.remove(websocket)

    def save_stats(self):
        # İstatistikleri dosyaya kaydet
        with open(self.stats_file, 'w') as f:
            tables = self.create_stats_table()
            for name, table in tables.items():
                f.write(f"\n{name.upper()} STATISTICS:\n")
                f.write(str(table))
                f.write("\n")

    async def start_server(self, host='0.0.0.0', port=8765):
        try:
            self.logger.info(f"Starting server on {host}:{port}")
            
            server = await websockets.serve(
                self.handle_client,
                host,
                port,
                ping_interval=None
            )
            
            self.logger.info("Server started successfully")
            await asyncio.Future()  # run forever
            
        except Exception as e:
            self.logger.error(f"Server error: {e}")

if __name__ == "__main__":
    # Gerekli kütüphaneleri kur
    os.system('pip3 install prettytable')
    
    server = TrafficServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        server.logger.info("Server shutting down...")
    except Exception as e:
        server.logger.error(f"Critical error: {e}")
