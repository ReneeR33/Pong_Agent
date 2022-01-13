from os import stat
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty
)
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.config import Config
from enum import Enum
import math

FIELD_SIZE_X = 15
FIELD_SIZE_Y = 11

BALL_SIZE_X = 1
BALL_SIZE_Y = 1

PADDLE_SIZE_X = 1
PADDLE_SIZE_Y = 4

AGENT_POSITION_X = 0
PLAYER_POSITION_X = FIELD_SIZE_X

SCALE = 32

Config.set('graphics', 'resizable', True)
Config.set('graphics', 'width', str((FIELD_SIZE_X + 1) * SCALE))
Config.set('graphics', 'height', str((FIELD_SIZE_Y + 1) * SCALE))

from kivy.core.window import Window

class Action(Enum):
    UP = 0
    DOWN = 1
    IDLE = 2

class BallDirection(Enum):
    L_U = 0
    L_D = 1
    R_U = 2
    R_D = 3

class Surface(Enum):
    VERTICAL = 0
    HORIZONTAL = 1

class PongPaddle(Widget):
    score = NumericProperty(0)

class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

class PongGame(Widget):
    ball = ObjectProperty(None)
    agent = ObjectProperty(None)
    player = ObjectProperty(None)

    print = False

    player_movement = Action.IDLE

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)

        self.ball.size = (BALL_SIZE_X * SCALE, BALL_SIZE_Y * SCALE)
        self.agent.size = (PADDLE_SIZE_X * SCALE, PADDLE_SIZE_Y * SCALE)
        self.player.size = (PADDLE_SIZE_X * SCALE, PADDLE_SIZE_Y * SCALE)

        self.state = (2, 2, (7, 9), BallDirection.R_D)
        self.initialize_utilities()

        print('initialized utilities')
        print(len(self.utilities))

        print('starting value iteration')
        for i in range(50):
            self.value_iteration(0.8)
        print('value iteration done')

    def initialize_utilities(self):
        self.utilities = {}

        for P_A in range(FIELD_SIZE_Y + 1):
            for P_P in range(FIELD_SIZE_Y + 1):
                for P_B_x in range(FIELD_SIZE_X + 1):
                    for P_B_y in range(FIELD_SIZE_Y + 1):
                        for D_B in range(4):
                            self.utilities[(P_A, P_P, (P_B_x, P_B_y), BallDirection(D_B))] = 0.0

    def collides(self, P_A, P_P, P_B):
        P_B_x, P_B_y = P_B
        return (((abs(P_B_x - AGENT_POSITION_X) <= (BALL_SIZE_X / 2) + (PADDLE_SIZE_X / 2)) and  
                 (abs(P_B_y - P_A) <= (BALL_SIZE_Y / 2) + (PADDLE_SIZE_Y / 2))) or
                ((abs(P_B_x - PLAYER_POSITION_X) <= (BALL_SIZE_X / 2) + (PADDLE_SIZE_X / 2)) and  
                 (abs(P_B_y - P_P) <= (BALL_SIZE_Y / 2) + (PADDLE_SIZE_Y / 2))))

    def get_next_state(self, s, a):
        if s == None:
            return None
        
        P_A, P_P, P_B, D_B = s
        P_B_x, P_B_y = P_B

        if P_B_x == 0 or P_B_x == FIELD_SIZE_X:
            return None

        P_A_next = P_A
        if a == Action.DOWN:
            if P_A > 0:
                P_A_next =  P_A - 1
        elif a == Action.UP:
            if P_A < FIELD_SIZE_Y:
                P_A_next = P_A + 1

        P_B_next, D_B_next = self.move_ball(P_A_next, P_P, P_B, D_B)

        next_state = (P_A_next, P_P, P_B_next, D_B_next)
        return next_state

    def move_ball(self, P_A, P_P, P_B, D_B):
        P_B_x, P_B_y = P_B

        P_B_x_next = P_B_x
        P_B_y_next = P_B_y
        D_B_next = D_B

        if self.collides(P_A, P_P, (P_B_x_next, P_B_y_next)):
            D_B_next = self.bounce_ball(D_B_next, Surface.VERTICAL)
            if self.print == True:
                print('collides paddle')
                print(D_B_next)

        if P_B_y_next == 0 or P_B_y_next == FIELD_SIZE_Y:
            D_B_next = self.bounce_ball(D_B_next, Surface.HORIZONTAL)
            if self.print == True:
                print('collides top or bottom')
                print(D_B_next)

        if D_B_next == BallDirection.L_D:
            P_B_y_next = P_B_y - 1
            P_B_x_next = P_B_x - 1
        elif D_B_next == BallDirection.L_U:
            P_B_y_next = P_B_y + 1
            P_B_x_next = P_B_x - 1
        elif D_B_next == BallDirection.R_D:
            P_B_y_next = P_B_y - 1
            P_B_x_next = P_B_x + 1
        else:
            P_B_y_next = P_B_y + 1
            P_B_x_next = P_B_x + 1

        if P_B_x_next < 0 or P_B_x_next > FIELD_SIZE_X or P_B_y_next < 0 or P_B_y_next > FIELD_SIZE_Y:
            P_B_x_next = P_B_x
            P_B_y_next = P_B_y

        return ((P_B_x_next, P_B_y_next), D_B_next)

    def get_next_action(self, s):
        best_action = None
        best_utility = None

        for a in range(3):
            next_state = self.get_next_state(s, Action(a))
            if next_state != None:
                utility = self.utilities[next_state]
                if best_action == None or utility > best_utility:
                    best_action = Action(a)
                    best_utility = utility

        return best_action

    def update(self, dt):
        agent_action = self.get_next_action(self.state)
        # agent_action = Action.IDLE

        if agent_action != None:
            self.print = True
            self.state = self.get_next_state(self.state, agent_action)
            if self.state != None:
                P_A, P_P, P_B, _ = self.state
                ball_pos_x, ball_pos_y = P_B

                self.ball.pos = ((ball_pos_x - int(BALL_SIZE_X / 2)) * SCALE, (ball_pos_y - int(BALL_SIZE_Y / 2)) * SCALE)
                self.agent.pos = (AGENT_POSITION_X * SCALE, (P_A - int(PADDLE_SIZE_Y / 2)) * SCALE)
                self.player.pos = (PLAYER_POSITION_X * SCALE, (P_P - int(PADDLE_SIZE_Y / 2)) * SCALE)

            self.print = False
        
        print(self.state)

    def reward(self, s):
        _, _, P_B, _ = s
        P_B_x, _ = P_B

        if P_B_x == 0:
            return -1

        return 0

    def value_iteration(self, g):
        for s in self.utilities:
            utilities = []
            for a in range(3):
                utility = 0.0
                next_state = self.get_next_state(s, Action(a))

                if next_state == None:
                    utilities.append(self.reward(s))
                else:
                    utility = self.reward(next_state) + g * self.utilities[next_state]
                    utilities.append(utility)

            self.utilities[s] = max(utilities)

    def bounce_ball(self, D_B, surface):
        D_B_next = D_B

        if surface == Surface.VERTICAL:
            if D_B == BallDirection.L_D:
                return BallDirection.R_D
            elif D_B == BallDirection.R_D:
                return BallDirection.L_D
            elif D_B == BallDirection.L_U:
                return BallDirection.R_U
            else:
                return BallDirection.L_U 
        elif surface == Surface.HORIZONTAL:
            if D_B == BallDirection.L_D:
                return BallDirection.L_U
            elif D_B == BallDirection.L_U:
                return BallDirection.L_D
            elif D_B == BallDirection.R_D:
                return BallDirection.R_U
            else:
                return BallDirection.R_D

        return D_B_next
 
class PongApp(App):
    def build(self):
        game = PongGame()
        Clock.schedule_interval(game.update, 8 / 60.0)
        return game

if __name__ == '__main__':
    PongApp().run()