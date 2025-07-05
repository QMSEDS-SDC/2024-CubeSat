"""
Test script for FSM integration
"""

from fsm import FSM
import time

if __name__ == "__main__":
    print("Starting CubeSat FSM...")
    
    try:
        # Initialize FSM
        cubesat = FSM()
        
        # Let it run for a bit
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        cubesat.running = False
    except Exception as e:
        print(f"Error: {e}")