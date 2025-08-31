#!/usr/bin/env python3
# setup.py - Person 1's Responsibility: Scene Setup with Dynamic Environment
# Complete Python implementation using PyOpenGL

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys

# Camera variables for dynamic movement
camera_x = 0
camera_y = 10
camera_z = 20
camera_look_x = 0
camera_look_y = 0
camera_look_z = 0

# Environment scrolling variables
road_offset = 0  # For scrolling road markings
environment_offset = 0  # For scrolling trees, lamp posts, etc.
scroll_speed = 0.5  # Base scrolling speed

# Dynamic object lists
trees = []
lamp_posts = []
road_segments = []
clouds = []

# Initialize dynamic objects
def init_dynamic_objects():
    """Initialize positions for dynamic objects"""
    global trees, lamp_posts, road_segments, clouds
    
    # Generate trees on both sides of the road
    trees = []
    for i in range(30):
        side = random.choice([-1, 1])
        x = side * random.uniform(25, 50)
        z = random.uniform(-100, 300)
        tree_type = random.randint(0, 2)  # Different tree types
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
    for i in range(10):
        x = random.uniform(-100, 100)
        y = random.uniform(40, 60)
        z = random.uniform(-100, 300)
        size = random.uniform(5, 15)
        clouds.append({'x': x, 'y': y, 'z': z, 'size': size})

def update_dynamic_objects(speed=0):
    """Update positions of dynamic objects based on car speed"""
    global road_offset, environment_offset, trees, lamp_posts, road_segments, clouds
    
    # Update offsets based on speed
    road_offset += speed
    environment_offset += speed
    
    # Update trees - move them backward and respawn
    for tree in trees:
        tree['z'] += speed
        # If tree moves behind camera, respawn it in front
        if tree['z'] > 30:
            tree['z'] = random.uniform(-200, -150)
            tree['x'] = random.choice([-1, 1]) * random.uniform(25, 50)
            tree['type'] = random.randint(0, 2)
            tree['size'] = random.uniform(0.8, 1.3)
    
    # Update lamp posts
    for lamp in lamp_posts:
        lamp['z'] += speed
        # Respawn lamp posts that go behind
        if lamp['z'] > 30:
            lamp['z'] -= 600  # Move to front
    
    # Update road segments for infinite road
    for segment in road_segments:
        segment['z'] += speed
        if segment['z'] > 30:
            segment['z'] -= 600
    
    # Update clouds (move slower for parallax effect)
    for cloud in clouds:
        cloud['z'] += speed * 0.3  # Clouds move slower
        if cloud['z'] > 50:
            cloud['z'] = random.uniform(-250, -200)
            cloud['x'] = random.uniform(-100, 100)
            cloud['y'] = random.uniform(40, 60)

def setup_camera():
    """Set up the camera view for the game"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 0.1, 1000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # Camera positioned behind and above the car
    gluLookAt(camera_x, camera_y, camera_z,
              camera_look_x, camera_look_y, camera_look_z,
              0, 1, 0)

def setup_lighting():
    """Set up lighting for the scene"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    
    # Main sunlight
    light0_position = [10.0, 20.0, 10.0, 0.0]
    light0_diffuse = [1.0, 1.0, 0.9, 1.0]
    light0_ambient = [0.3, 0.3, 0.3, 1.0]
    light0_specular = [1.0, 1.0, 1.0, 1.0]
    
    glLightfv(GL_LIGHT0, GL_POSITION, light0_position)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diffuse)
    glLightfv(GL_LIGHT0, GL_AMBIENT, light0_ambient)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light0_specular)
    
    # Fill light
    light1_position = [-10.0, 15.0, -10.0, 0.0]
    light1_diffuse = [0.3, 0.3, 0.4, 1.0]
    
    glLightfv(GL_LIGHT1, GL_POSITION, light1_position)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, light1_diffuse)

def setup_fog():
    """Set up fog for depth effect"""
    glEnable(GL_FOG)
    fog_color = [0.7, 0.8, 0.9, 1.0]
    glFogfv(GL_FOG_COLOR, fog_color)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 50.0)
    glFogf(GL_FOG_END, 200.0)
    glFogf(GL_FOG_DENSITY, 0.02)

def draw_dynamic_road():
    """Draw road with moving segments for infinite effect"""
    road_width = 20
    segment_length = 40
    
    # Draw main road segments
    for segment in road_segments:
        z_pos = segment['z']
        
        # Skip segments too far away
        if z_pos < -150 or z_pos > 50:
            continue
        
        # Vary road color slightly for each segment
        if segment['type'] == 0:
            glColor3f(0.2, 0.2, 0.2)  # Dark asphalt
        else:
            glColor3f(0.25, 0.25, 0.25)  # Lighter asphalt
        
        glBegin(GL_QUADS)
        glVertex3f(-road_width/2, 0, z_pos)
        glVertex3f(road_width/2, 0, z_pos)
        glVertex3f(road_width/2, 0, z_pos + segment_length)
        glVertex3f(-road_width/2, 0, z_pos + segment_length)
        glEnd()
        
        # Add road texture details
        draw_road_details(z_pos, segment_length, road_width)

def draw_road_details(z_start, length, width):
    """Add details like cracks and patches to road segments"""
    # Random road patches (darker areas)
    if random.random() > 0.7:
        patch_size = random.uniform(2, 5)
        patch_x = random.uniform(-width/3, width/3)
        patch_z = z_start + random.uniform(5, length-5)
        
        glColor3f(0.15, 0.15, 0.15)
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
    
    # Calculate offset for animation
    offset = (road_offset * 2) % (marking_length + gap_length)
    
    # Center line (dashed yellow) - animated
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
    
    # Side lines (solid white)
    glColor3f(1.0, 1.0, 1.0)
    for z in range(-150, 100, 40):
        # Left edge line segments
        glBegin(GL_QUADS)
        glVertex3f(-10 + marking_width, 0.1, z)
        glVertex3f(-10, 0.1, z)
        glVertex3f(-10, 0.1, z + 35)
        glVertex3f(-10 + marking_width, 0.1, z + 35)
        glEnd()
        
        # Right edge line segments
        glBegin(GL_QUADS)
        glVertex3f(10 - marking_width, 0.1, z)
        glVertex3f(10, 0.1, z)
        glVertex3f(10, 0.1, z + 35)
        glVertex3f(10 - marking_width, 0.1, z + 35)
        glEnd()

def draw_dynamic_trees():
    """Draw trees that move as car progresses with depth-based fading"""
    # Sort trees by depth (far to near) for proper transparency
    sorted_trees = sorted(trees, key=lambda t: -t['z'])
    
    for tree in sorted_trees:
        if tree['z'] < -100 or tree['z'] > 30:
            continue  # Skip trees too far away
        
        # Calculate fade based on distance using depth
        distance = abs(tree['z'])
        if distance > 80:
            # Far trees are more transparent (fade effect)
            alpha = max(0.3, 1.0 - (distance - 80) / 50)
            glDepthMask(GL_FALSE)  # Don't write to depth buffer for transparent objects
        else:
            alpha = 1.0
            glDepthMask(GL_TRUE)  # Write to depth buffer for opaque objects
        
        glPushMatrix()
        glTranslatef(tree['x'], 0, tree['z'])
        glScalef(tree['size'], tree['size'], tree['size'])
        
        # Apply alpha for distance fade
        glColor4f(1, 1, 1, alpha)
        
        # Different tree types
        if tree['type'] == 0:
            draw_pine_tree()
        elif tree['type'] == 1:
            draw_round_tree()
        else:
            draw_palm_tree()
        
        glPopMatrix()
    
    # Reset depth mask
    glDepthMask(GL_TRUE)

def draw_pine_tree():
    """Draw a pine tree"""
    # Trunk
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    glutSolidCylinder(0.5, 4, 8, 8)
    glPopMatrix()
    
    # Three layers of cone-shaped leaves
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
    
    # Round leaves
    glColor3f(0.2, 0.5, 0.1)
    glPushMatrix()
    glTranslatef(0, 6, 0)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()

def draw_palm_tree():
    """Draw a palm tree"""
    # Trunk (curved)
    glColor3f(0.5, 0.3, 0.1)
    for i in range(5):
        glPushMatrix()
        glTranslatef(i*0.1, i*1.2, 0)
        glRotatef(-90, 1, 0, 0)
        glutSolidCylinder(0.4, 1.2, 6, 6)
        glPopMatrix()
    
    # Palm leaves
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
    """Draw street lamp posts along the road"""
    for lamp in lamp_posts:
        if lamp['z'] < -100 or lamp['z'] > 30:
            continue
        
        # Draw on both sides of the road
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
            
            # Lamp light
            if lamp['light_on']:
                # Glowing effect
                glDisable(GL_LIGHTING)
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
    """Draw clouds that slowly move across the sky with depth-based rendering"""
    glDisable(GL_LIGHTING)
    
    # Sort clouds by depth for proper rendering
    sorted_clouds = sorted(clouds, key=lambda c: -c['z'])
    
    for cloud in sorted_clouds:
        if cloud['z'] < -200 or cloud['z'] > 50:
            continue
        
        # Use depth testing for cloud layering
        distance = abs(cloud['z'] + 50)
        alpha = max(0.4, min(0.9, 1.0 - distance / 300))
        
        # Disable depth writing for transparent clouds
        glDepthMask(GL_FALSE)
        glColor4f(1.0, 1.0, 1.0, alpha)
        
        glPushMatrix()
        glTranslatef(cloud['x'], cloud['y'], cloud['z'])
        
        # Draw cloud as multiple spheres with depth offset
        for i in range(3):
            x_offset = (i - 1) * cloud['size'] * 0.5
            # Use polygon offset to prevent z-fighting between cloud parts
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(-1.0, -1.0)
            glutSolidSphere(cloud['size'] * 0.7, 8, 8)
            glDisable(GL_POLYGON_OFFSET_FILL)
            glTranslatef(x_offset, 0, 0)
        
        glPopMatrix()
    
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)

def draw_boundary_walls():
    """Draw moving boundary walls/barriers"""
    wall_height = 3
    wall_segment_length = 20
    
    # Draw wall segments
    for z in range(-150, 100, wall_segment_length):
        z_pos = z + (environment_offset % wall_segment_length)
        
        if z_pos < -100 or z_pos > 30:
            continue
        
        # Left wall segment
        glColor3f(0.6, 0.6, 0.6)
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
            glColor3f(1.0, 1.0, 0.0)  # Yellow stripes
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
    """Draw moving ground/grass with texture variation"""
    # Draw ground in segments for better performance
    for x in range(-10, 11):
        for z in range(-10, 15):
            z_pos = z * 20 + (environment_offset * 0.5) % 20
            
            if z_pos < -150 or z_pos > 50:
                continue
            
            # Vary grass color
            green_variation = 0.4 + (x + z) % 3 * 0.1
            glColor3f(0.2, green_variation, 0.1)
            
            glBegin(GL_QUADS)
            glVertex3f(x * 20 - 10, -0.1, z_pos - 10)
            glVertex3f(x * 20 + 10, -0.1, z_pos - 10)
            glVertex3f(x * 20 + 10, -0.1, z_pos + 10)
            glVertex3f(x * 20 - 10, -0.1, z_pos + 10)
            glEnd()

def draw_sky_gradient():
    """Draw gradient sky background"""
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    glBegin(GL_QUADS)
    # Bottom (horizon) - lighter
    glColor3f(0.7, 0.85, 1.0)
    glVertex3f(-200, -50, -190)
    glVertex3f(200, -50, -190)
    
    # Top - darker blue
    glColor3f(0.3, 0.5, 0.9)
    glVertex3f(200, 100, -190)
    glVertex3f(-200, 100, -190)
    glEnd()
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

def init_scene():
    """Initialize OpenGL settings and dynamic objects"""
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)  # Better depth testing for overlapping objects
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.5, 0.7, 1.0, 1.0)
    
    # Set up depth range for better precision
    glDepthRange(0.0, 1.0)
    
    # Enable alpha blending for transparency effects
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Initialize dynamic objects
    init_dynamic_objects()
    
    # Enable fog
    setup_fog()
    
    # Material properties
    mat_specular = [1.0, 1.0, 1.0, 1.0]
    mat_shininess = [50.0]
    glMaterialfv(GL_FRONT, GL_SPECULAR, mat_specular)
    glMaterialfv(GL_FRONT, GL_SHININESS, mat_shininess)

def render_complete_scene(car_speed=0):
    """Main function to render all dynamic scene elements with proper depth ordering
    
    Args:
        car_speed: Current speed of the car (affects environment scrolling)
    """
    # Update dynamic objects based on car speed
    update_dynamic_objects(car_speed)
    
    # Set up camera and lighting
    setup_camera()
    setup_lighting()
    
    # Clear depth buffer properly
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Render sky first (farthest, no depth writing needed)
    glDepthMask(GL_FALSE)  # Don't write sky to depth buffer
    draw_sky_gradient()
    glDepthMask(GL_TRUE)
    
    # Enable depth testing with less-equal for better precision
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    
    # Draw opaque objects first (back to front isn't needed for opaque)
    draw_dynamic_ground()
    draw_dynamic_road()
    draw_dynamic_road_markings()
    draw_boundary_walls()
    draw_lamp_posts()
    
    # Draw objects that might have transparency (need sorting)
    draw_dynamic_trees()  # Trees fade with distance
    
    # Draw transparent objects last with depth testing but no depth writing
    glDepthFunc(GL_LESS)  # Standard depth testing for clouds
    draw_moving_clouds()  # Clouds are semi-transparent
    
    # Reset depth function to default
    glDepthFunc(GL_LEQUAL)

# Testing with simulated movement
if __name__ == "__main__":
    test_speed = 0
    acceleration = 0
    
    def keyboard(key, x, y):
        global test_speed, acceleration
        if key == b'w':  # Accelerate
            acceleration = 0.1
        elif key == b's':  # Brake
            acceleration = -0.1
        elif key == b' ':  # Stop
            test_speed = 0
            acceleration = 0
    
    def keyboard_up(key, x, y):
        global acceleration
        if key in [b'w', b's']:
            acceleration = 0
    
    def update_speed():
        global test_speed, acceleration
        test_speed += acceleration
        test_speed *= 0.98  # Friction
        test_speed = max(-2, min(test_speed, 5))  # Limit speed
    
    def display():
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        update_speed()
        render_complete_scene(test_speed)
        
        # Display speed for testing
        glDisable(GL_LIGHTING)
        glColor3f(1, 1, 1)
        glRasterPos2f(-0.9, 0.9)
        for char in f"Speed: {test_speed:.2f} (Use W/S keys)":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        glEnable(GL_LIGHTING)
        
        glutSwapBuffers()
    
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"3D Racing Game - Dynamic Scene Test")
    init_scene()
    glutDisplayFunc(display)
    glutIdleFunc(display)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    print("Controls: W = Accelerate, S = Brake, Space = Stop")
    glutMainLoop()