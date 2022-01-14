from ctypes.wintypes import SC_HANDLE
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
import random

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

    player_movement = Action.IDLE

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)

        self.ball.size = (BALL_SIZE_X * SCALE, BALL_SIZE_Y * SCALE)
        self.agent.size = (PADDLE_SIZE_X * SCALE, PADDLE_SIZE_Y * SCALE)
        self.player.size = (PADDLE_SIZE_X * SCALE, PADDLE_SIZE_Y * SCALE)

        self.initialize_states()
        self.initialize_policy()
        self.initialize_state()

        self.policy_iteration(0.8)

    def initialize_states(self):
        self.states = []

        for P_A in range(FIELD_SIZE_Y + 1):
            for P_P in range(FIELD_SIZE_Y + 1):
                for P_B_x in range(FIELD_SIZE_X + 1):
                    for P_B_y in range(FIELD_SIZE_Y + 1):
                        for D_B in range(4):
                            self.states.append((P_A, P_P, (P_B_x, P_B_y), BallDirection(D_B)))

    def initialize_policy(self):
        self.policy = {}

        for s in self.states:
            self.policy[s] = Action.IDLE

    def initialize_state(self):
        P_A = random.randint(0, FIELD_SIZE_Y)
        P_P = random.randint(0, FIELD_SIZE_Y)
        P_B_x = random.randint(4, FIELD_SIZE_X - 4)
        P_B_y = random.randint(0, FIELD_SIZE_Y)
        D_B = BallDirection(random.randint(0, 3))

        self.state = (P_A, P_P, (P_B_x, P_B_y), D_B)

    def collides(self, P_A, P_P, P_B):
        P_B_x, P_B_y = P_B
        return (((abs(P_B_x - AGENT_POSITION_X) <= (BALL_SIZE_X / 2) + (PADDLE_SIZE_X / 2)) and  
                 (abs(P_B_y - P_A) <= (BALL_SIZE_Y / 2) + (PADDLE_SIZE_Y / 2))) or
                ((abs(P_B_x - PLAYER_POSITION_X) <= (BALL_SIZE_X / 2) + (PADDLE_SIZE_X / 2)) and  
                 (abs(P_B_y - P_P) <= (BALL_SIZE_Y / 2) + (PADDLE_SIZE_Y / 2))))

    def get_next_state(self, s, a_a, a_p):
        if s == None:
            return None
        
        P_A, P_P, P_B, D_B = s
        P_B_x, P_B_y = P_B

        if P_B_x == 0 or P_B_x == FIELD_SIZE_X:
            return None

        P_A_next = self.move_paddle(P_A, a_a)
        P_P_next = self.move_paddle(P_P, a_p)
        P_B_next, D_B_next = self.move_ball(P_A_next, P_P, P_B, D_B)

        next_state = (P_A_next, P_P_next, P_B_next, D_B_next)
        return next_state

    def get_next_states(self, s, a_a):
        next_states = []

        for a in range(3):
            next_state = self.get_next_state(s, a_a, Action(a))
            if next_state == None:
                return []
            next_states.append((1 / 3, next_state))

        return next_states

    def move_paddle(self, P, a):
        P_next = P
        if a == Action.DOWN:
            if P > 0:
                P_next =  P - 1
        elif a == Action.UP:
            if P < FIELD_SIZE_Y:
                P_next = P + 1
        
        return P_next

    def move_ball(self, P_A, P_P, P_B, D_B):
        P_B_x, P_B_y = P_B

        P_B_x_next = P_B_x
        P_B_y_next = P_B_y
        D_B_next = D_B

        if self.collides(P_A, P_P, (P_B_x_next, P_B_y_next)):
            D_B_next = self.bounce_ball(D_B_next, Surface.VERTICAL)

        if P_B_y_next == 0 or P_B_y_next == FIELD_SIZE_Y:
            D_B_next = self.bounce_ball(D_B_next, Surface.HORIZONTAL)

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

    def update(self, dt):
        if self.state != None:
            P_A, P_P, P_B, _ = self.state
            P_B_x, P_B_y = P_B

            self.ball.pos = ((P_B_x - int(BALL_SIZE_X / 2)) * SCALE, (P_B_y - int(BALL_SIZE_Y / 2)) * SCALE)
            self.agent.pos = (AGENT_POSITION_X * SCALE, (P_A - int(PADDLE_SIZE_Y / 2)) * SCALE)
            self.player.pos = (PLAYER_POSITION_X * SCALE, (P_P - int(PADDLE_SIZE_Y / 2)) * SCALE)

            agent_action = self.policy[self.state]
            n = random.randint(0, 2)
            player_action = Action(n)

            self.state = self.get_next_state(self.state, agent_action, player_action)
        else:
            self.initialize_state()
        
        print(self.state)

    def reward(self, s):
        _, _, P_B, _ = s
        P_B_x, _ = P_B

        if P_B_x == 0:
            return -1

        return 0

    def q_value(self, s, a, U, g):
        next_states = self.get_next_states(s, a)

        if len(next_states) == 0:
            return self.reward(s)
        
        result = 0.0
        for p, next_state in next_states:
            result = result + p * (self.reward(next_state) + g * U[next_state])
        return result

    def update_utilities(self, U, g):
        for s in self.states:
            utilities = []
            for a in range(3):
                utilities.append(self.q_value(s, Action(a), U, g))

            U[s] = max(utilities)

    def policy_iteration(self, g):
        changed = True
        iteration = 0

        utilities = {}
        for s in self.states:
            utilities[s] = 0.0

        while changed:
            changed_count = 0
            iteration = iteration + 1
            changed = False

            self.update_utilities(utilities, g)

            for s in self.states:
                best_q_value = 0.0
                best_action = None

                for a in range(3):
                    q_value = self.q_value(s, Action(a), utilities, g)
                    if best_action == None or q_value >= best_q_value:
                        best_q_value = q_value
                        best_action = Action(a)
                
                if best_q_value > self.q_value(s, self.policy[s], utilities, g):
                    self.policy[s] = best_action
                    changed = True
                    changed_count = changed_count + 1

            print('{}: changed: {}'.format(iteration, changed_count))

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