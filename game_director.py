from AnnoyPong import AnnoyPong_copy
from AnnoyPong.AnnoyPong_copy import Game, Paddle, SCREEN_SIZE_X, SCREEN_SIZE_Y
import pygame
from organism_and_ecosystem import Organism, Ecosystem
import numpy as np
from statistics import mean

#POPULATION_SIZE = 5
#HOLDOUT_MATING = 0.5
#HIDDEN_LAYER_SIZE = 16
#FRAMES_PER_GAME = 2000

HIDDEN_LAYER_SIZE = 64
#HOLDOUT_MATING = 0.2
#HOLDOUT_ORGANISMS = 0.2
#POPULATION_SIZE = 50
#FRAMES_PER_GAME = 900 # ~15 seconds (60 secs per frame)

HOLDOUT_MATING = 0.4
HOLDOUT_ORGANISMS = 0.4
POPULATION_SIZE = 15
FRAMES_PER_GAME = 2700 # ~45 seconds (60 secs per frame)

#FIT_SCORE_ON_GOAL = 5 #10 als het beter gaat :D
FIT_SCORE_ON_GOAL = 20
FIT_SCORE_ON_BALL_HIT = .5

ORGANISM_WRITE_FOLDER = "organisms10x64x4/"
ORGANISMS_TO_PRELOAD_ON_START = [
    "organisms10x64x4/fit190.5_132.5_019_d507f3f5f4b848ed82ee8a2fc2b8899d_sz64.bin"
#    "organisms10x32x4/fit218.0_178.0_006_1ceab678927b4206bdffda89fdd1714f_sz32.bin",
#    "organisms10x32x4/fit218.0_178.0_006_1ceab678927b4206bdffda89fdd1714f_sz32.bin",

    #"organisms10x32x4/fit134.0_153.0_003_6d465ec0e4d14ff29f7f5bb4201d4122_sz32.bin",
    #"organisms10x32x4/fit653.5_a0dbaff0a657440a937ceff14c9291f3_sz32.bin",
    #"organisms10x32x4/fit341.0_541cf16a553a46c39d74c4ad7a0da1f4_sz32.bin",
#    "organisms8x32x4/fit097_c11fdbcd52da47dc8fd1cac7206a336e_sz32.bin", 
#    "organisms10x32x4/fit279.0_459511989c7a4b4c8b4552dfcc1f6689_sz32.bin",
    #"organisms10x32x4/fit215.5_b2b9f572af1b41659f940a20da4baa0f_sz32.bin",
#    "organisms10x32x4/fit299.5_9d69829464a24351b09a1b0b2b3ec86b_sz32.bin",
#    "organisms8x32x4/fit283_a42cffc02ae44516902d148a97baa19e_sz32.bin",
#    "organisms8x32x4/fit321_e1a37ceb2a98468daaa91605d4972edc_sz32.bin",
    #"organisms8x32x4/fit298_c11fdbcd52da47dc8fd1cac7206a336e_sz32.bin",
#    "organisms8x32x4/fit278_9b3d5f872745491c98f582155cf68171_sz32.bin",
    #"organisms8x32x4/fit288.0_1ceab678927b4206bdffda89fdd1714f_sz32.bin",
]
# Combi of Organism and Paddle :D
class AiPaddle(Paddle, Organism):
    def __init__(self, xy,  width, height, maxHeight, filename, game:Game):
        Paddle.__init__(self, xy,  width, height, maxHeight, filename, game)
        #Organism.__init__(self, [8, 16, 16, 16, 4], output='linear')
#        Organism.__init__(self, [8, HIDDEN_LAYER_SIZE, HIDDEN_LAYER_SIZE, HIDDEN_LAYER_SIZE, 4], output='sigmoid')
        Organism.__init__(self, [10, HIDDEN_LAYER_SIZE, HIDDEN_LAYER_SIZE, HIDDEN_LAYER_SIZE, 1], output='sigmoid')

class ConnectorAiPaddleToGame():
    # Role of this class;
    # give AiPaddle input based on Game state
    # let the Organism think
    # get AiPaddle output and propagate into Game
    # takes care of AiPaddle playing left or right. left always gets regular x input, right always get corrected x coords as if it is playing left as well
    def __init__(self, ai_paddle:AiPaddle, is_left_player:bool, game:Game, opponent:AiPaddle):
        self.ai_paddle = ai_paddle
        self.is_left_player = is_left_player
        self.game = game
        self.opponent = opponent
        if self.is_left_player:
            self.goal_coords = (self.game.goal2Right.x, self.game.goal2Right.y)
        else:
            self.goal_coords = (self.game.goal1Left.x, self.game.goal1Left.y)            

    def mirror_x(self,x): 
        return x if self.is_left_player else SCREEN_SIZE_X -x
    def do_one_think_step(self):
        def normalize_x(x):
            return x / float(SCREEN_SIZE_X)
        def normalize_y(y):
            return y / float(SCREEN_SIZE_Y)
        
        # Create an array with the inputs, first normalize them into -1 to1 
        neural_input = np.asarray([[
            normalize_x(self.mirror_x(self.ai_paddle.x)), 
            normalize_y(self.ai_paddle.y), 
            normalize_x(self.mirror_x(self.game.ball.x)),
            normalize_y(self.game.ball.y),
            self.game.ball.velx / self.game.ball.maxspeed,
            self.game.ball.vely / self.game.ball.maxspeed,
            normalize_x(self.mirror_x(self.goal_coords[0])),
            normalize_y(self.goal_coords[1]),
            normalize_x(self.mirror_x(self.opponent.x)),   #MBI is dit goed??
            normalize_y(self.opponent.y),
        ]])
        # Get the neural think output!!
        # and convert to list of 4 floats
        result_4 = self.ai_paddle.think(neural_input).tolist()[0]
        if False:
            # Ramp those sigmoid numbers > 0.5 will be True, else False
            #MBI niet zo'n succes
            ramp_half = [True  if x > 0.5 else False for x in result_4]
            # And map them to key up, right, down , left haahahahah!
            self.ai_paddle.queueUp(ramp_half[0])
            self.ai_paddle.queueRight(ramp_half[1] if self.is_left_player else ramp_half[3])
            self.ai_paddle.queueDown(ramp_half[2])
            self.ai_paddle.queueLeft(ramp_half[3] if self.is_left_player else ramp_half[2])
        the_num = result_4[0]
        assert the_num >= 0.0
        if the_num < 0.25:
            self.ai_paddle.queueUp(True)
        else:
            self.ai_paddle.queueUp(False)
            if the_num < 0.50:
                self.ai_paddle.queueRight(True) if self.is_left_player else self.ai_paddle.queueLeft(True) 
            else:
                self.ai_paddle.queueRight(False) if self.is_left_player else self.ai_paddle.queueLeft(False)
                if the_num < 0.75:
                    self.ai_paddle.queueDown(True)
                else:
                    self.ai_paddle.queueDown(False)
                    if the_num < 1.00: #should always be the case
                        self.ai_paddle.queueLeft(True) if self.is_left_player else self.ai_paddle.queueRight(True)
                    else:
                        self.ai_paddle.queueLeft(False) if self.is_left_player else self.ai_paddle.queueRight(False)

from datetime import datetime

class GameDirector():
    """ Glues the evolution to the existing AnnoyPong game"""

    def __init__(self,):
        self.game = AnnoyPong_copy.Game(time_mode = "realtime")
        self.frames_per_game = FRAMES_PER_GAME
        self.ecosytem = None
        self.caption_last_update_time = datetime.now()


    def _update_window_caption(self, game_nr, total_games, left_connector):
        # update the title bar with our frames per second etc. (not too much, cause windows does not like that many updates....)
        cur_time = datetime.now()
        if (cur_time - self.caption_last_update_time).microseconds > 100000:
            pygame.display.set_caption(
                f"Annoy Pong fps:{int(self.game.clock.get_fps()):4d}  frame:{self.game.frame:4d}/{self.frames_per_game}  " \
                f"game:{game_nr:2d}/{total_games:2d}  generation:{self.ecosystem.generation_nr}  bests last 20 gens: {[int(f) for f in ecosystem.best_organism_fitnesses[-20:]]} " \
                f"{left_connector.ai_paddle.get_description(False)}"
            )  
            self.caption_last_update_time = cur_time

    def _run_game_for_VS_version(self, ai_paddle_left: AiPaddle, ai_paddle_right: AiPaddle, game_nr, total_games):
        self.game.add_or_replace_paddles(ai_paddle_left, ai_paddle_right)                    
        self.game.full_reset_game()
        left_connector = ConnectorAiPaddleToGame(ai_paddle_left, True, self.game, ai_paddle_right)
        right_connector = ConnectorAiPaddleToGame(ai_paddle_right, False, self.game, ai_paddle_left)
        # run until something tells us to stop
        while self.game.frame < self.frames_per_game:            
            self.game.run_one_frame()
            # Let the connectors run the think step of the organisms!!
            left_connector.do_one_think_step()
            right_connector.do_one_think_step()
            self._update_window_caption(game_nr, total_games, left_connector)

        left_fit = self.game.score.leftscore * FIT_SCORE_ON_GOAL + ai_paddle_left.nr_of_ball_hits *FIT_SCORE_ON_BALL_HIT
        right_fit = self.game.score.rightscore * FIT_SCORE_ON_GOAL + ai_paddle_right.nr_of_ball_hits*FIT_SCORE_ON_BALL_HIT
        print ("left_fit", left_fit)
        print ("right_fit", right_fit)
        
        return (left_fit, right_fit)


    def _run_game_for_SINGLE_version(self, ai_paddle_left: AiPaddle, game_nr, total_games):
        self.game.add_or_replace_left_paddle(ai_paddle_left)
        self.game.full_reset_game()
        left_connector = ConnectorAiPaddleToGame(ai_paddle_left, True, self.game, self.game.rightpaddle)
        
        # run until something tells us to stop
        while self.game.frame < self.frames_per_game:            
            self.game.run_one_frame()
            # Let the connectors run the think step of the organisms!!
            left_connector.do_one_think_step()
            #right_connector.do_one_think_step()
            self._update_window_caption(game_nr, total_games, left_connector)

        left_fit = (self.game.score.leftscore - self.game.score.rightscore) * FIT_SCORE_ON_GOAL + ai_paddle_left.nr_of_ball_hits *FIT_SCORE_ON_BALL_HIT
        #right_fit = self.game.score.rightscore * FIT_SCORE_ON_GOAL + ai_paddle_right.nr_of_ball_hits*FIT_SCORE_ON_BALL_HIT
        print ("left_fit", left_fit)
        #print ("right_fit", right_fit)
        
        return left_fit
      

    def _run_game_for_AGAINST_BEST_version(self, ai_paddle_left: AiPaddle, ai_paddle_right: AiPaddle, game_nr, total_games):
        self.game.add_or_replace_paddles(ai_paddle_left, ai_paddle_right)                    
        self.game.full_reset_game()
        left_connector = ConnectorAiPaddleToGame(ai_paddle_left, True, self.game, ai_paddle_right)
        right_connector = ConnectorAiPaddleToGame(ai_paddle_right, False, self.game, ai_paddle_left)      

        # run until something tells us to stop
        while self.game.frame < self.frames_per_game:            
            self.game.run_one_frame()
            # Let the connectors run the think step of the organisms!!
            left_connector.do_one_think_step()
            right_connector.do_one_think_step()
            self._update_window_caption(game_nr, total_games, left_connector)
        left_fit = (self.game.score.leftscore - self.game.score.rightscore) * FIT_SCORE_ON_GOAL + ai_paddle_left.nr_of_ball_hits *FIT_SCORE_ON_BALL_HIT
        #right_fit = self.game.score.rightscore * FIT_SCORE_ON_GOAL + ai_paddle_right.nr_of_ball_hits*FIT_SCORE_ON_BALL_HIT
        print ("left_fit", left_fit)
        #print ("right_fit", right_fit)
        
        return left_fit


    # Let every organism game AGAINST last best organism, which is present at end of population
    def score_the_new_population_VS_version(self, population: list):
        # Run the game for the given population
        # For now let every organism game AGAINST last best organism, which is present at end of population
        scores = []
        best_organism = population[-1]
        scores_of_best_organism = []
        for i, challenger in enumerate(population[:-1]):
            # 
            print(f"Running next game {i+1}/{len(population)-1}. Starting Event Loop") 
            (challenger_score, cur_best_organism_score) = self._run_game_for_VS_version(challenger, best_organism, i+1, len(population)-1)
            scores_of_best_organism.append(cur_best_organism_score)
            scores.append(challenger_score)
        scores.append(mean(scores_of_best_organism))
        return scores

    # Left paddle will evolve while right paddle is just hanging in there in the middle (you can control it with cursor keys)
    def score_the_new_population_SINGLE_version(self, population: list):
        # Run the game for the given population
        scores = []
        for i, organism in enumerate(population):
            print(f"Running next game {i+1}/{len(population)}. Starting Event Loop. {organism.get_description(False)}") 
            score = self._run_game_for_SINGLE_version(organism, i+1, len(population))
            scores.append(score)
        return scores        

    # Let every organism game AGAINST the hard coded best organism, which is passed on as "best"
    def score_the_new_population_AGAINST_BEST_version(self, population: list, best: AiPaddle):
        # Run the game for the given population
        scores = []
        for i, organism in enumerate(population):
            print(f"Running next game {i+1}/{len(population)}. Starting Event Loop. {organism.get_description(False)}") 
            score = self._run_game_for_AGAINST_BEST_version(organism, best, i+1, len(population))
            scores.append(score)
        return scores     

    def exit(self):
        self.game.exit()        




if __name__ == '__main__':
    game_director = GameDirector()
    organism_creator = lambda : AiPaddle(
        (SCREEN_SIZE_X/16.0,SCREEN_SIZE_Y/2.0), SCREEN_SIZE_X/32.0, SCREEN_SIZE_Y/8.0,
        float(SCREEN_SIZE_Y), 'paddle2.jpg', game_director.game        
    )

    best = organism_creator()
    #best.unpickle_org("organisms8x32x4/" + "fit303_3d11d7294ce343efaeec7328a549901c_sz32.bin")
    best.unpickle_org("organisms10x32x4/fit218.0_178.0_006_1ceab678927b4206bdffda89fdd1714f_sz32.bin")

    # Ecosystem requires a function that maps all organisms to a list of fitnesses (real numbers)
    #scoring_all_organisms = lambda population : game_director.score_the_new_population_VS_version(population)
    scoring_all_organisms = lambda population : game_director.score_the_new_population_SINGLE_version(population)
    #scoring_all_organisms = lambda population : game_director.score_the_new_population_AGAINST_BEST_version(population, best)
    
    # Create the ecosystem
    ecosystem = Ecosystem(organism_creator, single_org_score_func=None, all_org_score_func=scoring_all_organisms, 
                          population_size=POPULATION_SIZE, holdout_mating=HOLDOUT_MATING, holdout_organisms=HOLDOUT_ORGANISMS, mating=True, 
                          organisms_to_preload_on_start=ORGANISMS_TO_PRELOAD_ON_START, organism_write_folder=ORGANISM_WRITE_FOLDER)
    game_director.ecosystem = ecosystem
    # Save the fitness score of the best organism in each generation
    
    # fixed number of generations in this case
    generations = 10000
    for generation in range(generations):
        
        ecosystem.determine_fitnesses()
        print(f"Fitnesses: {ecosystem.fitnesses}")
        ecosystem.new_generation()

    game_director.exit()
