from pacmanGame import *

import sys
import random
sys.path.insert(0, ".\\aima-python-master")
from utils import *

from collections import namedtuple

infinity = float('inf')
GameState = namedtuple('GameState', 'to_move, utility, pos')


class PacmanAdversarialGameProblem:

    def __init__(self, game):
        self.game = game
        self.maxDist = game.MAZE_WIDTH+game.MAZE_HEIGHT

    def actions(self, state):
        (x, y) = state.pos
        moves = []
        game=self.game
        if not game.isWall(x - 1, y):
            moves.append((x - 1, y))
        if not game.isWall(x + 1, y):
            moves.append((x + 1, y))
        if not game.isWall(x, y - 1):
            moves.append((x, y - 1))
        if not game.isWall(x, y + 1):
            moves.append((x, y + 1))
        return moves

    def result(self, state, move):
        return GameState(to_move=state.to_move,
                         utility=self.compute_utility(state.to_move),
                         pos=move)

    def utility(self, state):
        if state.to_move == "Pacman":
            return 1
        else:
            return -1

    def terminal_test(self, state,step):
        if state.to_move == "Pacman":
            return step == self.game.ghostPos[0]
        else:
            return step == self.game.pacmanPos[0]

    def compute_utility(self, to_move):
        if to_move == "Pacman":
            return 1
        else:
            return -1

    def evalForPacman(self, state, invulSeconds, pacMemory):

        totalScore = 0.0

        capsulePriority = 6
        foodPriority = 9

        #print("Max dist: ", self.maxDist)

        if invulSeconds == 0: #if Pac-Man is not invincible to the ghost, take precautionary measures
            d = self.manhattanDistance(state.pos, self.game.ghostPos[0])
            capsulePriority = 8 #prioritize becoming invincible
            if d <= 2: #if Pac-Man is literally right next to the ghost, RUN
                print("In distance ", d)
                totalScore -= 250
                capsulePriority = 10


        if len(self.game.capsulePos) > 0:
            d = self.minmanhattanDistance(self.game.capsulePos, state.pos)
            #print("Capsule d: ", self.maxDist - d)
            totalScore += (self.maxDist - d) * capsulePriority
            totalScore += len(self.game.capsulePos) * 3
        if len(self.game.foodPos) > 0:
            d = self.minmanhattanDistance(self.game.foodPos, state.pos)
            #print("Food d: ", self.maxDist - d)
            totalScore += (self.maxDist - d) * foodPriority
            totalScore += len(self.game.foodPos) * 6

        prevVisited = pacMemory.count(state.pos)
        totalScore -= prevVisited * 20

        #print(totalScore)
        return totalScore

    def manhattanDistance(self, xy1, xy2):
        return abs(xy1[0] - xy2[0]) + abs(xy1[1] - xy2[1])

    def minmanhattanDistance(self, listPos, state):
        (x1, y1) = state
        distances = [(abs(x1 - x2) + abs(y1 - y2)) for (x2, y2) in listPos]
        return min(distances)


class PacmanAdvGameAgent:
    def __init__(self,problem):
        self.problem = problem
        self.game = problem.game
        self.state = ()

    def get_action(self, invulSeconds, pacMemory):
        self.state = GameState(to_move = "Pacman",
                               utility = self.problem.compute_utility("Pacman"),
                               pos = self.problem.game.pacmanPos[0])
        step = alphabeta_search(self.state, self.problem, invulSeconds, pacMemory, d = 2, cutoff_test = None, eval_fn = self.problem.evalForPacman)
        prev = self.problem.game.pacmanPos[0]
        action = getDirection(prev, step)
        if self.problem.terminal_test(self.state, step):
            collision = True
        else:
            collision = False
        return (collision, action, step)


class GhostGameAgent:
    def __init__(self, problem,index=0):
        self.problem = problem
        self.state = GameState(to_move="Ghost",
                               utility=self.problem.compute_utility("Ghost"),
                               pos=self.problem.game.ghostPos[0])
        self.index=index

    def get_action(self, invulSeconds):
       # step = alphabeta_search(self.state, self.problem, d=2, cutoff_test=None, eval_fn=None)
        game=self.problem.game

        step = ghostMoving(self.actions(game.ghostPos[self.index]), game, invulSeconds)
        prev = game.ghostPos[self.index]
        action = getDirection(prev, step)
        if (self.problem.terminal_test(self.state, step)):
            collision = True
        else:
            collision = False
        return (collision, action, step)
        # else:
        #     raise NotImplementedError

    def actions(self, pos):
        (x, y) = pos
        moves = []
        game=self.problem.game
        if not game.isWall(x - 1, y):
            moves.append((x - 1, y))
        if not game.isWall(x + 1, y):
            moves.append((x + 1, y))
        if not game.isWall(x, y - 1):
            moves.append((x, y - 1))
        if not game.isWall(x, y + 1):
            moves.append((x, y + 1))
        return moves

def minmanhattanDistance(listPos, state):
    (x1, y1) = state
    distances=[(abs(x1 - x2) + abs(y1 - y2))
                for (x2, y2) in listPos]
    return min(distances)



def ghostMoving(moves, game, invulSeconds):
    i=random.randint(0,9)
    if i<3: #make movement random on occasion, so the ghost can break stalemates
        return random.choice(moves)
    else:
        ds = [manhattanDistance(pos, game.pacmanPos[0]) for pos in moves]
        if invulSeconds == 0: #if Pac-Man is not invincible, head directly for him
            return moves[ds.index(min(ds))]
        else: #if Pac-Man has eaten a power pellet, choose a path that will get the ghost further away
            return moves[ds.index(max(ds))]

def alphabeta_search(state, problem, invulSeconds, pacMemory, d=4, cutoff_test=None, eval_fn=None):
    """Search problem to determine best action; use alpha-beta pruning.
    This version cuts off search and uses an evaluation function."""

    player = state.to_move

    # Functions used by alphabeta
    def max_value(state, alpha, beta, depth):
        if cutoff_test(state, depth):
            return eval_fn(state, invulSeconds, pacMemory)
        v = -infinity
        for a in problem.actions(state):
            v = max(v, min_value(problem.result(state, a),
                                 alpha, beta, depth + 1))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def min_value(state, alpha, beta, depth):
        if cutoff_test(state, depth):
            return eval_fn(state, invulSeconds, pacMemory)
        v = infinity
        for a in problem.actions(state):
            v = min(v, max_value(problem.result(state, a),
                                 alpha, beta, depth + 1))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v

    # Body of alphabeta_search starts here:
    # The default test cuts off at depth d or at a terminal state
    cutoff_test = (cutoff_test or
                   (lambda state, depth: depth > d))
    #or problem.terminal_test(state
    eval_fn = eval_fn or (lambda state: problem.utility(state, player))
    best_score = -infinity
    beta = infinity
    best_action = None
    choices = []  # if more than one best, add it here
    for a in problem.actions(state):
        v = min_value(problem.result(state, a), best_score, beta, 1)
        choices.append((a, v))

    best_value = max(choices, key=lambda item: item[1])
    bests = [p for p in choices if best_value[1] == p[1]]
    # list = [a for a in bests if a[1] == v]
    if bests:
        (best_action, best_score) = random.choice(bests)
    return best_action

def minimax_decision(state, problem):
    """Given a state in a problem, calculate the best move by searching
    forward all the way to the terminal states. [Figure 5.3]"""

    player = problem.to_move(state)

    def max_value(state):
        if problem.terminal_test(state):
            return problem.utility(state, player)
        v = -infinity
        for a in problem.actions(state):
            v = max(v, min_value(problem.result(state, a)))
        return v

    def min_value(state):
        if problem.terminal_test(state):
            return problem.utility(state, player)
        v = infinity
        for a in problem.actions(state):
            v = min(v, max_value(problem.result(state, a)))
        return v

    # Body of minimax_decision:
    return argmax(problem.actions(state),
                  key=lambda a: min_value(problem.result(state, a)))
