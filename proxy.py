import socket
import sys
import os
import traceback
from multiprocessing import Process, Manager

buffer_size = 10000
max_conn = 10000


def read_blocked_sites():
    with open("blocked_sites.txt", "r") as file:
        return [line.strip() for line in file]

blocked_websites = read_blocked_sites()

def main():
    global listen_port
    try:
        listen_port = int(input("Enter a listening port: "))
    except KeyboardInterrupt:
        sys.exit(0)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", listen_port))
        s.listen(max_conn)
        print("[*] Initializing socket. Done.")
        print("[*] Socket binded successfully...")
        print("[*] Server started successfully [{}]".format(listen_port))
    except Exception as e:
        print(e)
        sys.exit(2)

    processes = []

    while True:
        try:
            conn, addr = s.accept()
            p = Process(target=conn_string, args=(conn, addr))
            p.start()
            processes.append(p)
        except KeyboardInterrupt:
            for p in processes:
                p.join()  # Wait for child processes to complete.
            s.close()
            print("\n[*] Shutting down...")
            sys.exit(1)
    s.close()

def conn_string(conn, addr):
    data = conn.recv(buffer_size)
    try:
        print(addr)
        first_line = data.decode('latin-1').split("\n")[0]
        print(first_line)
        url = first_line.split(" ")[1]
        print(url)
        
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]
            
        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int(temp[(port_pos + 1):][:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        print(webserver)
        proxy_server(webserver, port, conn, data, addr)
    except Exception as e:
        print(e)
        traceback.print_exc()

def proxy_server(webserver, port, conn, data, addr):
    print("{} {} {} {}".format(webserver, port, conn, addr))
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(data)
        
        first_line = data.decode('latin-1').split("\n")[0]
        url = first_line.split(" ")[1]
        
        for blocked_site in blocked_websites:
            if blocked_site in url:
                conn.send(b"HTTP/1.1 403 Forbidden\r\n\r\nWebsite blocked \n error 403")
                conn.close()
                return

        while True:
            reply = s.recv(4096)

            if len(reply) > 0:
                conn.send(reply)
                print("[*] Request sent: {} > {}".format(addr[0], webserver))
            else:
                break

        s.close()
        conn.close()

    except Exception as e:
        print(e)
        traceback.print_exc()
        s.close()
        conn.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
