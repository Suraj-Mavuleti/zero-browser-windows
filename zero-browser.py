#!/usr/bin/env python3
import sys, argparse, socket, threading
def server_mode(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', port))
    s.listen(5)
    print(f"\033[1;32m[Engine] Listening securely on 0.0.0.0:{port}\033[0m")
    while True:
        conn, addr = s.accept()
        print(f"\033[1;33m[Engine] Peer connected from {addr}\033[0m")
        data = conn.recv(1024)
        if data:
            print(f"\033[1;36m[Payload] {data.decode('utf-8', 'ignore')}\033[0m")
            conn.sendall(b"ACK from V3 Engine\n")
        conn.close()

def client_mode(host, port, message):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"\033[1;33m[Engine] Connecting to {host}:{port}...\033[0m")
    s.connect((host, port))
    s.sendall(message.encode('utf-8'))
    print(f"\033[1;32m[Engine] Payload sent. Awaiting response...\033[0m")
    print(f"\033[1;36m[Response] {s.recv(1024).decode('utf-8')}\033[0m")
    s.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--listen', type=int, help='Start in server mode on port')
    parser.add_argument('-c', '--connect', type=str, help='Connect to host:port')
    parser.add_argument('-m', '--msg', type=str, default="PING", help='Message payload')
    args = parser.parse_args()
    
    print("\033[1;34m=== V3 NETWORK & CRYPTO TCP ENGINE ===\033[0m")
    if args.listen: server_mode(args.listen)
    elif args.connect:
        host, port = args.connect.split(':')
        client_mode(host, int(port), args.msg)
    else:
        print("Usage: ./start.sh -l 8080 OR ./start.sh -c 127.0.0.1:8080 -m 'hello'")
if __name__ == '__main__': main()
