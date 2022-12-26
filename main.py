import sys
import pygame as pg
from typing import *
import random
import math

Vec2 = pg.math.Vector2
Vec3 = pg.math.Vector3
Vec = Vec2|Vec3

Number = float|int

def sqr(x):
    # Actually faster than x*x ! 
    # https://stackoverflow.com/questions/18453771/why-is-x3-slower-than-xxx/18453999#18453999
    return x**2

def cube(x):
    return x*x*x

def pow4(x):
    return x*x*x*x

def hex_to_rgb(code):
    return (code >> 16, (code >> 8) % 256, code % 256)

def to_vec3(v: Vec) -> Vec3:
    if isinstance(v, Vec3):
        return v
    elif isinstance(v, Vec2):
        return Vec3(v.x, v.y, 0.0)
    else:
        raise Exception(f"Attempt to convert {type(v)} to Vec3")

def to_vec2(v: Vec) -> Vec2:
    if isinstance(v, Vec2):
        return v
    elif isinstance(v, Vec3):
        return Vec2(v.x, v.y)
    else:
        raise Exception(f"Attempt to convert {type(v)} to Vec2")

# TODO: use button states (0: released; 1:just pressed; 2:down; 3:just released) 
# and implement is_key_pressed using this & modify is_key_down

def is_key_down(key):
    keys = pg.key.get_pressed()
    return keys[key]


def normalized(vec):
    if vec.length_squared() <= 0.000001:
        return vec
    return vec.normalize()

def get_directional_vector(directions):
    key_l, key_r, key_u, key_d = directions
    
    v = Vec2(0, 0)
    if is_key_down(key_l): v.x += -1
    if is_key_down(key_r): v.x += 1
    if is_key_down(key_u): v.y += -1
    if is_key_down(key_d): v.y += 1
    return normalized(v)

def get_directional_vector3(directions):
    return to_vec3(get_directional_vector(directions))

def draw_text(screen, text, pos=(0,0), color=None, **flags):
    if color == None: color = Colors.BLACK
    text = str(text)
    
    antialias = False
    for k in flags:
        if k == "antialias": antialias = flags[k]
    
    textsurface = Globals.game.font.render(text, antialias, color)  # "text", antialias, color
    screen.blit(textsurface, pos)


class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    MAGENTA = (255, 0, 255)


class Constants:
    DEFAULT_FRICTION = 5
    DEFAULT_MOVEMENT_FORCE = 3000


class Globals:
    game = None
     
     
class Image:
    def __init__(self, path:str, size=None) -> None:
        self.path = path
        self._image = pg.image.load(path)
        if size:
            self._image = pg.transform.scale(self._image, size)
        
        self.size = self.width, self.height = self._image.get_size()
    
    @property
    def image(self):
        return self._image
    
    @image.setter
    def image(self, val):
        self._image = val
    
    def draw(self, screen:pg.Surface, x:Vec2|Number, y:Number|None=None):
        if isinstance(x, Vec):
            screen.blit(self._image, x)
        elif isinstance(x, Number) and isinstance(y, Number):
            screen.blit(self._image, (x, y))
        else:
            raise Exception(f"Invalid type given : type(x) = {type(x)}, type(y) = {type(y)}")
    
class InputManager:
    def __init__(self, dict) -> None:
        self.controls = dict
        self.button_states = {key: 0 for key in dict}
        
        self.left = dict["left"]
        self.right = dict["right"]
        self.up = dict["up"]
        self.down = dict["down"]
        self.move = [self.left, self.right, self.up, self.down]
        
        self.dive = dict["dive"]
    
    def update(self, dt=0):
        for button in self.controls:
            is_down = is_key_down(self.controls[button])
            past_state = self.button_states[button]

            # 0 = unpressed; 1 = just pressed; 2 = held; 3 = just released

            if is_down:
                if past_state == 0:
                    self.button_states[button] = 1
                elif past_state == 1:
                    self.button_states[button] = 2
                elif past_state == 2:
                    self.button_states[button] = 2
                elif past_state == 3:
                    self.button_states[button] = 1
            else:
                if past_state == 0:
                    self.button_states[button] = 0
                elif past_state == 1:
                    self.button_states[button] = 3
                elif past_state == 2:
                    self.button_states[button] = 3
                elif past_state == 3:
                    self.button_states[button] = 0
                    
    def is_button_down(self, button):
        state = self.button_states[button]
        
        if state == 1 or state == 2:
            return True
        return False
                    
    def is_button_pressed(self, button):
        state = self.button_states[button]
        return state == 1

    def is_button_released(self, button):
        state = self.button_states[button]
        return state == 3
    
    def get_directional_vector(self):
        v = Vec2(0, 0)
        if self.is_button_down("left"): v.x += -1
        if self.is_button_down("right"): v.x += 1
        if self.is_button_down("up"): v.y += -1
        if self.is_button_down("down"): v.y += 1
        return normalized(v)

    def get_directional_vector3(self):
        return to_vec3(self.get_directional_vector())

class Object:
    def __init__(self) -> None:
        self._delete_me = False  
    
    def delete(self) -> None:
        self._delete_me = True



class ImageRenderer:
    def __init__(self, **flags) -> None:
        self.shadow = False
        self.shadow_opacity = 128
        self.image = None
        # for key in flags:
        #     if key == "shadow": self.shadow = flags[key]
        #     if key == "shadow_opacity": self.shadow_opacity = flags[key]

    def set_image(self, image: Image|str):
        if type(image) == Image:
            self.image = image
        elif type(image) == str:
            self.image = Image(image)
        return self    

    def render(self, screen, actor):
        if self.image:            
            x = actor.pos.x - self.image.width/2
            y = actor.pos.y - self.image.height/2 
            
            if self.shadow:# and actor.pos.z >= 0:
                pg.draw.circle(screen, (0,0,0, 125), to_vec2(actor.pos), actor.collision.radius)
            
            self.image.draw(screen, x, y - actor.pos.z)
            
            # if self.shadow and actor.pos.z < 0:
            #     pg.draw.circle(screen, (0,0,0, 125), to_vec2(actor.pos), actor.collision.radius)


class Actor(Object):
    """
    Object with a position, velocity and subject to forces.
    """
    def __init__(self, x=0, y=0, z=0) -> None:
        super().__init__()
        self.pos: Vec3 = Vec3(x, y, z)
        self.vel: Vec3 = Vec3(0, 0, 0)
        self.acc: Vec3 = Vec3(0, 0, 0)

        self.friction = Constants.DEFAULT_FRICTION
        self._forces: List[Vec3] = []
        
        self.gravity_force = Vec3(0, 0, -6.674 * 1000) * 0
        
        # self.density = 1 # 1.0 represents tensity of water
        # self.buoyancy_force = Vec3()
        
        self.renderer = ImageRenderer()
    
    def update(self, dt: float) -> None:
        self.apply_force(self.gravity_force)
        
        # Buoyancy on water
        # if self.pos.z <= 0:
        #     self.buoyancy_force = -self.gravity_force / self.density
        #     self.apply_force(self.buoyancy_force)
        
        self.apply_force(-self.vel * self.friction)
        self.acc = Vec3()
        for f in self._forces:
            self.acc += f
            
        print(self._forces)
        
        self._forces.clear()
        self.vel += self.acc * dt
        # self.vel *= self.friction ** dt
        
        self.pos += self.vel * dt
        
    def draw(self, screen: pg.Surface) -> None:
        self.renderer.render(screen, self)
        
    def apply_force(self, force: Vec) -> None:
        assert isinstance(force, Vec), f"Attempt to apply non-vector force: type {type(force)}"
        
        force = to_vec3(force)
        self._forces.append(force)
        return self

    def distance(self, other):
        return math.sqrt(self.distance_sq(other))

    def distance_sq(self, other):
        return (self.pos.x - other.pos.x)**2 + (self.pos.y - other.pos.y)**2

    def get_vector_to(self, other):
        return Vec3(other.pos.x - self.pos.x, other.pos.y - self.pos.y, other.pos.z - self.pos.z)
    
    def get_nomalized_vector_to(self, other):
        return self.get_vector_to(other).normalize()

class Collision:
    def __init__(self) -> None:
        pass
    
    def is_touching_sphere_sphere(self, a, b, a_pos: Vec, b_pos: Vec):
        a_pos = to_vec3(a_pos)
        b_pos = to_vec3(b_pos)

        dist_sq = (a_pos.x - b_pos.x)**2 + (a_pos.y - b_pos.y)**2
        return dist_sq <= (a.radius + b.radius)**2
    
    def is_touching_sphere_border(self, sph, border, sph_pos):
        sph_pos = to_vec2(sph_pos)
        sph_a = sph_pos - Vec2(sph.radius, sph.radius)
        sph_b = sph_pos + Vec2(sph.radius, sph.radius)
        
        in_bounds = border.a.x <= sph_a.x <= border.b.x \
            and border.a.y <= sph_a.y <= border.b.y \
            and border.a.x <= sph_b.x <= border.b.x \
            and border.a.y <= sph_b.y <= border.b.y

        return not in_bounds

class SphereCollision(Collision):
    def __init__(self, radius: Number) -> None:
        super().__init__()
        self.radius: Number = radius
        
    def is_touching(self, other, self_pos, other_pos):
        if isinstance(other, SphereCollision):
            return self.is_touching_sphere_sphere(self, other, self_pos, other_pos)
        if isinstance(other, SphereCollision):
            return self.is_touching_sphere_sphere(self, other, self_pos)
        
class BorderCollision(Collision):
    """
    Collision that represents the border of the play area. 
    Is defined by a rectangle, extending infinitely in the z direction, and infinitely outwards. 
    """
    def __init__(self, a:Vec, b:Vec):
        self.a = to_vec3(a)
        self.b = to_vec3(b)
    
    def is_touching(self, other, self_pos, other_pos):
        if isinstance(other, SphereCollision):
            return self.is_touching_sphere_border(other, self, other_pos)
        


class CollidableActor(Actor):
    """
    Actor with a collision. May or may not interact with other CollisionActor.
    """
    def __init__(self, x=0, y=0, z=0) -> None:
        super().__init__(x, y, z)
        
        self.collision: Collision|None = None
        self.is_solid = False
    
    def set_collision(self, coll: Collision):
        self.collision = coll
        return self
    
    def set_solid(self, val: bool):
        self.is_solid = val
        return self

    def is_touching(self, other: 'CollidableActor'):
        assert self.collision != None, "Collision not defined for self"
        assert isinstance(other, CollidableActor), "other is not CollidableActor"
        assert other.collision != None, "Collision not defined for other"
        
        return self.collision.is_touching(other.collision, self.pos, other.pos)
    
    def on_collision(self, other, dt):
        # To be implemented in subclasses
        # print(f"Collision between {self} and {other}")
        ...
    

class Player(CollidableActor):
    def __init__(self, x=0, y=0, z=0) -> None:
        super().__init__(x, y, z)
        
        self.input_manager = InputManager({
            "left": pg.K_LEFT,
            "right": pg.K_RIGHT,
            "up": pg.K_UP,
            "down": pg.K_DOWN,
            "dive": pg.K_LSHIFT,
        })
        
        self.swimming_force = Constants.DEFAULT_MOVEMENT_FORCE
        self.diving_force = Constants.DEFAULT_MOVEMENT_FORCE * 1.5
        self.current_force = self.swimming_force
        
        self.is_diving = False
        
        self.typ = 0
        
        self.renderer.shadow = True
        self.renderer.set_image(Image("./assets/img/player.png", (64, 64)))
        # self.renderer.shadow = True

    def update(self, dt):
        self.input_manager.update(dt)
        self.do_movement(dt)
        
        super().update(dt)
        
        
    def draw(self, screen):
        super().draw(screen)
        
        # pg.draw.circle(screen, (0,80,0, 125), to_vec2(self.pos), self.collision.radius)
        pos = Vec3(round(self.pos.x,1), round(self.pos.y,1), round(self.pos.z,1))
        
        draw_text(screen, str(self.pos), to_vec2(self.pos) + Vec2(0, 40))
        

    def do_movement(self, dt) -> None:
        dir = get_directional_vector3(self.input_manager.move)
        self.apply_force(dir * self.current_force)

        self.do_diving(dt)

    def do_diving(self, dt) -> None:
        # If just dived, make the player go down
        # if not self.is_diving and self.input_manager.is_button_pressed("dive"):
            # self.apply_force(Vec3(0,0,-10000))
        
        self.is_diving = self.input_manager.is_button_down("dive")
        
        if self.is_diving:
            self.current_force = self.diving_force
        else:
            self.current_force = self.swimming_force
            
        # if is_key_down(pg.K_a):
        #     self.apply_force(Vec3(0, 0, 3000))
            


class Ball(CollidableActor):
    def __init__(self, x=0, y=0, z=0) -> None:
        super().__init__(x, y, z)
        
        self.radius = 0
        
        self.kick_multiplier = 2
        
        self.air_friction = Constants.DEFAULT_FRICTION * 1
        self.water_friction = Constants.DEFAULT_FRICTION * 1.0
        self.friction = self.air_friction
    
    def set_radius(self, val):
        self.radius = val
        self.set_collision(SphereCollision(val))
        return self
        
    def draw(self, screen) -> None:
        pg.draw.circle(screen, Colors.GREEN, to_vec2(self.pos), self.radius)
        draw_text(screen, self.pos)
    
    def on_collision(self, other, dt):
        force = (self.kick_multiplier * other.vel.length() * (1/dt) * -self.get_nomalized_vector_to(other))
        self.apply_force(force)



class Game:
    def __init__(self, caption="My Game", width=640, height=480, **flags) -> None:
        if Globals.game:
            raise Exception("There can only be one game")
        Globals.game = self
        
        self.dimensions = self.width, self.height = width, height
        self.fps = 60
        self._clock = pg.time.Clock()     ## For syncing the FPS
        self._actors: List[Actor] = []
        
        pg.init()
        pg.mixer.init()  ## For sound

        self.is_fullscreen = False
        
        mode = 0
        for k,v in flags.items():
            if k == "fullscreen" and v:
                mode = pg.FULLSCREEN
             
        self.screen: pg.Surface = pg.display.set_mode(self.dimensions, mode)
        self.alpha_screen = pg.Surface(self.dimensions, pg.SRCALPHA)

        pg.display.set_caption(caption)
        
        self.frame = 0
        self.prevdt = 1/self.fps
        

    def main(self) -> None:
        # Main game loop.
        self.init()
        
        dt = 1/self.fps
        self.prevdt = 1/self.fps
        while True:
            self.update(dt)
            self.draw(self.screen)

            self.prevdt = dt
            dt = self._clock.tick(self.fps) / 1000
            
    def init(self):
        self.font = pg.font.Font("./assets/fonts/Nunito-Regular.ttf", 35)
        
        player = Player(self.width/2, self.height/2) \
            .set_collision(SphereCollision(40)) \
            .set_solid(True)
        player.typ = 0
        self.new_actor(player)
        
        # player2 = Player(30, 60) \
        #     .set_image(Image("./img/player.png", (64, 64))) \
        #     .set_collision(SphereCollision(40)) \
        #     .set_solid(True)
        # player2.typ = 1
        # self.new_actor(player2)
        
        ball = Ball(self.width/2 + 200, self.height/2) \
            .set_radius(30) \
            .set_solid(True)
        self.new_actor(ball)
        
    def update(self, dt:float) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit() 
                sys.exit() 
        
        self.do_collisions(dt)    
        
        # Call update method on all actors
        i = 0
        while i < len(self._actors):
            a = self._actors[i]
            
            # Delete deleted actors
            if a._delete_me:
                self._actors.pop(i)
            
            else:
                a.update(dt)
                i += 1
                            

        self.frame += 1
                
    def do_collisions(self, dt:Number):
        # TODO: This is slow if there are a lot of actors
        # Could be optimized by segmenting the world into chunks 
        for i in range(len(self._actors)):
            for j in range(i+1, len(self._actors)):
                a1 = self._actors[i]
                a2 = self._actors[j]
                if a1.is_touching(a2):
                    a1.on_collision(a2, dt)
                    a2.on_collision(a1, dt)
        
    def draw(self, screen) -> None:
        screen.fill(hex_to_rgb(0x0095e9))
        self.alpha_screen.fill((0,0,0,0))

        # Draw
        for a in self._actors:
            a.draw(self.alpha_screen)

        # Flip the display so that the things we drew actually show up.
        screen.blit(self.alpha_screen, (0,0))
        pg.display.flip()
    
    def new_actor(self, actor:Actor):
        self._actors.append(actor)
        


game = Game("Wow awesome game", 640*2, 480*1.6) 
game.main()
