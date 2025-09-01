#!/usr/bin/env python3
"""
3D Racing Game Environment with Rain, Day/Night Cycle, and Road Map
Environment and scenery setup only - no car mechanics
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Window constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

# Camera variables (from template)
camera_pos = [0, 20, 40]
camera_look = [0, 0, 0]
fovY = 60
camera_angle = 0

# Road configuration
ROAD_WIDTH = 20
road_segments = []
road_curves = []  # Define the actual road path

# Environment variables
environment_offset = 0
scroll_speed = 0.5  # Environment scrolling speed
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
    """Initialize the road path - creates a racing circuit"""
    global road_segments, road_curves
    
    # Create a racing circuit with curves and straights
    road_segments = []
    road_curves = []
    
    # Define road path points for a circuit
    circuit_points = [
        # Start/finish straight
        {'x': 0, 'z': 0, 'type': 'straight'},
        {'x': 0, 'z': -100, 'type': 'straight'},
        # First turn
        {'x': 30, 'z': -150, 'type': 'curve'},
        {'x': 60, 'z': -180, 'type': 'curve'},
        {'x': 100, 'z': -180, 'type': 'straight'},
        # Back straight
        {'x': 200, 'z': -180, 'type': 'straight'},
        # Second turn
        {'x': 250, 'z': -150, 'type': 'curve'},
        {'x': 280, 'z': -100, 'type': 'curve'},
        {'x': 280, 'z': 0, 'type': 'straight'},
        # Third turn
        {'x': 250, 'z': 50, 'type': 'curve'},
        {'x': 200, 'z': 80, 'type': 'curve'},
        {'x': 100, 'z': 80, 'type': 'straight'},
        # Final turn back to start
        {'x': 50, 'z': 50, 'type': 'curve'},
        {'x': 20, 'z': 20, 'type': 'curve'},
    ]
    
    # Generate road segments
    for i in range(len(circuit_points)):
        point = circuit_points[i]
        next_point = circuit_points[(i + 1) % len(circuit_points)]
        
        road_segments.append({
            'start': {'x': point['x'], 'z': point['z']},
            'end': {'x': next_point['x'], 'z': next_point['z']},
            'type': point['type']
        })
    
    road_curves = circuit_points

def init_environment():
    """Initialize all environment objects"""
    global trees, buildings, street_lights, clouds
    
    # Generate trees along the road
    trees = []
    for segment in road_segments:
        # Place trees along road segments
        for t in range(3):
            offset = random.uniform(25, 50)
            side = random.choice([-1, 1])
            
            # Interpolate position along segment
            alpha = random.random()
            x = segment['start']['x'] + alpha * (segment['end']['x'] - segment['start']['x'])
            z = segment['start']['z'] + alpha * (segment['end']['z'] - segment['start']['z'])
            
            # Add perpendicular offset
            dx = segment['end']['x'] - segment['start']['x']
            dz = segment['end']['z'] - segment['start']['z']
            length = math.sqrt(dx*dx + dz*dz)
            if length > 0:
                nx = -dz / length * offset * side
                nz = dx / length * offset * side
                x += nx
                z += nz
            
            height = random.uniform(8, 15)
            tree_type = random.choice(['pine', 'oak', 'palm'])
            trees.append({'x': x, 'z': z, 'height': height, 'type': tree_type})
    
    # Generate buildings in clusters
    buildings = []
    building_zones = [
        {'x': 150, 'z': -250, 'count': 8},
        {'x': -100, 'z': -100, 'count': 6},
        {'x': 350, 'z': 0, 'count': 7},
        {'x': 150, 'z': 150, 'count': 5}
    ]
    
    for zone in building_zones:
        for b in range(zone['count']):
            x = zone['x'] + random.uniform(-80, 80)
            z = zone['z'] + random.uniform(-80, 80)
            height = random.uniform(20, 50)
            width = random.uniform(15, 25)
            buildings.append({'x': x, 'z': z, 'height': height, 'width': width})
    
    # Generate street lights along the road
    street_lights = []
    for segment in road_segments:
        # Place lights at segment points
        street_lights.append({
            'x': segment['start']['x'],
            'z': segment['start']['z'],
            'on': False
        })
    
    # Generate clouds
    clouds = []
    for i in range(20):
        x = random.uniform(-300, 300)
        y = random.uniform(60, 100)
        z = random.uniform(-300, 300)
        size = random.uniform(15, 30)
        clouds.append({'x': x, 'y': y, 'z': z, 'size': size})

def init_rain_system():
    """Initialize rain particle system"""
    global rain_particles
    rain_particles = []
    for i in range(max_rain_particles):
        rain_particles.append({
            'x': random.uniform(-200, 200),
            'y': random.uniform(0, 100),
            'z': random.uniform(-300, 300),
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
    gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 1000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Look at the road
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
                particle['x'] = random.uniform(-200, 200)
                particle['y'] = random.uniform(80, 100)
                particle['z'] = random.uniform(-300, 300)
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
    """Draw the racing circuit road"""
    # Draw road segments
    for segment in road_segments:
        glColor3f(0.2, 0.2, 0.2) if weather_mode == "clear" else glColor3f(0.15, 0.15, 0.15)
        
        # Calculate road direction
        dx = segment['end']['x'] - segment['start']['x']
        dz = segment['end']['z'] - segment['start']['z']
        length = math.sqrt(dx*dx + dz*dz)
        
        if length > 0:
            # Perpendicular vector for road width
            nx = -dz / length * ROAD_WIDTH / 2
            nz = dx / length * ROAD_WIDTH / 2
            
            # Draw road segment
            glBegin(GL_QUADS)
            glVertex3f(segment['start']['x'] - nx, 0, segment['start']['z'] - nz)
            glVertex3f(segment['start']['x'] + nx, 0, segment['start']['z'] + nz)
            glVertex3f(segment['end']['x'] + nx, 0, segment['end']['z'] + nz)
            glVertex3f(segment['end']['x'] - nx, 0, segment['end']['z'] - nz)
            glEnd()
            
            # Draw center line
            glColor3f(1, 1, 0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            steps = int(length / 10)
            for i in range(0, steps, 2):
                t1 = i / float(steps)
                t2 = min((i + 1) / float(steps), 1.0)
                x1 = segment['start']['x'] + t1 * dx
                z1 = segment['start']['z'] + t1 * dz
                x2 = segment['start']['x'] + t2 * dx
                z2 = segment['start']['z'] + t2 * dz
                glVertex3f(x1, 0.01, z1)
                glVertex3f(x2, 0.01, z2)
            glEnd()
            
            # Side lines
            glColor3f(1, 1, 1)
            glBegin(GL_LINES)
            glVertex3f(segment['start']['x'] - nx, 0.01, segment['start']['z'] - nz)
            glVertex3f(segment['end']['x'] - nx, 0.01, segment['end']['z'] - nz)
            glVertex3f(segment['start']['x'] + nx, 0.01, segment['start']['z'] + nz)
            glVertex3f(segment['end']['x'] + nx, 0.01, segment['end']['z'] + nz)
            glEnd()
    
    # Draw wet effect
    if weather_mode in ["rain", "heavy_rain"]:
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glColor4f(0.3, 0.3, 0.4, 0.3 * rain_intensity)
        
        for segment in road_segments:
            dx = segment['end']['x'] - segment['start']['x']
            dz = segment['end']['z'] - segment['start']['z']
            length = math.sqrt(dx*dx + dz*dz)
            
            if length > 0:
                nx = -dz / length * ROAD_WIDTH / 2
                nz = dx / length * ROAD_WIDTH / 2
                
                glBegin(GL_QUADS)
                glVertex3f(segment['start']['x'] - nx, 0.02, segment['start']['z'] - nz)
                glVertex3f(segment['start']['x'] + nx, 0.02, segment['start']['z'] + nz)
                glVertex3f(segment['end']['x'] + nx, 0.02, segment['end']['z'] + nz)
                glVertex3f(segment['end']['x'] - nx, 0.02, segment['end']['z'] - nz)
                glEnd()
        
        glDepthMask(GL_TRUE)

def draw_street_lights():
    """Draw street lights along the road"""
    phase = get_time_phase()
    lights_on = phase in ["Night", "Dusk", "Dawn"] or weather_mode == "heavy_rain"
    
    for light in street_lights:
        glPushMatrix()
        glTranslatef(light['x'], 0, light['z'])
        
        # Light pole
        glColor3f(0.3, 0.3, 0.3)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        glutSolidCylinder(0.3, 10, 8, 8)
        glPopMatrix()
        
        # Light fixture
        if lights_on:
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 0.7)
            glPushMatrix()
            glTranslatef(0, 9.5, 0)
            glutSolidSphere(0.8, 10, 10)
            glPopMatrix()
            
            # Glow effect
            glEnable(GL_BLEND)
            glColor4f(1.0, 1.0, 0.5, 0.2)
            glPushMatrix()
            glTranslatef(0, 9.5, 0)
            glutSolidSphere(3, 8, 8)
            glPopMatrix()
            glEnable(GL_LIGHTING)
        else:
            glColor3f(0.5, 0.5, 0.5)
            glPushMatrix()
            glTranslatef(0, 9.5, 0)
            glutSolidSphere(0.8, 10, 10)
            glPopMatrix()
        
        glPopMatrix()

def draw_trees():
    """Draw trees"""
    for tree in trees:
        glPushMatrix()
        glTranslatef(tree['x'], 0, tree['z'])
        
        if tree['type'] == 'pine':
            glColor3f(0.4, 0.2, 0.1)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            glutSolidCylinder(0.8, tree['height']/3, 8, 8)
            glPopMatrix()
            
            glColor3f(0.1, 0.5, 0.1)
            for i in range(3):
                glPushMatrix()
                glTranslatef(0, tree['height']/3 + i*3, 0)
                glRotatef(-90, 1, 0, 0)
                glutSolidCone(4 - i*0.8, 4, 10, 10)
                glPopMatrix()
        
        elif tree['type'] == 'oak':
            glColor3f(0.3, 0.15, 0.05)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            glutSolidCylinder(1.0, tree['height']/2, 8, 8)
            glPopMatrix()
            
            glColor3f(0.2, 0.6, 0.1)
            glPushMatrix()
            glTranslatef(0, tree['height']*0.7, 0)
            glutSolidSphere(tree['height']/2, 12, 12)
            glPopMatrix()
        
        else:  # palm
            glColor3f(0.5, 0.3, 0.1)
            for i in range(6):
                glPushMatrix()
                glTranslatef(i*0.15, i*2, 0)
                glRotatef(-90, 1, 0, 0)
                glutSolidCylinder(0.6, 2, 6, 6)
                glPopMatrix()
            
            glColor3f(0.1, 0.7, 0.1)
            for angle in range(0, 360, 45):
                glPushMatrix()
                glTranslatef(0.9, 12, 0)
                glRotatef(angle, 0, 1, 0)
                glRotatef(30, 1, 0, 0)
                glScalef(4, 0.4, 1.2)
                glutSolidCube(1)
                glPopMatrix()
        
        glPopMatrix()

def draw_buildings():
    """Draw buildings"""
    for building in buildings:
        glPushMatrix()
        glTranslatef(building['x'], building['height']/2, building['z'])
        
        glColor3f(0.6, 0.6, 0.7)
        glPushMatrix()
        glScalef(building['width'], building['height'], building['width'])
        glutSolidCube(1)
        glPopMatrix()
        
        # Windows at night
        phase = get_time_phase()
        if phase in ["Night", "Dusk", "Dawn"]:
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 0.5)
            for floor in range(3, int(building['height']), 5):
                for window in range(-int(building['width']/2), int(building['width']/2), 4):
                    if random.random() > 0.2:
                        glPushMatrix()
                        glTranslatef(window, floor - building['height']/2, building['width']/2 + 0.1)
                        glutSolidCube(1.2)
                        glPopMatrix()
            glEnable(GL_LIGHTING)
        
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
    """Draw ground/grass"""
    glColor3f(0.3, 0.5, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-400, -0.1, -400)
    glVertex3f(400, -0.1, -400)
    glVertex3f(400, -0.1, 400)
    glVertex3f(-400, -0.1, 400)
    glEnd()

def draw_road_map():
    """Draw overhead map view of the road"""
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
    map_size = 180
    
    glEnable(GL_BLEND)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(map_x, map_y)
    glVertex2f(map_x + map_size, map_y)
    glVertex2f(map_x + map_size, map_y + map_size)
    glVertex2f(map_x, map_y + map_size)
    glEnd()
    
    # Map border
    glColor3f(0.8, 0.8, 0.8)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(map_x, map_y)
    glVertex2f(map_x + map_size, map_y)
    glVertex2f(map_x + map_size, map_y + map_size)
    glVertex2f(map_x, map_y + map_size)
    glEnd()
    
    # Draw road on map
    center_x = map_x + map_size/2
    center_y = map_y + map_size/2
    scale = 0.4
    
    glColor3f(0.5, 0.5, 0.5)
    glLineWidth(6.0)
    glBegin(GL_LINE_LOOP)
    for point in road_curves:
        x = center_x + point['x'] * scale
        y = center_y - point['z'] * scale  # Flip z for screen coordinates
        glVertex2f(x, y)
    glEnd()
    
    # Draw start/finish line
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(3.0)
    glBegin(GL_LINES)
    glVertex2f(center_x - 10, center_y)
    glVertex2f(center_x + 10, center_y)
    glEnd()
    
    # Map title
    glColor3f(1, 1, 1)
    glRasterPos2f(map_x + 5, map_y + map_size - 15)
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
    """Update environment animations"""
    global time_of_day, environment_offset
    
    # Update time
    if auto_time:
        time_of_day += time_speed
        if time_of_day > 1.0:
            time_of_day = 0.0
    
    # Update environment offset for subtle movement
    environment_offset += scroll_speed
    
    # Update clouds
    for cloud in clouds:
        cloud['x'] += 0.05
        if cloud['x'] > 400:
            cloud['x'] = -400
    
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
        exit(0)

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
        camera_pos[0] = radius * math.sin(math.radians(camera_angle))
        camera_pos[2] = radius * math.cos(math.radians(camera_angle))
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5
        radius = math.sqrt(camera_pos[0]**2 + camera_pos[2]**2)
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
    glutCreateWindow(b"Racing Game Environment - Track with Weather System")
    
    init_scene()
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutTimerFunc(0, timer, 0)
    
    print("=" * 60)
    print("RACING GAME ENVIRONMENT")
    print("=" * 60)
    print("ENVIRONMENT CONTROLS:")
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
    print("  - Complete racing circuit with curves")
    print("  - Dynamic weather with rain particles")
    print("  - Day/night cycle with proper lighting")
    print("  - Street lights (auto-on at night/rain)")
    print("  - Track map in top-right corner")
    print("  - Various tree types and buildings")
    print("  - Wet road effects during rain")
    print("\nESC: Exit")
    print("=" * 60)
    
    glutMainLoop()

if __name__ == "__main__":
    main()