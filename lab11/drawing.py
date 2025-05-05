import pygame
import socket
import threading
import sys
import asyncio
import platform

class RemoteDrawingServer:
    def __init__(self, host='127.0.0.1', port=5000, screen_width=800, screen_height=600, fps=60, buffer_size=1024):
        self.host = host
        self.port = port
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fps = fps
        self.buffer_size = buffer_size
        self.active_drawings = []
        self.ongoing_drawing = []
        self.server_socket = None
        self.client_socket = None
        self.screen = None
        self.clock = None

    def start(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Сервер: Удалённое рисование")
        self.clock = pygame.time.Clock()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"Сервер запущен на {self.host}:{self.port}, ожидание клиента...")
        self.client_socket, addr = self.server_socket.accept()
        print(f"Подключён клиент: {addr}")
        threading.Thread(target=self.receive_drawing_data, daemon=True).start()
        if platform.system() == "Emscripten":
            asyncio.ensure_future(self.run_server())
        else:
            asyncio.run(self.run_server())

    def receive_drawing_data(self):
        while True:
            try:
                data = self.client_socket.recv(self.buffer_size).decode('utf-8')
                if not data:
                    break
                if data == "NEW":
                    if self.ongoing_drawing:
                        self.active_drawings.append(self.ongoing_drawing)
                    self.ongoing_drawing = []
                else:
                    x, y = map(int, data.split(','))
                    self.ongoing_drawing.append((x, y))
            except:
                break
        if self.ongoing_drawing:
            self.active_drawings.append(self.ongoing_drawing)
        self.client_socket.close()

    async def run_server(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.screen.fill((255, 255, 255))
            for drawing in self.active_drawings:
                for i in range(1, len(drawing)):
                    pygame.draw.line(self.screen, (0, 0, 0), drawing[i - 1], drawing[i], 2)
            for i in range(1, len(self.ongoing_drawing)):
                pygame.draw.line(self.screen, (0, 0, 0), self.ongoing_drawing[i - 1], self.ongoing_drawing[i], 2)
            pygame.display.flip()
            self.clock.tick(self.fps)
            await asyncio.sleep(1.0 / self.fps)
        pygame.quit()
        self.client_socket.close()
        self.server_socket.close()

class RemoteDrawingClient:
    def __init__(self, host='127.0.0.1', port=5000, screen_width=800, screen_height=600, fps=60, buffer_size=1024):
        self.host = host
        self.port = port
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fps = fps
        self.buffer_size = buffer_size
        self.active_drawings = []
        self.ongoing_drawing = []
        self.client_socket = None
        self.screen = None
        self.clock = None

    def start(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Клиент: Удалённое рисование")
        self.clock = pygame.time.Clock()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            print(f"Подключено к серверу {self.host}:{self.port}")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            pygame.quit()
            return
        if platform.system() == "Emscripten":
            asyncio.ensure_future(self.run_client())
        else:
            asyncio.run(self.run_client())

    async def run_client(self):
        running = True
        drawing = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        drawing = True
                        if self.ongoing_drawing:
                            self.active_drawings.append(self.ongoing_drawing)
                        self.ongoing_drawing = []
                        try:
                            self.client_socket.send("NEW".encode('utf-8'))
                        except:
                            running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        drawing = False
                        if self.ongoing_drawing:
                            self.active_drawings.append(self.ongoing_drawing)
                        self.ongoing_drawing = []
            if drawing:
                x, y = pygame.mouse.get_pos()
                self.ongoing_drawing.append((x, y))
                try:
                    self.client_socket.send(f"{x},{y}".encode('utf-8'))
                except:
                    running = False

            self.screen.fill((255, 255, 255))
            for drawing in self.active_drawings:
                for i in range(1, len(drawing)):
                    pygame.draw.line(self.screen, (0, 0, 0), drawing[i - 1], drawing[i], 2)
            for i in range(1, len(self.ongoing_drawing)):
                pygame.draw.line(self.screen, (0, 0, 0), self.ongoing_drawing[i - 1], self.ongoing_drawing[i], 2)
            pygame.display.flip()
            self.clock.tick(self.fps)
            await asyncio.sleep(1.0 / self.fps)
        pygame.quit()
        self.client_socket.close()

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("Использование: python drawing.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        server = RemoteDrawingServer()
        server.start()
    else:
        client = RemoteDrawingClient()
        client.start()

if __name__ == "__main__":
    main()