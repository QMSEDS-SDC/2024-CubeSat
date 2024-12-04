# 2024 CubeSat Image Processing

## General Description

The current repo contains the collection of algorithms which perform the tasks involving image recorgnision and data processing steps for the CubeSat in Mystery Room tests.

The tasks that need to be fulfilled are:

- For Phase 2 (AOCS Check):
  - **Image Recorgnition:** Detect card cuttouts and identify numbers written on the card.
  - **Data Processing:** Calculate position of the cards and provide the input to AOCS system
- For Phase 3 (The Main Testing):
  - **Image Recorgnition:** Detect dock and the AprilTag on it
  - **Data Processing:** Use it to find localisation data which is supplied to AOCS.
    - While doing so log velocity and position data for sub-phase 1
    - Calculate and log spin rate for sub-phase 2
