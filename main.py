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

AGENT_POSITION_X = - (int(PADDLE_SIZE_X / 2))
BALL_POSITION_Y = 10

SCALE = 32

Config.set('graphics', 'resizable', True)
Config.set('graphics', 'width', str(FIELD_SIZE_X * SCALE))
Config.set('graphics', 'height', str(FIELD_SIZE_Y * SCALE))

from kivy.core.window import Window

class Action(Enum):
    UP = 0
    DOWN = 1
    IDLE = 2

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

        self.state = (0, (15, BALL_POSITION_Y))
        self.initialize_utilities()

        print('initialized utilities')
        print(len(self.utilities))

        print('starting value iteration')
        for i in range(20):
           self.value_iteration(0.8)
        print('value iteration done')

    def initialize_utilities(self):
        self.utilities = {}

        for P_A in range(FIELD_SIZE_Y + 1):
            for P_B_x in range(FIELD_SIZE_X + 1):
                self.utilities[(P_A, (P_B_x, BALL_POSITION_Y))] = 0.0

    def collides(self, P_A, P_B):
        P_B_x, P_B_y = P_B
        return ((abs(P_B_x - AGENT_POSITION_X) <= (BALL_SIZE_X / 2) + (PADDLE_SIZE_X / 2)) and  
                (abs(P_B_y - P_A) <= (BALL_SIZE_Y / 2) + (PADDLE_SIZE_Y / 2)))

    def get_next_state(self, s, a):
        if s == None:
            return None
        
        P_A, P_B = s
        P_B_x, P_B_y = P_B

        if P_B_x == 0 or self.collides(P_A, P_B):
            return None

        P_A_next = P_A
        if a == Action.DOWN:
            if P_A > 0:
                P_A_next =  P_A - 1
        elif a == Action.UP:
            if P_A < FIELD_SIZE_Y:
                P_A_next = P_A + 1

        P_B_x_next = P_B_x - 1

        next_state = (P_A_next, (P_B_x_next, P_B_y))
        return next_state

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

        if agent_action != None:
            self.state = self.get_next_state(self.state, agent_action)
            
            P_A, P_B = self.state
            ball_pos_x, ball_pos_y = P_B

            self.ball.pos = ((ball_pos_x - int(BALL_SIZE_X / 2)) * SCALE, (ball_pos_y - int(BALL_SIZE_Y / 2)) * SCALE)
            self.agent.pos = (AGENT_POSITION_X * SCALE, (P_A - int(PADDLE_SIZE_Y / 2)) * SCALE)

    def reward(self, s):
        P_A, P_B = s
        P_B_x, P_B_y = P_B

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
 
class PongApp(App):
    def build(self):
        game = PongGame()
        Clock.schedule_interval(game.update, 8 / 60.0)
        return game

if __name__ == '__main__':
    PongApp().run()