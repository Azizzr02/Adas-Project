# Wiring Guide: Raspberry Pi MCP2515 + TJA1050 to STM32F407

## Your Current Hardware

### Raspberry Pi Side:
- **MCP2515** CAN Controller (SPI interface)
- **TJA1050** CAN Transceiver (integrated on module)
- Combined as single module with CANH and CANL outputs

### STM32 Side:
- **STM32F407VG** with built-in CAN controller
- **Requires external CAN transceiver** (TJA1050, MCP2551, SN65HVD230, etc.)
- CAN controller pins: PB8 (RX), PB9 (TX)

---

## Critical Issue: Do you have a CAN transceiver on the STM32?

**The STM32 CAN controller (PB8/PB9) outputs 3.3V logic signals, NOT CAN bus signals!**

You MUST have a CAN transceiver (like TJA1050 or MCP2551) between the STM32 and the CAN bus.

```
STM32 PB8/PB9 → CAN Transceiver → CANH/CANL → CAN Bus
              (3.3V logic)      (differential)
```

---

## Correct Wiring with CAN Transceivers on Both Sides

### Option 1: Both sides have transceivers (CORRECT)

```
┌─────────────────────────┐                    ┌─────────────────────────┐
│  Raspberry Pi           │                    │   STM32F407             │
│                         │                    │                         │
│  ┌────────────────┐     │                    │   ┌────────────────┐    │
│  │ MCP2515 Module │     │                    │   │ CAN Transceiver│    │
│  │ with TJA1050   │     │   Twisted Pair     │   │  (TJA1050 or   │    │
│  │                │     │                    │   │   MCP2551)     │    │
│  │  CANH ─────────┼─────┼───[120Ω]───●──────┼───┼─── CANH        │    │
│  │  CANL ─────────┼─────┼────────────●──────┼───┼─── CANL        │    │
│  │  GND  ─────────┼─────┼────────────●──────┼───┼─── GND         │    │
│  │                │     │            │      │   │                │    │
│  └────────────────┘     │          [120Ω]   │   │  RX ← PB8      │    │
│                         │                    │   │  TX ← PB9      │    │
└─────────────────────────┘                    │   └────────────────┘    │
                                               │                         │
                                               └─────────────────────────┘
```

### Wiring Table:

| Raspberry Pi MCP2515 | CAN Bus | STM32 Transceiver | STM32 Pin |
|----------------------|---------|-------------------|-----------|
| CANH | ←→ | CANH | (via transceiver) |
| CANL | ←→ | CANL | (via transceiver) |
| GND | ←→ | GND | GND |
| - | - | RX | PB8 |
| - | - | TX | PB9 |

---

## Option 2: If STM32 has NO transceiver (PROBLEM!)

**This will NOT work!** You cannot connect STM32 PB8/PB9 directly to CANH/CANL.

**Solution:** Add a TJA1050 or MCP2551 transceiver module to STM32.

---

## TJA1050 / MCP2551 Transceiver Pinout (for STM32)

### 8-Pin DIP or SOIC Package:

| Pin | Name | Connect To |
|-----|------|------------|
| 1 | TXD | STM32 PB9 (CAN1_TX) |
| 2 | GND | STM32 GND |
| 3 | VCC | STM32 3.3V or 5V (check datasheet) |
| 4 | RXD | STM32 PB8 (CAN1_RX) |
| 5 | VREF | Leave unconnected (optional reference) |
| 6 | CANL | CAN Bus Low (twisted pair) |
| 7 | CANH | CAN Bus High (twisted pair) |
| 8 | RS/STBY | Connect to GND (normal mode) or 3.3V (standby) |

**For TJA1050:** Pin 8 (S) should be connected to GND for high-speed mode.

---

## Physical Connection Checklist

### 1. CAN Bus Cable
- [ ] Use **twisted pair** cable (Cat5/Cat6 ethernet works well)
- [ ] One pair for CANH/CANL
- [ ] Keep length under 1 meter for 500kbps (for testing)
- [ ] Use separate wire for common ground

### 2. Termination Resistors
- [ ] **120Ω resistor** between CANH and CANL on Raspberry Pi side
- [ ] **120Ω resistor** between CANH and CANL on STM32 side
- [ ] Both resistors MUST be present

### 3. Ground Connection
- [ ] **Common ground wire** connecting Raspberry Pi GND to STM32 GND
- [ ] This is CRITICAL for proper communication
- [ ] Without common ground, CAN will NOT work

### 4. Power
- [ ] Raspberry Pi: 5V power supply
- [ ] STM32: 5V via USB or external
- [ ] MCP2515 module: Usually 5V (check your module)
- [ ] STM32 CAN transceiver: 3.3V or 5V (check datasheet)

---

## Testing Procedure

### Step 1: Verify Hardware
1. Check if STM32 has CAN transceiver installed
2. Verify CANH and CANL connections (not swapped)
3. Confirm both 120Ω termination resistors present
4. Ensure common ground wire connected

### Step 2: Test with Oscilloscope (if available)
- Check CANH and CANL for differential signals
- CANH should be ~3.5V idle, CANL should be ~1.5V idle
- During transmission, signals should swing opposite directions

### Step 3: Test with Multimeter
- Measure resistance between CANH and CANL: should be ~60Ω (two 120Ω in parallel)
- Check continuity of ground wire

### Step 4: Software Test
```bash
# On Raspberry Pi
ip link set can0 down
ip link set can0 type can bitrate 500000 restart-ms 100
ip link set can0 up

# Send test message
cansend can0 300#0A00

# Check statistics
ip -s link show can0
# Should show TX packets WITHOUT errors if STM32 is acknowledging
```

### Step 5: Monitor STM32
- Orange LED (PD13): Should blink every 500ms (firmware running)
- Green LED (PD12): Should toggle on each CAN message received

---

## Common Issues and Solutions

### Issue: TX errors, dropped packets, no RX
**Cause:** STM32 not acknowledging CAN messages

**Solutions:**
1. Verify STM32 has CAN transceiver (cannot work without it!)
2. Check CANH and CANL are not swapped
3. Verify both 120Ω termination resistors present
4. Ensure common ground connected
5. Check cable is twisted pair
6. Verify bitrate is 500kbps on both sides
7. Ensure STM32 firmware is flashed and running

### Issue: "bus-off" error on Raspberry Pi
**Cause:** Too many errors (no ACK from STM32)

**Solution:**
```bash
ip link set can0 down
ip link set can0 type can bitrate 500000 restart-ms 100
ip link set can0 up
```

### Issue: STM32 not receiving (Green LED not toggling)
**Possible causes:**
1. CAN transceiver not connected to STM32
2. Wrong pins (must be PB8 for RX, PB9 for TX)
3. Firmware not flashed with PB8/PB9 configuration
4. CAN filter misconfigured

---

## Quick Diagnosis

Run this command on Raspberry Pi after attempting to send messages:

```bash
ip -s -d link show can0
```

**If you see:**
- `TX: packets 0, errors > 0, dropped > 0` → STM32 not acknowledging
- `state ERROR-ACTIVE` → Normal, waiting for valid messages
- `state ERROR-PASSIVE` → High error count, check wiring
- `state BUS-OFF` → Too many errors, CAN disabled, need reset

---

## What to Check Right Now

**Please verify:**

1. **Does your STM32 have a CAN transceiver chip connected?**
   - Look for an 8-pin IC near the CAN connector
   - Common chips: TJA1050, MCP2551, SN65HVD230

2. **Are the termination resistors installed?**
   - 120Ω between CANH and CANL on both sides

3. **Is there a ground wire connecting Raspberry Pi to STM32?**
   - Not just through CAN bus, needs separate wire

4. **What color/thickness are your CAN bus wires?**
   - Should be twisted pair (like ethernet cable)

Let me know what you find, and I can help troubleshoot further!
