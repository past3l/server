import asyncio
import websockets
import json
from datetime import datetime
import os

class TrafficServer:
    def __init__(self):
        self.clients = set()
        self.log_file = f"network_traffic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log_to_file(self, data):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def print_packet(self, data):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"=== Ağ Trafiği Analizi ===")
        print(f"Zaman: {data['timestamp']}")
        print(f"Protokol: {data['protocol']}")
        print(f"Kaynak: {data['source_ip']}")
        print(f"Hedef: {data['dest_ip']}")
        
        if data['ports']:
            print(f"Kaynak Port: {data['ports'].get('source_port')}")
            print(f"Hedef Port: {data['ports'].get('dest_port')}")
        
        print(f"Boyut: {data['size']} bytes")
        print(f"Veri: {data['data']}")
        print("-" * 80)

    async def handle_client(self, websocket, path):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.log_to_file(data)
                    self.print_packet(data)
                except json.JSONDecodeError:
                    print(f"Hatalı JSON verisi: {message}")
        finally:
            self.clients.remove(websocket)

    async def start_server(self, host='0.0.0.0', port=8765):
        async with websockets.serve(self.handle_client, host, port):
            print(f"Sunucu başlatıldı - {host}:{port}")
            print(f"Log dosyası: {self.log_file}")
            await asyncio.Future()  # Sonsuza kadar çalış

if __name__ == "__main__":
    server = TrafficServer()
    asyncio.run(server.start_server())
