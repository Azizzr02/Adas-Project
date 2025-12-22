# Complete Wiring Guide: Raspberry Pi + MCP2515 + TJA1050 ↔ STM32 + TJA1050

## Hardware Overview

### Raspberry Pi Side:
- **MCP2515 CAN Controller Module** (SPI interface)
- Built-in **TJA1050 CAN Transceiver**
- Pins: SI, SO, SCK, CS, INT, GND, VCC, CANH, CANL

### STM32 Side:
- **STM32F407VG Discovery Board**
- **TJA1050 CAN Transceiver Module**
- Pins: CANTX, CANRX, 3.3V, GND, CANH, CANL

---

## Part 1: Raspberry Pi GPIO to MCP2515 Module Wiring

### MCP2515 Module Connections

| MCP2515 Pin | Function | Connect To Raspberry Pi | Pi Pin Number | Pi GPIO |
|-------------|----------|-------------------------|---------------|---------|
| **VCC** | Power 5V | 5V Power | Pin 2 or 4 | 5V |
| **GND** | Ground | Ground | Pin 6, 9, 14, 20, 25, 30, 34, 39 | GND |
| **SI (MOSI)** | SPI Data Out | SPI0 MOSI | Pin 19 | GPIO10 |
| **SO (MISO)** | SPI Data In | SPI0 MISO | Pin 21 | GPIO9 |
| **SCK** | SPI Clock | SPI0 SCLK | Pin 23 | GPIO11 |
| **CS** | Chip Select | SPI0 CE0 | Pin 24 | GPIO8 |
| **INT** | Interrupt | GPIO Input | Pin 22 | GPIO25 |

### Raspberry Pi Pinout (40-pin header):
```
        3.3V  [ 1] [ 2]  5V  ← Connect VCC here
       GPIO2  [ 3] [ 4]  5V
       GPIO3  [ 5] [ 6]  GND ← Connect GND here
       GPIO4  [ 7] [ 8]  GPIO14
         GND  [ 9] [10]  GPIO15
      GPIO17  [11] [12]  GPIO18
      GPIO27  [13] [14]  GND
      GPIO22  [15] [16]  GPIO23
        3.3V  [17] [18]  GPIO24
GPIO10(MOSI)  [19] [20]  GND      ← SI connects to pin 19
 GPIO9(MISO)  [21] [22]  GPIO25   ← SO connects to pin 21, INT to pin 22
GPIO11(SCLK)  [23] [24]  GPIO8(CE0) ← SCK to pin 23, CS to pin 24
         GND  [25] [26]  GPIO7
       ...
```

### Wiring Summary - Raspberry Pi to MCP2515:
```
MCP2515 Module          Raspberry Pi 4
┌─────────────┐         ┌──────────────┐
│ VCC  ───────┼────────►│ Pin 2 (5V)   │
│ GND  ───────┼────────►│ Pin 6 (GND)  │
│ SI   ───────┼────────►│ Pin 19(GPIO10│ MOSI
│ SO   ───────┼────────►│ Pin 21(GPIO9)│ MISO
│ SCK  ───────┼────────►│ Pin 23(GPIO11│ SCLK
│ CS   ───────┼────────►│ Pin 24(GPIO8)│ CE0
│ INT  ───────┼────────►│ Pin 22(GPIO25│ Interrupt
│             │         └──────────────┘
│ CANH ───────┼──┐
│ CANL ───────┼──┼──► (To CAN Bus)
└─────────────┘  │
              [120Ω]
```

---

## Part 2: STM32 to TJA1050 Module Wiring

### STM32F407VG Pin Connections

| STM32 Pin | Function | Connect To TJA1050 | TJA1050 Pin |
|-----------|----------|-------------------|-------------|
| **PB9** | CAN1_TX | CANTX (TXD) | TX or TXD |
| **PB8** | CAN1_RX | CANRX (RXD) | RX or RXD |
| **3.3V** | Power | 3.3V or VCC | VCC (check module) |
| **GND** | Ground | GND | GND |

### TJA1050 Module Connections

| TJA1050 Pin | Function | Connect To |
|-------------|----------|------------|
| **VCC (3.3V)** | Power | STM32 3.3V pin |
| **GND** | Ground | STM32 GND pin |
| **CANTX (TXD)** | Transmit Data | STM32 PB9 |
| **CANRX (RXD)** | Receive Data | STM32 PB8 |
| **CANH** | CAN High | CAN Bus (twisted pair) |
| **CANL** | CAN Low | CAN Bus (twisted pair) |

**Note:** Some TJA1050 modules have a **RS/S pin** (standby/slope control):
- If present, connect to **GND** for high-speed mode
- If absent, module is already configured

### Wiring Summary - STM32 to TJA1050:
```
STM32F407VG Discovery        TJA1050 Module
┌──────────────────┐         ┌─────────────┐
│                  │         │             │
│ PB9 (CAN1_TX)────┼────────►│ CANTX (TXD) │
│ PB8 (CAN1_RX)────┼────────►│ CANRX (RXD) │
│ 3.3V      ───────┼────────►│ VCC (3.3V)  │
│ GND       ───────┼────────►│ GND         │
│                  │         │             │
│                  │         │ CANH ───────┼──┐
│                  │         │ CANL ───────┼──┼──► (To CAN Bus)
│                  │         └─────────────┘  │
│ PD13 (Orange LED)│ ← Blinks every 500ms  [120Ω]
│ PD12 (Green LED) │ ← Toggles on CAN RX
└──────────────────┘
```

---

## Part 3: CAN Bus Physical Connection

### Connecting MCP2515 to STM32 via CAN Bus

```
┌─────────────────────────────────────────────────────────────────┐
│                      CAN BUS CONNECTION                         │
└─────────────────────────────────────────────────────────────────┘

Raspberry Pi Side              CAN Bus Cable           STM32 Side
┌────────────────┐         ┌──────────────────┐      ┌────────────────┐
│  MCP2515       │         │  Twisted Pair    │      │  TJA1050       │
│  + TJA1050     │         │                  │      │  Module        │
│                │         │                  │      │                │
│  CANH ─────────┼─────────┼──● CANH (High)  ●┼──────┼─────── CANH   │
│  CANL ─────────┼─────────┼──● CANL (Low)   ●┼──────┼─────── CANL   │
│  GND  ─────────┼─────────┼──● Ground       ●┼──────┼─────── GND    │
│                │         │                  │      │                │
└────────────────┘         └──────────────────┘      └────────────────┘
       │                          │                          │
    [120Ω]                        │                       [120Ω]
  Termination                     │                    Termination
   Resistor                   Use Cat5/Cat6              Resistor
                             Ethernet Cable
                             (Twisted Pair)
```

### Cable Requirements:

1. **CANH to CANH:** Use one wire from a twisted pair (e.g., orange wire from Cat5)
2. **CANL to CANL:** Use the mate wire from the same twisted pair (e.g., orange-white from Cat5)
3. **GND to GND:** Use a separate wire for common ground (any color, e.g., blue from Cat5)
4. **Cable length:** Keep under 1 meter for initial testing (500 kbps supports up to 100m with proper cable)

### Termination Resistors:

**CRITICAL:** Both ends of the CAN bus MUST have 120Ω resistors.

**Raspberry Pi side:**
- Connect a 120Ω resistor between CANH and CANL on the MCP2515 module
- Some modules have this built-in (check documentation)
- If not built-in, solder or use screw terminals

**STM32 side:**
- Connect a 120Ω resistor between CANH and CANL on the TJA1050 module
- Can solder directly to the pins or use a breadboard

**To verify termination:**
- Use multimeter to measure resistance between CANH and CANL
- With both resistors: should read ~60Ω (two 120Ω in parallel)
- With only one: should read ~120Ω
- With neither: should read open circuit (infinite resistance)

---

## Complete Physical Wiring Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE SYSTEM WIRING                            │
└───────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐                    ┌─────────────────────────┐
│   RASPBERRY PI 4        │                    │    STM32F407VG          │
│   ┌─────────────────┐   │                    │    ┌────────────────┐   │
│   │   40-Pin GPIO   │   │                    │    │                │   │
│   │                 │   │                    │    │  PB9 (CAN_TX)  │   │
│   │ Pin 2  (5V)  ───┼───┼──┐                 │    │  PB8 (CAN_RX)  │   │
│   │ Pin 6  (GND) ───┼───┼──┼────┐            │    │  3.3V          │   │
│   │ Pin 19 (MOSI)───┼───┼──┼──┐ │            │    │  GND           │   │
│   │ Pin 21 (MISO)───┼───┼──┼┐ │ │            │    │                │   │
│   │ Pin 23 (SCLK)───┼───┼──┼┼─┼─┼─┐          │    │  PD12 Green●   │   │
│   │ Pin 24 (CE0) ───┼───┼──┼┼─┼─┼─┼─┐        │    │  PD13 Orange●  │   │
│   │ Pin 22 (GPIO25)─┼───┼──┼┼─┼─┼─┼─┼─┐      │    └────────┬───────┘   │
│   └─────────────────┘   │  │ ││ │ │ │ │ │    │             │           │
│                         │  │ ││ │ │ │ │ │    │             ▼           │
│   ┌─────────────────┐   │  │ ││ │ │ │ │ │    │    ┌────────────────┐   │
│   │  MCP2515 Module │   │  │ ││ │ │ │ │ │    │    │  TJA1050 Module│   │
│   │  with TJA1050   │   │  │ ││ │ │ │ │ │    │    │                │   │
│   │  VCC  ◄──────────────┘  │ ││ │ │ │ │    │    │  VCC  ◄────────┼───┼─ 3.3V
│   │  GND  ◄─────────────────┘ ││ │ │ │ │    │    │  GND  ◄────────┼───┼─ GND
│   │  SI   ◄───────────────────┘│ │ │ │ │    │    │  CANTX◄────────┼───┼─ PB9
│   │  SO   ◄────────────────────┘ │ │ │ │    │    │  CANRX◄────────┼───┼─ PB8
│   │  SCK  ◄──────────────────────┘ │ │ │    │    │                │   │
│   │  CS   ◄────────────────────────┘ │ │    │    │  CANH ─────────┼───┼──┐
│   │  INT  ◄──────────────────────────┘ │    │    │  CANL ─────────┼───┼──┼──┐
│   │                 │   │               │    │    └────────────────┘   │  │  │
│   │  CANH ──────────┼───┼───────────────┼────┼───────────────────────── ┼──┘  │
│   │  CANL ──────────┼───┼───────────────┼────┼──────────────────────────┘     │
│   │                 │   │               │    │                                 │
│   │     [120Ω]      │   │               │    │                       [120Ω]   │
│   │                 │   │               │    │                                 │
│   └─────────────────┘   │               │    └─────────────────────────────────┘
│                         │               │
│  GND ───────────────────┼───────────────┼────────────────────────── GND
│                         │               │          Common Ground
└─────────────────────────┘               └─────────────────────────────────────┘

         5V Power Supply                         5V/USB Power
```

---

## Step-by-Step Wiring Instructions

### Step 1: Wire Raspberry Pi to MCP2515 (SPI + Power)

**Use dupont wires (female-to-female recommended):**

1. **Power:**
   - MCP2515 **VCC** → Raspberry Pi Pin 2 (5V) - RED wire
   - MCP2515 **GND** → Raspberry Pi Pin 6 (GND) - BLACK wire

2. **SPI Communication:**
   - MCP2515 **SI (MOSI)** → Raspberry Pi Pin 19 (GPIO10) - YELLOW wire
   - MCP2515 **SO (MISO)** → Raspberry Pi Pin 21 (GPIO9) - BLUE wire
   - MCP2515 **SCK** → Raspberry Pi Pin 23 (GPIO11) - GREEN wire
   - MCP2515 **CS** → Raspberry Pi Pin 24 (GPIO8) - ORANGE wire
   - MCP2515 **INT** → Raspberry Pi Pin 22 (GPIO25) - WHITE wire

### Step 2: Wire STM32 to TJA1050 (CAN + Power)

**Use dupont wires:**

1. **Power:**
   - TJA1050 **VCC** → STM32 **3.3V** pin - RED wire
   - TJA1050 **GND** → STM32 **GND** pin - BLACK wire

2. **CAN Signals:**
   - TJA1050 **CANTX** → STM32 **PB9** - YELLOW wire
   - TJA1050 **CANRX** → STM32 **PB8** - GREEN wire

3. **If TJA1050 has RS/S pin:**
   - Connect **RS/S** → **GND** (for high-speed mode)

### Step 3: Connect CAN Bus (CANH, CANL, GND)

**Use Cat5/Cat6 Ethernet cable (has twisted pairs):**

1. **Cut and strip ethernet cable** (about 1 meter)
2. **Identify a twisted pair** (e.g., Orange + Orange-White)
3. **Wire connections:**
   - MCP2515 **CANH** → (Orange wire) → TJA1050 **CANH**
   - MCP2515 **CANL** → (Orange-White wire) → TJA1050 **CANL**
   - Raspberry Pi **GND** → (Blue wire) → STM32 **GND** (common ground)

### Step 4: Add Termination Resistors

**On MCP2515 side:**
- Solder or connect **120Ω resistor** between **CANH** and **CANL** pins
- Or check if module has built-in termination jumper

**On TJA1050 side:**
- Solder or connect **120Ω resistor** between **CANH** and **CANL** pins

---

## Verification Checklist

Before powering on, verify:

- [ ] **Raspberry Pi to MCP2515:** All 7 wires connected (VCC, GND, SI, SO, SCK, CS, INT)
- [ ] **STM32 to TJA1050:** All 4 wires connected (VCC, GND, CANTX, CANRX)
- [ ] **CAN Bus:** CANH to CANH, CANL to CANL (not crossed!)
- [ ] **Common Ground:** Raspberry Pi GND connected to STM32 GND
- [ ] **Termination:** 120Ω resistor on both sides
- [ ] **Power:** Raspberry Pi has 5V supply, STM32 has USB or 5V power
- [ ] **No shorts:** Check with multimeter that CANH and CANL are not shorted to GND

---

## Testing Procedure

### 1. Power On and Check LEDs

**STM32:**
- Orange LED (PD13) should start blinking every 500ms
- If not blinking: firmware not running or not flashed

**Raspberry Pi:**
- Should boot normally
- MCP2515 module may have power LED

### 2. Configure CAN on Raspberry Pi

```bash
ssh root@192.168.0.109

# Check if SPI is enabled
ls /dev/spi* 
# Should see: /dev/spidev0.0

# Check if MCP2515 is detected
dmesg | grep mcp
# Should see: "mcp251x spi0.0 can0: MCP2515 successfully initialized"

# Configure CAN interface
ip link set can0 down
ip link set can0 type can bitrate 500000 restart-ms 100
ip link set can0 up

# Verify interface is up
ip -details link show can0
# Should show: "state UP" and "bitrate 500000"
```

### 3. Send Test Messages

```bash
# Send single message
cansend can0 300#1400

# Check if STM32 acknowledged (green LED should toggle)
ip -s link show can0
```

**Expected result:**
- **TX packets:** Should increment (not stay at 0)
- **TX errors:** Should stay at 0 (if STM32 acknowledges)
- **STM32 Green LED (PD12):** Should toggle on each message

### 4. Continuous Test

```bash
# Send 10 messages with delays
for i in {1..10}; do 
  cansend can0 300#$(printf '%02X00' $i)
  echo "Message $i sent"
  sleep 0.3
done

# Check statistics
ip -s link show can0
```

---

## Troubleshooting Guide

### Issue: MCP2515 not detected on Raspberry Pi

**Check:**
```bash
# Enable SPI in raspi-config
sudo raspi-config
# Interface Options → SPI → Enable

# Check device tree overlay
cat /boot/config.txt | grep mcp2515

# Should have line like:
# dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
```

**If missing, add:**
```bash
sudo nano /boot/config.txt

# Add this line:
dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25,spimaxfrequency=2000000

# Save and reboot
sudo reboot
```

### Issue: CAN interface won't come up

```bash
# Check kernel messages
dmesg | tail -30

# Look for errors like:
# "mcp251x spi0.0: Cannot initialize MCP2515"
# "mcp251x spi0.0: Probe failed"
```

**Solutions:**
- Check SPI wiring (especially CS and INT pins)
- Verify 5V power to MCP2515
- Check oscillator frequency (8MHz is common)

### Issue: TX errors, STM32 not acknowledging

**Symptoms:**
```bash
ip -s link show can0
# Shows: TX errors > 0, dropped > 0
```

**Check:**
1. **Common ground:** Measure continuity between Raspberry Pi GND and STM32 GND
2. **Termination:** Measure resistance between CANH and CANL (should be ~60Ω)
3. **Wiring:** Verify CANH↔CANH and CANL↔CANL (not swapped)
4. **STM32 firmware:** Check orange LED is blinking (firmware running)
5. **TJA1050 power:** Verify 3.3V on VCC pin

### Issue: Green LED on STM32 not toggling

**Possible causes:**
1. STM32 CAN not initialized properly
2. Wrong pins (must be PB8/PB9)
3. CAN filter blocking messages
4. Firmware not flashed with PB8/PB9 configuration

**Test:**
- Re-flash STM32 firmware
- Check with logic analyzer or oscilloscope on PB8/PB9

---

## Quick Reference

### Important Pins:

**Raspberry Pi:**
- Pin 2: 5V
- Pin 6: GND
- Pin 19: MOSI (SI)
- Pin 21: MISO (SO)
- Pin 23: SCLK
- Pin 24: CE0 (CS)
- Pin 22: GPIO25 (INT)

**STM32:**
- PB8: CAN1_RX
- PB9: CAN1_TX
- PD12: Green LED (CAN RX indicator)
- PD13: Orange LED (Heartbeat)

**CAN Bus:**
- Bitrate: 500 kbps
- Termination: 120Ω at both ends
- Cable: Twisted pair

### CAN Message IDs:
- 0x100: Lane offset
- 0x200: Distance
- 0x300: Motor speed

---

**Document Created:** December 20, 2025
**Hardware:** Raspberry Pi 4 + MCP2515 + TJA1050 ↔ STM32F407VG + TJA1050
