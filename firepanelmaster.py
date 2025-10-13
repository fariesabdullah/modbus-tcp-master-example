import socket
import time

SLAVE_IP = "192.168.1.101"
SLAVE_PORT = 502
UNIT_ID = 1
FUNC_CODE = 0x02

def build_modbus_request(tid):
    # MBAP header
    transaction_hi = (tid >> 8) & 0xFF
    transaction_lo = tid & 0xFF
    protocol_hi = 0
    protocol_lo = 0
    length_hi = 0
    length_lo = 6  # unit(1) + func(1) + start addr(2) + quantity(2)
    unit_id = UNIT_ID

    # PDU
    start_addr_hi = 0
    start_addr_lo = 0
    quantity_hi = 0
    quantity_lo = 0x80  # request 128 inputs (enough for 40+40+40+8 bits)

    packet = bytearray([
        transaction_hi, transaction_lo,
        protocol_hi, protocol_lo,
        length_hi, length_lo,
        unit_id,
        FUNC_CODE,
        start_addr_hi, start_addr_lo,
        quantity_hi, quantity_lo
    ])
    return packet

def hexdump(data):
    return " ".join(f"{b:02X}" for b in data)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)

    try:
        sock.connect((SLAVE_IP, SLAVE_PORT))
        print(f"Connected to {SLAVE_IP}:{SLAVE_PORT}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    tid = 0
    try:
        while True:
            req = build_modbus_request(tid)
            print(f"Sending (TID={tid:04X}): {hexdump(req)}")

            try:
                sock.sendall(req)
                resp = sock.recv(260)
                if resp:
                    print(f"Received: {hexdump(resp)}")
            except Exception as e:
                print(f"Communication error: {e}")
                break

            tid = (tid + 1) & 0xFF  # roll over at 0xFF back to 0x00
            time.sleep(1.0)

    finally:
        sock.close()
        print("Connection closed")

if __name__ == "__main__":
    main()
