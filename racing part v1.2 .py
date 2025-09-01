#!/usr/bin/env python3
# Enhanced setup.py - Scene Setup with Dynamic Environment, Day/Night Cycle, and Rain
# Fixed timing: Each phase (Night/Dawn/Day/Dusk) lasts 60 seconds

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import time

# Camera variables for dynamic movement
camera_x = 0
camera_y = 10
camera_z = 20
camera_look_x = 0
camera_look_y = 0
camera_look_z = 0

# Environment scrolling variables
road_offset = 0
environment_offset = 0
scroll_speed = 0.5

# Dynamic object lists
trees = []
lamp_posts = []
road_segments = []
clouds = []
raindrops = []

# Weather and time system variables
current_time = 0.0  # 0.0 = midnight, 0.5 = noon, 1.0 = midnight

# FIXED TIMING CALCULATION:
# We have 4 phases: Night (0.0-0.25), Dawn (0.25-0.5), Day (0.5-0.75), Dusk (0.75-1.0)
# Each phase = 0.25 of the cycle
# If we want each phase to last 60 seconds:
# Total cycle = 4 phases * 60 seconds = 240 seconds
# Time increments from 0.0 to 1.0 over 240 seconds
# At 60 FPS (16ms per frame), we have 60 frames per second
# time_speed = 1.0 / (240 seconds * 60 frames/second) = 1.0 / 14400 ≈ 0.0000694
# But since the timer is called every 16ms (not exactly 60fps), we adjust:
# time_speed = 1.0 / (240 seconds * 62.5 calls/second) = 1.0 / 15000 ≈ 0.0000667

time_speed = 0.00000667  # Fixed: Makes full cycle ~240 seconds (60 seconds per phase)
auto_time = True  # Automatic time progression
weather_mode = "clear"  # "clear", "rain", "storm"
auto_weather = True  # Automatic weather changes
weather_timer = 0.0
weather_change_interval = 300  # Change weather every 5 minutes (300 frames at 60fps)

# For tracking actual time
phase_start_time = time.time()
current_phase = "Night"

# Rain system
rain_intensity = 0.0  # 0.0 to 1.0
target_rain_intensity = 0.0
rain_particles = []
max_rain_particles = 500

# Lightning system for storms
lightning_flash = 0.0
lightning_timer = 0.0
next_lightning = 0.0

def init_rain_system():
    """Initialize rain particles"""
    global rain_particles
    rain_particles = []
    for i in range(max_rain_particles):
        rain_particles.append({
            'x': random.uniform(-100, 100),
            'y': random.uniform(0, 80),
            'z': random.uniform(-150, 100),
            'speed': random.uniform(0.5, 1.5),
            'active': False
        })

def get_time_of_day():
    """Get descriptive time of day with proper boundaries"""
    # Fixed boundaries for 4 equal phases
    if 0.0 <= current_time < 0.25:
        return "Night"
    elif 0.25 <= current_time < 0.5:
        return "Dawn"
    elif 0.5 <= current_time < 0.75:
        return "Day"
    elif 0.75 <= current_time < 1.0:
        return "Dusk"
    else:
        return "Night"

def get_phase_progress():
    """Get progress through current phase (0.0 to 1.0)"""
    phase = get_time_of_day()
    if phase == "Night":
        return (current_time % 0.25) / 0.25
    elif phase == "Dawn":
        return ((current_time - 0.25) % 0.25) / 0.25
    elif phase == "Day":
        return ((current_time - 0.5) % 0.25) / 0.25
    elif phase == "Dusk":
        return ((current_time - 0.75) % 0.25) / 0.25
    return 0.0

def get_sun_position():
    """Calculate sun position based on time"""
    # Sun follows an arc across the sky
    sun_angle = (current_time - 0.5) * math.pi  # -π/2 to π/2
    sun_x = math.sin(sun_angle) * 100
    sun_y = max(5, math.cos(sun_angle) * 50)  # Never below horizon
    sun_z = -20
    return [sun_x, sun_y, sun_z]

def get_sky_colors():
    """Get sky colors based on time of day with smooth transitions"""
    time_of_day = get_time_of_day()
    phase_progress = get_phase_progress()
    
    if time_of_day == "Night":
        # Dark blue night sky
        return {
            'horizon': [0.1, 0.1, 0.3],
            'zenith': [0.05, 0.05, 0.15],
            'ambient': 0.1
        }
    elif time_of_day == "Dawn":
        # Transition from night to day
        night_weight = 1.0 - phase_progress
        day_weight = phase_progress
        return {
            'horizon': [
                0.1 * night_weight + 1.0 * day_weight,
                0.1 * night_weight + 0.6 * day_weight,
                0.3 * night_weight + 0.4 * day_weight
            ],
            'zenith': [
                0.05 * night_weight + 0.4 * day_weight,
                0.05 * night_weight + 0.6 * day_weight,
                0.15 * night_weight + 0.9 * day_weight
            ],
            'ambient': 0.1 * night_weight + 0.5 * day_weight
        }
    elif time_of_day == "Day":
        # Bright blue day
        return {
            'horizon': [0.7, 0.85, 1.0],
            'zenith': [0.3, 0.5, 0.9],
            'ambient': 0.8
        }
    elif time_of_day == "Dusk":
        # Transition from day to night
        day_weight = 1.0 - phase_progress
        night_weight = phase_progress
        return {
            'horizon': [
                0.7 * day_weight + 0.1 * night_weight,
                0.85 * day_weight + 0.1 * night_weight,
                1.0 * day_weight + 0.3 * night_weight
            ],
            'zenith': [
                0.3 * day_weight + 0.05 * night_weight,
                0.5 * day_weight + 0.05 * night_weight,
                0.9 * day_weight + 0.15 * night_weight
            ],
            'ambient': 0.8 * day_weight + 0.1 * night_weight
        }

def update_weather_system():
    """Update weather conditions"""
    global weather_mode, weather_timer, target_rain_intensity, rain_intensity
    global lightning_timer, next_lightning, lightning_flash
    
    weather_timer += 1  # Increment by frame
    
    # Automatic weather changes (every 5 minutes = 300 seconds = 18750 frames at ~60fps)
    if auto_weather and weather_timer >= weather_change_interval * 62.5:
        weather_timer = 0.0
        weather_options = ["clear", "rain", "storm"]
        weather_mode = random.choice(weather_options)
        print(f"Weather changed to: {weather_mode}")
    
    # Update rain intensity based on weather
    if weather_mode == "clear":
        target_rain_intensity = 0.0
    elif weather_mode == "rain":
        target_rain_intensity = 0.6
    elif weather_mode == "storm":
        target_rain_intensity = 1.0
    
    # Smooth rain intensity transition
    rain_intensity += (target_rain_intensity - rain_intensity) * 0.02
    rain_intensity = max(0.0, min(1.0, rain_intensity))
    
    # Lightning system for storms
    if weather_mode == "storm":
        lightning_timer += 0.1
        if lightning_timer >= next_lightning:
            lightning_flash = 1.0
            lightning_timer = 0.0
            next_lightning = random.uniform(2.0, 8.0)  # Random interval
    
    # Fade lightning flash
    if lightning_flash > 0:
        lightning_flash -= 0.1
        lightning_flash = max(0.0, lightning_flash)

def update_rain_particles(speed):
    """Update rain particle positions"""
    active_particles = int(rain_intensity * max_rain_particles)
    
    for i, particle in enumerate(rain_particles):
        if i < active_particles:
            particle['active'] = True
            # Move particle down and with wind
            particle['y'] -= particle['speed'] * 2
            particle['z'] += speed  # Move with environment
            particle['x'] += random.uniform(-0.1, 0.1)  # Wind effect
            
            # Reset particle if it hits ground or moves too far
            if particle['y'] < 0 or particle['z'] > 50:
                particle['x'] = random.uniform(-100, 100)
                particle['y'] = random.uniform(60, 80)
                particle['z'] = random.uniform(-200, -150)
                particle['speed'] = random.uniform(0.8, 2.0)
        else:
            particle['active'] = False

def draw_rain():
    """Draw rain particles"""
    if rain_intensity <= 0:
        return
    
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    
    # Draw rain as lines
    glColor4f(0.7, 0.7, 0.9, rain_intensity * 0.6)
    glLineWidth(1.0)
    
    glBegin(GL_LINES)
    for particle in rain_particles:
        if particle['active']:
            # Draw rain drop as a short line
            glVertex3f(particle['x'], particle['y'], particle['z'])
            glVertex3f(particle['x'], particle['y'] - 2, particle['z'])
    glEnd()
    
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)

def draw_lightning_flash():
    """Draw lightning flash effect"""
    if lightning_flash <= 0:
        return
    
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    
    # Full screen white flash
    glColor4f(1.0, 1.0, 1.0, lightning_flash * 0.3)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glBegin(GL_QUADS)
    glVertex2f(-1, -1)
    glVertex2f(1, -1)
    glVertex2f(1, 1)
    glVertex2f(-1, 1)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glDepthMask(GL_TRUE)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def init_dynamic_objects():
    """Initialize positions for dynamic objects"""
    global trees, lamp_posts, road_segments, clouds
    
    # Generate trees on both sides of the road
    trees = []
    for i in range(30):
        side = random.choice([-1, 1])
        x = side * random.uniform(25, 50)
        z = random.uniform(-100, 300)
        tree_type = random.randint(0, 2)
        size = random.uniform(0.8, 1.3)
        trees.append({'x': x, 'z': z, 'type': tree_type, 'size': size})
    
    # Generate lamp posts along the road
    lamp_posts = []
    for i in range(20):
        z = i * 30 - 100
        lamp_posts.append({'z': z, 'light_on': True})
    
    # Generate road segments for infinite road effect
    road_segments = []
    for i in range(15):
        z = i * 40 - 100
        road_segments.append({'z': z, 'type': random.randint(0, 1)})
    
    # Generate clouds
    clouds = []
    for i in range(15):  # More clouds for better effect
        x = random.uniform(-100, 100)
        y = random.uniform(40, 60)
        z = random.uniform(-100, 300)
        size = random.uniform(5, 15)
        density = random.uniform(0.4, 0.9)  # Cloud density for weather
        clouds.append({'x': x, 'y': y, 'z': z, 'size': size, 'density': density})
    
    # Initialize rain system
    init_rain_system()

def update_dynamic_objects(speed=0):
    """Update positions of dynamic objects based on car speed"""
    global road_offset, environment_offset, current_time, current_phase, phase_start_time
    
    # Update time with fixed speed for 60-second phases
    if auto_time:
        current_time += time_speed * 62.5  # Adjust for actual frame rate
        if current_time >= 1.0:
            current_time = 0.0
    
    # Track phase changes for debugging
    new_phase = get_time_of_day()
    if new_phase != current_phase:
        elapsed = time.time() - phase_start_time
        print(f"Phase changed from {current_phase} to {new_phase} after {elapsed:.1f} seconds")
        current_phase = new_phase
        phase_start_time = time.time()
    
    # Update weather
    update_weather_system()
    
    # Update rain particles
    update_rain_particles(speed)
    
    # Update offsets based on speed
    road_offset += speed
    environment_offset += speed
    
    # Update trees
    for tree in trees:
        tree['z'] += speed
        if tree['z'] > 30:
            tree['z'] = random.uniform(-200, -150)
            tree['x'] = random.choice([-1, 1]) * random.uniform(25, 50)
            tree['type'] = random.randint(0, 2)
            tree['size'] = random.uniform(0.8, 1.3)
    
    # Update lamp posts
    for lamp in lamp_posts:
        lamp['z'] += speed
        if lamp['z'] > 30:
            lamp['z'] -= 600
        
        # Auto lamp control based on time
        time_of_day = get_time_of_day()
        lamp['light_on'] = time_of_day in ["Night", "Dawn", "Dusk"] or weather_mode == "storm"
    
    # Update road segments
    for segment in road_segments:
        segment['z'] += speed
        if segment['z'] > 30:
            segment['z'] -= 600
    
    # Update clouds with weather effects
    for cloud in clouds:
        # Clouds move with weather intensity
        cloud_speed = speed * (0.2 + rain_intensity * 0.3)
        cloud['z'] += cloud_speed
        if cloud['z'] > 50:
            cloud['z'] = random.uniform(-250, -200)
            cloud['x'] = random.uniform(-100, 100)
            cloud['y'] = random.uniform(35, 65)
            cloud['density'] = random.uniform(0.4, 0.9)

def setup_camera():
    """Set up the camera view for the game"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 0.1, 1000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_x, camera_y, camera_z,
              camera_look_x, camera_look_y, camera_look_z,
              0, 1, 0)

def setup_lighting():
    """Set up lighting for the scene based on time and weather"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)  # Sun/Moon
    glEnable(GL_LIGHT1)  # Fill light
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    
    sky_colors = get_sky_colors()
    sun_pos = get_sun_position()
    time_of_day = get_time_of_day()
    
    # Main light (sun or moon)
    if time_of_day == "Night":
        # Moon light - cool and dim
        light0_diffuse = [0.3, 0.3, 0.4, 1.0]
        light0_ambient = [0.1, 0.1, 0.15, 1.0]
        light0_position = [-sun_pos[0], sun_pos[1], sun_pos[2], 0.0]
    else:
        # Sun light - warm and bright
        intensity = sky_colors['ambient']
        if weather_mode == "storm":
            intensity *= 0.3  # Darker during storms
        elif weather_mode == "rain":
            intensity *= 0.6  # Dimmer during rain
        
        light0_diffuse = [intensity, intensity * 0.95, intensity * 0.9, 1.0]
        light0_ambient = [intensity * 0.3, intensity * 0.3, intensity * 0.35, 1.0]
        light0_position = [sun_pos[0], sun_pos[1], sun_pos[2], 0.0]
    
    # Lightning override
    if lightning_flash > 0:
        flash_intensity = lightning_flash * 2.0
        light0_diffuse = [flash_intensity, flash_intensity, flash_intensity, 1.0]
        light0_ambient = [flash_intensity * 0.5, flash_intensity * 0.5, flash_intensity * 0.5, 1.0]
    
    glLightfv(GL_LIGHT0, GL_POSITION, light0_position)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diffuse)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light0_ambient)
    
    # Fill light
    fill_intensity = sky_colors['ambient'] * 0.4
    if weather_mode in ["rain", "storm"]:
        fill_intensity *= 0.5
    
    light1_diffuse = [fill_intensity * 0.8, fill_intensity * 0.8, fill_intensity, 1.0]
    light1_position = [-10.0, 15.0, -10.0, 0.0]
    
    glLightfv(GL_LIGHT1, GL_POSITION, light1_position)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, light1_diffuse)

def setup_fog():
    """Set up fog for depth effect based on weather"""
    glEnable(GL_FOG)
    
    # Fog color and density based on weather and time
    sky_colors = get_sky_colors()
    fog_color = sky_colors['horizon'] + [1.0]
    
    # Adjust fog for weather
    if weather_mode == "rain":
        fog_color = [0.6, 0.6, 0.7, 1.0]  # Gray fog
        fog_start = 30.0
        fog_end = 120.0
    elif weather_mode == "storm":
        fog_color = [0.4, 0.4, 0.5, 1.0]  # Dark gray fog
        fog_start = 20.0
        fog_end = 80.0
    else:
        fog_start = 50.0
        fog_end = 200.0
    
    glFogfv(GL_FOG_COLOR, fog_color)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, fog_start)
    glFogf(GL_FOG_END, fog_end)

def draw_dynamic_road():
    """Draw road with moving segments for infinite effect"""
    road_width = 20
    segment_length = 40
    
    for segment in road_segments:
        z_pos = segment['z']
        
        if z_pos < -150 or z_pos > 50:
            continue
        
        # Road color varies with weather
        if weather_mode == "rain" or weather_mode == "storm":
            if segment['type'] == 0:
                glColor3f(0.15, 0.15, 0.15)  # Darker when wet
            else:
                glColor3f(0.2, 0.2, 0.2)
        else:
            if segment['type'] == 0:
                glColor3f(0.2, 0.2, 0.2)
            else:
                glColor3f(0.25, 0.25, 0.25)
        
        glBegin(GL_QUADS)
        glVertex3f(-road_width/2, 0, z_pos)
        glVertex3f(road_width/2, 0, z_pos)
        glVertex3f(road_width/2, 0, z_pos + segment_length)
        glVertex3f(-road_width/2, 0, z_pos + segment_length)
        glEnd()
        
        # Add wet road reflections
        if weather_mode in ["rain", "storm"] and rain_intensity > 0.3:
            glEnable(GL_BLEND)
            glColor4f(0.3, 0.3, 0.4, 0.3 * rain_intensity)
            glBegin(GL_QUADS)
            glVertex3f(-road_width/2, 0.01, z_pos)
            glVertex3f(road_width/2, 0.01, z_pos)
            glVertex3f(road_width/2, 0.01, z_pos + segment_length)
            glVertex3f(-road_width/2, 0.01, z_pos + segment_length)
            glEnd()
            glDisable(GL_BLEND)
        
        draw_road_details(z_pos, segment_length, road_width)

def draw_road_details(z_start, length, width):
    """Add details like cracks and patches to road segments"""
    if random.random() > 0.7:
        patch_size = random.uniform(2, 5)
        patch_x = random.uniform(-width/3, width/3)
        patch_z = z_start + random.uniform(5, length-5)
        
        glColor3f(0.1, 0.1, 0.1)
        glBegin(GL_QUADS)
        glVertex3f(patch_x - patch_size/2, 0.01, patch_z - patch_size/2)
        glVertex3f(patch_x + patch_size/2, 0.01, patch_z - patch_size/2)
        glVertex3f(patch_x + patch_size/2, 0.01, patch_z + patch_size/2)
        glVertex3f(patch_x - patch_size/2, 0.01, patch_z + patch_size/2)
        glEnd()

def draw_dynamic_road_markings():
    """Draw animated lane markings"""
    marking_width = 0.3
    marking_length = 5
    gap_length = 5
    
    offset = (road_offset * 2) % (marking_length + gap_length)
    
    # Adjust marking brightness based on conditions
    if get_time_of_day() == "Night":
        glColor3f(0.8, 0.8, 0.0)  # Dimmer at night
    else:
        glColor3f(1.0, 1.0, 0.0)
    
    for z in range(-150, 100, marking_length + gap_length):
        z_pos = z + offset
        if -150 < z_pos < 50:
            glBegin(GL_QUADS)
            glVertex3f(-marking_width/2, 0.1, z_pos)
            glVertex3f(marking_width/2, 0.1, z_pos)
            glVertex3f(marking_width/2, 0.1, z_pos + marking_length)
            glVertex3f(-marking_width/2, 0.1, z_pos + marking_length)
            glEnd()
    
    # Side lines
    if get_time_of_day() == "Night":
        glColor3f(0.8, 0.8, 0.8)
    else:
        glColor3f(1.0, 1.0, 1.0)
    
    for z in range(-150, 100, 40):
        glBegin(GL_QUADS)
        glVertex3f(-10 + marking_width, 0.1, z)
        glVertex3f(-10, 0.1, z)
        glVertex3f(-10, 0.1, z + 35)
        glVertex3f(-10 + marking_width, 0.1, z + 35)
        glEnd()
        
        glBegin(GL_QUADS)
        glVertex3f(10 - marking_width, 0.1, z)
        glVertex3f(10, 0.1, z)
        glVertex3f(10, 0.1, z + 35)
        glVertex3f(10 - marking_width, 0.1, z + 35)
        glEnd()

def draw_dynamic_trees():
    """Draw trees with weather and time effects"""
    sorted_trees = sorted(trees, key=lambda t: -t['z'])
    
    for tree in sorted_trees:
        if tree['z'] < -100 or tree['z'] > 30:
            continue
        
        distance = abs(tree['z'])
        if distance > 80:
            alpha = max(0.2, 1.0 - (distance - 80) / 50)
            glDepthMask(GL_FALSE)
        else:
            alpha = 1.0
            glDepthMask(GL_TRUE)
        
        glPushMatrix()
        glTranslatef(tree['x'], 0, tree['z'])
        glScalef(tree['size'], tree['size'], tree['size'])
        
        # Weather effects on trees
        if weather_mode in ["rain", "storm"]:
            # Trees look darker and more saturated when wet
            glColor4f(0.7, 0.7, 0.7, alpha)
        else:
            glColor4f(1, 1, 1, alpha)
        
        # Tree swaying in storm
        if weather_mode == "storm":
            sway = math.sin(time.time() * 3 + tree['x']) * 2
            glRotatef(sway, 0, 0, 1)
        
        if tree['type'] == 0:
            draw_pine_tree()
        elif tree['type'] == 1:
            draw_round_tree()
        else:
            draw_palm_tree()
        
        glPopMatrix()
    
    glDepthMask(GL_TRUE)

def draw_pine_tree():
    """Draw a pine tree"""
    # Trunk
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    glutSolidCylinder(0.5, 4, 8, 8)
    glPopMatrix()
    
    # Leaves - color varies with weather
    if weather_mode in ["rain", "storm"]:
        glColor3f(0.05, 0.3, 0.05)  # Darker green when wet
    else:
        glColor3f(0.1, 0.4, 0.1)
    
    for i in range(3):
        glPushMatrix()
        glTranslatef(0, 3 + i*2, 0)
        glRotatef(-90, 1, 0, 0)
        glutSolidCone(3 - i*0.7, 3, 10, 10)
        glPopMatrix()

def draw_round_tree():
    """Draw a round leafy tree"""
    # Trunk
    glColor3f(0.3, 0.15, 0.05)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    glutSolidCylinder(0.6, 5, 8, 8)
    glPopMatrix()
    
    # Leaves
    if weather_mode in ["rain", "storm"]:
        glColor3f(0.15, 0.4, 0.05)
    else:
        glColor3f(0.2, 0.5, 0.1)
    
    glPushMatrix()
    glTranslatef(0, 6, 0)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()

def draw_palm_tree():
    """Draw a palm tree"""
    # Trunk
    glColor3f(0.5, 0.3, 0.1)
    for i in range(5):
        glPushMatrix()
        glTranslatef(i*0.1, i*1.2, 0)
        glRotatef(-90, 1, 0, 0)
        glutSolidCylinder(0.4, 1.2, 6, 6)
        glPopMatrix()
    
    # Leaves
    if weather_mode in ["rain", "storm"]:
        glColor3f(0.05, 0.5, 0.05)
    else:
        glColor3f(0.1, 0.6, 0.1)
    
    for angle in range(0, 360, 60):
        glPushMatrix()
        glTranslatef(0.5, 6, 0)
        glRotatef(angle, 0, 1, 0)
        glRotatef(45, 1, 0, 0)
        glScalef(3, 0.3, 1)
        glutSolidCube(1)
        glPopMatrix()

def draw_lamp_posts():
    """Draw street lamp posts with automatic lighting"""
    for lamp in lamp_posts:
        if lamp['z'] < -100 or lamp['z'] > 30:
            continue
        
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 12, 0, lamp['z'])
            
            # Lamp post
            glColor3f(0.3, 0.3, 0.3)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            glutSolidCylinder(0.2, 8, 8, 8)
            glPopMatrix()
            
            # Lamp arm
            glPushMatrix()
            glTranslatef(side * 2, 7.5, 0)
            glRotatef(90, 0, 0, 1)
            glutSolidCylinder(0.15, 2, 6, 6)
            glPopMatrix()
            
            # Lamp light with automatic control
            if lamp['light_on']:
                glDisable(GL_LIGHTING)
                if weather_mode == "storm":
                    # Flickering light in storm
                    flicker = 0.7 + 0.3 * random.random()
                    glColor3f(flicker, flicker, 0.7 * flicker)
                else:
                    glColor3f(1.0, 1.0, 0.7)
                glPushMatrix()
                glTranslatef(side * 4, 7.5, 0)
                glutSolidSphere(0.5, 8, 8)
                glPopMatrix()
                glEnable(GL_LIGHTING)
            else:
                glColor3f(0.5, 0.5, 0.5)
                glPushMatrix()
                glTranslatef(side * 4, 7.5, 0)
                glutSolidSphere(0.5, 8, 8)
                glPopMatrix()
            
            glPopMatrix()

def draw_moving_clouds():
    """Draw clouds with weather-based appearance"""
    glDisable(GL_LIGHTING)
    
    sorted_clouds = sorted(clouds, key=lambda c: -c['z'])
    
    for cloud in sorted_clouds:
        if cloud['z'] < -200 or cloud['z'] > 50:
            continue
        
        distance = abs(cloud['z'] + 50)
        base_alpha = max(0.3, min(0.9, 1.0 - distance / 300))
        
        # Weather affects cloud appearance
        if weather_mode == "storm":
            # Dark storm clouds
            glColor4f(0.3, 0.3, 0.4, base_alpha * cloud['density'])
        elif weather_mode == "rain":
            # Gray rain clouds
            glColor4f(0.6, 0.6, 0.7, base_alpha * cloud['density'])
        else:
            # White fluffy clouds
            glColor4f(1.0, 1.0, 1.0, base_alpha * cloud['density'] * 0.8)
        
        glDepthMask(GL_FALSE)
        
        glPushMatrix()
        glTranslatef(cloud['x'], cloud['y'], cloud['z'])
        
        # Larger, denser clouds in bad weather
        size_multiplier = 1.0
        if weather_mode in ["rain", "storm"]:
            size_multiplier = 1.5
        
        for i in range(4):  # More cloud parts for better effect
            x_offset = (i - 1.5) * cloud['size'] * 0.4 * size_multiplier
            y_offset = random.uniform(-1, 1)
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(-1.0, -1.0)
            glutSolidSphere(cloud['size'] * 0.7 * size_multiplier, 8, 8)
            glDisable(GL_POLYGON_OFFSET_FILL)
            glTranslatef(x_offset, y_offset, 0)
        
        glPopMatrix()
    
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)

def draw_boundary_walls():
    """Draw moving boundary walls/barriers"""
    wall_height = 3
    wall_segment_length = 20
    
    for z in range(-150, 100, wall_segment_length):
        z_pos = z + (environment_offset % wall_segment_length)
        
        if z_pos < -100 or z_pos > 30:
            continue
        
        # Wall color varies with time
        if get_time_of_day() == "Night":
            glColor3f(0.4, 0.4, 0.4)
        else:
            glColor3f(0.6, 0.6, 0.6)
        
        # Left wall segment
        glPushMatrix()
        glTranslatef(-11, wall_height/2, z_pos)
        glScalef(0.5, wall_height, wall_segment_length)
        glutSolidCube(1)
        glPopMatrix()
        
        # Right wall segment
        glPushMatrix()
        glTranslatef(11, wall_height/2, z_pos)
        glScalef(0.5, wall_height, wall_segment_length)
        glutSolidCube(1)
        glPopMatrix()
        
        # Warning stripes on walls
        if int(z/wall_segment_length) % 2 == 0:
            glColor3f(1.0, 1.0, 0.0)
            glPushMatrix()
            glTranslatef(-11, wall_height/2, z_pos)
            glScalef(0.55, wall_height * 0.3, wall_segment_length * 0.8)
            glutSolidCube(1)
            glPopMatrix()
            
            glPushMatrix()
            glTranslatef(11, wall_height/2, z_pos)
            glScalef(0.55, wall_height * 0.3, wall_segment_length * 0.8)
            glutSolidCube(1)
            glPopMatrix()

def draw_dynamic_ground():
    """Draw moving ground/grass with weather effects"""
    for x in range(-10, 11):
        for z in range(-10, 15):
            z_pos = z * 20 + (environment_offset * 0.5) % 20
            
            if z_pos < -150 or z_pos > 50:
                continue
            
            # Ground color varies with weather and time
            base_green = 0.4 + (x + z) % 3 * 0.1
            
            if weather_mode in ["rain", "storm"]:
                # Darker, muddier ground when wet
                glColor3f(0.15, base_green * 0.6, 0.05)
            elif get_time_of_day() == "Night":
                # Darker at night
                glColor3f(0.1, base_green * 0.3, 0.05)
            else:
                glColor3f(0.2, base_green, 0.1)
            
            glBegin(GL_QUADS)
            glVertex3f(x * 20 - 10, -0.1, z_pos - 10)
            glVertex3f(x * 20 + 10, -0.1, z_pos - 10)
            glVertex3f(x * 20 + 10, -0.1, z_pos + 10)
            glVertex3f(x * 20 - 10, -0.1, z_pos + 10)
            glEnd()

def draw_sky_gradient():
    """Draw gradient sky background based on time and weather"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    sky_colors = get_sky_colors()
    horizon_color = sky_colors['horizon']
    zenith_color = sky_colors['zenith']
    
    # Weather modifications
    if weather_mode == "storm":
        horizon_color = [0.2, 0.2, 0.3]
        zenith_color = [0.1, 0.1, 0.2]
    elif weather_mode == "rain":
        horizon_color = [c * 0.7 for c in horizon_color]
        zenith_color = [c * 0.8 for c in zenith_color]
    
    glBegin(GL_QUADS)
    # Bottom (horizon)
    glColor3fv(horizon_color)
    glVertex3f(-200, -50, -190)
    glVertex3f(200, -50, -190)
    
    # Top (zenith)
    glColor3fv(zenith_color)
    glVertex3f(200, 100, -190)
    glVertex3f(-200, 100, -190)
    glEnd()
    
    # Draw sun or moon
    draw_celestial_body()
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def draw_celestial_body():
    """Draw sun or moon based on time"""
    sun_pos = get_sun_position()
    time_of_day = get_time_of_day()
    
    if sun_pos[1] > 5:  # Only draw if above horizon
        glPushMatrix()
        glTranslatef(sun_pos[0], sun_pos[1], sun_pos[2])
        
        if time_of_day == "Night":
            # Moon
            glColor3f(0.9, 0.9, 1.0)
            glutSolidSphere(3, 12, 12)
        else:
            # Sun
            if weather_mode == "storm":
                glColor3f(0.6, 0.5, 0.3)  # Dim sun during storm
            elif weather_mode == "rain":
                glColor3f(0.8, 0.7, 0.5)  # Filtered sun during rain
            else:
                glColor3f(1.0, 1.0, 0.8)  # Bright sun
            
            glutSolidSphere(4, 16, 16)
            
            # Sun rays effect (only in clear weather)
            if weather_mode == "clear" and time_of_day == "Day":
                glEnable(GL_BLEND)
                glColor4f(1.0, 1.0, 0.5, 0.3)
                glutSolidSphere(6, 16, 16)
                glDisable(GL_BLEND)
        
        glPopMatrix()

def draw_stars():
    """Draw stars during night time"""
    if get_time_of_day() != "Night" or weather_mode in ["rain", "storm"]:
        return
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 1.0)
    glPointSize(2.0)
    
    # Pre-calculated star positions for consistency
    star_positions = [
        (-50, 45, -180), (30, 50, -180), (-80, 55, -180), (70, 48, -180),
        (-20, 60, -180), (90, 52, -180), (-100, 47, -180), (50, 58, -180),
        (-70, 62, -180), (10, 65, -180), (-40, 45, -180), (80, 60, -180)
    ]
    
    glBegin(GL_POINTS)
    for pos in star_positions:
        glVertex3f(pos[0], pos[1], pos[2])
    glEnd()
    
    glEnable(GL_LIGHTING)

def init_scene():
    """Initialize OpenGL settings and dynamic objects"""
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.5, 0.7, 1.0, 1.0)
    
    glDepthRange(0.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    init_dynamic_objects()
    setup_fog()
    
    mat_specular = [1.0, 1.0, 1.0, 1.0]
    mat_shininess = [50.0]
    glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)

def render_complete_scene(car_speed=0):
    """Main function to render all dynamic scene elements with weather and time effects"""
    update_dynamic_objects(car_speed)
    setup_camera()
    setup_lighting()
    setup_fog()
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Sky and celestial objects
    glDepthMask(GL_FALSE)
    draw_sky_gradient()
    draw_stars()
    glDepthMask(GL_TRUE)
    
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    
    # Opaque objects
    draw_dynamic_ground()
    draw_dynamic_road()
    draw_dynamic_road_markings()
    draw_boundary_walls()
    draw_lamp_posts()
    draw_dynamic_trees()
    
    # Transparent objects
    glDepthFunc(GL_LESS)
    draw_moving_clouds()
    
    # Weather effects
    draw_rain()
    draw_lightning_flash()
    
    glDepthFunc(GL_LEQUAL)

def draw_hud():
    """Draw heads-up display with weather and time information"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1000, 0, 800, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background panel
    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.5)
    glBegin(GL_QUADS)
    glVertex2f(10, 750)
    glVertex2f(350, 750)
    glVertex2f(350, 620)
    glVertex2f(10, 620)
    glEnd()
    glDisable(GL_BLEND)
    
    # Text color
    glColor3f(1, 1, 1)
    
    # Time and weather info
    time_str = f"Time: {get_time_of_day()} ({int(get_phase_progress() * 100)}%)"
    weather_str = f"Weather: {weather_mode.title()}"
    rain_str = f"Rain: {int(rain_intensity * 100)}%"
    auto_time_str = f"Auto Time: {'ON' if auto_time else 'OFF'}"
    auto_weather_str = f"Auto Weather: {'ON' if auto_weather else 'OFF'}"
    phase_timer = f"Phase Timer: ~60s each"
    
    info_lines = [time_str, weather_str, rain_str, auto_time_str, auto_weather_str, phase_timer]
    
    for i, line in enumerate(info_lines):
        glRasterPos2f(20, 720 - i * 18)
        for char in line:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    
    # Controls info
    controls = [
        "Controls:",
        "1-4: Set Time Phase",
        "  1: Night, 2: Dawn",
        "  3: Day, 4: Dusk",
        "R: Cycle Weather",
        "T: Toggle Auto Time",
        "Y: Toggle Auto Weather",
        "W/S: Speed Control",
        "Space: Stop"
    ]
    
    for i, line in enumerate(controls):
        glRasterPos2f(370, 720 - i * 15)
        for char in line:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

# Testing with simulated movement and weather controls
if __name__ == "__main__":
    test_speed = 0
    acceleration = 0
    
    def keyboard(key, x, y):
        global test_speed, acceleration, current_time, auto_time, weather_mode, auto_weather
        
        if key == b'w':  # Accelerate
            acceleration = 0.1
        elif key == b's':  # Brake
            acceleration = -0.1
        elif key == b' ':  # Stop
            test_speed = 0
            acceleration = 0
        elif key == b'1':  # Set to night
            current_time = 0.0
            auto_time = False
            print("Set to Night phase")
        elif key == b'2':  # Set to dawn
            current_time = 0.25
            auto_time = False
            print("Set to Dawn phase")
        elif key == b'3':  # Set to day
            current_time = 0.5
            auto_time = False
            print("Set to Day phase")
        elif key == b'4':  # Set to dusk
            current_time = 0.75
            auto_time = False
            print("Set to Dusk phase")
        elif key == b't':  # Toggle auto time
            auto_time = not auto_time
            print(f"Auto time: {'ON' if auto_time else 'OFF'}")
        elif key == b'r':  # Cycle weather
            weather_options = ["clear", "rain", "storm"]
            current_index = weather_options.index(weather_mode)
            weather_mode = weather_options[(current_index + 1) % len(weather_options)]
            auto_weather = False
            print(f"Weather set to: {weather_mode}")
        elif key == b'y':  # Toggle auto weather
            auto_weather = not auto_weather
            print(f"Auto weather: {'ON' if auto_weather else 'OFF'}")
        elif key == b'\x1b':  # ESC key
            sys.exit()
    
    def keyboard_up(key, x, y):
        global acceleration
        if key in [b'w', b's']:
            acceleration = 0
    
    def update_speed():
        global test_speed, acceleration
        test_speed += acceleration
        test_speed *= 0.98  # Friction
        test_speed = max(-2, min(test_speed, 5))
    
    def display():
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        update_speed()
        render_complete_scene(test_speed)
        draw_hud()
        glutSwapBuffers()
    
    def timer(value):
        glutPostRedisplay()
        glutTimerFunc(16, timer, 0)  # ~60 FPS
    
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"3D Racing Game - 60 Second Day/Night Phases")
    init_scene()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutTimerFunc(0, timer, 0)
    
    print("\n=== Enhanced Racing Game with Fixed Timing ===")
    print("Day/Night Cycle: Each phase lasts ~60 seconds")
    print("Phases: Night -> Dawn -> Day -> Dusk (240s total)")
    print("\nControls:")
    print("W/S = Accelerate/Brake, Space = Stop")
    print("1/2/3/4 = Set Time (Night/Dawn/Day/Dusk)")
    print("R = Cycle Weather (Clear/Rain/Storm)")
    print("T = Toggle Auto Time")
    print("Y = Toggle Auto Weather")
    print("ESC = Exit")
    print("\nStarting with automatic day/night cycle...")
    
    glutMainLoop()