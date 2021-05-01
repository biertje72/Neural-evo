import sys, os, math, random
import pygame
from pygame.locals import *
    
WORKING_PATH = "./AnnoyPong/"
gScreensize = (0,0)
DEBUG_SURPRISES = True
SCREEN_SIZE_X = 1280
SCREEN_SIZE_Y = 700
#min & max speed of ball, proportional to gScreensize.x :)
BALL_MIN_SPEED = SCREEN_SIZE_X / 120.0
BALL_MAX_SPEED = SCREEN_SIZE_X / 20.0
PADDLE_MOVE_SPEED = SCREEN_SIZE_X/90
#toffe sounds http://soundbible.com/tags-laser.html

TIME_MODES = ["realtime", "fast_image", "superfast_no_image"]
def next_time_mode(time_mode):
     new_index = (TIME_MODES.index(time_mode) + 1) % len(TIME_MODES)
     return TIME_MODES[new_index]

class Game(object):
    """Our game object! This is a fairly simple object that handles the
    initialization of pygame and sets up our game to run."""
 
    def __init__(self, time_mode:str):
        """Called when the the Game object is initialized. Initializes
        pygame and sets up our pygame window and other pygame tools
        that we will need for more complicated tutorials."""

        global gScreensize
        gScreensize = (SCREEN_SIZE_X, SCREEN_SIZE_Y)

        self._multiBall = None
        self.time_mode = time_mode
        
        # You can set the position of the window by using SDL environment variables before you initialise pygame. Environment variables can be set with the os.environ dict in python. 
        xWindowPos = 40 #100
        yWindowPos = 40 #100
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (xWindowPos,yWindowPos)

        # load and set up pygame
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
         
        # create our window
        self.window = pygame.display.set_mode(gScreensize)
 
        # clock for ticking
        self.clock = pygame.time.Clock()
 
        # set the window title
        pygame.display.set_caption("Maus pong")
 
        # tell pygame to only pay attention to certain events
        # we want to know if the user hits the X on the window, and we
        # want keys so we can close the window with the esc key
        pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])
 
        # make background -- all green, with black line down the middle
        self.background = pygame.Surface(gScreensize)
        self.background.fill((100, 255, 100))
        # draw the middleline vertically down the center
        pygame.draw.line(self.background, (0,0,0), (gScreensize[0]/2,0), (gScreensize[0]/2,gScreensize[1]), 2)
        self.middlelineRect = Rect((gScreensize[0]/2,0), (1,gScreensize[1]))
        self.window.blit(self.background, (0,0))
        # flip the display so the background is on there
        pygame.display.flip()
 
        # a sprite rendering group for our ball, walls and paddles
        self.sprites = pygame.sprite.RenderUpdates()

        # create walls
        wallThickness = gScreensize[0]/128.0;
        wall1 = Wall((0.0, 0.0), float(gScreensize[0]), wallThickness);
        self.sprites.add(wall1)
        wall2 = Wall((0.0, 0.0), wallThickness, float(gScreensize[1])*.75);
        self.sprites.add(wall2)
        wall3 = Wall((0.0, float(gScreensize[1])- wallThickness), float(gScreensize[0]), wallThickness);
        self.sprites.add(wall3)
        wall4 = Wall((float(gScreensize[0])- wallThickness, 0.0), wallThickness, float(gScreensize[1])*.75)
        self.sprites.add(wall4)
        self.walls = [wall1, wall2, wall3, wall4];

        # sound
        self.sound = Sound()
        self.sound.setBackgroundMusic([f"{WORKING_PATH}/music/Commando_c64_SID_TUNE.mp3", f"{WORKING_PATH}/music/Silver Surfer - Level 1 - Nes Music.mp3", f"{WORKING_PATH}/music/ContraJungleTheme.mp3"])
        self.sound.enabled = (self.time_mode == "realtime")

        # create goals
        self.goalThickness = gScreensize[0]/64.0;
        self.goal1Left = Goal((-self.goalThickness, 0.0), self.goalThickness, float(gScreensize[1]), 'left')
        self.sprites.add(self.goal1Left)
        self.goal2Right = Goal((float(gScreensize[0]), 0.0), self.goalThickness, float(gScreensize[1]), 'right')
        self.sprites.add(self.goal2Right)
        self.goals = [self.goal1Left, self.goal2Right];

        # create our paddles and add to sprite group
        self.leftpaddle = None
        self.rightpaddle = None
        left_paddle =  Paddle((SCREEN_SIZE_X/16.0,SCREEN_SIZE_Y/2.0), SCREEN_SIZE_X/32.0, SCREEN_SIZE_Y/8.0,
                             float(SCREEN_SIZE_Y), 'paddle2.jpg', self)
        right_paddle = Paddle((SCREEN_SIZE_X*15.0/16.0,SCREEN_SIZE_Y/2.0), SCREEN_SIZE_X/32.0, SCREEN_SIZE_Y/8.0,
                             float(SCREEN_SIZE_Y), 'paddle1.jpg', self)
        self.add_or_replace_paddles(left_paddle, right_paddle)                    
                                   
        # create balls
        self.ball = Ball((gScreensize[0]/2.0, gScreensize[1]/2.0), gScreensize[1]/32.0,
                         gScreensize[1]/32.0, 'ball1.jpg')
        self.sprites.add(self.ball)
        self.ball2 = None            
        self.ball3 = None            

        #self.ball. (True, 0.2)

        # score image
        self.score = Score((gScreensize[0]/2, gScreensize[1]/10), gScreensize[1]/6)
        self.sprites.add(self.score)

        # surprise manager
        self.surpriseManager = SurpriseManager(self, self.sprites)
        #self.surpriseManager.prepareForNextRound()
        self.surpriseManager.waitToShowNextSurprise()

        self.frame = 0
        #FOR NOW MBI self.sound.loadAndPlayBackground()
        
    def add_or_replace_paddles(self, left_paddle, right_paddle):
        self.add_or_replace_left_paddle(left_paddle)
        self.add_or_replace_right_paddle(right_paddle)
                
    def add_or_replace_left_paddle(self, paddle):
        self.sprites.remove(self.leftpaddle)
        self.leftpaddle = paddle
        self.leftpaddle.setBase((SCREEN_SIZE_X/16.0,SCREEN_SIZE_Y/2.0))
        self.sprites.add(self.leftpaddle)

    def add_or_replace_right_paddle(self, paddle):
        self.sprites.remove(self.rightpaddle)
        self.rightpaddle = paddle
        self.rightpaddle.setBase((SCREEN_SIZE_X*15.0/16.0,SCREEN_SIZE_Y/2.0))
        self.sprites.add(self.rightpaddle)

    def ReflectBallOnSweptAABB(self, ball, collisiontime, normalx, normaly):
            ball.setX (ball.x + ball.velx * collisiontime)
            ball.setY (ball.y + ball.vely * collisiontime)
            remainingtime = 1.0 - collisiontime;
            #deflect
            if (abs(normalx) > 0.0001):
                ball.velx = -ball.velx;
            if (abs(normaly) > 0.0001):
                ball.vely = -ball.vely;	
#            ball.rect.x += ball.velx * remainingtime;
            #ball.rect.y +=ball.vely * remainingtime;
            ball.setX (ball.x + ball.velx * remainingtime)
            ball.setY (ball.y + ball.vely * remainingtime)

    def handleBallPaddleCollision(self, ball, paddle):
        impulseDemping = 0.75
        collisionHandled = False
        collisiontimeY, normalxY, normalyY, doReflectY, doImpulseY =  MyVerticalCollision(ball, paddle)
        collisiontimeX, normalxX, normalyX, doReflectX, doImpulseX =  MyHorizontalCollision(ball, paddle)
        
        if collisiontimeY < collisiontimeX:
            collisiontime = collisiontimeY
            normalx = normalxY
            normaly = normalyY
            doReflect = doReflectY
            doImpulse = doImpulseY 
        else:
            collisiontime = collisiontimeX
            normalx = normalxX
            normaly = normalyX
            doReflect = doReflectX
            doImpulse = doImpulseX
        
        if collisiontime != 1.0:
            if collisiontime > 1.0:
                print('waaat??')
            if doReflect:
                self.ReflectBallOnSweptAABB(ball, collisiontime, normalx, normaly)
            if doImpulse:
                ball.velx += paddle.velx * impulseDemping
                ball.vely += paddle.vely * impulseDemping
            collisionHandled = True
        return collisionHandled 


    def manageBall(self, lBall):
        """This basically runs the game. Moves the ball and handles
        wall and paddle collisions."""
        collisionHandled = False;

        # Collision handling with paddles
        # Left paddle
        if not collisionHandled and not self.leftpaddle.ghostMode: 
            collisionHandled = self.handleBallPaddleCollision(lBall, self.leftpaddle)
            if collisionHandled:
                lBall.setLastHitBy(self.leftpaddle)
                self.sound.play("ballPadHit1")

             
        # Right paddle
        if not collisionHandled and not self.rightpaddle.ghostMode: 
            collisionHandled = self.handleBallPaddleCollision(lBall, self.rightpaddle)
            if collisionHandled:
                lBall.setLastHitBy(self.rightpaddle)
                self.sound.play("ballPadHit1")
    
        # Collision handling with walls
        if not collisionHandled:
            for wall in self.walls:
                if not collisionHandled:
                    collisionHandled = self.handleBallPaddleCollision(lBall, wall)

        # Collision with goals, just sprite based
        goalHit = False
        if pygame.sprite.collide_rect(lBall, self.goal1Left):
            self.score.right()
            goalHit = True
        if pygame.sprite.collide_rect(lBall, self.goal2Right):
            self.score.left()
            goalHit = True
        if goalHit:            
            if self.time_mode == "realtime":
                self.sound.play("applause1")
            self.surpriseManager.prepareForNextRound()
            if not self._multiBall:
                if self.time_mode == "realtime":
                    pygame.time.delay(1500)
            lBall.setLastHitBy(self.rightpaddle)
            lBall.reset()
            self.leftpaddle.resetToBase()
            self.rightpaddle.resetToBase()                    
            lBall.serve_vertically()
            #if self._multiBall:
            #    lBall.serve()

        # Let the surprisemanager check for collisions, and enable surprises if needed
        self.surpriseManager.handleCollisions(lBall)

        # No collision, move normally        
        if not collisionHandled: 
            # move the ball according to its velocity
            lBall.setX (lBall.x + lBall.velx)
            lBall.setY (lBall.y + lBall.vely)

        # Apply gravity if needed
        if lBall.gravity_on_off:
            lBall.vely += lBall.gravity
            maxspeed = lBall.maxspeed /4.0
            if lBall.velx > maxspeed:
                lBall.velx = maxspeed
            if lBall.vely > maxspeed:
                lBall.vely = maxspeed
        else:
            # This is the normal modus, when gravity is disabled :)
            # Bring down velocity of ball slowly to minspeed if needed (in steps of autobreakstepsize)
            # This is to make sure that any acceleration is slowly brought down to the minspeed of the ball
            # (minspeed = normal moving speed)
            # Also, we're maximizing ballspeed to maxspeed
            if (lBall.velx != 0.0 or lBall.vely != 0.0):
                ballspeed = math.sqrt (pow(lBall.velx, 2) + pow(lBall.vely, 2))
                newspeed = max(ballspeed - lBall.autobreakstepsize, lBall.minspeed)
                newspeed = min(lBall.maxspeed, newspeed)
                factor = newspeed/ballspeed
                lBall.velx *= factor
                lBall.vely *= factor

        if lBall.x < 0 or lBall.x > gScreensize[0] or lBall.y < 0 or lBall.y > gScreensize[1] :
            if False:
                print(lBall.x, lBall.y, 'OUTSIDE!')
        
        if self.ball.outsideScreen():
            self.ball.reset()
            self.ball.serve_vertically()

    def setInvisibleBall(self, bool):
        """Used as surprise, :)"""
        if bool:
            self.sprites.remove(self.ball)
        else:
            self.sprites.add(self.ball)

    def getInvisibleBall(self):
        return self.sprites.has(self.ball)

    # If starting, balls 2 and 3 will be served randomly from center
    def setMultiBall(self, bool):
        if bool and not self._multiBall:
            self.ball2 = Ball((gScreensize[0]/2.0, gScreensize[1]/2.0), gScreensize[1]/32.0, gScreensize[1]/32.0, 'ball1.jpg')
            self.ball3 = Ball((gScreensize[0]/2.0, gScreensize[1]/2.0), gScreensize[1]/32.0, gScreensize[1]/32.0, 'ball1.jpg')
            self.sprites.add(self.ball2)
            self.sprites.add(self.ball3)
            self.ball2.serve()
            self.ball3.serve()
            
        if not bool and self._multiBall:
            self.sprites.remove(self.ball2)
            self.sprites.remove(self.ball3)
            self.ball2 = None
            self.ball3 = None
            
        self._multiBall = bool

    def getMultiBall(self):
        return self._multiBall

    def setMagnet(self, bool, activated_by):
        if bool:
            if activated_by == self.leftpaddle:
                self.ball.reset((gScreensize[0]/4, gScreensize[1]/2))
            else:
                self.ball.reset((gScreensize[0]/4*3, gScreensize[1]/2))
    
    def run_one_frame(self):
        # tick pygame clock
        # you can limit the fps by passing the desired frames per second to tick()
        if self.time_mode == "realtime":
            self.clock.tick(60)
        else:
            self.clock.tick(0)

        # handle pygame events -- if user closes game, stop running
        running = self.handleEvents()

        # handle balls -- all our ball management here
        self.manageBall(self.ball)
        if (self.ball2 != None):
            self.manageBall(self.ball2)
        if (self.ball3 != None):
            self.manageBall(self.ball3)
            
        # update our sprites
        for sprite in self.sprites:
            sprite.update()

        # render our sprites
        self.sprites.clear(self.window, self.background)    # clears the window where the sprites currently are, using the background
        self.sprites.draw(self.window)              # calculates the 'dirty' rectangles that need to be redrawn

        # blit the dirty areas of the screen
        if self.time_mode != "superfast_no_image":
            pygame.display.update()                        # updates just the 'dirty' areas
        self.frame += 1



    def run_unattended(self):
        """Runs the game. Contains the game loop that computes and renders
        each frame."""
 
        print('Starting Event Loop') 
        running = True
        # run until something tells us to stop
        while running:            
            self.run_one_frame()
            # update the title bar with our frames per second
            pygame.display.set_caption(f'Annoy Pong {game.clock.get_fps()} fps')
        
        self.exit()
        
    def exit(self):
        pygame.quit()
        print('Quitting. Thanks for playing')

    def handleEvents(self):
        """Poll for PyGame events and behave accordingly. Return false to stop
        the event loop and end the game."""
 
        # poll for pygame events
        for event in pygame.event.get():
            
            # ask SurpriseManager to handle events.
            if self.surpriseManager.handleEvent(event):
                a=1 #nothing

            elif event.type == QUIT:
                return False

            # handle user input
##            elif event.type == MOUSEMOTION:
##                relX, relY = event.rel
##                
##                # paddle control
##                if relY < 2:
##                    self.rightpaddle.up(True)
##                elif relY > 2:
##                    self.rightpaddle.down(True)
##                else:
##                    self.rightpaddle.down(False)
                
                

            elif event.type == KEYDOWN:
                # if the user presses escape, quit the event loop.
                if event.key == K_ESCAPE:
                    return False

                if event.key == K_BACKSPACE:
                    self.time_mode = next_time_mode(self.time_mode)

                # Disaster recovery with space key :)
                if event.key == K_SPACE:
                    #if self.ball.velx == 0 and self.ball.vely == 0:
                    #self.ball.reset()
                    #self.ball.serve()
                    if (not self.leftpaddle.isInScreen() or not self.rightpaddle.isInScreen()):
                        self.leftpaddle.resetToBase()
                        self.rightpaddle.resetToBase()                    
                    if self.ball.outsideScreen():
                        self.ball.reset()

                if event.key == K_RETURN:
                    self.full_reset_game()

                # paddle control
                if event.key == K_w:
                    #self.leftpaddle.up(True)
                    self.leftpaddle.queueUp(True)
                if event.key == K_s:
                    #self.leftpaddle.down(True)
                    self.leftpaddle.queueDown(True)

                if event.key == K_a:
                    #self.leftpaddle.left(True)
                    self.leftpaddle.queueLeft(True)
                if event.key == K_d:
                    #self.leftpaddle.right(True)
                    self.leftpaddle.queueRight(True)
 
                if event.key == K_UP:
                    #self.rightpaddle.up(True)
                    self.rightpaddle.queueUp(True)
                if event.key == K_DOWN:
                    #self.rightpaddle.down(True)
                    self.rightpaddle.queueDown(True)

                if event.key == K_LEFT:
                    #self.rightpaddle.left(True)
                    self.rightpaddle.queueLeft(True)
                if event.key == K_RIGHT:
                    #self.rightpaddle.right(True)
                    self.rightpaddle.queueRight(True)
 
            elif event.type == KEYUP:
                # paddle control
                if event.key == K_w:
                    #self.leftpaddle.down(False)
                    self.leftpaddle.queueUp(False)
                if event.key == K_s:
                    #self.leftpaddle.up(False)
                    self.leftpaddle.queueDown(False)
 
                if event.key == K_a:
                    #self.leftpaddle.right(False)
                    self.leftpaddle.queueLeft(False)
                if event.key == K_d:
                    #self.leftpaddle.left(False)
                    self.leftpaddle.queueRight(False)

                if event.key == K_UP:
                    #self.rightpaddle.down(False)
                    self.rightpaddle.queueUp(False)
                if event.key == K_DOWN:
                    #self.rightpaddle.up(False)
                    self.rightpaddle.queueDown(False)

                if event.key == K_LEFT:
                    #self.rightpaddle.right(False)
                    self.rightpaddle.queueLeft(False)
                if event.key == K_RIGHT:
                    #self.rightpaddle.left(False)
                    self.rightpaddle.queueRight(False)
 
        return True

    def full_reset_game(self):
        self.ball.reset()
        self.leftpaddle.resetToBase()
        self.leftpaddle.nr_of_ball_hits = 0
        self.rightpaddle.resetToBase()
        self.rightpaddle.nr_of_ball_hits = 0
        self.score.reset()
        self.frame = 0
        self.ball.serve_vertically()


class Surprise(pygame.sprite.Sprite):
    """A sprite representing a good or bad surprise"""

    def __init__(self, name, imagefilename):
        pygame.sprite.Sprite.__init__(self)

        self.name = name
        self.xy = (0,0) #for now
        self.good_bad = None # either 'good' or 'bad'
        self.imagefilename = imagefilename
        self._onScreen = False
        self._isActivated = False # is the surprise activated?
        #self.activeDuration = 8000 #ms
        self.activated_by = None # Paddle that activated this Surprise

    def setActive(self, bool, activated_by = None):
        self._isActivated = bool
        self.activated_by = activated_by

    def getActive(self):
        return self._isActivated

    def getActivatedBy(self):
        return self.activated_by
        
    def setOnscreen(self, bool):
        #filename = 'knob.png'
        tmpimage = pygame.image.load(os.path.join(f"{WORKING_PATH}/./images", self.imagefilename))
        self.image = pygame.transform.smoothscale(tmpimage, (int(gScreensize[0] / 30), int(gScreensize[0] / 30)))

       # self.image = pygame.Surface()
        #if self.good_bad == 'bad':
        #    self.image.fill((255, 0, 0))
        #else:
        #    self.image.fill((0, 255, 0))
            
        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()
        self._onScreen = bool
        if bool:
            self.rect.x = gScreensize[0]/2
            if not DEBUG_SURPRISES:
                self.rect.x += random.randint(-gScreensize[0]/5, gScreensize[0]/5)
            self.rect.y = random.randint(0, gScreensize[1])
            
    def getOnscreen(self):
        return self._onScreen

    def handleEvent(self, event):
        """Returns true if event was handled by this instance"""
        # does nothing by default
        return False
    
class GravityPosSurprise(Surprise):
    def __init__(self, name, imagefilename, ball):
        Surprise.__init__(self, name, imagefilename)
        self.ball = ball
        self.good_bad = 'bad' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if bool:
            self.ball.setGravity (True, 0.2)
        else:
            self.ball.setGravity (False, 0.0)

class GravityNegSurprise(Surprise):
    def __init__(self, name, imagefilename, ball):
        Surprise.__init__(self, name, imagefilename)
        self.ball = ball
        self.good_bad = 'bad' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if bool:
            self.ball.setGravity (True, -0.2)
        else:
            self.ball.setGravity (False, 0.0)

class JumboPaddleSurprise(Surprise):
    def __init__(self, name, imagefilename, ball):
        Surprise.__init__(self, name, imagefilename)
        self.ball = ball
        self.good_bad = 'good' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if activated_by != None:
            if bool:
                activated_by.surpriseHeight(2.0)
            else:
                activated_by.surpriseHeight(1.0)

class MiniPaddleSurprise(Surprise):
    def __init__(self, name, imagefilename, ball):
        Surprise.__init__(self, name, imagefilename)
        self.ball = ball
        self.good_bad = 'bad' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if activated_by != None:
            if bool:
                activated_by.surpriseHeight(0.5)
            else:
                activated_by.surpriseHeight(1.0)

class FlashingBallSurprise(Surprise):
    def __init__(self, name, imagefilename, game):
        Surprise.__init__(self, name, imagefilename)
        self.game = game
        self.good_bad = 'bad' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if bool:
            pygame.time.set_timer(pygame.USEREVENT+4, 200)
        else:
            pygame.time.set_timer(pygame.USEREVENT+4, 0) #disable the timer
            if not self.game.getInvisibleBall():
                self.game.setInvisibleBall(False)

    def handleEvent(self, event):
        """Returns true if event was handled by this instance"""
        if event.type == pygame.USEREVENT+4:
            if self.game.getInvisibleBall():
                self.game.setInvisibleBall(True)
            else:
                self.game.setInvisibleBall(False)
            return True
        return False


class MultiBallSurprise(Surprise):
    def __init__(self, name, imagefilename, game):
        Surprise.__init__(self, name, imagefilename)
        self.game = game
        self.good_bad = 'good' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        self.game.setMultiBall(bool)


class SuperspeedSurprise(Surprise):
    def __init__(self, name, imagefilename, ball):
        Surprise.__init__(self, name, imagefilename)
        self.ball = ball
        self.good_bad = 'good' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        self.ball.setSuperspeed(bool)


class FlashSurprise(Surprise):
    def __init__(self, name, imagefilename, game):
        Surprise.__init__(self, name, imagefilename)
        self.game = game
        self.good_bad = 'good' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if activated_by != None:
            if activated_by == self.game.leftpaddle:
                activated_by = self.game.rightpaddle
            else: 
                activated_by = self.game.leftpaddle
            activated_by.setGhostMode(bool)

class MagnetSurprise(Surprise):
    def __init__(self, name, imagefilename, game):
        Surprise.__init__(self, name, imagefilename)
        self.game = game
        self.good_bad = 'good' # either 'good' or 'bad'
        
    def setActive(self, bool, activated_by):
        Surprise.setActive(self, bool, activated_by)
        if activated_by != None:
            self.game.setMagnet(bool, activated_by)

class SurpriseManager():
    
    def __init__(self, game, visiblespritegroup):
        self.game = game
        self.visiblespritegroup = visiblespritegroup # spritegroup
        self.surprises = [
            MagnetSurprise('MagnetSurprise',  'magnet.png', game),
            FlashSurprise('FlashSurprise',  'flash2.png', game),
            SuperspeedSurprise('SuperspeedSurprise',  'fire.jpg', game.ball),
            MultiBallSurprise('multiBall', 'multifire.jpg', game),
            FlashingBallSurprise('flashingBall',  'knob.png', game),
            JumboPaddleSurprise('jumboPaddle',  'knob.png', game.ball),
            MiniPaddleSurprise('miniPaddle', 'knob.png', game.ball),
            GravityPosSurprise('gravityPos',  'knob.png', game.ball),
            GravityNegSurprise('gravityNeg',  'knob.png', game.ball),
           ]
        
        #self.onScreen(0, True)

        #timing stuff
        self.timeBetweenSurprises = 6000 #ms  MBI
        self.timeBetweenSurprises = 90000000 #ms  MBI
        self.showTimeSurprise = 16000 #ms
        self.activeTimeSurprise = 16000 #ms

    def prepareForNextRound(self):
        # Called by game when a new round starts. Removes the suprises, and waits for new one
        #self.allOfScreen()
        #self.allDeactivate()        
        #self.waitToShowNextSurprise()
        return

    def handleCollisions(self, ball):
        for surp in self.surprises:
            if surp.getOnscreen():
                if pygame.sprite.collide_rect(ball, surp):
                    self.onScreen(surp, False)
                    surp.setActive(True, ball.getLastHitBy())
                    if surp.good_bad == 'bad':
                        self.game.sound.play("badSurprise")
                    else:
                        self.game.sound.play("goodSurprise")
                    self.waitToDeactivateSurprise() 
        
    def disableAllTimers(self):
        pygame.time.set_timer(pygame.USEREVENT+1, 0) #disable the timer
        pygame.time.set_timer(pygame.USEREVENT+2, 0) #disable the timer
        pygame.time.set_timer(pygame.USEREVENT+3, 0) #disable the timer
        
    def waitToShowNextSurprise(self):
        self.disableAllTimers()
        pygame.time.set_timer(pygame.USEREVENT+1, self.timeBetweenSurprises)

    def waitToHideSurprise(self):
        self.disableAllTimers()
        pygame.time.set_timer(pygame.USEREVENT+2, self.showTimeSurprise)
        
    def waitToDeactivateSurprise(self):
        self.disableAllTimers()
        pygame.time.set_timer(pygame.USEREVENT+3, self.activeTimeSurprise)

    def showNextSurprise(self):
        self.allOfScreen()
        self.onScreenIndex(random.randrange(0, len(self.surprises)), True)
        self.waitToHideSurprise()

    def hideSurprise(self):
        self.allOfScreen()
        # Start wait for next surprise
        self.waitToShowNextSurprise()
        
    def handleEvent(self, event):
        """Returns true if event was handled by this instance"""
        if event.type == pygame.USEREVENT+1:
            self.showNextSurprise()
            return True
        elif event.type == pygame.USEREVENT+2:
            self.hideSurprise()
            return True     
        elif event.type == pygame.USEREVENT+3:
            self.allDeactivate()
            # Start wait for next surprise
            self.waitToShowNextSurprise()    
            return True
        else:
            """ Let the active surprises handle their events if needed """
            for surp in self.surprises:
                if surp.getActive():
                    if surp.handleEvent(event):
                        return True
        return False


    def allOfScreen(self):
        #make sure all surprises are not shown
        for surp in self.surprises:
            self.onScreen(surp, False)

    def onScreenIndex(self, index, bool):
        # show/unshow the nth surprise-sprite on the screen
        self.onScreen (self.surprises[index], bool)
        print(self.surprises[index].name)
        
    def onScreen(self, surprise, bool):
        # show/unshow the surprise-sprite on the screen
        surprise.setOnscreen(bool)
        if surprise.getOnscreen():
            self.visiblespritegroup.add(surprise)
        else:
            self.visiblespritegroup.remove(surprise)
            
    def allDeactivate(self):
        for surp in self.surprises:
            if surp.getActive():
                surp.setActive(False, surp.getActivatedBy())


class Score(pygame.sprite.Sprite):
    """A sprite for the score."""
 
    def __init__(self, xy, fontsize):
        pygame.sprite.Sprite.__init__(self)
 
        self.xy = xy    # save xy -- will center our rect on it when we change the score
 
        self.font = pygame.font.Font(None, int(fontsize))  # load the default font, size 50
 
        self.leftscore = 0
        self.rightscore = 0
        self.fontsize = fontsize

        self.width = 1.0
        self.height = 1.0
        self.reRender()
        
    def update(self):
        return
        #pass

        #self.width += 1
        #self.height += 1
        #self.image = pygame.transform.scale(self.image, (int(self.width), int(self.height)))
        #self.rect = self.image.get_rect()
        #self.rect.center = self.xy
        
    def left(self):
        """Adds a point to the left side score."""
        self.leftscore += 1
        self.reRender()
 
    def right(self):
        """Adds a point to the right side score."""
        self.rightscore += 1
        self.reRender()
 
    def reset(self):
        """Resets the scores to zero."""
        self.leftscore = 0
        self.rightscore = 0
        self.reRender()
 
    def reRender(self):
        """Updates the score. Renders a new image and re-centers at the initial coordinates."""
        self.image = self.font.render("%d     %d"%(self.leftscore, self.rightscore), True, (0,0,0))
        self.rect = self.image.get_rect()
        self.rect.center = self.xy
        self.width = self.rect.width
        self.height = self.rect.height

# NO_MORE_MUSIC must not collide with any pygame events.
NO_MORE_MUSIC = 234

class Sound():
    def __init__(self):
        if pygame.mixer.get_init() == None:
            self.enabled = False
        else:
            self.enabled = True
            pygame.mixer.music.set_endevent(NO_MORE_MUSIC)

        if self.enabled:
            self.effects = {
                "ballPadHit1":pygame.mixer.Sound(f"{WORKING_PATH}/sounds/ball.wav"),
                "applause1":pygame.mixer.Sound(f"{WORKING_PATH}/sounds/Applause.wav"),
                "demonlol":pygame.mixer.Sound(f"{WORKING_PATH}/sounds/demonlol.wav"),
                "badSurprise":pygame.mixer.Sound(f"{WORKING_PATH}/sounds/badSurprise.wav"),
                "goodSurprise":pygame.mixer.Sound(f"{WORKING_PATH}/sounds/goodSurprise.wav")
                }
            
    def processEvent(self, event):
        if event.type == NO_MORE_MUSIC:
            print("bla")
            self.loadAndPlayBackground()
            return None
        else:
            return event
        
    def play(self, effect):
        if self.enabled:
            self.effects[effect].play()
            
    def setBackgroundMusic(self, filenames):
        self.filenames = filenames
        
    def loadAndPlayBackground(self):
        for filename in self.filenames:
            if filename == self.filenames[0]:
                pygame.mixer.music.load(filename)
            else:
                pygame.mixer.music.queue(filename)

        pygame.mixer.music.set_volume(50)
        pygame.mixer.music.play(0) #-1 loop forever
            
            

class SweptAabbSprite(pygame.sprite.Sprite):
    def __init__(self, xy, width, height, velx, vely):
        pygame.sprite.Sprite.__init__(self)

        self.width = width
        self.height = height
        self.velx = velx;
        self.vely = vely;
        if not hasattr(self, 'image'):
            self.image = pygame.Surface((self.width, self.height))

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()
        self.rect.centerx, self.rect.centery = xy
        self.x, self.y = xy
        self.setBase(xy)

    def setX (self, x):
        self.x = x
        self.rect.centerx = x

    def setY (self, y):
        self.y = y
        self.rect.centery = y

    def resetToBase(self):
        """Reset to base position"""
        self.x = self.baseX;
        self.y = self.baseY;
    
    def setBase(self, xy):
        self.baseX, self.baseY = xy

    def getTop (self):
        return self.y - self.height / 2.0

    def getBottom (self):
        return self.y + self.height / 2.0

    def getLeft (self):
        return self.x - self.width / 2.0

    def getRight (self):
        return self.x + self.width / 2.0

class Wall(SweptAabbSprite):
    """A wall sprite. Subclasses the pygame sprite class."""
 
    def __init__(self, xy,  width, height):
        SweptAabbSprite.__init__(self, xy, width, height, 0, 0)
        self.image.fill((0, 0, 0))

        # set position
        self.setX (xy[0]+width/2.0)
        self.setY (xy[1]+height/2.0)
        #self.rect.topleft = xy


class Goal(SweptAabbSprite):
    def __init__(self, xy,  width, height, player):
        SweptAabbSprite.__init__(self, xy, width, height, 0, 0)
        # set position
        self.setX (xy[0]+width/2.0)
        self.setY (xy[1]+height/2.0)
        self.player = player
    
        
"""ball maybe moving in x and y dirs, paddle may only be moving in y direction"""
#1.0 = no collision
def MyVerticalCollision(b, p):
    collisionTime = 1.0 #will be between 0 and 1, 1.0 = no collision
    normalx, normaly, doReflect, doImpulse = 0.0, 0.0, False, False

        
    #evaluate case1: ball bottom hits on top of paddle
    by0 = b.getBottom() #time 0
    by1 = b.getBottom() + b.vely #time 1
    py0 = p.getTop()
    py1 = p.getTop() + p.vely

    if by0 <= py0:
        try:
            time = (py0-by0)/(by1-by0-py1+py0)
            if time >= 0.0 and time < 1.0:
                #also check if we collide horizontally
                bCollRightx = b.getRight() + time * b.velx
                bCollLeftx = b.getLeft() + time * b.velx
                pCollRightx = p.getRight() + time * p.velx
                pCollLeftx = p.getLeft() + time * p.velx
                if bCollRightx > pCollLeftx and bCollLeftx < pCollRightx:
                    normalx = 0.0
                    normaly = 1.0
                    collisionTime= time
        except ZeroDivisionError:
            collisionTime = 1.0 #no collision
            
    #evaluate case2: ball top hits on bottom of paddle
    by0 = b.getTop() #time 0
    by1 = b.getTop() + b.vely #time 1
    py0 = p.getBottom()
    py1 = p.getBottom() + p.vely

    if by0 >= py0:
        #MBI following block is copy of above, move to function 
        try:
            time = (py0-by0)/(by1-by0-py1+py0)
            if time >= 0.0 and time < 1.0:
                #also check if we collide horizontally
                bCollRightx = b.getRight() + time * b.velx
                bCollLeftx = b.getLeft() + time * b.velx
                pCollRightx = p.getRight() + time * p.velx
                pCollLeftx = p.getLeft() + time * p.velx
                if bCollRightx > pCollLeftx and bCollLeftx < pCollRightx:
                    normalx = 0.0
                    normaly = 1.0
                    collisionTime= time
        except ZeroDivisionError:
            collisionTime = 1.0 #no collision

    # set doReflect and doImpulse corrrectly
    if collisionTime != 1.0:
        if p.vely * b.vely <= 0.0:
            doReflect = True;
            doImpulse = True;
        elif abs(b.vely) > abs(p.vely):
            doReflect = True;
            doImpulse = False;
        elif abs(p.vely) > abs(b.vely):
            doReflect = False;
            doImpulse = True;
            
    return collisionTime, normalx, normaly, doReflect, doImpulse

#1.0 = no collision
def MyHorizontalCollision(b, p):
    collisionTime = 1.0 #will be between 0 and 1, 1.0 = no collision
    normalx, normaly, doReflect, doImpulse = 0.0, 0.0, False, False
        
    #evaluate case1: ball right hits on left of paddle
    by0 = b.getRight() #time 0
    by1 = b.getRight() + b.velx #time 1
    py0 = p.getLeft()
    py1 = p.getLeft() + p.velx

    if by0 <= py0:
        try:
            time = (py0-by0)/(by1-by0-py1+py0)
            if time >= 0.0 and time < 1.0:
                #also check if we collide vertically
                bCollBottomy = b.getBottom() + time * b.vely
                bCollTopy = b.getTop() + time * b.vely
                pCollBottomy = p.getBottom() + time * p.vely
                pCollTopy = p.getTop() + time * p.vely
                if bCollBottomy > pCollTopy and bCollTopy < pCollBottomy:
                    normalx = 1.0
                    normaly = 0.0
                    collisionTime= time
        except ZeroDivisionError:
            collisionTime = 1.0 #no collision
            
    #evaluate case2: ball left hits on right of paddle
    by0 = b.getLeft() #time 0
    by1 = b.getLeft() + b.velx #time 1
    py0 = p.getRight()
    py1 = p.getRight() + p.velx

    if by0 >= py0:
        #MBI following block is copy of above, move to function 
        try:
            time = (py0-by0)/(by1-by0-py1+py0)
            if time >= 0.0 and time < 1.0:
                #also check if we collide vertically
                bCollBottomy = b.getBottom() + time * b.vely
                bCollTopy = b.getTop() + time * b.vely
                pCollBottomy = p.getBottom() + time * p.vely
                pCollTopy = p.getTop() + time * p.vely
                if bCollBottomy > pCollTopy and bCollTopy < pCollBottomy:
                    normalx = 1.0
                    normaly = 0.0
                    collisionTime= time
        except ZeroDivisionError:
            collisionTime = 1.0 #no collision

    # set doReflect and doImpulse corrrectly
    if collisionTime != 1.0:
        if p.velx * b.velx <= 0.0:
            doReflect = True;
            doImpulse = True;
        elif abs(b.velx) > abs(p.velx):
            doReflect = True;
            doImpulse = False;
        elif abs(p.velx) > abs(b.velx):
            doReflect = False;
            doImpulse = True;
        # also apply some impulse if we're moving vertically
        if not doImpulse:
            if p.vely * b.vely < 0.0:
                doImpulse = True;
            elif abs(p.vely) > abs(b.vely):
                doImpulse = True;
                
    return collisionTime, normalx, normaly, doReflect, doImpulse


#THIS FUNCTION IS OLD, NOT USED ANYMORE
"""This collision assumes b2 is static. b1 can be moving.
   The return value is a number between 0 and 1 that indicates when the collision occurred.
    A value of 0 indicates the start of the movement and 1 indicates the end. If we get a value
    of 1, we can assume that there was no collision. A value of 0.5 means that the collision
    occurred halfway through the frame. This will also be used later to respond to the collision."""
def ColideSweptAABB(b1, b2):
    #From http://stackoverflow.com/questions/354883/how-do-you-return-multiple-values-in-python
    xInvEntry = 0.0
    yInvEntry = 0.0
    xInvExit= 0.0
    yInvExit = 0.0

    # find the distance between the objects on the near and far sides for both x and y
    if b1.velx > 0.0:
        xInvEntry = b2.rect.left - (b1.rect.left + b1.width);
        xInvExit = (b2.rect.left + b2.width) - b1.rect.left;
    else:
        xInvEntry = (b2.rect.left + b2.width) - b1.rect.left;
        xInvExit = b2.rect.left - (b1.rect.left + b1.width);

    if b1.vely > 0.0:
        yInvEntry = b2.rect.top - (b1.rect.top + b1.height);
        yInvExit = (b2.rect.top + b2.height) - b1.rect.top;
    else:
        yInvEntry = (b2.rect.top + b2.height) - b1.rect.top;
        yInvExit = b2.rect.top - (b1.rect.top + b1.height);

    # find time of collision and time of leaving for each axis (if statement is to prevent divide by zero)
    xEntry = 0.0
    yEntry = 0.0
    xExit = 0.0
    yExit = 0.0

    if b1.velx == 0.0:
        xEntry = -float("inf")
        xExit = float("inf")
    else:
        xEntry = xInvEntry / b1.velx;
        xExit = xInvExit / b1.velx;

    if b1.vely == 0.0:
        yEntry = -float("inf")
        yExit = float("inf")
    else:
        yEntry = yInvEntry / b1.vely;
        yExit = yInvExit / b1.vely;

    # find the earliest/latest times of collision
    entryTime = max(xEntry, yEntry)
    exitTime = min(xExit, yExit)

    # if there was no collision
    if entryTime > exitTime or xEntry < 0.0 and yEntry < 0.0 or xEntry > 1.0 or yEntry > 1.0:
        normalx = 0.0
        normaly = 0.0
        return (1.0, normalx, normaly)
    
    else: # if there was a collision
        # calculate normal of collided surface
        if xEntry > yEntry:
            if xInvEntry < 0.0:
                normalx = 1.0;
                normaly = 0.0;
            else:
                normalx = -1.0
                normaly = 0.0
        else:
            if yInvEntry < 0.0:
                normalx = 0.0
                normaly = 1.0
            else:
                normalx = 0.0
                normaly = -1.0

        #return the time of collision
        return (entryTime, normalx, normaly);

    
        
class Paddle(SweptAabbSprite):
    """A paddle sprite. Subclasses the pygame sprite class.
    Handles its own position so it will not go off the screen."""
 
    def __init__(self, xy,  width, height, maxHeight, filename, game:Game):
        self.filename = filename
        tmpimage = pygame.image.load(os.path.join(f"{WORKING_PATH}/images", filename))
        self.image = pygame.transform.smoothscale(tmpimage, (int(width), int(height)))

        SweptAabbSprite.__init__(self, xy, width, height, 0, 0)

        # the movement speed of our paddle (= pixels/frame)
        self.movementspeedX = PADDLE_MOVE_SPEED
        self.movementspeedY = PADDLE_MOVE_SPEED
 
        self.baseHeight = height

        self.walls = game.walls
        self.goals = game.goals
        self.middlelineRect = game.middlelineRect
        self.sound = game.sound
        self.ghostMode = False

        self.moveQueue = []

        self.nr_of_ball_hits = 0
        
        
    def surpriseHeight(self, factor):
        """Set/unset heigth factor for surpsises"""
        self.height = factor * self.baseHeight
        tmpimage = pygame.image.load(os.path.join(f"{WORKING_PATH}/images", self.filename))
        self.image = pygame.transform.smoothscale(tmpimage, (int(self.width), int(self.height)))
        self.rect = self.image.get_rect()

    def setGhostMode(self, bool):
        self.ghostMode = bool

        
    def isInScreen (self):
        return self.x >= 0 and self.x < gScreensize[0] and self.y >= 0 and self.y < gScreensize[1]
               
    

    def up(self, bool):
        """Increases the vertical velocity"""
        #self.vely -= self.movementspeedY
        if bool:
            self.vely = -self.movementspeedY
        else:
            self.vely = 0
 
    def down(self, bool):
        """Decreases the vertical velocity"""
        #self.vely += self.movementspeedY
        if bool:
            self.vely = self.movementspeedY
        else:
            self.vely = 0 
            
    def left(self, bool):
        """Increases the vertical velocity"""
        #self.velx -= self.movementspeedX
        if bool:
            self.velx = -self.movementspeedX
        else:
            self.velx = 0
 
    def right(self, bool):
        """Decreases the vertical velocity"""
        #self.velx += self.movementspeedX
        if bool:
            self.velx = self.movementspeedX
        else:
            self.velx = 0

    
    def determineDominantDirection(self):
        """ Based on the keys pressed, determine the resulting direction """
        verticalDir = None
        horizontalDir = None
        for direction in reversed(self.moveQueue):
            if direction == 'up' and verticalDir == None:
                verticalDir = 'up'
                self.vely = -self.movementspeedY
                
            elif direction == 'down' and verticalDir == None:
                verticalDir = 'down'
                self.vely = self.movementspeedY
                
            elif direction == 'left' and horizontalDir == None:
                horizontalDir = 'left'
                self.velx = -self.movementspeedX    
            elif direction == 'right' and horizontalDir == None:
                horizontalDir = 'right'
                self.velx = self.movementspeedX
        if verticalDir == None:
            self.vely = 0
        if horizontalDir == None:
            self.velx = 0

    def queueUp(self, bool):
        try:
            self.moveQueue.remove('up')
        except:
            pass
        if bool:
            self.moveQueue.append('up')
        self.determineDominantDirection()
        
    def queueDown(self, bool):
        try:
            self.moveQueue.remove('down')
        except:
            pass
        if bool:
            self.moveQueue.append('down')
        self.determineDominantDirection()
            
    def queueLeft(self, bool):
        try:
            self.moveQueue.remove('left')
        except:
            pass
        if bool:
            self.moveQueue.append('left')
        self.determineDominantDirection()
 
    def queueRight(self, bool):
        try:
            self.moveQueue.remove('right')
        except:
            pass
        if bool:
            self.moveQueue.append('right')
        self.determineDominantDirection()


    def _checkCollisions(self): 
        collision = False
        # My collision detection with walls
        for wall in self.walls:
            if not collision and pygame.sprite.collide_rect(wall, self):
                collision = True          
        # Check collision with middle line
        if not collision and self.middlelineRect.colliderect(self.rect):
            collision = True
        return collision
    
    def move(self, dx, dy):
        oldx = self.x
        oldy = self.y
        self.setX (self.x + dx)
        self.setY (self.y + dy)
                                   
        collision = self._checkCollisions()          
        if collision:
            # See if we can move in just x or y, will improve experience
            self.setX (oldx + dx)
            self.setY (oldy)
            collision = self._checkCollisions()          
            if not collision:
                return
            self.velx = 0 #MBI added
            self.setX (oldx)
            self.setY (oldy + dy)
            collision = self._checkCollisions()          
            if not collision:
                return
            self.vely = 0 #MBI added                
            # Jump back to last, not colliding, position. Assumes that walls are not moving! :)
            # Kind of poor-man collision handling
            self.setX (oldx)
            self.setY (oldy)
                                   
            
        else:                           
            # Collision with goals, just sprite based
            for goal in self.goals:
                if pygame.sprite.collide_rect(goal, self):
                    self.sound.play("demonlol")
                    
    def update(self):
        """Called to update the sprite. Do this every frame. Handles
        moving the sprite by its velocity"""
        self.move(self.velx, self.vely)


    

class Ball(SweptAabbSprite):
    """A ball sprite. Subclasses the pygame sprite class."""
 
    def __init__(self, xy, width, height, filename):
        tmpimage = pygame.image.load(os.path.join(f"{WORKING_PATH}/images", filename))
        self.image = pygame.transform.smoothscale(tmpimage, (int(width), int(height)))
        SweptAabbSprite.__init__(self, xy, width, height, 0, 0)

        #self.rect = self.image.get_rect()

        #self.startXY = self.rect.center
        
        self.minspeed = BALL_MIN_SPEED
        self.maxspeed = BALL_MAX_SPEED
        #speed will go from max to minspeed slowly with every frame. Determine the stepsize here 
        self.autobreakstepsize = (self.maxspeed - self.minspeed) / 240.0

        #surprises
        self.gravity_on_off = False

        # a variable that has the value of the player that last hit the ball in this run
        # if ball was not hit, = None
        self._lastHitBy = None
        self.superspeed = False

        
    def reset(self, xy = None):
        """Put the ball back in the middle and stop it from moving"""
        #self.rect.centerx, self.rect.centery = self.startXY
        #self.setX (self.startXY[0])
        #self.setY (self.startXY[1])
        if (xy == None):
            self.resetToBase()
        else:
            self.x, self.y = xy
            
        self.velx = 0
        self.vely = 0
        self._lastHitBy = None

        #temp
        #self.rect.centerx, self.rect.centery = gScreensize[0]-100, 300

    def setLastHitBy(self, paddle):
        self._lastHitBy = paddle
        paddle.nr_of_ball_hits += 1 

    def getLastHitBy(self):
        return self._lastHitBy;

    def outsideScreen(self):
        return self.x < -10 or self.x > gScreensize[0]+10 or self.y < -10 or self.y > gScreensize[1]+10 

    def serve_vertically(self):
        # Always launch upwards with random direction
        #angle = -90.0
        #angle  += 90.0 - random.random() * 180.0

        # Always launch upwards/left with random direction
        angle = -90.0
        angle += (2*random.random()-1.0) * 80.0 # not 90 to prevent ping-pong effect which gives organism free fitness...

#        if random.random() > .5:
            #angle = 90.0
        #else:
            #angle = -90.0
        # do the trig to get the x and y components
        x = math.cos(math.radians(angle))
        y = math.sin(math.radians(angle))
        self.velx = self.minspeed * x
        self.vely = self.minspeed * y
        
    def serve(self):
        #temp
        #self.rect.centerx, self.rect.centery = gScreensize[0]-50, 100
#        self.setX (gScreensize[0]-50)
 #       self.setY (100)
        
        angle = random.randint(-45, 45)    
 
        # if close to zero, adjust again
        if abs(angle) < 5 or abs(angle-180) < 5:
            angle = random.randint(10,20)
 
        # pick a side with a random call
        if random.random() > .5:
           angle += 180
 
        # do the trig to get the x and y components
        x = math.cos(math.radians(angle))
        y = math.sin(math.radians(angle))
        self.velx = self.minspeed * x
        self.vely = self.minspeed * y

    
    def setGravity(self, on_off_bool, gravity):
        """ Surprise function """
        self.gravity_on_off = on_off_bool
        self.gravity = gravity
        
    def setSuperspeed(self, on_off_bool):
        """ Surprise function """
        if self.superspeed != on_off_bool:
            self.superspeed = on_off_bool
            if self.superspeed:
                self.minspeed *= 3.5
                self.maxspeed *= 3.5
            else:   
                self.minspeed /= 3.5
                self.maxspeed /= 3.5
                


# create a game and run it
if __name__ == '__main__':

    game = Game(mode_play=True)
    game.run_unattended()

    # For Neural evolution
    # Controlling behavior
    # self.limit_fps = False

    # NN INPUTS, LET OP, ZORGEN DAT DEZE coords gelijk zijn zelfs als paddle links of rechts staat!
    # Als volgt: altijd een paddle inputs geven alsof hij links staat (zelfs al staat ie in echt rechts)
    # als rechts staat alles doen als SCREEN_SIZE_X-x en y gelijk laten
    #
    # - self paddle x  (always as if self is at left side of the game!)
    # - self paddle y  (always as if self is at left side of the game!)
    # - ball x         (always as if self is at left side of the game!)
    # - ball y         (always as if self is at left side of the game!) 
    # - ball speed x
    # - ball speed y
    # - opponent x     (always as if opponent is at right side of the game!)
    # - opponent y     (always as if opponent is at right side of the game!) 
    #
    # Later doen?
    # - surprise x
    # - surprise y
    #   en indicatie dat er een surprise actief is?... boolean ofzo?

    # NN OUTPUTS (ook weer op letten dat paddle links of rechts kan staan in een potje, dan links en rechts omdraaien?)
    # - up pressed    --> True? paddle.queueUp(True), otherwise paddle.queueUp(False)
    # - down pressed    --> True? paddle.queueDown(True), otherwise paddle.queueDown(False)
    # - left pressed etc
    # - right pressed etc


