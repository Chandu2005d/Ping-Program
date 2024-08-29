import os
import socket
import struct
import select
import time
import sys

ICMP_ECHO_REQUEST = 8

def checksum(source_string):
    """
    A function to calculate the checksum of our packet.
    """
    count_to = (len(source_string) // 2) * 2
    sum = 0
    count = 0

    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + this_val
        sum = sum & 0xffffffff
        count = count + 2

    if count_to < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def create_packet(id):
    """
    Create a new echo request packet based on the given "id".
    """
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, id, 1)
    data = struct.pack("d", time.time())
    my_checksum = checksum(header + data)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), id, 1)
    return header + data

def do_one_ping(dest_addr, timeout):
    """
    Send one ping to the given "dest_addr" and return the delay.
    """
    icmp = socket.getprotobyname("icmp")
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error as e:
        print("Socket could not be created. Error Code : " + str(e[0]) + " Message " + e[1])
        sys.exit()

    my_id = os.getpid() & 0xFFFF
    packet = create_packet(my_id)
    my_socket.sendto(packet, (dest_addr, 1))
    delay = receive_one_ping(my_socket, my_id, timeout, dest_addr)

    my_socket.close()
    return delay

def receive_one_ping(my_socket, my_id, timeout, dest_addr):
    """
    Receive the ping from the socket.
    """
    time_left = timeout
    while True:
        started_select = time.time()
        what_ready = select.select([my_socket], [], [], time_left)
        how_long_in_select = (time.time() - started_select)
        if what_ready[0] == []:
            return "Request timed out."

        time_received = time.time()
        rec_packet, addr = my_socket.recvfrom(1024)

        icmp_header = rec_packet[20:28]
        type, code, checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)

        if packet_id == my_id:
            bytes_in_double = struct.calcsize("d")
            time_sent = struct.unpack("d", rec_packet[28:28 + bytes_in_double])[0]
            return time_received - time_sent

        time_left = time_left - how_long_in_select
        if time_left <= 0:
            return "Request timed out."

def ping(host, timeout=1):
    """
    Send a ping to the specified host.
    """
    dest = socket.gethostbyname(host)
    print(f"Pinging {dest} using Python:")
    print("")

    for i in range(4):
        delay = do_one_ping(dest, timeout)
        if isinstance(delay, float):
            print(f"64 bytes from {dest}: icmp_seq={i} ttl=55 time={delay*1000:.2f} ms")
        else:
            print(f"Request timed out for icmp_seq={i}")
        time.sleep(1)

def main():
    print("PING PROGRAM DEVELOPED BY CHANDU DISSANAYAKE")
    print("--------------------------------------------")
    while True:
        host = input("Enter the host name or IP address: ")
        ping(host)
        again = input("Do you want to ping again? (yes/no): ").strip().lower()
        if again != 'yes':
            print("Exiting the Ping program.")
            break

if __name__ == "__main__":
    main()