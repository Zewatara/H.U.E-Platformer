from dis import dis
from multiprocessing.connection import wait
from time import time
import turtle
import pygame, sys, os, random
clock = pygame.time.Clock()

from pygame.locals import *
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init() # initiates pygame
pygame.mixer.set_num_channels(12)

pygame.display.set_caption('Hue (Hazardous utopian entity)')

WINDOW_SIZE = (1200,1200)

screen = pygame.display.set_mode(WINDOW_SIZE,0,32) # initiate the window

display = pygame.Surface((400,400)) # used as the surface for rendering, which is scaled

loadingLevel = False

moving_right = False
moving_left = False
vertical_momentum = 0
air_timer = 0

game_level = 1

true_scroll = [0,0]

def load_map(path):
    f = open(path + '.txt','r')
    data = f.read()
    f.close()
    data = data.split('\n')
    game_map = []
    for row in data:
        game_map.append(list(row))
    return game_map

global animation_frames
animation_frames = {}

def load_animation(path,frame_durations):
    global animation_frames
    animation_name = path.split('/')[-1]
    animation_frame_data = []
    n = 0
    for frame in frame_durations:
        animation_frame_id = animation_name + '_' + str(n)
        img_loc = path + '/' + animation_frame_id + '.png'
        # player_animations/idle/idle_0.png
        animation_image = pygame.image.load(img_loc).convert()
        animation_image.set_colorkey((255,255,255))
        animation_frames[animation_frame_id] = animation_image.copy()
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data

def change_action(action_var,frame,new_value):
    if action_var != new_value:
        action_var = new_value
        frame = 0
    return action_var,frame
        

animation_database = {}

animation_database['run'] = load_animation('player_animations/run',[7,7])
animation_database['idle'] = load_animation('player_animations/idle',[7,7,40])

game_map = load_map('stage3')

#sprites-stage1
scifi_background_plate = pygame.image.load('Tiles/scifi/scifi_background_plate.png').convert()
scifi_background_script = pygame.image.load('Tiles/scifi/scifi_background_script.png').convert()
scifi_background_vent = pygame.image.load('Tiles/scifi/scifi_background_vent.png').convert()
scifi_background = pygame.image.load('Tiles/scifi/scifi_background.png').convert()
scifi_cornerL = pygame.image.load('Tiles/scifi/scifi_cornerL.png').convert()
scifi_cornerR = pygame.image.load('Tiles/scifi/scifi_cornerR.png').convert()
scifi_Down_cornerL = pygame.image.load('Tiles/scifi/scifi_Down_cornerL.png').convert()
scifi_Down_cornerR = pygame.image.load('Tiles/scifi/scifi_Down_cornerR.png').convert()
scifi_floor = pygame.image.load('Tiles/scifi/scifi_floor.png').convert()
scifi_floorA = pygame.image.load('Tiles/scifi/scifi_floorA.png').convert()
scifi_Frame = pygame.image.load('Tiles/scifi/scifi_Frame.png').convert()
scifi_FrameFilled = pygame.image.load('Tiles/scifi/scifi_FrameFilled.png').convert()
scifi_roof = pygame.image.load('Tiles/scifi/scifi_roof.png').convert()
scifi_wallL = pygame.image.load('Tiles/scifi/scifi_wallL.png').convert()
scifi_wallR = pygame.image.load('Tiles/scifi/scifi_wallR.png').convert()
scifi_weird_wallL = pygame.image.load('Tiles/scifi/scifi_weird_wallL.png').convert()
scifi_weird_wallR = pygame.image.load('Tiles/scifi/scifi_weird_wallR.png').convert()
scifi_Weirdfloor = pygame.image.load('Tiles/scifi/scifi_Weirdfloor.png').convert()
stage1_portal = pygame.image.load('Tiles/misc/stage1_portal.png').convert_alpha()

land_sound = pygame.mixer.Sound('Sound/SFX/land.wav')
portal_sound = pygame.mixer.Sound('Sound/SFX/portal.wav')
death_sound = pygame.mixer.Sound('Sound/SFX/death.wav')
#jump_sound = pygame.mixer.Sound('Sound/SFX/jump.wav')
grass_sounds = [pygame.mixer.Sound('Sound/SFX/step1.wav'),pygame.mixer.Sound('Sound/SFX/step2.wav')]
jump_sounds = [pygame.mixer.Sound('Sound/SFX/jump1.wav'),pygame.mixer.Sound('Sound/SFX/jump2.wav'),pygame.mixer.Sound('Sound/SFX/jump3.wav'),pygame.mixer.Sound('Sound/SFX/jump4.wav'),pygame.mixer.Sound('Sound/SFX/jump5.wav')]
grass_sounds[0].set_volume(0.2)
grass_sounds[1].set_volume(0.2)

pygame.mixer.music.load('Sound/Music/track1.mp3')
pygame.mixer.music.play(-1)

player_action = 'idle'
player_frame = 0
player_flip = False
grounded = False

grass_sound_timer = 0

player_rect = pygame.Rect(30,100,5,13)

TargetColor = [115,89,120]
background_objects = [[0.25,[120,10,70,400]],[0.25,[280,30,40,400]],[0.5,[30,40,40,400]],[0.5,[130,90,100,400]],[0.5,[300,80,120,400]],[0.25,[420,10,70,400]],[0.25,[580,30,40,400]],[0.5,[420,40,40,400]],[0.5,[430,90,100,400]],[0.5,[700,80,120,400]],[0.5,[1130,40,40,400]],[0.5,[1230,90,100,400]],[0.5,[1400,80,120,400]]]
#background_objects = [[0,[0,0,0,0]]]

def collision_test(rect,tiles):
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list

def move(rect,movement,tiles):
    collision_types = {'top':False,'bottom':False,'right':False,'left':False}
    rect.x += movement[0]
    hit_list = collision_test(rect,tiles)
    for tile in hit_list:
        if movement[0] > 0:
            rect.right = tile.left
            collision_types['right'] = True
        elif movement[0] < 0:
            rect.left = tile.right
            collision_types['left'] = True
    rect.y += movement[1]
    hit_list = collision_test(rect,tiles)
    for tile in hit_list:
        if movement[1] > 0:
            rect.bottom = tile.top
            collision_types['bottom'] = True
        elif movement[1] < 0:
            rect.top = tile.bottom
            collision_types['top'] = True
    return rect, collision_types

while True: # game loop

    if (game_level == 2 and loadingLevel == True):
        i = 0
        Target = [153, 204, 255]
        if Target[0] < TargetColor[0] :
            i += 1
            TargetColor[0] += -1 
        if Target[1] < TargetColor[1] :
            i += 1
            TargetColor[1] += -1 
        if Target[2] < TargetColor[2] :
            i += 1
            TargetColor[2] += -1 

        if Target[0] > TargetColor[0] :
            i += 1
            TargetColor[0] += 1
        if Target[1] > TargetColor[1] :
            i += 1
            TargetColor[1] += 1
        if Target[2] > TargetColor[2] :
            i += 1
            TargetColor[2] += 1 

        if (i == 0):
            loadingLevel = False


    display.fill(TargetColor) # clear screen by filling it with blue

    if grass_sound_timer > 0:
        grass_sound_timer -= 1

    if (player_rect[1] > 500) :
        if game_level == 1:
            death_sound.play()
            player_rect = pygame.Rect(30,100,5,13)

    print(player_rect[0])
    if (player_rect[0] > 6370 and game_level == 1) :
        load_map('stage2')
        player_rect = pygame.Rect(30,100,5,13)
        game_level = 2
        loadingLevel = True
        portal_sound.play()
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.load('Sound/Music/Qente_MASTER.wav')
        pygame.mixer.music.play(-1, 0, 1000) 

    true_scroll[0] += (player_rect.x-true_scroll[0]-152)/20
    true_scroll[1] += (player_rect.y-true_scroll[1]-106)/20
    scroll = true_scroll.copy()
    scroll[0] = int(scroll[0])
    scroll[1] = int(scroll[1])

    if scroll[1] <= 16 :
        scroll[1] = 16

    if scroll[1] >= 197 :
        scroll[1] = 197

    #pygame.draw.rect(display,(7,80,75),pygame.Rect(0,120,300,80))
    for background_object in background_objects:
        obj_rect = pygame.Rect(background_object[1][0]-scroll[0]*background_object[0],background_object[1][1]-scroll[1]*background_object[0],background_object[1][2],background_object[1][3])
        if background_object[0] == 0.5:
            pygame.draw.rect(display,(155,115,155),obj_rect)
        else:
            pygame.draw.rect(display,(224,150,180),obj_rect)

    tile_rects = []
    y = 0
    for layer in game_map:
        x = 0
        for tile in layer:

            if (x*16-scroll[0]-64) < 364 and (x*16-scroll[0]) > -80 :

                if game_level == 1 :
                    if tile == 'q':
                        display.blit(scifi_background_plate,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'w':
                        display.blit(scifi_background_script,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'e':
                        display.blit(scifi_background_vent,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'r':
                        display.blit(scifi_background,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 't':
                        display.blit(scifi_cornerL,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'y':
                        display.blit(scifi_cornerR,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'u':
                        display.blit(scifi_Down_cornerL,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'i':
                        display.blit(scifi_Down_cornerR,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'o':
                        display.blit(scifi_floor,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'p':
                        display.blit(scifi_floorA,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'a':
                        display.blit(scifi_Frame,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 's':
                        display.blit(scifi_FrameFilled,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'd':
                        display.blit(scifi_roof,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'f':
                        display.blit(scifi_wallL,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'g':
                        display.blit(scifi_wallR,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'h':
                        display.blit(scifi_weird_wallL,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'j':
                        display.blit(scifi_weird_wallR,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'k':
                        display.blit(scifi_Weirdfloor,(x*16-scroll[0],y*16-scroll[1]))
                    if tile == 'x':
                        display.blit(stage1_portal,(x*16-scroll[0],y*16-scroll[1]))
                        print(scroll[0])
            if tile != '0' and tile != 'x':
                tile_rects.append(pygame.Rect(x*16,y*16,16,16))
            x += 1
        y += 1

    player_movement = [0,0]
    if moving_right == True:
        player_movement[0] += 2
    if moving_left == True:
        player_movement[0] -= 2
    player_movement[1] += vertical_momentum
    vertical_momentum += 0.2
    if vertical_momentum > 6:
        vertical_momentum = 6

    if player_movement[0] == 0:
        player_action,player_frame = change_action(player_action,player_frame,'idle')
    if player_movement[0] > 0:
        player_flip = False
        player_action,player_frame = change_action(player_action,player_frame,'run')
    if player_movement[0] < 0:
        player_flip = True
        player_action,player_frame = change_action(player_action,player_frame,'run')

    player_rect,collisions = move(player_rect,player_movement,tile_rects)

    if collisions['bottom'] == True:
        air_timer = 0
        vertical_momentum = 0
        if player_movement[0] != 0:
            if grass_sound_timer == 0:
                grass_sound_timer = 15
                random.choice(grass_sounds).play()
    else:
        air_timer += 1

    player_frame += 1
    if player_frame >= len(animation_database[player_action]):
        player_frame = 0
    player_img_id = animation_database[player_action][player_frame]
    player_img = animation_frames[player_img_id]
    display.blit(pygame.transform.flip(player_img,player_flip,False),(player_rect.x-scroll[0],player_rect.y-scroll[1]))


    for event in pygame.event.get(): # event loop
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_RIGHT:
                moving_right = True
            if event.key == K_LEFT:
                moving_left = True
            if event.key == K_UP:
                if air_timer < 6:
                    random.choice(jump_sounds).play()
                    vertical_momentum = -4
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                moving_right = False
            if event.key == K_LEFT:
                moving_left = False
        
    screen.blit(pygame.transform.scale(display,WINDOW_SIZE),(0,0))
    pygame.display.update()
    clock.tick(60)
