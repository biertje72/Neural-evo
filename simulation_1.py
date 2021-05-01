from organism_and_ecosystem import Organism, Ecosystem
import numpy as np

def main():
    # The function to create the initial population, will be passed on as generator for Ecosystem
    organism_creator = lambda : Organism([1, 16, 16, 16, 1], output='linear')
    # The function we are trying to learn. numpy doesn't have tau...
    true_function = lambda x : np.sin(2 * np.pi * x) #
    # The loss function, mean squared error, will serve as the negative fitness
    loss_function = lambda y_true, y_estimate : np.mean((y_true - y_estimate)**2)

    # our local scoring function
    def simulate_and_evaluate_score(organism, replicates=1):
        """
        Randomly generate `replicates` samples in [0,1],
        use the organism to predict their corresponding value,
        and return the fitness score of the organism
        """
        X = np.random.random((replicates, 1))
        predictions = organism.think(X)
        score = -loss_function(true_function(X), predictions)
        return score

    # Ecosystem requires a function that maps an organism to a real number fitness
    scoring_function = lambda organism : simulate_and_evaluate_score(organism, replicates=100)
    # Create the ecosystem
    ecosystem = Ecosystem(organism_creator, scoring_function, None, 
                        population_size=100, holdout_mating=0.1, mating=True)
    ## Save the fitness score of the best organism in each generation
    best_organism_scores = [ecosystem.get_best_organism(include_fitness=True)[1]]
    
    # fixed number of generations in this case
    generations = 201
    for _ in range(generations):
        ecosystem.generation()
        this_generation_best = ecosystem.get_best_organism(include_fitness=True)
        best_organism_scores.append(this_generation_best[1])
        print("this_generation_best", this_generation_best)
        # [Visualization code omitted...]


if __name__ == "__main__":
    main()
else:
    print("utility mod is imported into another module")