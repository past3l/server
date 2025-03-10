import asyncio
import websockets
import json
from datetime import datetime
import os

class TrafficServer:
    def __init__(self):
        self.clients = set()
        self.log_dir = "traffic_logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"network_traffic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.total_packets = 0

    def log_to_file(self, data):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

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
        print(f"Veri: {data['data']}")
        print("-" * 80)
        print(f"\nLog Dosyası: {self.log_file}")
        print("Ctrl+C ile programı sonlandırabilirsiniz.")

    async def handle_client(self, websocket):  # path parametresini kaldırdık
        client_ip = websocket.remote_address[0]
        print(f"Yeni bağlantı: {client_ip}")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.total_packets += 1
                    self.log_to_file(data)
                    self.print_packet(data)
                except json.JSONDecodeError:
                    print(f"Hatalı JSON verisi: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"Bağlantı kapandı: {client_ip}")
        finally:
            self.clients.remove(websocket)

    async def start_server(self, host='0.0.0.0', port=8765):
        try:
            server = await websockets.serve(
                self.handle_client,  # handler fonksiyonu
                host,               # host
                port,               # port
                ping_interval=None  # ping kontrolünü kapat
            )
            
            print(f"=== Traffic Analyzer Server ===")
            print(f"Sunucu başlatıldı - {host}:{port}")
            print(f"Sunucu IP: 194.135.82.193")
            print(f"Log dizini: {self.log_dir}")
            print(f"Log dosyası: {self.log_file}")
            print("\nBağlantı bekleniyor...")
            
            await asyncio.Future()  # Sonsuza kadar çalış
            
        except Exception as e:
            print(f"Sunucu hatası: {e}")

if __name__ == "__main__":
    try:
        server = TrafficServer()
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")
    except Exception as e:
        print(f"Kritik hata: {e}")
