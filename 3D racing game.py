#!/usr/bin/env python3
"""
3D Racing Game Environment with Fixed-Length Straight Track
Lamp posts and buildings positioned beside the road
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

# Camera variables (from template)
camera_pos = [0, 30, 60]  # Raised and moved back for better view
camera_look = [0, 0, 0]
fovY = 60
camera_angle = 0

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
    
    # Set clear color and depth
    glClearColor(0.5, 0.7, 1.0, 1.0)
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

def setup_camera():
    """Configure camera with perspective projection (from template)"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Raised and moved back for better view of longer road
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 2000)  # Extended far plane to 2000
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
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
    
    # Side lines (continuous)
    glColor3f(1, 1, 1)
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # Left side line
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_START)
    glVertex3f(-ROAD_WIDTH/2, 0.01, ROAD_END)
    # Right side line
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_START)
    glVertex3f(ROAD_WIDTH/2, 0.01, ROAD_END)
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
    """Draw sky with sun/moon"""
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glDisable(GL_DEPTH_TEST)
    
    sky_colors = get_sky_colors()
    
    # Weather adjustment
    if weather_mode == "heavy_rain":
        sky_colors['top'] = [c * 0.5 for c in sky_colors['top']]
        sky_colors['bottom'] = [c * 0.6 for c in sky_colors['bottom']]
    elif weather_mode == "rain":
        sky_colors['top'] = [c * 0.7 for c in sky_colors['top']]
        sky_colors['bottom'] = [c * 0.8 for c in sky_colors['bottom']]
    
    # Sky gradient
    glBegin(GL_QUADS)
    glColor3fv(sky_colors['bottom'])
    glVertex3f(-400, 0, -400)
    glVertex3f(400, 0, -400)
    glColor3fv(sky_colors['top'])
    glVertex3f(400, 200, -400)
    glVertex3f(-400, 200, -400)
    glEnd()
    
    # Sun/Moon
    sun_angle = time_of_day * 2 * math.pi
    sun_x = 100 * math.cos(sun_angle)
    sun_y = 100 * math.sin(sun_angle) + 50
    
    if sun_y > 10:
        glPushMatrix()
        glTranslatef(sun_x, sun_y, -350)
        
        phase = get_time_phase()
        if phase == "Night":
            glColor3f(0.9, 0.9, 1.0)
            glutSolidSphere(5, 16, 16)
        else:
            glColor3fv(sky_colors['sun'])
            glutSolidSphere(8, 20, 20)
        
        glPopMatrix()
    
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
    """Draw overhead map view of the straight road"""
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
    global time_of_day
    
    # Update time
    if auto_time:
        time_of_day += time_speed
        if time_of_day > 1.0:
            time_of_day = 0.0
    
    # Update clouds (they still move)
    for cloud in clouds:
        cloud['x'] += 0.05
        if cloud['x'] > 300:
            cloud['x'] = -300
    
    # Update rain
    update_rain_particles()

def display():
    """Main display function"""
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
    draw_road_map()
    draw_hud()
    
    update_environment()
    
    glutSwapBuffers()

def keyboard(key, x, y):
    """Handle keyboard input"""
    global weather_mode, time_of_day, auto_time, use_fog
    
    if key == b'1':  # Night
        time_of_day = 0.0
        auto_time = False
    elif key == b'2':  # Dawn
        time_of_day = 0.25
        auto_time = False
    elif key == b'3':  # Day
        time_of_day = 0.5
        auto_time = False
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
    elif key == b'\x1b':  # ESC
        sys.exit(0)

def special_keys(key, x, y):
    """Handle special keys (from template)"""
    global camera_pos, camera_look, camera_angle
    
    if key == GLUT_KEY_UP:
        camera_pos[1] += 2
    elif key == GLUT_KEY_DOWN:
        camera_pos[1] -= 2
    elif key == GLUT_KEY_LEFT:
        camera_angle -= 5
        # Rotate camera around center
        radius = math.sqrt(camera_pos[0]**2 + camera_pos[2]**2)
        if radius > 0:
            camera_pos[0] = radius * math.sin(math.radians(camera_angle))
            camera_pos[2] = radius * math.cos(math.radians(camera_angle))
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5
        radius = math.sqrt(camera_pos[0]**2 + camera_pos[2]**2)
        if radius > 0:
            camera_pos[0] = radius * math.sin(math.radians(camera_angle))
            camera_pos[2] = radius * math.cos(math.radians(camera_angle))

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
    glutCreateWindow(b"Racing Game Environment - Fixed Length Track")
    
    init_scene()
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutTimerFunc(0, timer, 0)
    
    print("=" * 60)
    print("RACING GAME ENVIRONMENT - FIXED LENGTH TRACK")
    print("=" * 60)
    print("TRACK INFO:")
    print(f"  Road Length: {ROAD_END - ROAD_START} units")
    print(f"  Start Position: {ROAD_START}")
    print(f"  Finish Position: {ROAD_END}")
    print("\nENVIRONMENT CONTROLS:")
    print("  1-4: Set Time Phase")
    print("    1: Night (moonlight, street lights on)")
    print("    2: Dawn (sunrise colors)")
    print("    3: Day (bright sunlight)")
    print("    4: Dusk (sunset colors)")
    print("  R: Cycle Weather (Clear -> Rain -> Heavy Rain)")
    print("  T: Toggle Auto Time (day/night cycle)")
    print("  F: Toggle Extra Fog")
    print("  Arrow Keys: Rotate/Move Camera")
    print("\nFEATURES:")
    print("  - Fixed-length straight road (not infinite)")
    print("  - Green START line and checkered FINISH line")
    print("  - Lamp posts beside road with colored markers at start/finish")
    print("  - Buildings beside road with proper spacing")
    print("  - Trees between and beyond buildings")
    print("  - Dynamic weather with rain particles")
    print("  - Day/night cycle with proper lighting")
    print("  - Street lights auto-on at night/rain")
    print("  - Track map showing the complete road")
    print("  - Wet road effects during rain")
    print("\nESC: Exit")
    print("=" * 60)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
