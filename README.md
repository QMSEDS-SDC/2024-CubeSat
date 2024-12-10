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

### Internal Functionality

Acts as a bridge between the API and data processing modules:

- Executes commands received from the API.
- Triggers data processing algorithms as needed.
- Manages operational tasks and relays system status and data to the Ground Station.
