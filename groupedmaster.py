import socket
import time

SLAVE_IP = "192.168.1.101"
SLAVE_PORT = 502
UNIT_ID = 1
FUNC_CODE = 0x02

# Define block requests (start_addr, quantity, label)
REQUEST_BLOCKS = [
    (0x0000, 40, "Fire"),     # Fire block
    (0x0028, 40, "Fault"),    # Fault block (40 decimal = 0x28)
    (0x0050, 40, "Isolate"),  # Isolate block (80 decimal = 0x50)
    (0x0078, 8,  "Common"),   # Common block (120 decimal = 0x78)
]

def build_modbus_request(tid, start_addr, quantity):
    # MBAP header
    transaction_hi = (tid >> 8) & 0xFF
    transaction_lo = tid & 0xFF
    protocol_hi = 0
    protocol_lo = 0
    length_hi = 0
    length_lo = 6  # unit(1) + func(1) + start addr(2) + quantity(2)
    unit_id = UNIT_ID

    # PDU
    start_addr_hi = (start_addr >> 8) & 0xFF
    start_addr_lo = start_addr & 0xFF
    quantity_hi = (quantity >> 8) & 0xFF
    quantity_lo = quantity & 0xFF

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
            for start_addr, quantity, label in REQUEST_BLOCKS:
                req = build_modbus_request(tid, start_addr, quantity)
                print(f"Sending {label} block (TID={tid:04X}): {hexdump(req)}")

                try:
                    sock.sendall(req)
                    resp = sock.recv(260)
                    if resp:
                        print(f"Received {label}: {hexdump(resp)}")
                except Exception as e:
                    print(f"Communication error: {e}")
                    sock.close()
                    return

                tid = (tid + 1) & 0xFFFF  # 16-bit transaction ID rollover
                time.sleep(1.0)

    finally:
        sock.close()
        print("Connection closed")

if __name__ == "__main__":
    main()
