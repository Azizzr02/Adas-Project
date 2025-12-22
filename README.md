Real‑Time ADAS with CAN Communication and Motor Control
=====================================================

Short overview
--------------
This project demonstrates an end-to-end Advanced Driver Assistance System (ADAS) that integrates computer vision inference (YOLOP), embedded Linux (Yocto) with CAN support, a Raspberry Pi CAN gateway, and an STM32-based real-time motor controller. The system implements autonomous emergency braking by mapping vision-derived distance measurements to motor PWM commands sent over a CAN bus.

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

What I committed here
---------------------
- README.md (this file)
- .gitignore
- LICENSE (MIT)
- repository skeleton folders

How to publish to GitHub (recommended)
-------------------------------------
1. Create a new repository on GitHub under your account (e.g. github.com/azizzr02/adas-realtime-can).
2. Locally, add the real project files to the folders above (or copy full paths):
   - STM32 project: /home/aziz/stm32/adas_motor
   - ADAS app: /home/aziz/yocto/layers/meta-adas/recipes-adas/adas-app/files/
   - Pi CAN server & init scripts: /home/aziz/yocto/layers/meta-adas/
   - Yocto layer: /home/aziz/yocto/layers/meta-adas
3. Add remote and push:

   git remote add origin https://github.com/azizzr02/REPO_NAME.git
   git branch -M main
   git push -u origin main

Notes
-----
- Replace REPO_NAME with the repository name you create on GitHub.
- If you prefer SSH, use the SSH remote URL instead of HTTPS and ensure your SSH key is added to GitHub.
- Remove any sensitive data (password hashes, private keys) before pushing. The Yocto image's /etc/passwd example contains a hashed password — remove or sanitize it.

Contact
-------
Developed by Aziz (azizzr02) & Oussema

License: MIT
