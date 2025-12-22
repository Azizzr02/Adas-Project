# CRITICAL: Common Ground Wiring for CAN Bus Communication

## The Golden Rule: ALL GROUNDS MUST BE CONNECTED TOGETHER

This is the #1 reason why CAN communication fails!

---

## Why Common Ground is Critical

CAN is a **differential signal protocol**. It measures the voltage **difference** between CANH and CANL.

```
CANH voltage - CANL voltage = CAN signal

Example:
CANH = 3.5V, CANL = 1.5V → Difference = 2.0V (valid CAN signal)
```

If grounds are not connected:
- Each device has a different ground reference
- The differential signal measurement is wrong
- Receiver sees garbage
- CAN communication fails completely

---

## Correct Common Ground Wiring

### All Four Devices Must Share ONE Ground Reference:

```
┌──────────────────────────────────────────────────────────┐
│                    COMMON GROUND (Star Point)            │
└──────────────────────────────────────────────────────────┘
              │        │        │        │
              ▼        ▼        ▼        ▼
        ┌─────────┬─────────┬─────────┬─────────┐
        │         │         │         │         │
     Raspberry   MCP2515   TJA1050   STM32    Power
        Pi       Module    Module    GND      Supply
       GND        GND       GND              GND
```

### Detailed Wiring:

**Use a common ground junction (star point):**

1. **Raspberry Pi GND pin** → Common Ground Wire
2. **MCP2515 Module GND** → Common Ground Wire
3. **TJA1050 Module GND** → Common Ground Wire
4. **STM32 GND pin** → Common Ground Wire
5. **Power Supply GND** → Common Ground Wire (if external)

---

## Step-by-Step Ground Wiring

### Option 1: Soldered Star Point (BEST)

1. Strip all four GND wires (or more)
2. Twist them together tightly
3. Solder all together at one point
4. Shrink wrap with heat shrink tubing
5. Connect to chassis ground or main GND rail

```
        Raspberry Pi GND ─┐
                          ├─► [Solder Joint] ◄─ Main GND Rail
        MCP2515 GND ──────┤
                          ├─► To all devices
        TJA1050 GND ──────┤
                          │
        STM32 GND ────────┘
```

### Option 2: Using Breadboard or Terminal Block

1. Connect all GND wires to same row on breadboard
2. Or use a terminal block/rail with multiple connectors

```
Terminal Block:
┌──────────────────────┐
│ GND Rail             │
├──────────────────────┤
│ Raspberry Pi GND ──► ●
│ MCP2515 GND ──────► ●
│ TJA1050 GND ──────► ●
│ STM32 GND ──────── ●
│ Power Supply GND ─► ●
└──────────────────────┘
```

---

## Complete Wiring With Common Ground

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  CORRECT COMMON GROUND WIRING                           │
└─────────────────────────────────────────────────────────────────────────┘

                           ★ COMMON GROUND ★
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Raspberry Pi │ │  MCP2515+    │ │  STM32 +     │
        │      4       │ │  TJA1050     │ │  TJA1050     │
        │              │ │              │ │              │
        │ Pin 6 ──GND──┼─┤ GND ─────────┤─┤ GND          │
        │ Pin 2 ─5V┐   │ │              │ │              │
        │          │   │ │ VCC ◄───5V───┤ │ VCC ◄───3.3V │
        │ SPI pins ├───┤ │              │ │              │
        │ SCK,    │   │ │ SI/SO/SCK/CS  │ │ CANTX ◄──┐   │
        │ MOSI,   └───┤ │ (SPI interface)│ │ CANRX ◄──┤   │
        │ MISO,CS,INT │ │              │ │          │   │
        │              │ │ CANH ────────┼─┼──────┐  │   │
        │              │ │ CANL ────────┼─┼──┐   │  │   │
        └──────────────┘ │              │ │  │   │  │   │
                         └──────────────┘ │  │   │  │   │
                                          │  │   │  │   │
                         [120Ω Termination]  │   │  │   │
                              Resistor     │   │  │   │
                                    ●──────┘   │  │   │
                                          ●────┘  │   │
                                                  │   │
                         ┌──────────────────────┬─┘   │
                         │                      │     │
                         ▼                      ▼     ▼
                    CAN Bus to STM32      CAN Bus
                    (PB8/PB9 through      Physical
                     TJA1050)             Connection
```

---

## Verification Checklist

**Before powering on, verify:**

- [ ] **Raspberry Pi GND** connected to common ground
- [ ] **MCP2515 GND** connected to common ground
- [ ] **TJA1050 GND** connected to common ground
- [ ] **STM32 GND** connected to common ground
- [ ] All ground connections are **soldered or crimped** (not just touching)
- [ ] Ground wire is **low resistance** (measure with multimeter: should be < 0.1Ω)
- [ ] No breaks or loose connections in ground path

---

## Testing Common Ground

### With Multimeter:

**Continuity Test (Ohm Mode):**
1. Turn everything OFF
2. Set multimeter to resistance/ohm mode (Ω)
3. Touch probes to different GND points
4. Should read **0Ω** (or very close, < 0.1Ω)

**Test all combinations:**
- Raspberry Pi GND ↔ MCP2515 GND: **0Ω** ✓
- Raspberry Pi GND ↔ TJA1050 GND: **0Ω** ✓
- Raspberry Pi GND ↔ STM32 GND: **0Ω** ✓
- MCP2515 GND ↔ TJA1050 GND: **0Ω** ✓
- MCP2515 GND ↔ STM32 GND: **0Ω** ✓
- TJA1050 GND ↔ STM32 GND: **0Ω** ✓

If any reading is **not 0Ω**, there's a break in the ground connection!

---

## Why This Fixes CAN Communication

**Without common ground:**
- Each device thinks GND is at different voltage level
- CAN differential signal measurement is incorrect
- Receiver interprets data as noise/errors
- Result: 1,368,672 RX errors (like you're seeing!)

**With proper common ground:**
- All devices reference same GND = 0V
- CAN differential signal is measured correctly
- Receiver gets clean, valid CAN signals
- Result: Clean CAN communication, 0 errors

---

## Common Ground Mistakes to Avoid

❌ **WRONG:**
- Only connecting GND through CAN bus (CANL is NOT a substitute for GND!)
- Different GND wires for different devices
- Long, thin GND wires (use thick wire, short paths)
- GND connections through a connector with bad contact

✓ **CORRECT:**
- Dedicated GND wire from all devices to common point
- Star topology (all connect to one junction)
- Thick, short GND wires (low resistance)
- Soldered or crimped connections (not loose wires)

---

## Quick Diagnosis

If you're seeing:
- **High RX errors:** Almost certainly missing or bad common ground
- **TX errors:** Could be common ground OR termination resistors
- **"bus-off" errors:** Typically common ground issue
- **Garbage data received:** 100% common ground problem

The fact that you have **1,368,672 RX errors** strongly suggests **no common ground or very poor ground connection**.

---

## Action Items

**Right Now:**

1. **Check if common ground wire exists** between Raspberry Pi and STM32
2. **If NO ground wire:** Solder/crimp one immediately
3. **If ground wire exists:** Test with multimeter for continuity (should be 0Ω)
4. **Measure resistance between CANH and CANL:** Should be ~60Ω (if both 120Ω termination resistors present)

**Then test:**
```bash
# On Raspberry Pi
ip link set can0 down
ip link set can0 type can bitrate 500000 restart-ms 100
ip link set can0 up
cansend can0 300#0A00
ip -s link show can0
```

**Expected result after fixing ground:**
- TX packets: 1 (or more)
- TX errors: 0 (or very low)
- RX errors: Should drop dramatically (not in millions!)

---

**Last Updated:** December 20, 2025
**Most Common Cause of CAN Failures:** Missing or bad common ground (I'd say 80% of problems!)
