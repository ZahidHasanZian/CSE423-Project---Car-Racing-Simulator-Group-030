#!/usr/bin/env python3
"""
3D Racing Game with Player Vehicle, Obstacles, Powerups, and Collision Detection
Extended from the original template with complete racing game mechanics
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time
import sys

# Window constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

# Camera variables - Multiple Camera Modes System
camera_pos = [0, 6, 8]
camera_look = [0, 0, 0]
fovY = 75
camera_angle = 0

# Camera modes system
camera_mode = 0  # 0=Chase, 1=Drone, 2=Cinematic, 3=Free
camera_modes = ["Chase", "Drone", "Cinematic", "Free"]
camera_follow_vehicle = True  # Only for Free mode
camera_smooth_factor = 0.15   # Smooth camera transitions

# Camera positioning variables
current_camera_x = 0.0
current_camera_y = 6.0
current_camera_z = 8.0

# Camera mode specific settings
camera_settings = {
    "Chase": {"distance": 8, "height": 6, "smooth": 0.15},
    "Drone": {"distance": 15, "height": 12, "smooth": 0.10},
    "Cinematic": {"distance": 12, "height": 8, "smooth": 0.08},
    "Free": {"distance": 10, "height": 5, "smooth": 0.20}
}

# Road configuration
ROAD_WIDTH = 20
ROAD_LENGTH = 2000  # Total road length (fixed) - increased from 500
ROAD_START = -1000  # Road starts here - extended from -250
ROAD_END = 1000     # Road ends here - extended from 250
road_segments = []

# Environment variables
trees = []
buildings = []
street_lights = []
clouds = []

# Weather and time
time_of_day = 0.5  # 0=midnight, 0.25=dawn, 0.5=noon, 0.75=dusk, 1=midnight
weather_mode = "clear"  # clear, rain, heavy_rain
rain_particles = []
max_rain_particles = 800
rain_intensity = 0.0
auto_time = True
time_speed = 0.0001

# Visual effects
use_fog = False
use_lighting = True

# ===== NEW RACING GAME FEATURES =====

# Game state
game_state = "main_menu"  # main_menu, playing, game_over, paused
score = 0
lives = 3
game_time = 0.0

# Main menu variables
menu_selection = 0  # Current menu item (0-4)
menu_page = "main"  # main, settings, instructions, high_scores
selected_vehicle = "car"  # Default vehicle selection
difficulty = "normal"  # easy, normal, hard

# High scores system
high_scores = []  # List of (time, vehicle, date) tuples
max_high_scores = 10  # Maximum number of high scores to keep

def load_high_scores():
    """Load high scores from file"""
    global high_scores
    try:
        with open("high_scores.txt", "r") as f:
            lines = f.readlines()
            high_scores = []
            for line in lines:
                if line.strip():
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        time_val = float(parts[0])
                        vehicle = parts[1]
                        date = parts[2]
                        high_scores.append((time_val, vehicle, date))
            # Sort by time (ascending - lower is better)
            high_scores.sort(key=lambda x: x[0])
    except FileNotFoundError:
        high_scores = []
        print("No high scores file found, starting fresh")

def save_high_scores():
    """Save high scores to file"""
    try:
        with open("high_scores.txt", "w") as f:
            for time_val, vehicle, date in high_scores:
                f.write(f"{time_val},{vehicle},{date}\n")
    except Exception as e:
        print(f"Error saving high scores: {e}")

def add_high_score(time_val, vehicle):
    """Add a new high score if it qualifies"""
    global high_scores
    from datetime import datetime
    
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Add new score
    high_scores.append((time_val, vehicle, current_date))
    
    # Sort by time (ascending - lower is better)
    high_scores.sort(key=lambda x: x[0])
    
    # Keep only top scores
    if len(high_scores) > max_high_scores:
        high_scores = high_scores[:max_high_scores]
    
    # Save to file
    save_high_scores()
    
    # Check if this is a new high score
    if high_scores[0] == (time_val, vehicle, current_date):
        print(f"NEW HIGH SCORE! {time_val:.2f} seconds with {vehicle}!")
    else:
        print(f"Score added: {time_val:.2f} seconds with {vehicle}")

# Player vehicle
class Vehicle:
    def __init__(self, vehicle_type="car"):
        self.type = vehicle_type
        self.reset_position()
        self.setup_vehicle_properties()
    
    def setup_vehicle_properties(self):
        """Set vehicle-specific properties with realistic physics"""
        if self.type == "cycle":
            self.max_speed = 1.4  # Reduced from 8.0 - light and nimble
            self.acceleration = 0.10  # Reduced for more gradual build-up
            self.turn_speed = 4.0  # Much more realistic turning - was 5.0
            self.brake_power = 0.8  # Effective braking for light vehicle
            self.drift_factor = 0.9  # High drift - very light
            self.weight = 0.3
            self.size = [1.5, 1.0, 3.0]  # width, height, length
        elif self.type == "bike":
            self.max_speed = 1.8  # Reduced from 10.0 - balanced performance
            self.acceleration = 0.18  # Moderate acceleration
            self.turn_speed = 3.5  # Much more realistic turning - was 4.0
            self.brake_power = 1.0  # Strong braking
            self.drift_factor = 0.6  # Medium drift - balanced
            self.weight = 0.6
            self.size = [2.0, 1.2, 4.0]
        else:  # car
            self.max_speed = 2.0  # Reduced from 12.0 - powerful but controlled
            self.acceleration = 0.20  # Strong but not instant
            self.turn_speed = 2.8  # Much more realistic turning - was 3.5
            self.brake_power = 1.2  # Very strong braking for heavy vehicle
            self.drift_factor = 0.2  # Low drift - very stable
            self.weight = 1.0
            self.size = [2.5, 1.5, 5.0]
    
    def reset_position(self):
        """Reset vehicle to starting position"""
        self.x = 0.0
        self.z = ROAD_START + 10  # Start slightly after the start line
        self.y = 0.5  # Slightly above ground
        self.rotation = 0.0  # Facing forward
        self.speed = 0.0
        self.velocity_x = 0.0
        self.velocity_z = 0.0
        
        # Enhanced physics variables
        self.target_rotation = 0.0  # Smooth rotation target
        self.rotation_velocity = 0.0  # Rotation momentum
        self.sideways_velocity = 0.0  # Drift/slide velocity
        self.engine_rpm = 0.0  # Engine sound simulation
        self.suspension_offset = 0.0  # Bounce effect
        self.tilt_angle = 0.0  # Banking in turns
    
    def update(self, keys_pressed):
        """Update vehicle position and physics with realistic momentum and braking"""
        if game_state != "playing":
            return
        
        # Enhanced input handling with realistic feel
        throttle_input = 0.0
        brake_input = 0.0
        steering_input = 0.0
        
        # Throttle (forward) - W key or Up arrow
        if keys_pressed.get(b'w') or keys_pressed.get(b'W') or keys_pressed.get(GLUT_KEY_UP):
            throttle_input = 1.0
        
        # Brake (slow down) - S key or Down arrow (NOT reverse)
        if keys_pressed.get(b's') or keys_pressed.get(b'S') or keys_pressed.get(GLUT_KEY_DOWN):
            brake_input = 1.0
        
        # Steering (left/right)
        if keys_pressed.get(b'a') or keys_pressed.get(b'A') or keys_pressed.get(GLUT_KEY_LEFT):
            steering_input = 1.0
        elif keys_pressed.get(b'd') or keys_pressed.get(b'D') or keys_pressed.get(GLUT_KEY_RIGHT):
            steering_input = -1.0
        
        # Realistic acceleration with momentum system
        # Calculate speed limit with stackable speed boost
        if speed_boost_active:
            current_multiplier = speed_boost_multiplier + (speed_boost_stack_count - 1) * 0.2
            speed_limit = self.max_speed * current_multiplier
        else:
            speed_limit = self.max_speed
        
        if throttle_input > 0:
            # Progressive acceleration - builds up gradually like real vehicles
            # Faster acceleration at low speeds, slower at high speeds
            acceleration_factor = 1.0 - (self.speed / speed_limit) * 0.6
            self.speed = min(self.speed + self.acceleration * acceleration_factor * throttle_input, speed_limit)
            self.engine_rpm = min(self.engine_rpm + 0.08, 1.0)
        elif brake_input > 0:
            # Enhanced braking - can bring vehicle to complete stop
            # Braking is effective at all speeds, with extra force at low speeds
            if self.speed > 0.5:
                # At higher speeds, use normal brake power
                brake_effectiveness = min(1.0, self.speed / 2.0)
                self.speed = max(0, self.speed - self.brake_power * brake_effectiveness * brake_input)
            else:
                # At low speeds, use stronger braking to ensure complete stop
                self.speed = max(0, self.speed - self.brake_power * 2.0 * brake_input)
            
            # Ensure complete stop when brake is held
            if self.speed < 0.1:
                self.speed = 0.0
                self.velocity_x = 0.0
                self.velocity_z = 0.0
            
            self.engine_rpm = max(self.engine_rpm - 0.15, 0.0)
        else:
            # Natural momentum and deceleration - vehicle keeps moving like real life
            # Very gradual slowdown to maintain realistic feel
            decel_factor = 0.008 + (self.speed / speed_limit) * 0.012  # Much gentler deceleration
            if self.speed > 0:
                self.speed = max(0, self.speed - decel_factor)
                # Ensure complete stop at very low speeds
                if self.speed < 0.05:
                    self.speed = 0.0
                    self.velocity_x = 0.0
                    self.velocity_z = 0.0
            elif self.speed < 0:
                self.speed = min(0, self.speed + decel_factor)
                # Ensure complete stop at very low speeds
                if self.speed > -0.05:
                    self.speed = 0.0
                    self.velocity_x = 0.0
                    self.velocity_z = 0.0
            
            # Engine RPM naturally decreases but maintains some momentum
            self.engine_rpm = max(self.engine_rpm - 0.03, 0.0)
        
        # Enhanced steering with momentum and speed-dependent response
        if abs(steering_input) > 0:
            # Speed-dependent steering sensitivity - much more realistic
            # At low speeds: more sensitive for parking/tight turns
            # At high speeds: much less sensitive for stability
            # Add extra dampening at very high speeds for safety
            speed_factor = self.speed / speed_limit
            if speed_factor > 0.8:  # Very high speeds
                steering_sensitivity = 0.1  # Very low sensitivity for safety
            else:
                steering_sensitivity = 1.0 - speed_factor * 0.8  # Normal speed dependency
            
            # Additional dampening for realistic feel
            base_steering_dampening = 0.6  # Reduce overall steering responsiveness
            
            # Weight-based steering factor - heavier vehicles turn more slowly
            weight_steering_factor = 1.0 - (self.weight * 0.3)  # Heavier = slower turning
            
            # Calculate target rotation with realistic dampening and weight consideration
            turn_amount = steering_input * self.turn_speed * steering_sensitivity * base_steering_dampening * weight_steering_factor
            
            # Limit maximum turn rate for stability
            max_turn_per_frame = 0.8  # Maximum degrees per frame
            turn_amount = max(-max_turn_per_frame, min(max_turn_per_frame, turn_amount))
            
            # ROTATION RESTRICTION: Once vehicle crosses start line, prevent 180° turns
            # This ensures vehicle can only face roughly forward along the road
            if self.z > ROAD_START + 5:  # Vehicle has crossed start line
                # Calculate the allowed rotation range (roughly forward direction)
                # Allow turning left/right but prevent complete 180° rotation
                max_rotation_left = 90.0   # Maximum left turn (90 degrees left)
                max_rotation_right = -90.0  # Maximum right turn (90 degrees right)
                
                # Calculate new target rotation
                new_target_rotation = self.target_rotation + turn_amount
                
                # Clamp rotation to allowed range
                if new_target_rotation > max_rotation_left:
                    new_target_rotation = max_rotation_left
                    # Notify player when rotation is clamped
                    if not hasattr(self, 'rotation_clamp_notified'):
                        print(f"Rotation restricted! {self.type.title()} can only turn up to 90° left/right after crossing start line.")
                        self.rotation_clamp_notified = True
                elif new_target_rotation < max_rotation_right:
                    new_target_rotation = max_rotation_right
                    # Notify player when rotation is clamped
                    if not hasattr(self, 'rotation_clamp_notified'):
                        print(f"Rotation restricted! {self.type.title()} can only turn up to 90° left/right after crossing start line.")
                        self.rotation_clamp_notified = True
                
                # Only update target rotation if it's within allowed range
                if new_target_rotation != self.target_rotation:
                    self.target_rotation = new_target_rotation
            else:
                # Before crossing start line, allow full rotation for parking/maneuvering
                self.target_rotation += turn_amount
                # Reset notification flag when back before start line
                if hasattr(self, 'rotation_clamp_notified'):
                    delattr(self, 'rotation_clamp_notified')
            
            # Smooth rotation with momentum - more gradual
            rotation_diff = self.target_rotation - self.rotation
            self.rotation_velocity += rotation_diff * 0.05  # Reduced from 0.1 for more gradual response
            self.rotation_velocity *= 0.85  # Increased damping from 0.9 for more stability
            self.rotation += self.rotation_velocity
            
            # ROTATION CLAMPING: Ensure current rotation stays within allowed range after start line
            if self.z > ROAD_START + 5:  # Vehicle has crossed start line
                # Clamp current rotation to prevent 180° turns
                max_rotation_left = 90.0   # Maximum left turn (90 degrees left)
                max_rotation_right = -90.0  # Maximum right turn (90 degrees right)
                
                # Add small buffer zone for smoother clamping
                buffer_zone = 2.0  # Degrees
                
                if self.rotation > max_rotation_left - buffer_zone:
                    # Gradually slow down rotation as it approaches the limit
                    if self.rotation > max_rotation_left:
                        self.rotation = max_rotation_left
                        self.rotation_velocity = 0  # Stop rotation momentum when clamped
                    else:
                        # Slow down rotation velocity as it approaches the limit
                        self.rotation_velocity *= 0.5
                elif self.rotation < max_rotation_right + buffer_zone:
                    # Gradually slow down rotation as it approaches the limit
                    if self.rotation < max_rotation_right:
                        self.rotation = max_rotation_right
                        self.rotation_velocity = 0  # Stop rotation momentum when clamped
                    else:
                        # Slow down rotation velocity as it approaches the limit
                        self.rotation_velocity *= 0.5
            
            # Calculate tilt angle for banking effect
            self.tilt_angle = rotation_diff * 0.2  # Reduced from 0.3 for subtler banking
        else:
            # Return to neutral when not steering - more realistic
            # Gradually return to current rotation (don't snap back)
            self.target_rotation = self.rotation
            self.rotation_velocity *= 0.7  # More gradual return to neutral (was 0.8)
            self.tilt_angle *= 0.85  # Return to level more gradually (was 0.9)
        
        # Enhanced movement physics with drift mechanics
        if abs(self.speed) > 0.1:
            angle_rad = math.radians(self.rotation)
            
            # Calculate forward velocity
            forward_velocity = math.cos(angle_rad) * self.speed
            
            # Enhanced drift mechanics
            if abs(self.rotation_velocity) > 0.5 and self.speed > 2.0:
                # Vehicle is drifting - add sideways velocity
                drift_intensity = abs(self.rotation_velocity) * self.drift_factor
                self.sideways_velocity += math.sin(angle_rad) * drift_intensity * 0.1
            else:
                # Normal movement - gradually reduce sideways velocity
                self.sideways_velocity *= 0.95
            
            # Apply sideways velocity (drift effect)
            self.velocity_x = math.sin(angle_rad) * self.speed + self.sideways_velocity
            self.velocity_z = forward_velocity
            
            # Suspension effects
            self.suspension_offset = math.sin(time.time() * 10) * 0.05 * (self.speed / speed_limit)
            
                    # PREVENTIVE BOUNDARY CHECK with enhanced physics
        new_x = self.x + self.velocity_x
        new_z = self.z + self.velocity_z
        
        # Check X boundaries (left/right)
        x_within_bounds = abs(new_x) <= ROAD_WIDTH / 2
        
        # Check Z boundaries (forward/backward) - allow backward movement but prevent going completely off track
        # Allow temporary boundary violation during turning maneuvers for full 360-degree turns
        z_within_bounds = new_z >= ROAD_START  # Allow backward movement to start line
        
        # Check if vehicle is turning (has significant rotation velocity)
        # Also consider if vehicle is reversing for more turning freedom
        is_turning = abs(self.rotation_velocity) > 0.5
        is_reversing = self.velocity_z < 0  # Vehicle is moving backward
        
        if x_within_bounds and z_within_bounds:
            # Both X and Z movements are within bounds
            self.x = new_x
            self.z = new_z
        elif x_within_bounds and not z_within_bounds:
            # Only X movement is allowed (car trying to go backwards)
            self.x = new_x
            # Allow temporary Z boundary violation during turning for full 360-degree turns
            # Give more freedom during reverse turning for full 360-degree maneuvers
            if (is_turning and new_z >= ROAD_START - 2.0) or (is_reversing and new_z >= ROAD_START - 3.0):
                self.z = new_z
            # Don't update z otherwise - car stays at current z
        elif not x_within_bounds and z_within_bounds:
            # Only Z movement is allowed (car trying to go sideways)
            self.z = new_z
            # Don't update x - car stays at current x
        else:
            # Both movements would put car out of bounds
            # Allow temporary boundary violation during turning for full 360-degree turns
            # Give more freedom during reverse turning for full 360-degree maneuvers
            if is_turning or is_reversing:
                if new_z >= ROAD_START - 3.0:  # Allow 3 units beyond start during turns/reverse
                    self.z = new_z
                if abs(new_x) <= ROAD_WIDTH / 2 + 1.5:  # Allow 1.5 units beyond sides during turns/reverse
                    self.x = new_x
            
                    # Apply drift physics to boundary hits
        if not x_within_bounds:
            # Bounce off boundaries with drift effect
            self.sideways_velocity *= -0.5  # Reverse drift direction
            self.rotation_velocity *= -0.3  # Slight rotation bounce
        
        # Enhanced reverse turning - allow more freedom during reverse maneuvers
        if is_reversing and abs(self.rotation_velocity) > 0.8:
            # Vehicle is reversing and turning sharply - allow temporary boundary extension
            # This enables full 360-degree turns while reversing
            if self.z < ROAD_START - 1.0 and self.z >= ROAD_START - 4.0:
                # Allow temporary extension beyond start boundary during reverse turning
                pass  # Don't reset position during reverse turning maneuvers
        
        # Check road boundaries - STRICT BOUNDARY ENFORCEMENT
        road_left_edge = -ROAD_WIDTH / 2
        road_right_edge = ROAD_WIDTH / 2
        road_start_edge = ROAD_START  # Allow backward movement to start line
        
        # Prevent car from going beyond road boundaries - IMMEDIATE CORRECTION
        global boundary_hit_timer, boundary_hit_intensity
        
        # Check if car is out of bounds and correct immediately
        if self.x < road_left_edge:
            self.x = road_left_edge
            self.speed *= 0.3  # Significant slowdown when hitting left edge
            self.velocity_x = 0  # Stop horizontal movement
            # Trigger boundary hit feedback
            boundary_hit_timer = 0.5  # 0.5 seconds of feedback
            boundary_hit_intensity = 2.0
        elif self.x > road_right_edge:
            self.x = road_right_edge
            self.speed *= 0.3  # Significant slowdown when hitting right edge
            self.velocity_x = 0  # Stop horizontal movement
            # Trigger boundary hit feedback
            boundary_hit_timer = 0.5  # 0.5 seconds of feedback
            boundary_hit_intensity = 2.0
        
        # Check Z boundaries (forward/backward) - prevent going backwards beyond start
        # Allow temporary boundary violation during turning maneuvers for full 360-degree turns
        if self.z < road_start_edge:
            # Check if vehicle is turning or reversing - allow temporary boundary violation
            if (abs(self.rotation_velocity) > 0.5 and self.z >= road_start_edge - 2.0) or \
               (self.velocity_z < 0 and self.z >= road_start_edge - 3.0):
                # Allow temporary boundary violation during turns or reverse maneuvers
                pass
            else:
                # Normal boundary enforcement
                self.z = road_start_edge
                self.speed *= 0.3  # Significant slowdown when hitting start boundary
                self.velocity_z = 0  # Stop backward movement
                # Trigger boundary hit feedback
                boundary_hit_timer = 0.5  # 0.5 seconds of feedback
                boundary_hit_intensity = 2.0
        
        # EMERGENCY RESET - if car somehow gets completely out of bounds
        # Allow temporary boundary violation during turning maneuvers for full 360-degree turns
        if abs(self.x) > ROAD_WIDTH / 2 + 1.0 or self.z < ROAD_START:
            # Check if vehicle is turning or reversing - allow temporary boundary violation
            if abs(self.rotation_velocity) > 0.5 or self.velocity_z < 0:
                if abs(self.x) > ROAD_WIDTH / 2 + 2.5 or self.z < ROAD_START - 3.0:
                    # Only reset if way out of bounds during turns or reverse maneuvers
                    self.x = 0.0  # Reset to road center
                    self.z = ROAD_START + 5  # Reset to safe position after start line
                    self.speed *= 0.3  # More aggressive speed reduction
                    self.velocity_x = 0  # Stop all horizontal movement
                    self.velocity_z = 0  # Stop forward movement temporarily
            else:
                # Normal emergency reset
                self.x = 0.0  # Reset to road center
                self.z = ROAD_START + 5  # Reset to safe position after start line
                self.speed *= 0.3  # More aggressive speed reduction
                self.velocity_x = 0  # Stop all horizontal movement
                self.velocity_z = 0  # Stop forward movement temporarily
        
        # Check if reached finish
        if self.z >= ROAD_END:
            self.handle_finish()
        

    

    
    def handle_collision(self, collision_type):
        """Handle different types of collisions"""
        global lives, game_state, shield_count
        
        if collision_type == "obstacle":
            if shield_count > 0:
                shield_count -= 1
                print(f"Shield protected you from collision! Remaining shields: {shield_count}")
                return
            else:
                lives -= 1
                print(f"Collision! Lives remaining: {lives}")
                if lives <= 0:
                    game_state = "game_over"
                else:
                    self.reset_position()
        
        elif collision_type == "road_edge":
            lives -= 1
            print(f"Fell off road! Lives remaining: {lives}")
            if lives <= 0:
                game_state = "game_over"
            else:
                self.reset_position()
    
    def handle_finish(self):
        """Handle reaching the finish line"""
        global game_state, score
        game_state = "game_over"
        score = int(game_time * 100) + lives * 1000
        print(f"Congratulations! You finished in {game_time:.1f} seconds!")
        print(f"Final Score: {score}")
        
        # Add to high scores
        add_high_score(game_time, self.type)
    
    def get_aabb(self):
        """Get vehicle's AABB for collision detection"""
        half_width = self.size[0] / 2
        half_length = self.size[2] / 2
        return {
            'x': self.x - half_width,
            'y': self.y,
            'z': self.z - half_length,
            'width': self.size[0],
            'height': self.size[1],
            'length': self.size[2]
        }

# Game objects
player_vehicle = Vehicle("car")
keys_pressed = {}

# Obstacles
class Obstacle:
    def __init__(self, x, z, obstacle_type="box"):
        self.x = x
        self.z = z
        self.y = 0.5
        self.type = obstacle_type
        self.rotation = 0.0
        self.size = [2.0, 2.0, 2.0] if obstacle_type == "box" else [1.5, 2.0, 1.5]
        self.collected = False
    
    def update(self):
        """Update obstacle animation"""
        self.rotation += 1.0  # Rotate slowly
    
    def get_aabb(self):
        """Get obstacle's AABB for collision detection"""
        half_width = self.size[0] / 2
        half_length = self.size[2] / 2
        return {
            'x': self.x - half_width,
            'y': self.y,
            'z': self.z - half_length,
            'width': self.size[0],
            'height': self.size[1],
            'length': self.size[2]
        }

obstacles = []

# Powerups
class Powerup:
    def __init__(self, x, z, powerup_type="speed"):
        self.x = x
        self.z = z
        self.y = 1.0
        self.type = powerup_type
        self.rotation = 0.0
        self.scale = 1.0
        self.scale_direction = 1
        self.collected = False
        self.size = 1.0
    
    def update(self):
        """Update powerup animation with hovering effects"""
        if self.collected:
            return
        
        self.rotation += 3.0  # Rotate faster than obstacles
        
        # Enhanced hovering animation
        # Vertical floating motion
        self.y = 1.0 + math.sin(time.time() * 3.0) * 0.3
        
        # Pulsing scale effect
        self.scale += 0.02 * self.scale_direction
        if self.scale > 1.2:
            self.scale_direction = -1
        elif self.scale < 0.8:
            self.scale_direction = 1
        
        # Add slight horizontal sway
        self.x += math.sin(time.time() * 2.0) * 0.01
    
    def get_aabb(self):
        """Get powerup's AABB for collision detection"""
        half_size = self.size / 2
        return {
            'x': self.x - half_size,
            'y': self.y - half_size,
            'z': self.z - half_size,
            'width': self.size,
            'height': self.size,
            'length': self.size
        }

powerups = []

# Powerup effects - Stackable system
shield_count = 0  # Number of shields stacked
shield_duration = 10.0  # Duration per shield in seconds
speed_boost_active = False
speed_boost_timer = 0.0
speed_boost_multiplier = 1.5
speed_boost_stack_count = 0  # Number of speed boosts stacked

# Road boundary feedback
boundary_hit_timer = 0.0
boundary_hit_intensity = 0.0

# Collision detection
def has_collided(aabb1, aabb2):
    """AABB collision detection"""
    return (aabb1['x'] < aabb2['x'] + aabb2['width'] and
            aabb1['x'] + aabb1['width'] > aabb2['x'] and
            aabb1['z'] < aabb2['z'] + aabb2['length'] and
            aabb1['z'] + aabb1['length'] > aabb2['z'])

def check_collisions():
    """Check all collisions in the game"""
    global shield_count, speed_boost_active, speed_boost_timer, speed_boost_stack_count, obstacles, powerups
    
    vehicle_aabb = player_vehicle.get_aabb()
    
    # Check obstacle collisions
    for obstacle in obstacles:
        if not obstacle.collected and has_collided(vehicle_aabb, obstacle.get_aabb()):
            player_vehicle.handle_collision("obstacle")
            obstacle.collected = True
    
    # Check powerup collisions
    for powerup in powerups:
        if not powerup.collected and has_collided(vehicle_aabb, powerup.get_aabb()):
            if powerup.type == "speed":
                # Stackable speed boost - extend timer and increase stack count
                speed_boost_stack_count += 1
                speed_boost_timer += 5.0  # Add 5 seconds per boost
                speed_boost_active = True
                print(f"Speed boost activated! Stack: {speed_boost_stack_count}, Duration: {speed_boost_timer:.1f}s")
            elif powerup.type == "shield":
                # Stackable shield - add to shield count
                shield_count += 1
                print(f"Shield activated! Total shields: {shield_count}")
            powerup.collected = True

# Object spawning
def spawn_objects():
    """Spawn obstacles and powerups with enhanced boundary checking"""
    global obstacles, powerups
    

    
    # Spawn obstacles periodically
    if len(obstacles) < 8 and random.random() < 0.02:
        # Ensure obstacles spawn well within road boundaries with margin for their size
        margin = 5.0  # Increased from 4.0 to ensure objects are clearly within visible track
        spawn_min_x = -ROAD_WIDTH/2 + margin
        spawn_max_x = ROAD_WIDTH/2 - margin
        x = random.uniform(spawn_min_x, spawn_max_x)
        z = random.uniform(player_vehicle.z + 50, player_vehicle.z + 200)
        
        # Don't spawn obstacles after the finish line
        if z < ROAD_END - 50:  # Leave 50 units before finish line
            obstacle_type = random.choice(["box", "cylinder"])
            obstacles.append(Obstacle(x, z, obstacle_type))
            
            

    # Spawn powerups periodically
    if len(powerups) < 4 and random.random() < 0.01:
        # Ensure powerups spawn well within road boundaries with margin for their size
        margin = 4.0  # Increased from 4.0 to ensure objects are clearly within visible track
        spawn_min_x = -ROAD_WIDTH/2 + margin
        spawn_max_x = ROAD_WIDTH/2 - margin
        x = random.uniform(spawn_min_x, spawn_max_x)
        z = random.uniform(player_vehicle.z + 30, player_vehicle.z + 150)
        
        # Don't spawn powerups after the finish line
        if z < ROAD_END - 50:  # Leave 50 units before finish line
            powerup_type = random.choice(["speed", "shield"])
            powerups.append(Powerup(x, z, powerup_type))
            
            

    # Clean up objects that are too far behind
    obstacles = [obs for obs in obstacles if obs.z > player_vehicle.z - 100]
    powerups = [pwr for pwr in powerups if pwr.z > player_vehicle.z - 100]
    


# ===== EXISTING TEMPLATE FUNCTIONS (MODIFIED) =====

def init_scene():
    """Initialize OpenGL settings with proper depth configuration"""
    # Enable depth testing
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glDepthRange(0.0, 1.0)
    
    # Enable smooth shading (from template requirement)
    glShadeModel(GL_SMOOTH)
    
    # Enable other features
    glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Set initial clear color
    update_clear_color()
    glClearDepth(1.0)
    
    # Initialize environment
    init_road_layout()
    init_environment()
    init_rain_system()
    
    # Setup initial lighting
    setup_lighting()

def init_road_layout():
    """Initialize fixed-length straight road segments"""
    global road_segments
    
    road_segments = []
    segment_length = 40
    
    # Create fixed road segments from start to end
    num_segments = int((ROAD_END - ROAD_START) / segment_length) + 1
    
    for i in range(num_segments):
        z_position = ROAD_START + (i * segment_length)
        road_segments.append({
            'z': z_position,
            'type': 'straight'
        })

def init_environment():
    """Initialize all environment objects positioned beside the fixed road"""
    global trees, buildings, street_lights, clouds
    
    # Generate street lights BESIDE the road along its length
    street_lights = []
    lamp_spacing = 50
    
    for z in range(ROAD_START, ROAD_END + 1, lamp_spacing):
        # Left side lamp posts
        street_lights.append({
            'x': -(ROAD_WIDTH/2 + 5),  # 5 units away from road edge
            'z': z,
            'side': 'left'
        })
        # Right side lamp posts
        street_lights.append({
            'x': (ROAD_WIDTH/2 + 5),  # 5 units away from road edge
            'z': z,
            'side': 'right'
        })
    
    # Add special markers at start and end
    # Start line markers
    street_lights.append({'x': -(ROAD_WIDTH/2 + 5), 'z': ROAD_START, 'side': 'left', 'special': 'start'})
    street_lights.append({'x': (ROAD_WIDTH/2 + 5), 'z': ROAD_START, 'side': 'right', 'special': 'start'})
    # Finish line markers
    street_lights.append({'x': -(ROAD_WIDTH/2 + 5), 'z': ROAD_END, 'side': 'left', 'special': 'finish'})
    street_lights.append({'x': (ROAD_WIDTH/2 + 5), 'z': ROAD_END, 'side': 'right', 'special': 'finish'})
    
    # Generate buildings BESIDE the road
    buildings = []
    building_spacing = 80
    
    for z in range(ROAD_START + 50, ROAD_END - 50, building_spacing):
        # Buildings on left side
        if random.random() > 0.3:
            buildings.append({
                'x': -(ROAD_WIDTH/2 + random.uniform(20, 40)),
                'z': z + random.uniform(-10, 10),
                'height': random.uniform(25, 45),
                'width': random.uniform(15, 25),
                'depth': random.uniform(15, 20)
            })
        
        # Buildings on right side
        if random.random() > 0.3:
            buildings.append({
                'x': (ROAD_WIDTH/2 + random.uniform(20, 40)),
                'z': z + random.uniform(-10, 10),
                'height': random.uniform(25, 45),
                'width': random.uniform(15, 25),
                'depth': random.uniform(15, 20)
            })
    
    # Generate trees along the road
    trees = []
    tree_spacing = 25
    
    for z in range(ROAD_START - 50, ROAD_END + 50, tree_spacing):
        # Trees on left side
        if random.random() > 0.2:
            x_offset = random.choice([
                random.uniform(15, 18),  # Between road and buildings
                random.uniform(50, 70)   # Beyond buildings
            ])
            trees.append({
                'x': -(ROAD_WIDTH/2 + x_offset),
                'z': z + random.uniform(-10, 10),
                'height': random.uniform(10, 18),
                'type': random.choice(['pine', 'oak', 'palm'])
            })
        
        # Trees on right side
        if random.random() > 0.2:
            x_offset = random.choice([
                random.uniform(15, 18),
                random.uniform(50, 70)
            ])
            trees.append({
                'x': (ROAD_WIDTH/2 + x_offset),
                'z': z + random.uniform(-10, 10),
                'height': random.uniform(10, 18),
                'type': random.choice(['pine', 'oak', 'palm'])
            })
    
    # Generate clouds
    clouds = []
    for i in range(15):
        clouds.append({
            'x': random.uniform(-200, 200),
            'y': random.uniform(60, 100),
            'z': random.uniform(ROAD_START - 100, ROAD_END + 100),
            'size': random.uniform(15, 30)
        })

def init_rain_system():
    """Initialize rain particle system"""
    global rain_particles
    rain_particles = []
    for i in range(max_rain_particles):
        rain_particles.append({
            'x': random.uniform(-150, 150),
            'y': random.uniform(0, 100),
            'z': random.uniform(ROAD_START - 50, ROAD_END + 50),
            'speed': random.uniform(1.5, 3.0),
            'active': False
        })

def get_time_phase():
    """Get current time phase"""
    if 0.0 <= time_of_day < 0.2:
        return "Night"
    elif 0.2 <= time_of_day < 0.35:
        return "Dawn"
    elif 0.35 <= time_of_day < 0.65:
        return "Day"
    elif 0.65 <= time_of_day < 0.8:
        return "Dusk"
    else:
        return "Night"

def get_sky_colors():
    """Get sky colors based on time of day"""
    phase = get_time_phase()
    
    colors = {
        "Night": {
            'top': [0.0, 0.0, 0.2],
            'bottom': [0.1, 0.1, 0.3],
            'sun': [0.9, 0.9, 1.0],
            'ambient': 0.15
        },
        "Dawn": {
            'top': [0.4, 0.3, 0.6],
            'bottom': [1.0, 0.6, 0.4],
            'sun': [1.0, 0.8, 0.6],
            'ambient': 0.4
        },
        "Day": {
            'top': [0.4, 0.6, 1.0],
            'bottom': [0.7, 0.85, 1.0],
            'sun': [1.0, 1.0, 0.8],
            'ambient': 0.8
        },
        "Dusk": {
            'top': [0.3, 0.2, 0.5],
            'bottom': [0.8, 0.5, 0.3],
            'sun': [1.0, 0.7, 0.5],
            'ambient': 0.5
        }
    }
    
    return colors.get(phase, colors["Day"])

def update_clear_color():
    """Update the clear color based on time of day"""
    sky_colors = get_sky_colors()
    
    # Apply weather effects
    if weather_mode == "heavy_rain":
        clear_color = [c * 0.5 for c in sky_colors['bottom']]
    elif weather_mode == "rain":
        clear_color = [c * 0.7 for c in sky_colors['bottom']]
    else:
        clear_color = sky_colors['bottom']
    
    glClearColor(clear_color[0], clear_color[1], clear_color[2], 1.0)

def setup_camera():
    """Configure camera with perspective projection (from template)"""
    global current_camera_x, current_camera_y, current_camera_z
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Raised and moved back for better view of longer road
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 2000)  # Extended far plane to 2000
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Multiple camera modes system
    if game_state == "playing":
        current_mode = camera_modes[camera_mode]
        settings = camera_settings[current_mode]
        
        # All camera modes are automatic
        vehicle_angle_rad = math.radians(player_vehicle.rotation)
        
        if current_mode == "Chase":
            # Standard chase camera
            target_camera_x = player_vehicle.x - settings["distance"] * math.sin(vehicle_angle_rad)
            target_camera_z = player_vehicle.z - settings["distance"] * math.cos(vehicle_angle_rad)
            target_camera_y = player_vehicle.y + settings["height"]
            
        elif current_mode == "Drone":
            # High, wide drone view
            target_camera_x = player_vehicle.x - settings["distance"] * math.sin(vehicle_angle_rad)
            target_camera_z = player_vehicle.z - settings["distance"] * math.cos(vehicle_angle_rad)
            target_camera_y = player_vehicle.y + settings["height"]
            
        elif current_mode == "Cinematic":
            # Smooth, movie-like following
            target_camera_x = player_vehicle.x - settings["distance"] * math.sin(vehicle_angle_rad)
            target_camera_z = player_vehicle.z - settings["distance"] * math.cos(vehicle_angle_rad)
            target_camera_y = player_vehicle.y + settings["height"]
            
        elif current_mode == "Free":
            # Free camera - balanced view
            target_camera_x = player_vehicle.x - settings["distance"] * math.sin(vehicle_angle_rad)
            target_camera_z = player_vehicle.z - settings["distance"] * math.cos(vehicle_angle_rad)
            target_camera_y = player_vehicle.y + settings["height"]
        
        # Smooth camera movement
        current_camera_x += (target_camera_x - current_camera_x) * settings["smooth"]
        current_camera_y += (target_camera_y - current_camera_y) * settings["smooth"]
        current_camera_z += (target_camera_z - current_camera_z) * settings["smooth"]
        
        # Add screen shake effect when hitting road boundaries
        if boundary_hit_intensity > 0:
            shake_x = random.uniform(-boundary_hit_intensity, boundary_hit_intensity)
            shake_y = random.uniform(-boundary_hit_intensity * 0.5, boundary_hit_intensity * 0.5)
            current_camera_x += shake_x
            current_camera_y += shake_y
        
        # Look at vehicle
        gluLookAt(current_camera_x, current_camera_y, current_camera_z,
                  player_vehicle.x, player_vehicle.y + 1, player_vehicle.z,
                  0, 1, 0)
    else:
        # Static camera for menu
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  camera_look[0], camera_look[1], camera_look[2],
                  0, 1, 0)

def setup_lighting():
    """Setup dynamic lighting based on time of day"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)  # Sun/Moon
    glEnable(GL_LIGHT1)  # Ambient fill
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    
    sky_colors = get_sky_colors()
    phase = get_time_phase()
    
    # Sun/Moon position
    sun_angle = time_of_day * 2 * math.pi
    sun_x = math.cos(sun_angle) * 150
    sun_y = math.sin(sun_angle) * 80 + 40
    sun_z = -100
    
    # Weather dimming
    weather_dimming = 1.0
    if weather_mode == "rain":
        weather_dimming = 0.6
    elif weather_mode == "heavy_rain":
        weather_dimming = 0.4
    
    # Main light
    intensity = sky_colors['ambient'] * weather_dimming
    if phase == "Night":
        light0_diffuse = [0.3, 0.3, 0.4, 1.0]
        light0_ambient = [0.1, 0.1, 0.15, 1.0]
    else:
        light0_diffuse = [intensity, intensity * 0.95, intensity * 0.9, 1.0]
        light0_ambient = [intensity * 0.3, intensity * 0.3, intensity * 0.35, 1.0]
    
    glLightfv(GL_LIGHT0, GL_POSITION, [sun_x, sun_y, sun_z, 0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diffuse)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light0_ambient)
    
    # Fill light
    glLightfv(GL_LIGHT1, GL_POSITION, [-50, 30, 50, 0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [intensity * 0.3, intensity * 0.3, intensity * 0.3, 1.0])

def setup_fog():
    """Setup fog with weather integration"""
    should_use_fog = use_fog or weather_mode in ["rain", "heavy_rain"]
    
    if should_use_fog:
        glEnable(GL_FOG)
        
        if weather_mode == "heavy_rain":
            fog_color = [0.5, 0.5, 0.6, 1.0]
            glFogf(GL_FOG_DENSITY, 0.025)
        elif weather_mode == "rain":
            fog_color = [0.6, 0.6, 0.7, 1.0]
            glFogf(GL_FOG_DENSITY, 0.015)
        else:
            fog_color = [0.7, 0.7, 0.8, 1.0]
            glFogf(GL_FOG_DENSITY, 0.008)
        
        glFogfv(GL_FOG_COLOR, fog_color)
        glFogi(GL_FOG_MODE, GL_EXP)
    else:
        glDisable(GL_FOG)

def update_rain_particles():
    """Update rain particle positions"""
    global rain_intensity
    
    if weather_mode == "clear":
        rain_intensity = 0.0
        active_particles = 0
    elif weather_mode == "rain":
        rain_intensity = 0.6
        active_particles = int(0.6 * max_rain_particles)
    elif weather_mode == "heavy_rain":
        rain_intensity = 1.0
        active_particles = max_rain_particles
    else:
        active_particles = 0
    
    for i, particle in enumerate(rain_particles):
        if i < active_particles:
            particle['active'] = True
            particle['y'] -= particle['speed']
            particle['x'] += random.uniform(-0.1, 0.1)  # Wind
            
            if particle['y'] < 0:
                particle['x'] = random.uniform(-150, 150)
                particle['y'] = random.uniform(80, 100)
                particle['z'] = random.uniform(ROAD_START - 50, ROAD_END + 50)
        else:
            particle['active'] = False

def draw_rain():
    """Draw rain particles"""
    if weather_mode == "clear":
        return
    
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    
    if weather_mode == "heavy_rain":
        glColor4f(0.6, 0.6, 0.8, 0.8)
        glLineWidth(2.0)
    else:
        glColor4f(0.7, 0.7, 0.9, 0.6)
        glLineWidth(1.0)
    
    glBegin(GL_LINES)
    for particle in rain_particles:
        if particle['active']:
            glVertex3f(particle['x'], particle['y'], particle['z'])
            glVertex3f(particle['x'] - 0.5, particle['y'] - 4, particle['z'] - 0.5)
    glEnd()
    
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)

def draw_road():
    """Draw fixed-length straight road with start and finish lines"""
    # Main road surface
    glColor3f(0.2, 0.2, 0.2) if weather_mode == "clear" else glColor3f(0.15, 0.15, 0.15)
    
    # Draw the complete road from start to end
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_WIDTH/2, 0, ROAD_START)
    glVertex3f(ROAD_WIDTH/2, 0, ROAD_START)
    glVertex3f(ROAD_WIDTH/2, 0, ROAD_END)
    glVertex3f(-ROAD_WIDTH/2, 0, ROAD_END)
    glEnd()
    
    # Debug: Draw spawn boundaries as colored lines
    if game_state == "playing":
        # Obstacle spawn boundary (green line)
        glColor3f(0.0, 1.0, 0.0)  # Green
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for z in range(int(ROAD_START), int(ROAD_END), 10):
            # Left boundary
            glVertex3f(-ROAD_WIDTH/2 + 4.0, 0.02, z)
            glVertex3f(-ROAD_WIDTH/2 + 4.0, 0.02, z + 5)
            # Right boundary
            glVertex3f(ROAD_WIDTH/2 - 4.0, 0.02, z)
            glVertex3f(ROAD_WIDTH/2 - 4.0, 0.02, z + 5)
        glEnd()
        
        # Powerup spawn boundary (blue line)
        glColor3f(0.0, 0.0, 1.0)  # Blue
        glBegin(GL_LINES)
        for z in range(int(ROAD_START), int(ROAD_END), 10):
            # Left boundary
            glVertex3f(-ROAD_WIDTH/2 + 3.0, 0.02, z)
            glVertex3f(-ROAD_WIDTH/2 + 3.0, 0.02, z + 5)
            # Right boundary
            glVertex3f(ROAD_WIDTH/2 - 3.0, 0.02, z)
            glVertex3f(ROAD_WIDTH/2 - 3.0, 0.02, z + 5)
        glEnd()
    
    # Draw start line (green)
    glColor3f(0, 1, 0)
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_START)
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_START)
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_START + 2)
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_START + 2)
    glEnd()
    
    # Draw finish line (checkered pattern)
    checker_size = 2
    for x in range(int(-ROAD_WIDTH/2), int(ROAD_WIDTH/2), checker_size):
        for z in range(0, 4, checker_size):
            if (int(x/checker_size) + int(z/checker_size)) % 2 == 0:
                glColor3f(1, 1, 1)
            else:
                glColor3f(0, 0, 0)
            glBegin(GL_QUADS)
            glVertex3f(x, 0.01, ROAD_END - 4 + z)
            glVertex3f(x + checker_size, 0.01, ROAD_END - 4 + z)
            glVertex3f(x + checker_size, 0.01, ROAD_END - 4 + z + checker_size)
            glVertex3f(x, 0.01, ROAD_END - 4 + z + checker_size)
            glEnd()
    
    # Center lane markings
    glColor3f(1, 1, 0)
    for z in range(ROAD_START + 10, ROAD_END - 10, 20):
        if (z - ROAD_START) % 40 < 20:  # Dashed line
            glBegin(GL_QUADS)
            glVertex3f(-0.3, 0.01, z)
            glVertex3f(0.3, 0.01, z)
            glVertex3f(0.3, 0.01, z + 15)
            glVertex3f(-0.3, 0.01, z + 15)
            glEnd()
    
    # Side lines (continuous) - THICKER AND MORE VISIBLE
    glColor3f(1, 0, 0)  # Changed to RED for better visibility
    glLineWidth(5.0)  # Increased from 3.0 to make more visible
    glBegin(GL_LINES)
    # Left side line
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_START)
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_END)
    # Right side line
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_START)
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_END)
    glEnd()
    
    # Additional boundary markers - small red cubes at regular intervals
    marker_spacing = 20
    for z in range(int(ROAD_START), int(ROAD_END), marker_spacing):
        # Left boundary marker
        glColor3f(1.0, 0.0, 0.0)  # Red
        glPushMatrix()
        glTranslatef(-ROAD_WIDTH/2 - 0.5, 0.5, z)
        glutSolidCube(1.0)
        glPopMatrix()
        
        # Right boundary marker
        glPushMatrix()
        glTranslatef(ROAD_WIDTH/2 + 0.5, 0.5, z)
        glutSolidCube(1.0)
        glPopMatrix()
    
    # Enhanced road boundary visualization - add floating boundary indicators
    glColor3f(1.0, 0.0, 0.0)  # Red
    for z in range(int(ROAD_START), int(ROAD_END), 10):
        # Left boundary floating indicator
        glPushMatrix()
        glTranslatef(-ROAD_WIDTH/2, 2.0, z)
        glutSolidSphere(0.3, 8, 8)
        glPopMatrix()
        
        # Right boundary floating indicator
        glPushMatrix()
        glTranslatef(ROAD_WIDTH/2, 2.0, z)
        glutSolidSphere(0.3, 8, 8)
        glPopMatrix()
    
    # Additional boundary clarity - draw vertical boundary walls
    glColor4f(1.0, 0.0, 0.0, 0.3)  # Semi-transparent red
    glEnable(GL_BLEND)
    
    # Left boundary wall
    glBegin(GL_QUADS)
    for z in range(int(ROAD_START), int(ROAD_END), 20):
        glVertex3f(-ROAD_WIDTH/2 - 0.1, 0, z)
        glVertex3f(-ROAD_WIDTH/2 - 0.1, 3, z)
        glVertex3f(-ROAD_WIDTH/2 - 0.1, 3, z + 20)
        glVertex3f(-ROAD_WIDTH/2 - 0.1, 0, z + 20)
    glEnd()
    
    # Right boundary wall
    glBegin(GL_QUADS)
    for z in range(int(ROAD_START), int(ROAD_END), 20):
        glVertex3f(ROAD_WIDTH/2 + 0.1, 0, z)
        glVertex3f(ROAD_WIDTH/2 + 0.1, 3, z)
        glVertex3f(ROAD_WIDTH/2 + 0.1, 3, z + 20)
        glVertex3f(ROAD_WIDTH/2 + 0.1, 0, z + 20)
    glEnd()
    
    glDisable(GL_BLEND)
    
    # Bright boundary markers at exact road edges
    glColor3f(1.0, 1.0, 0.0)  # Bright yellow
    glLineWidth(3.0)
    glBegin(GL_LINES)
    for z in range(int(ROAD_START), int(ROAD_END), 10):
        # Left edge marker
        glVertex3f(-ROAD_WIDTH/2, 0.05, z)
        glVertex3f(-ROAD_WIDTH/2, 0.05, z + 5)
        # Right edge marker
        glVertex3f(ROAD_WIDTH/2, 0.05, z)
        glVertex3f(ROAD_WIDTH/2, 0.05, z + 5)
    glEnd()
    
    # Road boundary warning stripes (red and white) - helps player see track limits
    warning_width = 2.0  # Increased from 1.0 to make more visible
    stripe_length = 4.0  # Increased from 3.0 to make more visible
    spacing = 2.0  # Reduced from 3.0 to make stripes closer together
    
    for z in range(int(ROAD_START), int(ROAD_END), int(spacing + stripe_length)):
        # Left boundary warning
        glColor3f(1.0, 0.0, 0.0)  # Red
        glBegin(GL_QUADS)
        glVertex3f(-ROAD_WIDTH/2 - warning_width, 0.02, z)
        glVertex3f(-ROAD_WIDTH/2, 0.02, z)
        glVertex3f(-ROAD_WIDTH/2, 0.02, z + stripe_length)
        glVertex3f(-ROAD_WIDTH/2 - warning_width, 0.02, z + stripe_length)
        glEnd()
        
        # Right boundary warning
        glBegin(GL_QUADS)
        glVertex3f(ROAD_WIDTH/2, 0.02, z)
        glVertex3f(ROAD_WIDTH/2 + warning_width, 0.02, z)
        glVertex3f(ROAD_WIDTH/2 + warning_width, 0.02, z + stripe_length)
        glVertex3f(ROAD_WIDTH/2, 0.02, z + stripe_length)
        glEnd()
        
        # White stripes between red ones
        glColor3f(1.0, 1.0, 1.0)  # White
        glBegin(GL_QUADS)
        glVertex3f(-ROAD_WIDTH/2 - warning_width, 0.02, z + stripe_length)
        glVertex3f(-ROAD_WIDTH/2, 0.02, z + stripe_length)
        glVertex3f(-ROAD_WIDTH/2, 0.02, z + stripe_length + spacing)
        glVertex3f(-ROAD_WIDTH/2 - warning_width, 0.02, z + stripe_length + spacing)
        glEnd()
        
        glBegin(GL_QUADS)
        glVertex3f(ROAD_WIDTH/2, 0.02, z + stripe_length)
        glVertex3f(ROAD_WIDTH/2 + warning_width, 0.02, z + stripe_length)
        glVertex3f(ROAD_WIDTH/2 + warning_width, 0.02, z + stripe_length + spacing)
        glVertex3f(ROAD_WIDTH/2, 0.02, z + stripe_length + spacing)
        glEnd()
        
        # Add diagonal warning stripes for extra visibility
        glColor3f(1.0, 0.5, 0.0)  # Orange
        glBegin(GL_QUADS)
        # Left diagonal
        glVertex3f(-ROAD_WIDTH/2 - warning_width, 0.03, z)
        glVertex3f(-ROAD_WIDTH/2 - warning_width, 0.03, z + stripe_length)
        glVertex3f(-ROAD_WIDTH/2 - warning_width + 0.5, 0.03, z + stripe_length)
        glVertex3f(-ROAD_WIDTH/2 - warning_width + 0.5, 0.03, z)
        glEnd()
        
        # Right diagonal
        glBegin(GL_QUADS)
        glVertex3f(ROAD_WIDTH/2 + warning_width - 0.5, 0.03, z)
        glVertex3f(ROAD_WIDTH/2 + warning_width - 0.5, 0.03, z + stripe_length)
        glVertex3f(ROAD_WIDTH/2 + warning_width, 0.03, z + stripe_length)
        glVertex3f(ROAD_WIDTH/2 + warning_width, 0.03, z)
        glEnd()
    
    # Wet road reflection if raining
    if weather_mode in ["rain", "heavy_rain"]:
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glColor4f(0.3, 0.3, 0.4, 0.3 * rain_intensity)
        
        glBegin(GL_QUADS)
        glVertex3f(-ROAD_WIDTH/2, 0.02, ROAD_START)
        glVertex3f(ROAD_WIDTH/2, 0.02, ROAD_START)
        glVertex3f(ROAD_WIDTH/2, 0.02, ROAD_END)
        glVertex3f(-ROAD_WIDTH/2, 0.02, ROAD_END)
        glEnd()
        
        glDepthMask(GL_TRUE)

def draw_street_lights():
    """Draw street lights beside the road"""
    phase = get_time_phase()
    lights_on = phase in ["Night", "Dusk", "Dawn"] or weather_mode == "heavy_rain"
    
    for light in street_lights:
        z_pos = light['z']
        
        # Check if this is a special marker
        is_special = 'special' in light
        
        glPushMatrix()
        glTranslatef(light['x'], 0, z_pos)
        
        # Light pole
        if is_special:
            if light['special'] == 'start':
                glColor3f(0, 0.8, 0)  # Green for start
            else:
                glColor3f(0.8, 0, 0)  # Red for finish
        else:
            glColor3f(0.3, 0.3, 0.3)
        
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glutSolidCylinder(0.2, 10, 8, 8)
        glPopMatrix()
        
        # Horizontal arm extending toward road
        glPushMatrix()
        glTranslatef(0, 9.5, 0)
        if light['side'] == 'left':
            glRotatef(-90, 0, 1, 0)
        else:
            glRotatef(90, 0, 1, 0)
        glRotatef(90, 0, 0, 1)
        glutSolidCylinder(0.15, 3, 6, 6)
        glPopMatrix()
        
        # Light fixture
        light_x = 3 if light['side'] == 'left' else -3
        
        if lights_on or is_special:
            glDisable(GL_LIGHTING)
            if is_special:
                if light['special'] == 'start':
                    glColor3f(0, 1, 0)  # Green light for start
                else:
                    glColor3f(1, 0, 0)  # Red light for finish
            else:
                glColor3f(1.0, 1.0, 0.7)
            
            glPushMatrix()
            glTranslatef(light_x, 9.5, 0)
            glutSolidSphere(0.5, 10, 10)
            glPopMatrix()
            
            # Light glow
            glEnable(GL_BLEND)
            if is_special:
                if light['special'] == 'start':
                    glColor4f(0, 1, 0, 0.3)
                else:
                    glColor4f(1, 0, 0, 0.3)
            else:
                glColor4f(1.0, 1.0, 0.5, 0.2)
            
            glPushMatrix()
            glTranslatef(light_x, 9.5, 0)
            glutSolidSphere(2.5, 8, 8)
            glPopMatrix()
            
            glEnable(GL_LIGHTING)
        else:
            glColor3f(0.5, 0.5, 0.5)
            glPushMatrix()
            glTranslatef(light_x, 9.5, 0)
            glutSolidSphere(0.5, 10, 10)
            glPopMatrix()
        
        glPopMatrix()

def draw_buildings():
    """Draw buildings beside the road"""
    for building in buildings:
        z_pos = building['z']
        
        glPushMatrix()
        glTranslatef(building['x'], building['height']/2, z_pos)
        
        # Main building structure
        glColor3f(0.6, 0.6, 0.7)
        glPushMatrix()
        glScalef(building['width'], building['height'], building['depth'])
        glutSolidCube(1)
        glPopMatrix()
        
        # Windows at night
        phase = get_time_phase()
        if phase in ["Night", "Dusk", "Dawn"]:
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 0.5)
            
            # Front windows facing the road
            for floor in range(3, int(building['height']), 5):
                for window_x in range(-int(building['width']/2) + 2, int(building['width']/2) - 1, 3):
                    if random.random() > 0.2:
                        glPushMatrix()
                        if building['x'] > 0:  # Building on right side
                            glTranslatef(window_x, floor - building['height']/2, -building['depth']/2 - 0.1)
                        else:  # Building on left side
                            glTranslatef(window_x, floor - building['height']/2, building['depth']/2 + 0.1)
                        glutSolidCube(1.5)
                        glPopMatrix()
            
            glEnable(GL_LIGHTING)
        
        glPopMatrix()

def draw_trees():
    """Draw trees beside the road"""
    for tree in trees:
        z_pos = tree['z']
        
        glPushMatrix()
        glTranslatef(tree['x'], 0, z_pos)
        
        if tree['type'] == 'pine':
            # Pine tree trunk
            glColor3f(0.4, 0.2, 0.1)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            glutSolidCylinder(0.8, tree['height']/3, 8, 8)
            glPopMatrix()
            
            # Pine tree layers
            glColor3f(0.1, 0.5, 0.1)
            for i in range(3):
                glPushMatrix()
                glTranslatef(0, tree['height']/3 + i*3, 0)
                glRotatef(-90, 1, 0, 0)
                glutSolidCone(4 - i*0.8, 4, 10, 10)
                glPopMatrix()
        
        elif tree['type'] == 'oak':
            # Oak tree trunk
            glColor3f(0.3, 0.15, 0.05)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            glutSolidCylinder(1.0, tree['height']/2, 8, 8)
            glPopMatrix()
            
            # Oak tree crown
            glColor3f(0.2, 0.6, 0.1)
            glPushMatrix()
            glTranslatef(0, tree['height']*0.7, 0)
            glutSolidSphere(tree['height']/2, 12, 12)
            glPopMatrix()
        
        else:  # palm
            # Palm tree trunk
            glColor3f(0.5, 0.3, 0.1)
            for i in range(6):
                glPushMatrix()
                glTranslatef(i*0.15, i*2, 0)
                glRotatef(-90, 1, 0, 0)
                glutSolidCylinder(0.6, 2, 6, 6)
                glPopMatrix()
            
            # Palm leaves
            glColor3f(0.1, 0.7, 0.1)
            for angle in range(0, 360, 45):
                glPushMatrix()
                glTranslatef(0.9, tree['height'], 0)
                glRotatef(angle, 0, 1, 0)
                glRotatef(30, 1, 0, 0)
                glScalef(4, 0.4, 1.2)
                glutSolidCube(1)
                glPopMatrix()
        
        glPopMatrix()

def draw_sky():
    """Draw sky with sun/moon - covers entire visible area, SINGLE COLOR EVERYWHERE."""
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glDisable(GL_DEPTH_TEST)

    sky_colors = get_sky_colors()
    # Pick one color for the whole sky (e.g. 'top')
    solid_color = sky_colors['top']

    # Weather adjustment
    if weather_mode == "heavy_rain":
        solid_color = [c * 0.5 for c in solid_color]
    elif weather_mode == "rain":
        solid_color = [c * 0.7 for c in solid_color]

    glColor3fv(solid_color)
    # Front face
    glBegin(GL_QUADS)
    glVertex3f(-500, -50, -500)
    glVertex3f(500, -50, -500)
    glVertex3f(500, 300, -500)
    glVertex3f(-500, 300, -500)
    glEnd()
    # Right face
    glBegin(GL_QUADS)
    glVertex3f(500, -50, -500)
    glVertex3f(500, -50, 1500)
    glVertex3f(500, 300, 1500)
    glVertex3f(500, 300, -500)
    glEnd()
    # Left face
    glBegin(GL_QUADS)
    glVertex3f(-500, -50, -500)
    glVertex3f(-500, -50, 1500)
    glVertex3f(-500, 300, 1500)
    glVertex3f(-500, 300, -500)
    glEnd()
    # Back face
    glBegin(GL_QUADS)
    glVertex3f(-500, -50, 1500)
    glVertex3f(500, -50, 1500)
    glVertex3f(500, 300, 1500)
    glVertex3f(-500, 300, 1500)
    glEnd()
    # Top face (ceiling)
    glBegin(GL_QUADS)
    glVertex3f(-500, 300, -500)
    glVertex3f(500, 300, -500)
    glVertex3f(500, 300, 1500)
    glVertex3f(-500, 300, 1500)
    glEnd()

    # Sun/Moon
    sun_angle = time_of_day * 2 * math.pi
    sun_x = 100 * math.cos(sun_angle)
    sun_y = 100 * math.sin(sun_angle) + 50
    sun_z = 0  # Changed from -350 to be more centered

    if sun_y > 10:
        glPushMatrix()
        glTranslatef(sun_x, sun_y, sun_z)
        phase = get_time_phase()
        if phase == "Night":
            glColor3f(0.9, 0.9, 1.0)
            glutSolidSphere(5, 16, 16)
            # Add moon glow effect
            glEnable(GL_BLEND)
            glColor4f(0.8, 0.8, 1.0, 0.2)
            glutSolidSphere(10, 12, 12)
        else:
            glColor3fv(sky_colors['sun'])
            glutSolidSphere(8, 20, 20)
            # Add sun glow effect
            glEnable(GL_BLEND)
            glColor4f(sky_colors['sun'][0], sky_colors['sun'][1], sky_colors['sun'][2], 0.3)
            glutSolidSphere(15, 16, 16)
        glPopMatrix()

    # Stars at night
    phase = get_time_phase()
    if phase == "Night":
        glColor3f(1.0, 1.0, 1.0)
        glPointSize(2.0)
        glBegin(GL_POINTS)
        random.seed(42)  # Fixed seed for consistent star positions
        for i in range(100):
            star_x = random.uniform(-450, 450)
            star_y = random.uniform(100, 280)
            star_z = random.uniform(-450, 1400)
            glVertex3f(star_x, star_y, star_z)
        glEnd()
        random.seed()  # Reset seed

    glEnable(GL_DEPTH_TEST)
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)
def draw_clouds():
    """Draw clouds"""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glDepthMask(GL_FALSE)
    
    for cloud in clouds:
        glPushMatrix()
        glTranslatef(cloud['x'], cloud['y'], cloud['z'])
        
        if weather_mode == "heavy_rain":
            glColor4f(0.3, 0.3, 0.4, 0.9)
        elif weather_mode == "rain":
            glColor4f(0.5, 0.5, 0.6, 0.8)
        else:
            glColor4f(1, 1, 1, 0.5)
        
        for i in range(4):
            glPushMatrix()
            glTranslatef(i * cloud['size']/3 - cloud['size']/2, random.uniform(-2, 2), 0)
            glutSolidSphere(cloud['size']/2, 10, 10)
            glPopMatrix()
        
        glPopMatrix()
    
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)

def draw_ground():
    """Draw ground/grass beside the road"""
    glColor3f(0.3, 0.5, 0.2)
    
    # Left side ground
    glBegin(GL_QUADS)
    glVertex3f(-400, -0.1, ROAD_START - 100)
    glVertex3f(-(ROAD_WIDTH/2 + 1), -0.1, ROAD_START - 100)
    glVertex3f(-(ROAD_WIDTH/2 + 1), -0.1, ROAD_END + 100)
    glVertex3f(-400, -0.1, ROAD_END + 100)
    glEnd()
    
    # Right side ground  
    glBegin(GL_QUADS)
    glVertex3f((ROAD_WIDTH/2 + 1), -0.1, ROAD_START - 100)
    glVertex3f(400, -0.1, ROAD_START - 100)
    glVertex3f(400, -0.1, ROAD_END + 100)
    glVertex3f((ROAD_WIDTH/2 + 1), -0.1, ROAD_END + 100)
    glEnd()
    
    # Ground before road start
    glBegin(GL_QUADS)
    glVertex3f(-400, -0.1, ROAD_START - 100)
    glVertex3f(400, -0.1, ROAD_START - 100)
    glVertex3f(400, -0.1, ROAD_START)
    glVertex3f(-400, -0.1, ROAD_START)
    glEnd()
    
    # Ground after road end
    glBegin(GL_QUADS)
    glVertex3f(-400, -0.1, ROAD_END)
    glVertex3f(400, -0.1, ROAD_END)
    glVertex3f(400, -0.1, ROAD_END + 100)
    glVertex3f(-400, -0.1, ROAD_END + 100)
    glEnd()

def draw_road_map():
    """Draw overhead map view of the straight road with vehicle position"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Map background
    map_x = WINDOW_WIDTH - 200
    map_y = WINDOW_HEIGHT - 200
    map_width = 60
    map_height = 180
    
    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(map_x, map_y)
    glVertex2f(map_x + map_width, map_y)
    glVertex2f(map_x + map_width, map_y + map_height)
    glVertex2f(map_x, map_y + map_height)
    glEnd()
    
    # Map border
    glColor3f(0.8, 0.8, 0.8)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(map_x, map_y)
    glVertex2f(map_x + map_width, map_y)
    glVertex2f(map_x + map_width, map_y + map_height)
    glVertex2f(map_x, map_y + map_height)
    glEnd()
    
    # Draw straight road on map
    center_x = map_x + map_width/2
    glColor3f(0.5, 0.5, 0.5)
    glLineWidth(8.0)
    glBegin(GL_LINES)
    glVertex2f(center_x, map_y + 10)
    glVertex2f(center_x, map_y + map_height - 10)
    glEnd()
    
    # Draw start and finish markers
    glColor3f(0, 1, 0)  # Green for start
    glPointSize(10.0)
    glBegin(GL_POINTS)
    glVertex2f(center_x, map_y + map_height - 20)
    glEnd()
    
    glColor3f(1, 0, 0)  # Red for finish
    glBegin(GL_POINTS)
    glVertex2f(center_x, map_y + 20)
    glEnd()
    
    # Draw vehicle position on map (ONLY when game is playing)
    if game_state == "playing":
        # Calculate vehicle position on map
        # Map represents road from ROAD_START to ROAD_END
        # Map height represents this distance
        road_length = ROAD_END - ROAD_START
        map_road_length = map_height - 20  # Leave 10 units margin top and bottom
        
        # Calculate vehicle's Z position relative to road start/end
        vehicle_progress = (player_vehicle.z - ROAD_START) / road_length
        vehicle_map_y = map_y + map_height - 20 - (vehicle_progress * map_road_length)
        
        # Calculate vehicle's X position relative to road width
        road_half_width = ROAD_WIDTH / 2
        vehicle_x_ratio = player_vehicle.x / road_half_width
        vehicle_map_x = center_x + (vehicle_x_ratio * (map_width / 2 - 5))
        
        # Clamp vehicle position to map bounds
        vehicle_map_x = max(map_x + 5, min(map_x + map_width - 5, vehicle_map_x))
        vehicle_map_y = max(map_y + 10, min(map_y + map_height - 10, vehicle_map_y))
        
        # Draw vehicle as a colored dot
        if player_vehicle.type == "cycle":
            glColor3f(1.0, 0.8, 0.0)  # Golden yellow for bicycle
        elif player_vehicle.type == "bike":
            glColor3f(0.0, 0.0, 0.5)  # Dark blue for motorcycle
        else:
            glColor3f(0.8, 0.2, 0.2)  # Red for car
        
        glPointSize(8.0)
        glBegin(GL_POINTS)
        glVertex2f(vehicle_map_x, vehicle_map_y)
        glEnd()
        
        # Draw vehicle direction indicator (small line showing which way it's facing)
        direction_length = 6.0
        angle_rad = math.radians(player_vehicle.rotation)
        dir_x = vehicle_map_x + math.sin(angle_rad) * direction_length
        dir_y = vehicle_map_y - math.cos(angle_rad) * direction_length
        
        glColor3f(1.0, 1.0, 1.0)  # White direction indicator
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(vehicle_map_x, vehicle_map_y)
        glVertex2f(dir_x, dir_y)
        glEnd()
    
    # Map title
    glColor3f(1, 1, 1)
    glRasterPos2f(map_x + 5, map_y + map_height - 15)
    for char in "TRACK MAP":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_hud():
    """Draw HUD with environment information"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Info panel
    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.6)
    glBegin(GL_QUADS)
    glVertex2f(10, WINDOW_HEIGHT - 100)
    glVertex2f(300, WINDOW_HEIGHT - 100)
    glVertex2f(300, WINDOW_HEIGHT - 10)
    glVertex2f(10, WINDOW_HEIGHT - 10)
    glEnd()
    
    # Environment info
    glColor3f(1, 1, 1)
    
    # Time
    time_text = f"Time: {get_time_phase()}"
    glRasterPos2f(20, WINDOW_HEIGHT - 30)
    for char in time_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Weather
    weather_text = f"Weather: {weather_mode.replace('_', ' ').title()}"
    glRasterPos2f(20, WINDOW_HEIGHT - 55)
    for char in weather_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Auto time
    auto_text = f"Auto Time: {'ON' if auto_time else 'OFF'}"
    glRasterPos2f(20, WINDOW_HEIGHT - 80)
    for char in auto_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    # Controls panel
    glColor4f(0, 0, 0, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(10, 10)
    glVertex2f(700, 10)
    glVertex2f(700, 40)
    glVertex2f(10, 40)
    glEnd()
    
    # Controls
    glColor3f(1, 1, 1)
    controls = "1-4: Time (Night/Dawn/Day/Dusk) | R: Weather | T: Auto Time | F: Fog | Arrows: Camera | ESC: Exit"
    glRasterPos2f(15, 22)
    for char in controls:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def update_environment():
    """Update environment animations for fixed road"""
    global time_of_day, game_time
    
    # Update time
    if auto_time:
        time_of_day += time_speed
        if time_of_day > 1.0:
            time_of_day = 0.0
    
    # Update game time
    if game_state == "playing":
        game_time += 0.016  # Assuming 60 FPS
    
    # Update clouds (they still move)
    for cloud in clouds:
        cloud['x'] += 0.05
        if cloud['x'] > 300:
            cloud['x'] = -300
    
    # Update rain
    update_rain_particles()
    
    # Update game objects
    if game_state == "playing":
        player_vehicle.update(keys_pressed)
        check_collisions()
        spawn_objects()
        
        # Update obstacles
        for obstacle in obstacles:
            obstacle.update()
        
        # Update powerups
        for powerup in powerups:
            powerup.update()
        
        # Update speed boost
        global speed_boost_active, speed_boost_timer, speed_boost_stack_count
        if speed_boost_active:
            speed_boost_timer -= 0.016
            if speed_boost_timer <= 0:
                speed_boost_active = False
                speed_boost_stack_count = 0
                print("Speed boost expired!")
        
        # Update boundary hit feedback
        global boundary_hit_timer, boundary_hit_intensity
        if boundary_hit_timer > 0:
            boundary_hit_timer -= 0.016
            boundary_hit_intensity *= 0.95  # Gradually reduce intensity
            if boundary_hit_timer <= 0:
                boundary_hit_intensity = 0.0

def draw_player_vehicle():
    """Draw the player's vehicle"""
    if game_state != "playing":
        return
    
    
    glPushMatrix()
    glTranslatef(player_vehicle.x, player_vehicle.y + player_vehicle.suspension_offset, player_vehicle.z)
    glRotatef(player_vehicle.rotation, 0, 1, 0)
    glRotatef(player_vehicle.tilt_angle, 1, 0, 0)  # Apply tilt for banking effect
    
    # Apply speed boost effect with stacking multiplier
    if speed_boost_active:
        # Increase speed boost effectiveness based on stack count
        current_multiplier = speed_boost_multiplier + (speed_boost_stack_count - 1) * 0.2
        glColor3f(1.0, 0.8, 0.0)  # Golden glow
    else:
        # Vehicle-specific colors based on type
        if player_vehicle.type == "cycle":
            glColor3f(1.0, 0.8, 0.0)  # Golden yellow for bicycle
        elif player_vehicle.type == "bike":
            glColor3f(0.0, 0.0, 0.5)  # Dark blue for motorcycle
        else:
            glColor3f(0.8, 0.2, 0.2)  # Red for car
    
    # Add drift effect glow when drifting
    if abs(player_vehicle.sideways_velocity) > 0.5:
        glEnable(GL_BLEND)
        drift_intensity = min(abs(player_vehicle.sideways_velocity) * 0.5, 0.3)
        glColor4f(1.0, 0.5, 0.0, drift_intensity)  # Orange drift glow
        # Draw drift trail
        glPushMatrix()
        glTranslatef(0, 0.1, 0)
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(0.1, 2.0, 8, 8)
        glPopMatrix()
        glDisable(GL_BLEND)
        glColor3f(0.8, 0.2, 0.2)  # Reset to vehicle color
    
    # Draw vehicle body
    if player_vehicle.type == "cycle":
        draw_motorcycle()
    elif player_vehicle.type == "bike":
        # Rotate bike 180 degrees to make it backward facing from camera POV
        glRotatef(180, 0, 1, 0)
        draw_bike()
    else:
        draw_car()
    
    glPopMatrix()
    
    # Draw shield effect if shields are active
    if shield_count > 0:
        draw_shield_effect()


def draw_shield_effect():
    """Draw a subtle glowing shield effect around the vehicle when shields are active"""
    global shield_count
    
    # Set up for transparent shield effect
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Shield color based on number of shields (more shields = brighter)
    intensity = min(1.0, 0.2 + (shield_count * 0.15))
    glColor4f(0.0, 0.6, 1.0, intensity * 0.4)  # More subtle cyan with transparency
    
    # Draw shield effect around the vehicle
    glPushMatrix()
    # Position at vehicle center, slightly above
    glTranslatef(player_vehicle.x, player_vehicle.y + 0.5, player_vehicle.z)
    
    # Draw a single subtle shield layer
    # Use a smaller, more appropriate size for the vehicle
    glutWireSphere(1.8, 8, 8)  # Much smaller and less detailed
    
    glPopMatrix()
    
    # Disable blending
    glDisable(GL_BLEND)

def draw_car():
    """Draw a highly detailed and realistic sports car"""
    # Main body (lower section) - more aerodynamic
    glColor3f(0.9, 0.1, 0.1)  # Bright red body with metallic sheen
    glPushMatrix()
    glTranslatef(0, 0.6, 0)
    glScalef(2.2, 0.8, 4.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Upper body/cabin - sleeker design
    glPushMatrix()
    glTranslatef(0, 1.2, -0.3)
    glScalef(1.8, 1.0, 2.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Hood - more curved and aerodynamic
    glPushMatrix()
    glTranslatef(0, 0.9, 1.8)
    glScalef(2.0, 0.25, 1.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Front bumper with air intake
    glColor3f(0.6, 0.1, 0.1)  # Darker red
    glPushMatrix()
    glTranslatef(0, 0.4, 2.2)
    glScalef(2.1, 0.3, 0.4)
    glutSolidCube(1)
    glPopMatrix()
    
    # Air intake grille
    glColor3f(0.2, 0.2, 0.2)  # Dark grille
    glPushMatrix()
    glTranslatef(0, 0.5, 2.1)
    glScalef(1.8, 0.2, 0.1)
    glutSolidCube(1)
    glPopMatrix()
    
    # Trunk - more integrated
    glColor3f(0.8, 0.15, 0.15)
    glPushMatrix()
    glTranslatef(0, 0.9, -2.0)
    glScalef(2.0, 0.3, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Side skirts
    glColor3f(0.6, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 0.3, 0)
    glScalef(2.3, 0.1, 4.0)
    glutSolidCube(1)
    glPopMatrix()
    
    # Wheels with much more detail
    wheel_positions = [
        (-1.1, 0.4, -1.6), (1.1, 0.4, -1.6),  # Front wheels
        (-1.1, 0.4, 1.6), (1.1, 0.4, 1.6)     # Rear wheels
    ]
    
    for i, (x, y, z) in enumerate(wheel_positions):
        # Wheel rim - more detailed
        glColor3f(0.3, 0.3, 0.3)  # Dark metallic
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 0, 1, 0)
        glutSolidCylinder(0.5, 0.25, 16, 16)
        glPopMatrix()
        
        # Rim center cap
        glColor3f(0.8, 0.8, 0.8)  # Silver
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 0, 1, 0)
        glutSolidCylinder(0.15, 0.26, 8, 8)
        glPopMatrix()
        
        # Tire with tread pattern
        glColor3f(0.05, 0.05, 0.05)  # Very dark
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 0, 1, 0)
        glutSolidCylinder(0.65, 0.2, 16, 16)
        glPopMatrix()
        
        # Brake caliper
        glColor3f(0.8, 0.2, 0.2)  # Red brake
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(90, 0, 1, 0)
        glutSolidCylinder(0.2, 0.3, 8, 8)
        glPopMatrix()
    
    # Headlights with housing
    glColor3f(0.1, 0.1, 0.1)  # Dark housing
    glPushMatrix()
    glTranslatef(-0.7, 0.8, 2.1)
    glScalef(0.4, 0.3, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.7, 0.8, 2.1)
    glScalef(0.4, 0.3, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Headlight lenses
    glColor3f(1.0, 1.0, 0.9)  # Bright white
    glPushMatrix()
    glTranslatef(-0.7, 0.8, 2.15)
    glutSolidSphere(0.15, 12, 12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.7, 0.8, 2.15)
    glutSolidSphere(0.15, 12, 12)
    glPopMatrix()
    
    # Taillights with housing
    glColor3f(0.1, 0.1, 0.1)  # Dark housing
    glPushMatrix()
    glTranslatef(-0.6, 0.8, -2.1)
    glScalef(0.3, 0.25, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.6, 0.8, -2.1)
    glScalef(0.3, 0.25, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    
    # Taillight lenses
    glColor3f(1.0, 0.2, 0.1)  # Bright red
    glPushMatrix()
    glTranslatef(-0.6, 0.8, -2.18)
    glutSolidSphere(0.12, 10, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.6, 0.8, -2.18)
    glutSolidSphere(0.12, 10, 10)
    glPopMatrix()
    
    # Windows with better proportions
    glColor3f(0.1, 0.15, 0.25)  # Dark blue tint
    # Front windshield
    glPushMatrix()
    glTranslatef(0, 1.6, 0.3)
    glRotatef(20, 1, 0, 0)
    glScalef(1.7, 0.05, 1.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Rear windshield
    glPushMatrix()
    glTranslatef(0, 1.6, -1.2)
    glRotatef(-20, 1, 0, 0)
    glScalef(1.7, 0.05, 1.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Side windows
    glPushMatrix()
    glTranslatef(0, 1.6, -0.5)
    glScalef(1.7, 0.8, 1.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Side mirrors
    glColor3f(0.8, 0.15, 0.15)
    glPushMatrix()
    glTranslatef(-1.2, 1.4, 0.5)
    glScalef(0.1, 0.3, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(1.2, 1.4, 0.5)
    glScalef(0.1, 0.3, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Exhaust pipes
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(-0.4, 0.3, -2.3)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.08, 0.4, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.4, 0.3, -2.3)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.08, 0.4, 8, 8)
    glPopMatrix()
    
    # Spoiler
    glColor3f(0.6, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 1.8, -2.0)
    glScalef(1.5, 0.1, 0.3)
    glutSolidCube(1)
    glPopMatrix()
    
    # Spoiler supports
    glPushMatrix()
    glTranslatef(-0.6, 1.6, -2.0)
    glScalef(0.05, 0.4, 0.05)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.6, 1.6, -2.0)
    glScalef(0.05, 0.4, 0.05)
    glutSolidCube(1)
    glPopMatrix()
    
    # Interior details
    glColor3f(0.05, 0.05, 0.05)  # Very dark interior
    # Dashboard
    glPushMatrix()
    glTranslatef(0, 1.4, 0.8)
    glScalef(1.6, 0.1, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Steering wheel
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 1.3, 0.6)
    glRotatef(90, 1, 0, 0)
    glutSolidTorus(0.15, 0.25, 8, 8)
    glPopMatrix()
    
    # Seats
    glColor3f(0.1, 0.1, 0.1)
    # Driver seat
    glPushMatrix()
    glTranslatef(-0.4, 1.0, 0.2)
    glScalef(0.6, 0.3, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    # Passenger seat
    glPushMatrix()
    glTranslatef(0.4, 1.0, 0.2)
    glScalef(0.6, 0.3, 0.8)
    glutSolidCube(1)
    glPopMatrix()

def draw_bike():
    """Draw a sleek, modern sport motorcycle"""
    
    # Main frame - streamlined and aerodynamic
    glColor3f(0.0, 0.0, 0.8)  # Vibrant blue main body
    glPushMatrix()
    glTranslatef(0, 0.6, 0)
    glScalef(0.8, 0.3, 2.8)  # Slimmer, more aerodynamic
    glutSolidCube(1)
    glPopMatrix()
    
    # Upper fairing - smooth and curved
    glColor3f(0.0, 0.0, 0.8)  # Blue fairing
    glPushMatrix()
    glTranslatef(0, 1.2, 0.4)
    glScalef(0.9, 0.8, 1.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Front fairing - aerodynamic design
    glColor3f(0.0, 0.0, 0.8)  # Blue front fairing
    glPushMatrix()
    glTranslatef(0, 1.4, 0.8)
    glScalef(0.7, 0.6, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Fuel tank - streamlined
    glColor3f(0.0, 0.0, 0.8)  # Blue fuel tank
    glPushMatrix()
    glTranslatef(0, 1.1, -0.2)
    glScalef(0.8, 0.7, 1.0)
    glutSolidCube(1)
    glPopMatrix()
    
    # Seat - integrated design
    glColor3f(0.05, 0.05, 0.05)  # Black seat
    glPushMatrix()
    glTranslatef(0, 1.3, -0.8)
    glScalef(0.7, 0.2, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Seat padding
    glColor3f(0.1, 0.1, 0.1)  # Dark grey padding
    glPushMatrix()
    glTranslatef(0, 1.4, -0.8)
    glScalef(0.6, 0.1, 0.7)
    glutSolidCube(1)
    glPopMatrix()
    
    # Handlebar - sleek design
    glColor3f(0.2, 0.2, 0.2)  # Dark handlebar
    glPushMatrix()
    glTranslatef(0, 1.6, 0.6)
    glScalef(1.2, 0.06, 0.06)
    glutSolidCube(1)
    glPopMatrix()
    
    # Handlebar grips
    glColor3f(0.05, 0.05, 0.05)  # Black grips
    glPushMatrix()
    glTranslatef(-0.6, 1.6, 0.6)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.6, 1.6, 0.6)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    
    # Front fork - slim and modern
    glColor3f(0.4, 0.4, 0.4)  # Metallic fork
    glPushMatrix()
    glTranslatef(0, 0.8, 1.0)
    glScalef(0.08, 1.0, 0.08)
    glutSolidCube(1)
    glPopMatrix()
    
    # Wheels - modern sport bike style
    # Front wheel
    glColor3f(0.1, 0.1, 0.1)  # Dark tire
    glPushMatrix()
    glTranslatef(0, 0, 1.0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.7, 0.15, 16, 16)
    glPopMatrix()
    
    # Front wheel rim - solid disc style
    glColor3f(0.7, 0.7, 0.7)  # Silver rim
    glPushMatrix()
    glTranslatef(0, 0, 1.0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.55, 0.17, 16, 16)
    glPopMatrix()
    
    # Rear wheel - slightly larger
    glColor3f(0.1, 0.1, 0.1)  # Dark tire
    glPushMatrix()
    glTranslatef(0, 0, -1.0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.75, 0.18, 16, 16)
    glPopMatrix()
    
    # Rear wheel rim - solid disc style
    glColor3f(0.7, 0.7, 0.7)  # Silver rim
    glPushMatrix()
    glTranslatef(0, 0, -1.0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.6, 0.2, 16, 16)
    glPopMatrix()
    
    # Exhaust system - sleek and modern
    glColor3f(0.3, 0.3, 0.3)  # Dark metallic
    # Main exhaust pipe
    glPushMatrix()
    glTranslatef(0.4, 0.4, -0.6)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.06, 1.0, 8, 8)
    glPopMatrix()
    
    # Exhaust muffler
    glColor3f(0.2, 0.2, 0.2)  # Darker muffler
    glPushMatrix()
    glTranslatef(0.4, 0.4, -1.5)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.12, 0.3, 8, 8)
    glPopMatrix()
    
    # Headlight - modern LED style
    glColor3f(0.05, 0.05, 0.05)  # Dark housing
    glPushMatrix()
    glTranslatef(0, 1.3, 1.0)
    glScalef(0.4, 0.3, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Headlight lens
    glColor3f(1.0, 1.0, 0.9)  # Bright white
    glPushMatrix()
    glTranslatef(0, 1.3, 1.1)
    glutSolidSphere(0.15, 12, 12)
    glPopMatrix()
    
    # Taillight - modern LED style
    glColor3f(0.05, 0.05, 0.05)  # Dark housing
    glPushMatrix()
    glTranslatef(0, 1.0, -1.8)
    glScalef(0.25, 0.2, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    
    # Taillight lens
    glColor3f(1.0, 0.1, 0.1)  # Bright red
    glPushMatrix()
    glTranslatef(0, 1.0, -1.9)
    glutSolidSphere(0.12, 10, 10)
    glPopMatrix()
    
    # Turn signals - modern LED style
    glColor3f(1.0, 0.6, 0.0)  # Amber
    # Front left
    glPushMatrix()
    glTranslatef(-0.5, 1.2, 1.0)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    # Front right
    glPushMatrix()
    glTranslatef(0.5, 1.2, 1.0)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    # Rear left
    glPushMatrix()
    glTranslatef(-0.3, 0.9, -1.6)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    # Rear right
    glPushMatrix()
    glTranslatef(0.3, 0.9, -1.6)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    
    # Rider - realistic proportions
    glColor3f(0.8, 0.6, 0.5)  # Skin tone
    # Helmet
    glPushMatrix()
    glTranslatef(0, 2.1, -0.6)
    glutSolidSphere(0.2, 12, 12)
    glPopMatrix()
    
    # Helmet visor
    glColor3f(0.1, 0.1, 0.2)  # Dark visor
    glPushMatrix()
    glTranslatef(0, 2.1, -0.8)
    glRotatef(20, 1, 0, 0)
    glScalef(0.15, 0.04, 0.12)
    glutSolidCube(1)
    glPopMatrix()
    
    # Helmet body
    glColor3f(0.0, 0.0, 0.8)  # Blue helmet
    glPushMatrix()
    glTranslatef(0, 2.1, -0.6)
    glutSolidSphere(0.2, 12, 12)
    glPopMatrix()
    
    # Body - racing suit
    glColor3f(0.05, 0.05, 0.05)  # Black suit
    glPushMatrix()
    glTranslatef(0, 1.7, -0.3)
    glScalef(0.6, 1.1, 0.6)
    glutSolidCube(1)
    glPopMatrix()
    
    # Racing suit accents
    glColor3f(0.0, 0.0, 0.8)  # Blue accents
    glPushMatrix()
    glTranslatef(0, 1.7, -0.3)
    glScalef(0.6, 0.08, 0.6)
    glutSolidCube(1)
    glPopMatrix()
    
    # Arms - realistic positioning
    glColor3f(0.05, 0.05, 0.05)
    # Left arm
    glPushMatrix()
    glTranslatef(-0.35, 1.5, -0.6)
    glRotatef(40, 0, 0, 1)
    glScalef(0.15, 0.5, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    # Right arm
    glPushMatrix()
    glTranslatef(0.35, 1.5, -0.6)
    glRotatef(-40, 0, 0, 1)
    glScalef(0.15, 0.5, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    
    # Legs - realistic positioning
    glColor3f(0.05, 0.05, 0.05)
    # Left leg
    glPushMatrix()
    glTranslatef(-0.15, 1.0, 0.1)
    glScalef(0.2, 0.7, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    # Right leg
    glPushMatrix()
    glTranslatef(0.15, 1.0, 0.1)
    glScalef(0.2, 0.7, 0.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Foot pegs
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(-0.25, 0.2, -0.6)
    glScalef(0.08, 0.08, 0.25)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.25, 0.2, -0.6)
    glScalef(0.08, 0.08, 0.25)
    glutSolidCube(1)
    glPopMatrix()
    
    # Instrument cluster - modern digital style
    glColor3f(0.05, 0.05, 0.05)  # Dark housing
    glPushMatrix()
    glTranslatef(0, 1.5, -1.0)
    glScalef(0.35, 0.15, 0.08)
    glutSolidCube(1)
    glPopMatrix()
    
    # Speedometer display
    glColor3f(0.0, 0.8, 0.0)  # Green digital display
    glPushMatrix()
    glTranslatef(0, 1.5, -0.96)
    glScalef(0.25, 0.1, 0.01)
    glutSolidCube(1)
    glPopMatrix()
    
    # Side panels - sleek design
    glColor3f(0.05, 0.05, 0.05)  # Black side panels
    glPushMatrix()
    glTranslatef(0, 0.4, 0)
    glScalef(0.9, 0.2, 2.5)
    glutSolidCube(1)
    glPopMatrix()
    
    # Engine cover - streamlined
    glColor3f(0.3, 0.3, 0.4)  # Metallic engine cover
    glPushMatrix()
    glTranslatef(0, 0.5, 0)
    glScalef(0.7, 0.4, 1.5)
    glutSolidCube(1)
    glPopMatrix()

def draw_motorcycle():
    """Draw a highly detailed and realistic racing bicycle"""
    # Main frame (diamond shape) - more realistic proportions and better wheel alignment
    glColor3f(1.0, 0.7, 0.0)  # Bright gold frame with metallic sheen
    # Top tube - connects head tube to seat tube
    glPushMatrix()
    glTranslatef(0, 1.3, 0)
    glRotatef(-25, 1, 0, 0)
    glScalef(0.08, 0.08, 1.6)
    glutSolidCube(1)
    glPopMatrix()
    
    # Down tube - connects head tube to bottom bracket
    glPushMatrix()
    glTranslatef(0, 0.7, 0)
    glRotatef(35, 1, 0, 0)
    glScalef(0.08, 0.08, 1.6)
    glutSolidCube(1)
    glPopMatrix()
    
    # Seat tube - connects seat to bottom bracket
    glPushMatrix()
    glTranslatef(0, 0.4, -0.9)
    glScalef(0.08, 1.1, 0.08)
    glutSolidCube(1)
    glPopMatrix()
    
    # Head tube - connects top tube and down tube to front fork
    glPushMatrix()
    glTranslatef(0, 1.1, 0.9)
    glScalef(0.08, 0.9, 0.08)
    glutSolidCube(1)
    glPopMatrix()
    
    # Chain stays - connect bottom bracket to rear wheel
    glPushMatrix()
    glTranslatef(0, 0.3, -0.7)
    glScalef(0.06, 0.06, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Seat tube support - additional bracing
    glPushMatrix()
    glTranslatef(0, 0.6, -0.8)
    glRotatef(-15, 1, 0, 0)
    glScalef(0.06, 0.06, 0.4)
    glutSolidCube(1)
    glPopMatrix()
    
    # Bottom bracket - connects down tube, seat tube, and chain stays
    glColor3f(0.8, 0.5, 0.0)  # Darker gold
    glPushMatrix()
    glTranslatef(0, 0.3, -0.9)
    glScalef(0.12, 0.12, 0.12)
    glutSolidCube(1)
    glPopMatrix()
    
    # Seat - more comfortable looking
    glColor3f(0.05, 0.05, 0.05)  # Very dark
    glPushMatrix()
    glTranslatef(0, 1.1, -0.9)
    glScalef(0.25, 0.08, 0.35)
    glutSolidCube(1)
    glPopMatrix()
    
    # Seat padding
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 1.15, -0.9)
    glScalef(0.2, 0.03, 0.3)
    glutSolidCube(1)
    glPopMatrix()
    
    # Handlebar with more detail
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(0, 1.5, 0.9)
    glScalef(0.9, 0.08, 0.08)
    glutSolidCube(1)
    glPopMatrix()
    
    # Handlebar grips
    glColor3f(0.1, 0.1, 0.1)  # Black grips
    glPushMatrix()
    glTranslatef(-0.4, 1.5, 0.9)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.4, 1.5, 0.9)
    glutSolidSphere(0.06, 8, 8)
    glPopMatrix()
    
    # Front fork
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(0, 0.8, 1.0)  # Aligned with front wheel position
    glScalef(0.06, 0.8, 0.06)
    glutSolidCube(1)
    glPopMatrix()
    
    # Simple wheels - back to working version
    # Front wheel
    glColor3f(0.1, 0.1, 0.1)  # Dark tire
    glPushMatrix()
    glTranslatef(0, 0, 1.0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.6, 0.1, 16, 16)
    glPopMatrix()
    
    # Front wheel rim
    glColor3f(0.8, 0.8, 0.8)  # Silver rim
    glPushMatrix()
    glTranslatef(0, 0, 1.0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.5, 0.12, 16, 16)
    glPopMatrix()
    
    # Rear wheel
    glColor3f(0.1, 0.1, 0.1)  # Dark tire
    glPushMatrix()
    glTranslatef(0, 0, -0.9)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.6, 0.1, 16, 16)
    glPopMatrix()
    
    # Rear wheel rim
    glColor3f(0.8, 0.8, 0.8)  # Silver rim
    glPushMatrix()
    glTranslatef(0, 0, -0.9)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.5, 0.12, 16, 16)
    glPopMatrix()
    
    # Pedals with more detail
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(0, 0.25, -0.9)
    glScalef(0.35, 0.08, 0.12)
    glutSolidCube(1)
    glPopMatrix()
    
    # Pedal arms
    glColor3f(0.3, 0.3, 0.3)  # Darker
    glPushMatrix()
    glTranslatef(0, 0.4, -0.9)
    glScalef(0.06, 0.3, 0.06)
    glutSolidCube(1)
    glPopMatrix()
    
    # Chainring
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(0, 0.3, -0.9)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.25, 0.04, 16, 16)
    glPopMatrix()
    
    # Chainring teeth
    glColor3f(0.3, 0.3, 0.3)  # Darker
    for angle in range(0, 360, 20):
        glPushMatrix()
        glTranslatef(0, 0.3, -0.9)
        glRotatef(angle, 0, 1, 0)
        glTranslatef(0.25, 0, 0)
        glRotatef(90, 0, 1, 0)
        glutSolidCylinder(0.02, 0.05, 4, 4)
        glPopMatrix()
    
    # Brake system
    glColor3f(0.2, 0.2, 0.2)  # Dark
    # Front brake
    glPushMatrix()
    glTranslatef(0, 0.4, 1.0)  # Aligned with front wheel position
    glScalef(0.15, 0.1, 0.05)
    glutSolidCube(1)
    glPopMatrix()
    # Rear brake
    glPushMatrix()
    glTranslatef(0, 0.4, -0.9)  # Aligned with rear wheel position
    glScalef(0.15, 0.1, 0.05)
    glutSolidCube(1)
    glPopMatrix()
    
    # Gear shifters
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(-0.3, 1.4, 0.9)
    glutSolidSphere(0.04, 8, 8)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.3, 1.4, 0.9)
    glutSolidSphere(0.04, 8, 8)
    glPopMatrix()
    
    # Rider with much more detail
    glColor3f(0.8, 0.6, 0.5)  # Skin tone
    # Head
    glPushMatrix()
    glTranslatef(0, 1.9, 0.4)
    glutSolidSphere(0.18, 16, 16)
    glPopMatrix()
    
    # Helmet
    glColor3f(0.1, 0.1, 0.1)  # Black helmet
    glPushMatrix()
    glTranslatef(0, 2.0, 0.4)
    glutSolidSphere(0.2, 16, 16)
    glPopMatrix()
    
    # Helmet visor
    glColor3f(0.1, 0.15, 0.25)  # Dark blue tint
    glPushMatrix()
    glTranslatef(0, 2.0, 0.55)
    glRotatef(-15, 1, 0, 0)
    glScalef(0.15, 0.02, 0.1)
    glutSolidCube(1)
    glPopMatrix()
    
    # Body - racing jersey
    glColor3f(0.8, 0.2, 0.2)  # Red jersey
    glPushMatrix()
    glTranslatef(0, 1.5, 0.2)
    glScalef(0.5, 0.9, 0.3)
    glutSolidCube(1)
    glPopMatrix()
    
    # Jersey details
    glColor3f(0.1, 0.1, 0.1)  # Black accents
    glPushMatrix()
    glTranslatef(0, 1.5, 0.2)
    glScalef(0.5, 0.05, 0.3)
    glutSolidCube(1)
    glPopMatrix()
    
    # Shorts
    glColor3f(0.0, 0.0, 0.6)  # Dark blue shorts
    glPushMatrix()
    glTranslatef(0, 1.1, -0.1)
    glScalef(0.45, 0.4, 0.25)
    glutSolidCube(1)
    glPopMatrix()
    
    # Shorts details
    glColor3f(0.1, 0.1, 0.1)  # Black accents
    glPushMatrix()
    glTranslatef(0, 1.1, -0.1)
    glScalef(0.45, 0.05, 0.25)
    glutSolidCube(1)
    glPopMatrix()
    
    # Arms
    glColor3f(0.8, 0.6, 0.5)  # Skin tone
    # Left arm
    glPushMatrix()
    glTranslatef(-0.3, 1.4, 0.3)
    glRotatef(-30, 0, 0, 1)
    glScalef(0.15, 0.5, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    # Right arm
    glPushMatrix()
    glTranslatef(0.3, 1.4, 0.3)
    glRotatef(30, 0, 0, 1)
    glScalef(0.15, 0.5, 0.15)
    glutSolidCube(1)
    glPopMatrix()
    
    # Legs
    glColor3f(0.8, 0.6, 0.5)  # Skin tone
    # Left leg
    glPushMatrix()
    glTranslatef(-0.15, 1.0, -0.2)
    glScalef(0.18, 0.7, 0.18)
    glutSolidCube(1)
    glPopMatrix()
    # Right leg
    glPushMatrix()
    glTranslatef(0.15, 1.0, -0.2)
    glScalef(0.18, 0.7, 0.18)
    glutSolidCube(1)
    glPopMatrix()
    
    # Cycling shoes
    glColor3f(0.1, 0.1, 0.1)  # Black shoes
    glPushMatrix()
    glTranslatef(-0.15, 0.25, -0.9)
    glScalef(0.12, 0.08, 0.25)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.15, 0.25, -0.9)
    glScalef(0.12, 0.08, 0.25)
    glutSolidCube(1)
    glPopMatrix()
    
    # Water bottle
    glColor3f(0.0, 0.6, 0.8)  # Blue bottle
    glPushMatrix()
    glTranslatef(0.4, 1.0, -0.3)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.08, 0.3, 8, 8)
    glPopMatrix()
    
    # Bottle cage
    glColor3f(0.4, 0.4, 0.4)  # Metallic
    glPushMatrix()
    glTranslatef(0.4, 1.0, -0.3)
    glScalef(0.15, 0.1, 0.35)
    glutSolidCube(1)
    glPopMatrix()
    
    # Add some final details
    # Water bottle cap
    glColor3f(0.2, 0.2, 0.2)  # Dark cap
    glPushMatrix()
    glTranslatef(0.4, 1.0, -0.3)
    glutSolidSphere(0.08, 8, 8)
    glPopMatrix()
    
    # Frame decals
    glColor3f(0.8, 0.5, 0.0)  # Lighter gold
    glPushMatrix()
    glTranslatef(0, 1.0, 0)
    glScalef(0.1, 0.05, 0.8)
    glutSolidCube(1)
    glPopMatrix()
    
    # Racing number
    glColor3f(1.0, 1.0, 1.0)  # White
    glPushMatrix()
    glTranslatef(0, 1.2, 0.2)
    glScalef(0.3, 0.1, 0.1)
    glutSolidCube(1)
    glPopMatrix()

def draw_obstacles():
    """Draw all obstacles"""
    for obstacle in obstacles:
        if obstacle.collected:
            continue
        

        
        glPushMatrix()
        glTranslatef(obstacle.x, obstacle.y, obstacle.z)
        glRotatef(obstacle.rotation, 0, 1, 0)
        
        glColor3f(0.8, 0.4, 0.2)  # Brown color
        
        if obstacle.type == "box":
            glScalef(obstacle.size[0], obstacle.size[1], obstacle.size[2])
            glutSolidCube(1)
        else:  # cylinder
            glRotatef(90, 1, 0, 0)
            glutSolidCylinder(obstacle.size[0]/2, obstacle.size[2], 8, 8)
        
        glPopMatrix()

def draw_powerups():
    """Draw all powerups with realistic icons and hovering animations"""
    for powerup in powerups:
        if powerup.collected:
            continue
        

        
        glPushMatrix()
        glTranslatef(powerup.x, powerup.y, powerup.z)
        glRotatef(powerup.rotation, 0, 1, 0)
        glScalef(powerup.scale, powerup.scale, powerup.scale)
        
        if powerup.type == "speed":
            # Lightning bolt powerup
            glColor3f(1.0, 1.0, 0.0)  # Bright yellow
            
            # Draw lightning bolt using multiple cubes
            # Main bolt body
            glPushMatrix()
            glTranslatef(0, 0, 0)
            glRotatef(45, 0, 0, 1)
            glScalef(0.1, 0.8, 0.1)
            glutSolidCube(1)
            glPopMatrix()
            
            # Top branch
            glPushMatrix()
            glTranslatef(-0.2, 0.3, 0)
            glRotatef(-30, 0, 0, 1)
            glScalef(0.1, 0.4, 0.1)
            glutSolidCube(1)
            glPopMatrix()
            
            # Bottom branch
            glPushMatrix()
            glTranslatef(0.2, -0.3, 0)
            glRotatef(30, 0, 0, 1)
            glScalef(0.1, 0.4, 0.1)
            glutSolidCube(1)
            glPopMatrix()
            
            # Add lightning glow effect
            glEnable(GL_BLEND)
            glColor4f(1.0, 1.0, 0.0, 0.4)
            glPushMatrix()
            glTranslatef(0, 0, 0)
            glutSolidSphere(0.8, 8, 8)
            glPopMatrix()
            glDisable(GL_BLEND)
            
        else:  # shield
            # Shield powerup
            glColor3f(0.0, 0.8, 1.0)  # Bright blue
            
            # Draw shield using curved shape (approximated with cubes)
            # Main shield body
            glPushMatrix()
            glTranslatef(0, 0, 0)
            glScalef(0.6, 0.8, 0.1)
            glutSolidCube(1)
            glPopMatrix()
            
            # Shield top curve
            glPushMatrix()
            glTranslatef(0, 0.4, 0)
            glScalef(0.4, 0.2, 0.1)
            glutSolidCube(1)
            glPopMatrix()
            
            # Shield handle
            glColor3f(0.8, 0.6, 0.2)  # Gold handle
            glPushMatrix()
            glTranslatef(0, -0.2, 0)
            glScalef(0.1, 0.3, 0.1)
            glutSolidCube(1)
            glPopMatrix()
            
            # Shield cross
            glColor3f(1.0, 1.0, 1.0)  # White cross
            glPushMatrix()
            glTranslatef(0, 0, 0.06)
            glScalef(0.1, 0.4, 0.02)
            glutSolidCube(1)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, 0, 0.06)
            glScalef(0.4, 0.1, 0.02)
            glutSolidCube(1)
            glPopMatrix()
            
            # Add shield glow effect
            glEnable(GL_BLEND)
            glColor4f(0.0, 0.8, 1.0, 0.3)
            glPushMatrix()
            glTranslatef(0, 0, 0)
            glutSolidSphere(0.8, 8, 8)
            glPopMatrix()
            glDisable(GL_BLEND)
        
        glPopMatrix()

def draw_game_hud():
    """Draw game-specific HUD elements"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Game info panel
    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(10, WINDOW_HEIGHT - 150)
    glVertex2f(350, WINDOW_HEIGHT - 150)
    glVertex2f(350, WINDOW_HEIGHT - 10)
    glVertex2f(10, WINDOW_HEIGHT - 10)
    glEnd()
    
    # Game info
    glColor3f(1, 1, 1)
    
    # Game state
    state_text = f"Game: {game_state.upper()}"
    glRasterPos2f(20, WINDOW_HEIGHT - 30)
    for char in state_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Lives
    lives_text = f"Lives: {lives}"
    glRasterPos2f(20, WINDOW_HEIGHT - 55)
    for char in lives_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Score
    score_text = f"Score: {score}"
    glRasterPos2f(20, WINDOW_HEIGHT - 80)
    for char in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Game time
    time_text = f"Time: {game_time:.1f}s"
    glRasterPos2f(20, WINDOW_HEIGHT - 105)
    for char in time_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Camera mode
    current_mode = camera_modes[camera_mode]
    camera_text = f"Camera: {current_mode}"
    glRasterPos2f(20, WINDOW_HEIGHT - 130)
    for char in camera_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Vehicle type
    vehicle_text = f"Vehicle: {player_vehicle.type.title()}"
    glRasterPos2f(20, WINDOW_HEIGHT - 155)
    for char in vehicle_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Rotation restriction indicator
    if player_vehicle.z > ROAD_START + 5:  # Vehicle has crossed start line
        glColor3f(0.8, 0.6, 0.0)  # Orange color for restriction notice
        restriction_text = "Rotation Restricted: Forward Only"
        glRasterPos2f(20, WINDOW_HEIGHT - 155)
        for char in restriction_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Reset color for other elements
    glColor3f(1, 1, 1)
    
    # Powerup status - Updated for stackable system
    if shield_count > 0:
        shield_text = f"Shields: {shield_count}"
        glColor3f(0, 1, 1)
        glRasterPos2f(20, WINDOW_HEIGHT - 155)
        for char in shield_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    if speed_boost_active:
        boost_text = f"Speed Boost: {speed_boost_timer:.1f}s (x{speed_boost_stack_count})"
        glColor3f(1, 1, 0)
        glRasterPos2f(200, WINDOW_HEIGHT - 155)
        for char in boost_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Road boundary warning
    if game_state == "playing":
        road_left_edge = -ROAD_WIDTH / 2
        road_right_edge = ROAD_WIDTH / 2
        distance_to_left = player_vehicle.x - road_left_edge
        distance_to_right = road_right_edge - player_vehicle.x
        
        # Warning when close to edges (within 3 units)
        if distance_to_left < 3.0 or distance_to_right < 3.0:
            warning_color = [1.0, 0.0, 0.0] if min(distance_to_left, distance_to_right) < 1.5 else [1.0, 1.0, 0.0]
            glColor3f(*warning_color)
            
            if distance_to_left < distance_to_right:
                warning_text = f"LEFT EDGE WARNING: {distance_to_left:.1f}m"
                glRasterPos2f(350, WINDOW_HEIGHT - 155)
            else:
                warning_text = f"RIGHT EDGE WARNING: {distance_to_right:.1f}m"
                glRasterPos2f(350, WINDOW_HEIGHT - 155)
            
            for char in warning_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Warning when close to start line (trying to go backwards)
        distance_to_start = player_vehicle.z - (ROAD_START + 5)
        if distance_to_start < 3.0:
            warning_color = [1.0, 0.0, 0.0] if distance_to_start < 1.5 else [1.0, 1.0, 0.0]
            glColor3f(*warning_color)
            warning_text = f"START LINE WARNING: {distance_to_start:.1f}m"
            glRasterPos2f(350, WINDOW_HEIGHT - 175)
            for char in warning_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Game over screen
    if game_state == "game_over":
        glColor4f(0, 0, 0, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 - 100)
        glVertex2f(WINDOW_WIDTH/2 + 200, WINDOW_HEIGHT/2 - 100)
        glVertex2f(WINDOW_WIDTH/2 + 200, WINDOW_HEIGHT/2 + 100)
        glVertex2f(WINDOW_WIDTH/2 - 200, WINDOW_HEIGHT/2 + 100)
        glEnd()
        
        glColor3f(1, 1, 1)
        if lives <= 0:
            game_over_text = "GAME OVER"
            glRasterPos2f(WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2 + 20)
            for char in game_over_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
            
            restart_text = "Press SPACE to return to menu"
            glRasterPos2f(WINDOW_WIDTH/2 - 120, WINDOW_HEIGHT/2 - 20)
            for char in restart_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        else:
            finish_text = "FINISHED!"
            glRasterPos2f(WINDOW_WIDTH/2 - 60, WINDOW_HEIGHT/2 + 20)
            for char in finish_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
            
            restart_text = "Press SPACE to return to menu"
            glRasterPos2f(WINDOW_WIDTH/2 - 120, WINDOW_HEIGHT/2 - 20)
            for char in restart_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Controls panel
    glColor4f(0, 0, 0, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(10, 10)
    glVertex2f(800, 10)
    glVertex2f(800, 70)
    glVertex2f(10, 70)
    glEnd()
    
    # Controls
    glColor3f(1, 1, 1)
    controls = "W or Up: Forward | S or Down: Brake (slow down) | A/D or Left/Right: Turn | 1-3: Change Vehicle | SPACE: Restart | C: Camera | ESC: Exit"
    glRasterPos2f(15, 25)
    for char in controls:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    vehicle_controls = "Vehicle Types: 1=Cycle (fast turning), 2=Bike (balanced), 3=Car (high speed)"
    glRasterPos2f(15, 45)
    for char in vehicle_controls:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_main_menu():
    """Draw the main menu interface"""
    global menu_selection, menu_page, selected_vehicle, difficulty
    
    # Disable depth testing for 2D overlay
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Draw semi-transparent background overlay
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.7)  # Dark overlay
    glBegin(GL_QUADS)
    glVertex2f(-1, -1)
    glVertex2f(1, -1)
    glVertex2f(1, 1)
    glVertex2f(-1, 1)
    glEnd()
    glDisable(GL_BLEND)
    
    # Set up 2D orthographic projection for menu
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    if menu_page == "main":
        # Main menu title
        glColor3f(1.0, 1.0, 0.0)  # Yellow title
        glRasterPos2f(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT - 100)
        title = "🏁 RACING GAME 🏁"
        for char in title:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
        
        # Menu options
        menu_options = ["Play Game", "Settings", "Instructions", "High Scores", "Exit"]
        start_y = WINDOW_HEIGHT // 2 + 50
        
        for i, option in enumerate(menu_options):
            if i == menu_selection:
                glColor3f(1.0, 0.8, 0.0)  # Bright yellow for selection
                # Draw selection arrow
                glRasterPos2f(WINDOW_WIDTH // 2 - 200, start_y - i * 40)
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('▶'))
            else:
                glColor3f(0.8, 0.8, 0.8)  # Gray for unselected
            
            glRasterPos2f(WINDOW_WIDTH // 2 - 150, start_y - i * 40)
            for char in option:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Current settings display
        glColor3f(0.6, 0.6, 0.6)
        glRasterPos2f(50, 100)
        settings_text = f"Vehicle: {selected_vehicle.title()} | Difficulty: {difficulty.title()}"
        for char in settings_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
        
        # Controls hint
        glColor3f(0.5, 0.5, 0.5)
        glRasterPos2f(50, 50)
        controls_text = "Use ↑↓ to navigate, ENTER to select, ESC to exit"
        for char in controls_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
        
        # Debug info
        glColor3f(0.3, 0.3, 0.3)
        glRasterPos2f(50, 20)
        debug_text = f"Selection: {menu_selection}, Page: {menu_page}"
        for char in debug_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(char))
    
    elif menu_page == "settings":
        # Settings page
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 100)
        title = "⚙️ SETTINGS"
        for char in title:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
        
        # Vehicle selection
        glColor3f(0.8, 0.8, 0.8)
        glRasterPos2f(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 + 50)
        vehicle_text = "Vehicle Type:"
        for char in vehicle_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        vehicles = ["Cycle (Fast turning)", "Bike (Balanced)", "Car (High speed)"]
        vehicle_types = ["cycle", "bike", "car"]
        
        for i, (vehicle, vtype) in enumerate(zip(vehicles, vehicle_types)):
            if vtype == selected_vehicle:
                glColor3f(1.0, 0.8, 0.0)
                glRasterPos2f(WINDOW_WIDTH // 2 - 180, WINDOW_HEIGHT // 2 - i * 30)
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('●'))
            else:
                glColor3f(0.6, 0.6, 0.6)
            
            glRasterPos2f(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - i * 30)
            for char in vehicle:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        
        # Navigation instructions
        glColor3f(0.8, 0.8, 0.8)
        glRasterPos2f(WINDOW_WIDTH // 2 - 100, 150)
        nav_text = "Use ↑↓ to change vehicle, ESC to go back"
        for char in nav_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
        
        # Quick selection hint
        glColor3f(0.6, 0.6, 0.6)
        glRasterPos2f(WINDOW_WIDTH // 2 - 80, 120)
        quick_text = "Or press 1/2/3 for quick selection"
        for char in quick_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(char))
    
    elif menu_page == "instructions":
        # Instructions page
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT - 100)
        title = "📖 INSTRUCTIONS"
        for char in title:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
        
        # Instructions text
        instructions = [
            "CONTROLS:",
            "W/↑: Accelerate",
            "S/↓: Brake",
            "A/D or ←/→: Turn",
            "1/2/3: Change Vehicle",
            "SPACE: Restart (in game)",
            "",
            "CAMERA MODES:",
            "C: Cycle through camera modes",
            "V: Quick switch to Chase Cam",
            "B: Quick switch to Drone Cam",
            "",
            "• Chase: Standard following camera",
            "• Drone: High, wide, strategic view",
            "• Cinematic: Smooth, movie-like",
            "• Free: Balanced, versatile view",
            "",
            "OBJECTIVES:",
            "• Reach the finish line",
            "• Avoid obstacles",
            "• Collect powerups",
            "• Don't fall off the road!",
            "",
            "POWERUPS:",
            "• Speed Boost: Increases speed",
            "• Shield: Protects from collisions"
        ]
        
        start_y = WINDOW_HEIGHT - 150
        for i, instruction in enumerate(instructions):
            if instruction.endswith(":"):
                glColor3f(1.0, 0.8, 0.0)  # Yellow for headers
            else:
                glColor3f(0.8, 0.8, 0.8)  # Gray for content
            
            glRasterPos2f(100, start_y - i * 25)
            for char in instruction:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
        
        # Back option
        glColor3f(0.8, 0.8, 0.8)
        glRasterPos2f(WINDOW_WIDTH // 2 - 50, 50)
        back_text = "Press ESC to go back"
        for char in back_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    elif menu_page == "high_scores":
        # High scores page
        glColor3f(1.0, 1.0, 0.0)
        glRasterPos2f(WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT - 100)
        title = "🏆 HIGH SCORES 🏆"
        for char in title:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
        
        # High scores list
        if not high_scores:
            glColor3f(0.8, 0.8, 0.8)
            glRasterPos2f(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2)
            no_scores_text = "No high scores yet!"
            for char in no_scores_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
            
            glRasterPos2f(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 40)
            play_text = "Complete a race to set your first high score!"
            for char in play_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
        else:
            # Display top 10 high scores
            glColor3f(0.8, 0.8, 0.8)
            glRasterPos2f(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT - 150)
            header_text = "Rank  Time     Vehicle  Date"
            for char in header_text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
            
            start_y = WINDOW_HEIGHT - 180
            for i, (time_val, vehicle, date) in enumerate(high_scores[:10]):
                # Highlight top 3 scores
                if i < 3:
                    if i == 0:
                        glColor3f(1.0, 0.8, 0.0)  # Gold for 1st
                    elif i == 1:
                        glColor3f(0.8, 0.8, 0.8)  # Silver for 2nd
                    else:
                        glColor3f(0.8, 0.5, 0.2)  # Bronze for 3rd
                else:
                    glColor3f(0.6, 0.6, 0.6)  # Gray for others
                
                # Format the score line
                rank = f"{i+1:2d}."
                time_str = f"{time_val:6.2f}s"
                vehicle_str = f"{vehicle:8s}"
                date_str = date[:10]  # Just the date part
                
                score_text = f"{rank}  {time_str}  {vehicle_str}  {date_str}"
                glRasterPos2f(WINDOW_WIDTH // 2 - 200, start_y - i * 25)
                for char in score_text:
                    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
        
        # Back option
        glColor3f(0.8, 0.8, 0.8)
        glRasterPos2f(WINDOW_WIDTH // 2 - 50, 50)
        back_text = "Press ESC to go back"
        for char in back_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    # Restore 3D projection
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    # Re-enable depth testing and lighting
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def display():
    """Main display function"""
    # Update clear color based on time
    update_clear_color()
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    setup_camera()
    setup_lighting()
    setup_fog()
    
    # Draw scene in proper order
    draw_sky()
    draw_ground()
    draw_road()
    draw_street_lights()
    draw_buildings()
    draw_trees()
    draw_clouds()
    draw_rain()
    
    # Draw game objects
    draw_obstacles()
    draw_powerups()
    draw_player_vehicle()
    
    # Draw UI elements
    if game_state == "main_menu":
        draw_main_menu()
    else:
        draw_road_map()
        draw_hud()
        draw_game_hud()
    
    update_environment()
    
    glutSwapBuffers()

def keyboard(key, x, y):
    """Handle keyboard input"""
    global weather_mode, time_of_day, auto_time, use_fog, game_state, player_vehicle, lives, score, game_time
    global menu_selection, menu_page, selected_vehicle, difficulty, camera_mode, camera_follow_vehicle
    
    # Handle main menu navigation
    if game_state == "main_menu":
        print(f"Menu key pressed: {key}, selection: {menu_selection}, page: {menu_page}")  # Debug
        if key == b'\r' or key == b'\n' or key == b' ':  # Enter key or Space
            print(f"Enter/Space pressed, selection: {menu_selection}")  # Debug
            if menu_page == "main":
                if menu_selection == 0:  # Play Game
                    game_state = "playing"
                    player_vehicle = Vehicle(selected_vehicle)
                    print(f"Starting game with {selected_vehicle}!")
                    print("Game started successfully!")
                elif menu_selection == 1:  # Settings
                    menu_page = "settings"
                    menu_selection = 0  # Reset selection for settings
                    print("Entered settings page")
                elif menu_selection == 2:  # Instructions
                    menu_page = "instructions"
                    print("Entered instructions page")
                elif menu_selection == 3:  # High Scores
                    menu_page = "high_scores"
                    print("Entered high scores page")
                elif menu_selection == 4:  # Exit
                    print("Thanks for playing!")
                    print("Exiting game...")  # Debug
                    import os
                    os._exit(0)  # Force exit
        elif key == b'\x1b':  # Escape key
            if menu_page == "main":
                print("Thanks for playing!")
                import os
                os._exit(0)  # Force exit
            else:
                menu_page = "main"
                menu_selection = 0
        elif key == b'1' and menu_page == "settings":
            selected_vehicle = "cycle"
        elif key == b'2' and menu_page == "settings":
            selected_vehicle = "bike"
        elif key == b'3' and menu_page == "settings":
            selected_vehicle = "car"
        return  # Don't process other keys when in menu
    
    if key == b'1':  # Change to cycle
        if game_state == "playing":
            player_vehicle = Vehicle("cycle")
            print("Switched to Cycle - Fast turning, lower speed")
    elif key == b'2':  # Change to bike
        if game_state == "playing":
            player_vehicle = Vehicle("bike")
            print("Switched to Bike - Balanced performance")
    elif key == b'3':  # Change to car
        if game_state == "playing":
            player_vehicle = Vehicle("car")
            print("Switched to Car - High speed, slower turning")
    elif key == b' ':  # Space bar - return to main menu
        if game_state == "game_over":
            game_state = "main_menu"
            menu_selection = 0
            menu_page = "main"
            lives = 3
            score = 0
            game_time = 0.0
            player_vehicle.reset_position()
            obstacles.clear()
            powerups.clear()
            shield_count = 0
            speed_boost_active = False
            speed_boost_timer = 0.0
            speed_boost_stack_count = 0
            
            # Reset camera position
            global current_camera_x, current_camera_y, current_camera_z
            current_camera_x = 0.0
            current_camera_y = 30.0
            current_camera_z = 60.0
            
            # Reset boundary feedback
            global boundary_hit_timer, boundary_hit_intensity
            boundary_hit_timer = 0.0
            boundary_hit_intensity = 0.0
            
            print("Returned to main menu!")
    elif key == b'4':  # Dusk
        time_of_day = 0.75
        auto_time = False
    elif key == b'r' or key == b'R':  # Cycle weather
        modes = ["clear", "rain", "heavy_rain"]
        idx = modes.index(weather_mode)
        weather_mode = modes[(idx + 1) % len(modes)]
        print(f"Weather: {weather_mode.replace('_', ' ').title()}")
    elif key == b't' or key == b'T':  # Toggle auto time
        auto_time = not auto_time
        print(f"Auto Time: {'ON' if auto_time else 'OFF'}")
    elif key == b'f' or key == b'F':  # Toggle fog
        use_fog = not use_fog
        print(f"Fog: {'ON' if use_fog else 'OFF'}")
    elif key == b'c' or key == b'C':  # Cycle camera modes
        camera_mode = (camera_mode + 1) % len(camera_modes)
        new_mode = camera_modes[camera_mode]
        print(f"Camera Mode: {new_mode}")
        
        if game_state != "playing":
            print("Note: Camera modes only affect gameplay, not menu view")
    elif key == b'v' or key == b'V':  # Quick switch to Chase Cam
        camera_mode = 0  # Chase mode
        print("Quick switch to Chase Cam")
    elif key == b'b' or key == b'B':  # Quick switch to Drone Cam
        camera_mode = 1  # Drone mode
        print("Quick switch to Drone Cam")
    elif key == b'\x1b':  # ESC
        sys.exit(0)
    
    # Store key press for vehicle movement
    keys_pressed[key] = True
    


def keyboard_up(key, x, y):
    """Handle key release"""
    if key in keys_pressed:
        del keys_pressed[key]

def special_keys(key, x, y):
    """Handle special keys (from template)"""
    global camera_pos, camera_look, camera_angle, game_state, menu_selection, menu_page, selected_vehicle
    global current_camera_x, current_camera_y, current_camera_z
    
    # Handle menu navigation
    if game_state == "main_menu":
        if menu_page == "main":
            if key == GLUT_KEY_UP:
                menu_selection = (menu_selection - 1) % 5
            elif key == GLUT_KEY_DOWN:
                menu_selection = (menu_selection + 1) % 5
        elif menu_page == "settings":
            if key == GLUT_KEY_UP:
                # Cycle through vehicle types: car -> bike -> cycle -> car
                if selected_vehicle == "car":
                    selected_vehicle = "bike"
                elif selected_vehicle == "bike":
                    selected_vehicle = "cycle"
                elif selected_vehicle == "cycle":
                    selected_vehicle = "car"
            elif key == GLUT_KEY_DOWN:
                # Cycle through vehicle types: car -> cycle -> bike -> car
                if selected_vehicle == "car":
                    selected_vehicle = "cycle"
                elif selected_vehicle == "cycle":
                    selected_vehicle = "bike"
                elif selected_vehicle == "bike":
                    selected_vehicle = "car"
        return  # Don't process camera controls when in menu
    
    
    # Store special key press for vehicle movement
    keys_pressed[key] = True

def special_keys_up(key, x, y):
    """Handle special key release"""
    if key in keys_pressed:
        del keys_pressed[key]

def timer(value):
    """Timer for consistent frame rate"""
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)  # ~60 FPS

def main():
    """Main function"""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"3D Racing Game - Complete Edition")
    
    # Load high scores
    load_high_scores()
    
    init_scene()
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_keys)
    glutSpecialUpFunc(special_keys_up)
    glutTimerFunc(0, timer, 0)
    
    print("=" * 70)
    print("3D RACING GAME - COMPLETE EDITION")
    print("=" * 70)
    print("GAME FEATURES:")
    print("  ✓ Player Vehicle Movement (W/S or Up/Down, A/D or Left/Right)")
    print("  ✓ Multiple Vehicle Types (Cycle, Bike, Car)")
    print("  ✓ Random Obstacles (Boxes, Cylinders)")
    print("  ✓ Powerups (Speed Boost & Shield)")
    print("  ✓ Collision Detection (AABB method)")
    print("  ✓ Game Over Conditions")
    print("  ✓ Enhanced Vehicle Physics (Momentum, Drift, Suspension)")
    print("\nVEHICLE CONTROLS:")
    print("  1: Cycle - Fast turning, light & nimble (max 4.0)")
    print("  2: Bike - Balanced performance (max 5.5)")
    print("  3: Car - High speed, slower turning (max 7.0)")
    print("  W or Up: Forward (gradual acceleration)")
    print("  S or Down: Brake (slow down, no reverse)")
    print("  A/D or Left/Right: Turn")

    print("  SPACE: Restart game")
    print("\nENVIRONMENT CONTROLS:")
    print("  4: Set Time Phase")
    print("  R: Cycle Weather")
    print("  T: Toggle Auto Time")
    print("  F: Toggle Fog")
    print("  C: Cycle camera modes (Chase/Drone/Cinematic/Free)")
    print("  V: Quick switch to Chase Cam")
    print("  B: Quick switch to Drone Cam")
    print("\nGAME OBJECTIVES:")
    print("  - Reach the finish line without losing all lives")
    print("  - Avoid obstacles (use shield powerup for protection)")
    print("  - Collect powerups for advantages")
    print("  - Don't fall off the road!")
    print("\nESC: Exit")
    print("=" * 70)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
