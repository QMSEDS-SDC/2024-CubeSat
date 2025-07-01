# 2024 CubeSat Side Code

## General Description

This repository contains the codebase for the CubeSat's On-Board Computer (OBC). It encompasses functionality for data processing, communications, and internal system operations.

### Tasks Overview

#### **Phase 2: AOCS Check**

- **Image Recognition**:
  - Detect card cutouts and identify numbers written on the cards.
- **Data Processing**:
  - Calculate the position of the cards and provide inputs to the AOCS system.

#### **Phase 3: Main Testing**

- **Image Recognition**:
  - Detect the dock and identify the AprilTag on it.
- **Data Processing**:
  - Compute localization data for the AOCS system.
    - Log velocity and position data (Sub-phase 1).
    - Calculate and log spin rate (Sub-phase 2).

### Communications Module

The repository includes implementations for:

- **Satellite-Side API**: Handles commands from the Ground Station, including system overrides.
- **Ground API Calls**: Transmits data back to the Ground Station based on current commands and override settings.

The message will be in the form of:

1. **Type:** Kind of information it is
2. **Message:** The message

The different types are (they will be values of their respective keys, so format is value1: value2):

1. `"status": ["sensor1", "sensor2", ...]` {from all possible inputs available at a glance}
2. `"data": {"type_of_data": data}`  {for generic data ot part of the below}
3. `"init": 1/2/3`
4. `"response": 1/0`
5. `"p2_info": {0: [AOCS POS], 1: [AOCS POS], ..., 9: [AOCS POS]}`
6. `"p2_cmd": [digit1, digit2, ...]`
7. `"p3_info": {"init": [img array], "final": [img array]}`
8. `"img": [img_array]`
9. `"optional": "live"/"manual"`
10. `"shutdown": num_seconds`
11. `"error": -1`

And 2nd value of `get` - means it is a request of this kind of info

The messages will be encrypted.

### Internal Functionality

Acts as a bridge between the API and data processing modules:

- Executes commands received from the API.
- Triggers data processing algorithms as needed.
- Manages operational tasks and relays system status and data to the Ground Station.

### Pre-requisite

Enable I2C using `raspi-config` on the .
