import json
import os
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

CONFIG_PATH = 'settings.json'

class RedirectorEngine:
    def __init__(self):
        self.config = []
        self.active_sockets = {}
        self.listeners = {}
        self.running = False
        self.lock = threading.Lock()
        self.last_modified = 0

    def load_config(self):
        try:
            if not os.path.exists(CONFIG_PATH):
                return
                
            mtime = os.path.getmtime(CONFIG_PATH)
            if mtime == self.last_modified:
                return
                
            with open(CONFIG_PATH, 'r') as f:
                raw_data = f.read()
                if not raw_data.strip():
                    self.config = []
                    return
                    
                new_config = json.loads(raw_data)
                
            if isinstance(new_config, list) and all(isinstance(x, dict) for x in new_config):
                self.config = new_config
                self.last_modified = mtime
        except:
            pass

    def manage_ports(self):
        if not self.running:
            for sock in self.listeners.values():
                sock['socket'].close()
            self.listeners.clear()
            return
            
        needed_ports = {rule['internal_port']: rule for rule in self.config}
        
        for port in list(self.listeners.keys()):
            stored = self.listeners[port].get('rule')
            current = needed_ports.get(port)
            if current and current != stored:
                self.listeners[port]['socket'].close()
                del self.listeners[port]
                
        for port, rule in needed_ports.items():
            if port not in self.listeners:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.bind((rule['internal_ip'], port))
                    sock.listen(5)
                    self.listeners[port] = {'socket': sock, 'rule': rule}
                    threading.Thread(
                        target=self.start_listener, 
                        args=(sock, rule),
                        daemon=True
                    ).start()
                except:
                    pass

    def start_listener(self, listener, rule):
        while self.running:
            try:
                client, addr = listener.accept()
                dest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dest.connect((rule['external_ip'], rule['external_port']))
                
                with self.lock:
                    self.active_sockets[client] = (rule, dest)
                    
                threading.Thread(
                    target=self.transfer_data, 
                    args=(client, dest),
                    daemon=True
                ).start()
                threading.Thread(
                    target=self.transfer_data, 
                    args=(dest, client),
                    daemon=True
                ).start()
            except:
                break

    def transfer_data(self, source, target):
        while True:
            try:
                data = source.recv(4096)
                if not data:
                    break
                target.sendall(data)
            except:
                break
        try:
            source.close()
            target.close()
        except:
            pass
        with self.lock:
            if source in self.active_sockets:
                del self.active_sockets[source]

class RedirectorGUI:
    def __init__(self, engine):
        self.engine = engine
        self.root = tk.Tk()
        self.root.title("Port Redirector")
        self.editing_index = None
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(main_frame, columns=("Name", "InIP", "InPort", "OutIP", "OutPort"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        editor_frame = ttk.LabelFrame(main_frame, text="Rule Editor")
        editor_frame.pack(fill=tk.X, pady=10)
        
        self.fields = {
            'name': tk.Entry(editor_frame),
            'in_ip': tk.Entry(editor_frame),
            'in_port': tk.Entry(editor_frame),
            'out_ip': tk.Entry(editor_frame),
            'out_port': tk.Entry(editor_frame)
        }
        
        labels = ["Name", "Internal IP", "Internal Port", "External IP", "External Port"]
        for i, (key, field) in enumerate(self.fields.items()):
            ttk.Label(editor_frame, text=labels[i]).grid(row=i, column=0, sticky='w')
            field.grid(row=i, column=1, sticky='ew', padx=5)
        editor_frame.grid_columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="Save", command=self.save_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit", command=self.edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        self.start_btn = ttk.Button(control_frame, text="Start", command=self.start_service)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(control_frame, text="Stop", state=tk.DISABLED, command=self.stop_service)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_table()
        self.root.after(5000, self.auto_refresh)
    
    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, rule in enumerate(self.engine.config):
            self.tree.insert("", "end", values=(
                rule['name'],
                rule['internal_ip'],
                rule['internal_port'],
                rule['external_ip'],
                rule['external_port']
            ), tags=(idx,))
    
    def auto_refresh(self):
        self.refresh_table()
        self.root.after(5000, self.auto_refresh)
    
    def clear_fields(self):
        self.editing_index = None
        for field in self.fields.values():
            field.delete(0, tk.END)
    
    def save_rule(self):
        try:
            new_rule = {
                'name': self.fields['name'].get(),
                'internal_ip': self.fields['in_ip'].get(),
                'internal_port': int(self.fields['in_port'].get()),
                'external_ip': self.fields['out_ip'].get(),
                'external_port': int(self.fields['out_port'].get())
            }
            if self.editing_index is not None:
                self.engine.config[self.editing_index] = new_rule
            else:
                self.engine.config.append(new_rule)
            self.persist_config()
            self.engine.manage_ports()
            self.refresh_table()
            self.clear_fields()
        except ValueError:
            messagebox.showerror("Input Error", "Invalid port number")
    
    def delete_rule(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            idx = int(item['tags'][0])
            del self.engine.config[idx]
            self.persist_config()
            self.engine.manage_ports()
            self.refresh_table()
    
    def edit_rule(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            idx = int(item['tags'][0])
            rule = self.engine.config[idx]
            self.editing_index = idx
            self.fields['name'].delete(0, tk.END)
            self.fields['name'].insert(0, rule['name'])
            self.fields['in_ip'].delete(0, tk.END)
            self.fields['in_ip'].insert(0, rule['internal_ip'])
            self.fields['in_port'].delete(0, tk.END)
            self.fields['in_port'].insert(0, str(rule['internal_port']))
            self.fields['out_ip'].delete(0, tk.END)
            self.fields['out_ip'].insert(0, rule['external_ip'])
            self.fields['out_port'].delete(0, tk.END)
            self.fields['out_port'].insert(0, str(rule['external_port']))
    
    def persist_config(self):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.engine.config, f, indent=2)
    
    def start_service(self):
        self.engine.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.engine.manage_ports()
    
    def stop_service(self):
        self.engine.running = False
        self.stop_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.engine.manage_ports()

def main():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            json.dump([], f, indent=2)
            
    engine = RedirectorEngine()
    engine.load_config()
    
    gui = RedirectorGUI(engine)
    
    threading.Thread(
        target=lambda: [engine.load_config(), engine.manage_ports()] or time.sleep(1),
        daemon=True
    ).start()
    
    gui.root.mainloop()

if __name__ == "__main__":
    main()