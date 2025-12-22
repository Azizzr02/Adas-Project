# ADAS Motor Control - Complete Hardware Wiring Guide

## System Overview
- **Raspberry Pi** → CAN Bus → **STM32F407VG Discovery** → **XXD 40A ESC** → **A2212 Brushless Motor**

---

## 1. STM32F407VG Discovery Board Pin Configuration

### CAN Bus Interface (Communication)
| STM32 Pin | Function | Connect To |
|-----------|----------|------------|
| **PB8**   | CAN1_RX  | CAN Transceiver RX pin |
| **PB9**   | CAN1_TX  | CAN Transceiver TX pin |

### PWM Output (Motor Control)
| STM32 Pin | Function | Connect To |
|-----------|----------|------------|
| **PB6**   | TIM4_CH1 (PWM) | ESC Signal Wire (White/Yellow) |

### Status LEDs (Already on Discovery Board)
| STM32 Pin | Function | Description |
|-----------|----------|-------------|
| **PD12**  | LED_GREEN  | Toggles on every CAN message received |
| **PD13**  | LED_ORANGE | Heartbeat (blinks every 500ms) |

### Power
| STM32 Pin | Function | Connect To |
|-----------|----------|------------|
| **5V**    | Power Input | 5V supply or USB |
| **GND**   | Ground | Common ground with all devices |

---

## 2. CAN Transceiver Wiring (Both Sides)

### STM32 Side - CAN Transceiver (e.g., MCP2551, SN65HVD230, TJA1050)

| CAN Transceiver Pin | Connect To |
|---------------------|------------|
| **VCC**             | STM32 3.3V or 5V (check transceiver datasheet) |
| **GND**             | STM32 GND |
| **TX (TXD)**        | STM32 PB9 (CAN1_TX) |
| **RX (RXD)**        | STM32 PB8 (CAN1_RX) |
| **CANH**            | CAN Bus High (twisted pair cable) |
| **CANL**            | CAN Bus Low (twisted pair cable) |

### Raspberry Pi Side - CAN Controller (e.g., MCP2515 with TJA1050)

#### MCP2515 CAN Controller Module
| MCP2515 Pin | Connect To Raspberry Pi |
|-------------|-------------------------|
| **VCC**     | Pin 2 (5V) or Pin 1 (3.3V) - check module |
| **GND**     | Pin 6, 9, 14, 20, 25, 30, 34, or 39 (GND) |
| **SCK**     | Pin 23 (GPIO 11 - SPI0 SCLK) |
| **MOSI**    | Pin 19 (GPIO 10 - SPI0 MOSI) |
| **MISO**    | Pin 21 (GPIO 9 - SPI0 MISO) |
| **CS**      | Pin 24 (GPIO 8 - SPI0 CE0) |
| **INT**     | Pin 22 (GPIO 25) - Interrupt |

#### CAN Bus Physical Connection
| Pin | Connect To |
|-----|------------|
| **CANH** | CAN Bus High (connect to STM32 CANH via twisted pair) |
| **CANL** | CAN Bus Low (connect to STM32 CANL via twisted pair) |

---

## 3. CAN Bus Physical Layer

### Wiring Between Raspberry Pi and STM32

```
Raspberry Pi CAN Transceiver          STM32 CAN Transceiver
    [CANH] -----(Twisted Pair)------- [CANH]
    [CANL] -----(Twisted Pair)------- [CANL]
    [GND]  ----------(Wire)----------- [GND]
```

### Critical Requirements:
1. **Use twisted pair cable** for CANH and CANL (Cat5/Cat6 cable works well)
2. **Keep cable length under 40cm for 500kbps** (or use proper CAN-rated cable for longer distances)
3. **120Ω termination resistors** at BOTH ends of the bus:
   - Connect 120Ω resistor between CANH and CANL on Raspberry Pi side
   - Connect 120Ω resistor between CANH and CANL on STM32 side
4. **Common ground** between Raspberry Pi and STM32 is ESSENTIAL

### Termination Resistor Placement:
```
[RPI CAN]--[120Ω]--[CANH]========[CANH]--[120Ω]--[STM32 CAN]
                   [CANL]========[CANL]
```

---

## 4. ESC (Electronic Speed Controller) Wiring

### XXD 40A ESC Connections

#### Power Connections (High Current)
| ESC Wire | Color | Connect To |
|----------|-------|------------|
| **Battery +** | Red (Thick) | LiPo Battery Positive (11.1V or 14.8V 3S/4S) |
| **Battery -** | Black (Thick) | LiPo Battery Negative (GND) |

#### Motor Connections (3-Phase)
| ESC Wire | Color | Connect To |
|----------|-------|------------|
| **Motor Phase A** | Yellow/Blue | A2212 Motor Wire 1 |
| **Motor Phase B** | Yellow/Blue | A2212 Motor Wire 2 |
| **Motor Phase C** | Yellow/Blue | A2212 Motor Wire 3 |

**Note:** If motor spins in wrong direction, swap any two motor wires.

#### Signal/Control Connections (Low Current)
| ESC Wire | Color | Connect To |
|----------|-------|------------|
| **Signal (PWM)** | White/Yellow | STM32 PB6 (TIM4_CH1) |
| **5V BEC Output** | Red (Thin) | Optional: Can power STM32 5V pin |
| **Ground** | Black/Brown (Thin) | STM32 GND (MUST be connected) |

---

## 5. A2212 Brushless Motor

### Motor Specifications
- Type: Outrunner brushless motor
- KV Rating: ~1000 KV (RPM per volt)
- Voltage: 11.1V (3S LiPo) or 14.8V (4S LiPo)
- 3 wires connect to ESC (order doesn't matter, can swap for direction)

### Motor Wiring
| Motor | Connect To |
|-------|------------|
| Wire 1 | ESC Phase A |
| Wire 2 | ESC Phase B |
| Wire 3 | ESC Phase C |

---

## 6. Power Supply Setup

### Power Distribution
```
┌─────────────┐
│ LiPo Battery│ (11.1V or 14.8V)
│  3S or 4S   │
└──────┬──────┘
       │
       ├──────────► ESC (Red/Black thick wires)
       │
       │            ESC 5V BEC Output (5V regulated)
       │            ├──────────► STM32 5V pin (optional)
       │            └──────────► Servos/other 5V devices
       │
       └─► Voltage Regulator (if needed)
           └──────────► Raspberry Pi 5V input
```

### Important Power Notes:
1. **Never connect LiPo directly to Raspberry Pi or STM32** (they need 5V, battery is 11-15V)
2. **ESC BEC Output** provides 5V and can power STM32 (check current rating)
3. **Common ground** must connect: Battery GND → ESC GND → STM32 GND → Raspberry Pi GND
4. **Raspberry Pi** needs separate 5V power supply (5V 3A recommended)

---

## 7. Complete System Wiring Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 4                             │
│  ┌────────────┐    ┌──────────────────┐                     │
│  │   Camera   │    │  MCP2515 Module  │                     │
│  │  Module    │───►│  (SPI CAN)       │                     │
│  └────────────┘    │  CANH ──┐        │                     │
│                    │  CANL ──┼────┐   │                     │
│                    └─────────┼────┼───┘                     │
│                              │    │                          │
│  [GND]──────────────────────┼────┼──────────────┐          │
└──────────────────────────────┼────┼──────────────┼──────────┘
                               │    │              │
                            [120Ω]  │              │
                               │    │              │
      CAN Bus (Twisted Pair)   │    │              │
      ═════════════════════════╪════╪══════════    │
                               │    │              │
                            [120Ω]  │              │
                               │    │              │
┌──────────────────────────────┼────┼──────────────┼──────────┐
│              STM32F407VG DISCOVERY BOARD                     │
│                              │    │              │           │
│  ┌──────────────────┐        │    │              │           │
│  │  CAN Transceiver │        │    │              │           │
│  │   (MCP2551 or    │        │    │              │           │
│  │    SN65HVD230)   │        │    │              │           │
│  │                  │        │    │              │           │
│  │  RX ◄─── PB8     │        │    │              │           │
│  │  TX ───► PB9     │        │    │              │           │
│  │  CANH ───────────┘        │              Common Ground    │
│  │  CANL ────────────────────┘                   │           │
│  └──────────────────┘                            │           │
│                                                   │           │
│  PB6 (TIM4_CH1 PWM) ──────────────────┐          │           │
│                                        │          │           │
│  PD12 (Green LED)  ●  Blinks on CAN RX│          │           │
│  PD13 (Orange LED) ●  Heartbeat 500ms │          │           │
│                                        │          │           │
│  GND ──────────────────────────────────┼──────────┘           │
└────────────────────────────────────────┼────────────────────── ┘
                                         │
                                         │ Signal Wire
                                         │ Ground Wire
                                         ▼
┌────────────────────────────────────────────────────────────┐
│                   XXD 40A ESC                              │
│                                                            │
│  Signal Input (White) ◄── PWM from PB6                   │
│  GND (Black/Brown)    ◄── STM32 GND                      │
│  5V BEC (Red thin)    ──► Optional: STM32 5V             │
│                                                            │
│  Battery + (Red thick)    ◄── LiPo Battery (+) 11-15V    │
│  Battery - (Black thick)  ◄── LiPo Battery (-) GND       │
│                                                            │
│  Motor A (Yellow) ──┐                                     │
│  Motor B (Yellow) ──┼──► To A2212 Brushless Motor        │
│  Motor C (Yellow) ──┘                                     │
└────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   A2212 Motor         │
              │   Brushless Outrunner │
              │   with Propeller      │
              └───────────────────────┘
```

---

## 8. Troubleshooting Checklist

### CAN Bus Not Working
- [ ] Check CANH and CANL are connected (not swapped)
- [ ] Verify 120Ω termination resistors at BOTH ends
- [ ] Confirm common ground between Raspberry Pi and STM32
- [ ] Check twisted pair cable quality and length
- [ ] Verify both sides configured for 500 kbps
- [ ] Test with `candump can0` on Raspberry Pi
- [ ] Check if green LED (PD12) toggles on STM32 when message sent

### Motor Not Responding
- [ ] ESC properly powered from LiPo battery
- [ ] ESC signal wire connected to STM32 PB6
- [ ] ESC ground connected to STM32 ground
- [ ] ESC calibration done (firmware does this on boot)
- [ ] Motor wires connected to all 3 ESC outputs
- [ ] Check if orange LED (PD13) is blinking (firmware running)

### Power Issues
- [ ] LiPo battery charged (check voltage: 3S = 11.1V nominal, 4S = 14.8V)
- [ ] All grounds connected together (common ground)
- [ ] Raspberry Pi has separate 5V power supply
- [ ] STM32 powered via USB or ESC BEC (5V)
- [ ] Check for loose connections

---

## 9. Safety Warnings

⚠️ **IMPORTANT SAFETY PRECAUTIONS:**

1. **Remove propeller** during initial testing and development
2. **Secure the vehicle** before testing with propeller attached
3. **LiPo battery safety:**
   - Never discharge below 3.0V per cell
   - Use fireproof LiPo charging bag
   - Never leave charging unattended
   - Store at storage voltage (3.8V per cell)
4. **ESC arming:** Motor will spin after ESC arms (2-3 seconds after power-on)
5. **Emergency stop:** Keep power disconnect readily accessible
6. **Eye protection** recommended when testing with propeller

---

## 10. Testing Procedure

### Step 1: Test Power
1. Connect LiPo to ESC
2. ESC should beep
3. STM32 orange LED should start blinking

### Step 2: Test CAN Communication
1. Power on Raspberry Pi and configure CAN
2. Send test message: `cansend can0 300#1400`
3. STM32 green LED should toggle
4. Check with: `ip -s link show can0` (should show TX packets, not errors)

### Step 3: Test Motor (WITHOUT PROPELLER)
1. Send motor command: `cansend can0 300#0A00` (10%)
2. Motor should spin slowly
3. Stop: `cansend can0 300#0000`

### Step 4: Full System Test
1. Verify all LEDs working
2. Test range of speeds (0-85%)
3. Monitor CAN bus traffic
4. Check for error messages

---

## Pin Summary Table

| Function | STM32 Pin | Connected To | Notes |
|----------|-----------|--------------|-------|
| CAN RX | PB8 | CAN Transceiver RX | With pull-up |
| CAN TX | PB9 | CAN Transceiver TX | Push-pull |
| PWM Motor | PB6 | ESC Signal Wire | 50Hz, 1-2ms pulses |
| Green LED | PD12 | On-board LED | Toggles on CAN RX |
| Orange LED | PD13 | On-board LED | Heartbeat 500ms |
| Ground | GND | Common ground | Critical! |
| Power | 5V | USB or ESC BEC | 5V input |

---

## Additional Notes

- **CAN Bitrate:** 500 kbps on both Raspberry Pi and STM32
- **PWM Frequency:** 50 Hz (standard for ESCs)
- **PWM Range:** 1ms (0%) to 2ms (100%)
- **Safety Limit:** Speed capped at 85% in firmware
- **CAN IDs:**
  - 0x100: Lane offset (future steering)
  - 0x200: Distance measurement
  - 0x300: Motor speed command

---

**Last Updated:** December 20, 2025
**Firmware Version:** Compatible with current STM32 code (PB8/PB9 CAN pins)
