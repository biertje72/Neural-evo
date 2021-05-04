# Based on great code found here: https://towardsdatascience.com/evolving-neural-networks-b24517bb3701
import copy
#from game_director import AiPaddle
import numpy as np
import uuid
import json
import pickle

LOG_DEBUG = True
MUTATE_STDEV=0.03 #ORIGINAL
# #MUTATE_STDEV=0.003 MAURICE TRIED
#MUTATE_STDEV=0.3  MAURICE TRIED


class Organism():
    def __init__(self, dimensions, use_bias=True, output='softmax'):
        self.layers = []
        self.biases = []
        self.use_bias = use_bias
        self.output = self._activation(output)

        # Some enhancements
        # Convert a UUID to a 32-character hexadecimal string
        self.uuid_hex = uuid.uuid4().hex
        self.parent_1_uuid = None
        self.parent_2_uuid = None
        self.fitnesses = []  # oldest to latest
        self.generation_nrs_active = []  # oldest to latest
        self.family_age = 0

        for i in range(len(dimensions)-1):
            shape = (dimensions[i], dimensions[i+1])
            std = np.sqrt(2 / sum(shape))
            layer = np.random.normal(0, std, shape)
            bias = np.random.normal(0, std, (1,  dimensions[i+1])) * use_bias
            self.layers.append(layer)
            self.biases.append(bias)


    def pickle_org(self, path):
        temp = (self.layers, self.biases, self.uuid_hex, self.parent_1_uuid, self.parent_2_uuid, self.fitnesses, self.generation_nrs_active, self.family_age)
        with open(path,'wb') as f:
           pickle.dump(temp, f)
     
    def unpickle_org(self, path):
         with open(path,'rb') as f:
            read_layers = []
            (read_layers, self.biases, self.uuid_hex, self.parent_1_uuid, self.parent_2_uuid, self.fitnesses, self.generation_nrs_active, self.family_age) = pickle.load(f)
            # Hack/check to see if nr input layers has changed, and act accordinlgy.
            # Do we want to do same for hidden layer and output layer?? MBI
            read_input_layer_shape = read_layers[0].shape[0]
            cur_input_layer_shape = self.layers[0].shape[0]
            if cur_input_layer_shape != read_input_layer_shape:
                self.layers = read_layers
                from numpy import  vstack, zeros
                self.layers[0] = vstack([self.layers[0], zeros([2,32])])  # FOR NOW JUST ADD 2 NEURONS WITH 32 WEIGHTS
                True
            else:
                self.layers = read_layers

            
    def _activation(self, output):
        # activation function for output layer
        # softmax; for classification where you need outputs to produce a vector that is non-negative and sums to 1.
        # sigmoid; (logistic) for classification, where multiple answers are OK
        # linear; for regression, values are unbounded
        # Softmax outputs produce a vector that is non-negative and sums to 1. It's useful when you have mutually exclusive categories ("these images only contain cats or dogs, not both"). You can use softmax if you have 2,3,4,5,... mutually exclusive labels.
        # Using 2,3,4,... sigmoid outputs produce a vector where each element is a probability. It's useful when you have categories that are not mutually exclusive ("these images can contain cats, dogs, or both cats and dogs together"). You use as many sigmoid neurons as you have categories, and your labels should not be mutually exclusive.
        # Using the identity/linear function as an output can be helpful when your outputs are unbounded. For example, some company's profit or loss for a quarter could be unbounded on either side.
        if output == 'softmax':
            return lambda X : np.exp(X) / np.sum(np.exp(X), axis=1).reshape(-1, 1)
        if output == 'sigmoid':
            return lambda X : (1 / (1 + np.exp(-X)))
        if output == 'linear':
            return lambda X : X

    #def predict(self, X): old name
    def think(self, X):
        # Process the neural network based on input vector X!
        # Repeatedly applies ReLU function to input layers and output function to output layer
        # The rectified linear activation function or ReLU for short is a piecewise linear function
        # that will output the input directly if it is positive, otherwise, it will output zero.
        if not X.ndim == 2:
            raise ValueError(f'Input has {X.ndim} dimensions, expected 2')
        if not X.shape[1] == self.layers[0].shape[0]:
            raise ValueError(f'Input has {X.shape[1]} features, expected {self.layers[0].shape[0]}')
        for index, (layer, bias) in enumerate(zip(self.layers, self.biases)):
            X = X @ layer + np.ones((X.shape[0], 1)) @ bias
            if index == len(self.layers) - 1:
                X = self.output(X) # output activation
            else:
                X = np.clip(X, 0, np.inf)  # ReLU
        
        return X

    #MBI wat doet deze fie??
    # Runs the network, and if deterministic==True 
    def predict_choice(self, X, deterministic=True):
        probabilities = self.think(X)
        if deterministic:
            # ik denk dat deze de index van de maximale output neuron geeft
            return np.argmax(probabilities, axis=1).reshape((-1, 1))
        # volgende geeft iets van waarschijnlijkheden terug bij deterministic==False
        # moeten wel samen 1 zijn en allemaal >=0
        if any(np.sum(probabilities, axis=1) != 1):
            raise ValueError(f'Output values must sum to 1 to use deterministic=False')
        if any(probabilities < 0):
            raise ValueError(f'Output values cannot be negative to use deterministic=False')
        choices = np.zeros(X.shape[0])
        for i in range(X.shape[0]):
            U = np.random.rand(X.shape[0])
            c = 0
            while U > probabilities[i, c]:
                U -= probabilities[i, c]
                c += 1
            else:
                choices[i] = c
        return choices.reshape((-1,1))

    # the mutation step is realized as the addition of Gaussian noise to each weight and each bias
    # in the network. 
    # We do not change the activations or architecture of the network here, although a more advanced
    # evolutionary algorithm could certainly do so by adding or removing nodes in the hidden layers.
    def mutate(self, stdev=MUTATE_STDEV): 
        for i in range(len(self.layers)):
            self.layers[i] += np.random.normal(0, stdev, self.layers[i].shape)
            if self.use_bias:
                self.biases[i] += np.random.normal(0, stdev, self.biases[i].shape)

    # Mate this organism with other, by randomly selecting layers from one or the other.
    # If mutate==True, child will be randomly mutated afterwards
    def mate(self, other, organism_creator, mutate=True):
        if self.use_bias != other.use_bias:
            raise ValueError('Both parents must use bias or not use bias')
        if not len(self.layers) == len(other.layers):
            raise ValueError('Both parents must have same number of layers')
        if not all(self.layers[x].shape == other.layers[x].shape for x in range(len(self.layers))):
            raise ValueError('Both parents must have same shape')

        child = organism_creator()
        child.parent_1_uuid = self.uuid_hex
        child.parent_2_uuid = other.uuid_hex
        child.family_age = max(self.family_age, other.family_age)

        for i in range(len(child.layers)):
            pass_on = np.random.rand(1, child.layers[i].shape[1]) < 0.5
            child.layers[i] = pass_on * self.layers[i] + ~pass_on * other.layers[i]
            child.biases[i] = pass_on * self.biases[i] + ~pass_on * other.biases[i]
        if mutate:
            child.mutate()
        return child

    def set_parent_uuids(self, parent_1_uuid: str, parent_2_uuid: str):
        self.parent_1_uuid = parent_1_uuid
        self.parent_2_uuid = parent_2_uuid

    def get_description(self, inc_parents = True):
        desc = f"{self.uuid_hex} {self.fitnesses:} {self.generation_nrs_active}, "
        if inc_parents:
            desc += f"{self.parent_1_uuid}, {self.parent_2_uuid}, "
        desc += f"{self.family_age}"
        return desc


class Ecosystem():
    def __init__(self, original_f, single_org_score_func=None, all_org_score_func=None, population_size=100, holdout_mating='sqrt', holdout_organisms='sqrt', mating=True, organisms_to_preload_on_start=[], organism_write_folder=""):
        """
        original_f must be a function to produce Organisms, used for the original population.
        single_org_score_func must be a function which accepts an Organism as input and returns a float.
        or you pass all_org_score_func, which scores all organisms at once (handy when you want to have more control, e.g. in case of fighting organisms)
            must return a list with scores.
        holdout_mating: strategy for organisms that are allowed to mate. must be one of sqrt, log, or a number. If sqrt or log, then self.holdout_mating
        will be set to number that matched sqrt or log of population_size. You can also pass that number yourself.
            holdout_mating defines the fraction of best in population that is allowed to mate.
            nr_holdout_mating will contain the actual number calculated by applying holdout_mating.
        holdout_organisms: strategy to define the fraction of best in population that is allowed to stay in next generation round.
            nr_holdout_organisms will contain the actual number calculated by applying holdout_organisms.
        """
        assert bool(single_org_score_func) ^ bool(all_org_score_func) # ^ = XOR :)

        self.generation_nr = 1
        self.population_size = population_size
        self.organism_creator = original_f
        self.population = [self.organism_creator() for _ in range(population_size)]
        if self.generation_nr == 1:
            for i, organims_pickle_bin in enumerate(organisms_to_preload_on_start):
                print(f"First generation, adding following organism to it: {organims_pickle_bin}")
                organism_to_sacrifice = self.population[i]
                organism_to_sacrifice.unpickle_org(organims_pickle_bin)
        self.fitnesses = []
        self.best_organism_fitnesses = []   # per generation the highest score
        self.single_org_score_func = single_org_score_func
        self.all_org_score_func = all_org_score_func
        self.organism_write_folder = organism_write_folder

        if holdout_mating == 'sqrt':
            self.nr_holdout_mating = max(1, int(np.sqrt(population_size)))
        elif holdout_mating == 'log':
            self.nr_holdout_mating = max(1, int(np.log(population_size)))
        elif holdout_mating > 0 and holdout_mating < 1:
            self.nr_holdout_mating = max(1, int(holdout_mating * population_size))
        else:
            self.nr_holdout_mating = max(1, int(holdout_mating))

        if holdout_organisms == 'sqrt':
            self.nr_holdout_organisms = max(1, int(np.sqrt(population_size)))
        elif holdout_organisms == 'log':
            self.nr_holdout_organisms = max(1, int(np.log(population_size)))
        elif holdout_organisms > 0 and holdout_organisms < 1:
            self.nr_holdout_organisms = max(1, int(holdout_organisms * population_size))
        else:
            self.nr_holdout_organisms = max(1, int(holdout_organisms))

        self.mating = mating

    # Applies the self.single_org_score_func to self.population.
    # If repeats>1 then scoring function will be applied multiple times for one organism and average score is determined.
    def determine_fitnesses(self, repeats=1):
        print("Determine fitnesses for population:")
        self.print_population(prefix="\t")

        # calculate scores
        if self.single_org_score_func:
            self.fitnesses = [np.mean([self.single_org_score_func(x) for _ in range(repeats)]) for x in self.population]
        else:
            self.fitnesses = self.all_org_score_func(self.population)
        # sort population based on scores
        self.population = [self.population[x] for x in np.argsort(self.fitnesses)[::-1]]
        self.fitnesses = np.sort(self.fitnesses)[::-1]
        self.best_organism_fitnesses.append(self.fitnesses[0])

        for i, organism in enumerate(self.population):
            organism.fitnesses.append(self.fitnesses[i])
            organism.generation_nrs_active.append(self.generation_nr)
            organism.family_age += 1

        print("After fitnesses calculations (best to worst):")
        self.print_population(prefix="\t")

        # Pickle the best organism :)
        from statistics import median
        best_org = self.population[0]
        best_org.pickle_org(
            f"{self.organism_write_folder}/fit{best_org.fitnesses[-1]:03}_" +
            f"{median(best_org.fitnesses):03}_" +
            f"{len(best_org.fitnesses):03}_" +
            f"{best_org.uuid_hex}_sz{best_org.layers[0].shape[1]}.bin"
        )

    # Will replace current population with new population based on scoring, mating, mutating.
    def new_generation(self):
        new_population = []
        for nr in range(self.population_size - self.nr_holdout_organisms):
            parent_1_idx = nr % self.nr_holdout_mating  # holdout_mating= number of best organisms that always may mate (and/or mutate)
            if self.mating: # requires 2nd parent, picked here using exp distibution
                parent_2_idx = min(self.population_size - 1, int(np.random.exponential(self.nr_holdout_mating)))
            else:
                # no mating, mate with self
                parent_2_idx = parent_1_idx
            if LOG_DEBUG:
                print(f"Mating {parent_1_idx} and {parent_2_idx} ({self.population[parent_1_idx].uuid_hex} and {self.population[parent_2_idx].uuid_hex})")
            offspring = self.population[parent_1_idx].mate(self.population[parent_2_idx], self.organism_creator)
            new_population.append(offspring)
        new_population.extend(self.population[0:self.nr_holdout_organisms]) # Ensure best organisms survive
        if LOG_DEBUG:
            for org in self.population[0:self.nr_holdout_organisms]:
                print(f"Adding best to population too: {org.uuid_hex}")

        self.population = new_population
        print("Generation with new population:")
        self.print_population(prefix="\t")
        self.generation_nr += 1



    # Sometimes you want to do it in 1 call
    def generation(self, repeats=1): #, keep_best=True
        self.determine_fitnesses(repeats)
        self.new_generation()

    def print_population(self, prefix=""):
        for org in self.population:
            print(f"{prefix}{org.get_description()}")
    
    # For current population will run scoring (with or without repeats) and returns the one BEST
    # organism only. No mating & mutating done after that, population is left in tact.
    # When include_fitness=True, also return the score
    #
    def get_best_organism(self, repeats=1, include_fitness=False):
        assert self.single_org_score_func != None
        rewards = [np.mean(self.single_org_score_func(x)) for _ in range(repeats) for x in self.population]
        if include_fitness:
            best = np.argsort(rewards)[-1]
            return self.population[best], rewards[best]
        else:
            return self.population[np.argsort(rewards)[-1]]