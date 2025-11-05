import socket
import time

SLAVE_IP = "192.168.1.101"
SLAVE_PORT = 502
UNIT_ID = 1
FUNC_CODE = 0x02  # Read Discrete Inputs

# --- Poll groups: (Start Address, Quantity, Label) ---
poll_groups = [
    (0x0000, 40, "FIRE"),        # 40 fire inputs
    (0x0040, 40, "FAULT"),       # 40 fault inputs
    (0x0080, 40, "ISOLATE"),     # 40 isolate inputs
    (0x00C0, 8,  "COMMON"),      # 8 common signals

    # ✅ Optional custom polls
    (0x0003, 1, "CUSTOM_1"),     # Example custom poll (1 bit)
    (0x0008, 3, "CUSTOM_2"),     # Example custom poll (3 bits)
]


def build_modbus_request(tid, start_addr, quantity):
    """Builds a Modbus TCP request frame."""
    transaction_hi = (tid >> 8) & 0xFF
    transaction_lo = tid & 0xFF
    protocol_hi = 0
    protocol_lo = 0
    length_hi = 0
    length_lo = 6  # unit(1) + func(1) + start(2) + qty(2)
    unit_id = UNIT_ID

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
    """Formats bytes as hex string."""
    return " ".join(f"{b:02X}" for b in data)


def connect_slave():
    """Try to connect to the Modbus slave and return the socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    try:
        sock.connect((SLAVE_IP, SLAVE_PORT))
        print(f"✅ Connected to {SLAVE_IP}:{SLAVE_PORT}")
        return sock
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def main():
    tid = 0
    sock = connect_slave()
    if not sock:
        return

    try:
        while True:
            for start_addr, quantity, label in poll_groups:
                req = build_modbus_request(tid, start_addr, quantity)
                print(f"\n[{label}] Sending (TID={tid:04X}) Addr={start_addr:04X}, Qty={quantity}: {hexdump(req)}")

                try:
                    sock.sendall(req)
                    resp = sock.recv(260)
                    if resp:
                        print(f"[{label}] Received: {hexdump(resp)}")
                    else:
                        print(f"[{label}] ⚠ No response received.")
                except (socket.timeout, OSError) as e:
                    print(f"[{label}] ⚠ Communication error: {e}")
                    print("🔁 Reconnecting...")
                    sock.close()
                    time.sleep(2)
                    sock = connect_slave()
                    if not sock:
                        print("❌ Could not reconnect, exiting.")
                        return
                    continue

                tid = (tid + 1) & 0xFFFF
                time.sleep(1.0)  # 1s delay between polls

    finally:
        sock.close()
        print("🔌 Connection closed.")


if __name__ == "__main__":
    main()
