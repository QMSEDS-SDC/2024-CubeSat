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

1. **Header:** Kind of information it is
2. **Message:** The message

The messages come under the following classification:

1. Ground -> CubeSat
   1. Command
      1. Initiate Phase 1
      2. Initiate Phase 2
      3. Initiate Phase 3
   2. Give at a Glance Info - Give data based on config
   3. Phase Commands
      1. Move to these numbers in Phase 2
      2. Correction of detection in Phase 2
      3. Determine the position moved to is correct in Phase 3
   4. Extra Features
      1. Enable Live feed
      2. Enable Manual AOCS Control
   5. Regular Pings - Verification
2. CubeSat -> Ground
   1. Data
      1. Phase 1 Data - The sensor info
      2. Phase 2 Data - Images, Detected numbers, Their Positions
      3. Phase 3 Data - Current View Img, Relative Position, Final Position
      4. At a Glance Data - The sensor info
   2. Regular Pings - Confirmation
   3. Extra Features
      1. Provide image frames for video
      2. Inform of AOCS position when AOCS Control is enabled

The messages will be encrypted.

### Internal Functionality

Acts as a bridge between the API and data processing modules:

- Executes commands received from the API.
- Triggers data processing algorithms as needed.
- Manages operational tasks and relays system status and data to the Ground Station.
