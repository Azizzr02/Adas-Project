Real‑Time ADAS with CAN Communication and Motor Control
=====================================================

Short overview
--------------
This project demonstrates an end-to-end Advanced Driver Assistance System (ADAS) that integrates computer vision inference (YOLOP), embedded Linux (Yocto) with CAN support, a Raspberry Pi CAN gateway, and an STM32-based real-time motor controller. The system implements autonomous emergency braking by mapping vision-derived distance measurements to motor PWM commands sent over a CAN bus.Check this link for a video Description : https://www.linkedin.com/posts/aziz-zouari_adas-autonomousvehicles-embeddedsystems-activity-7408880455871049728-kYnw?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEUbiZABfS1t5to2wDJqG505PlvHZFRtQac

Quick architecture
------------------
- Laptop: YOLOP model (panoptic segmentation) → measures lane offset & distance → sends UDP packets (to Pi:5555)
- Raspberry Pi 4: custom Yocto image with MCP2515 driver & SocketCAN → Python UDP→CAN gateway (adas_can_server.py)
- CAN bus (500 kbps): 11-bit IDs
  - 0x100: lane offset
  - 0x200: distance
  - 0x300: motor control (speed, steering as int16 little-endian)
- STM32F407: receives CAN, generates 50 Hz PWM (1–2 ms pulse width) via TIM4 to control ESC/motor

Repository layout (scaffold)
---------------------------
- stm32_firmware/    → place STM32CubeMX project, Core/Src, Core/Inc, .ioc
- raspberry_pi/      → adas_can_server.py, init scripts, wiring notes
- adas_application/  → adas_yolopgg_can.py, requirements, model weights pointers
- yocto_meta/        → meta-adas layer, recipes-adas (Yocto recipes)
- docs/              → diagrams, wiring, demo notes, changelog




Contact
-------
Developed by Aziz (azizzr02) & Oussema

License: MIT
