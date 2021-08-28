from hashlib import new
import sys
import time
from mido import MidiFile
from Feature import main
import Preprocess
import MusicSegmentation_2
from Individual import Individual
from Fitness import updateFitness
from ILBDM import ILBDM
import Utility 
import Constant as C

import numpy as np
import random
from zodb import ZODB, transaction
import copy
import Demo
import MusicTree


def startGA(num_generations, num_parents_mating, population, max_population):
    for generation in range(num_generations):
        # Measuring the fitness of each chromosome in the population.
        for individual in population:
            updateFitness(individual)
        population.sort(key=lambda x: x.fitness, reverse=True)
        population = population[0:max_population]

        print("==================\ngeneration: \n", generation)

        for individual in population:
            if individual.isAncestor == True:
                print("*", end="")
            print(round(individual.fitness, 6))
        # print("\n", population[0].parsedMIDI.noteSeq[C.INTERVALINDEX])

        ''' terminate '''

        ''' Selecting the best parents in the population for mating. '''
        parents = select_mating_pool(population, num_parents_mating)

        ''' Generating next generation using crossover. '''
        offspring_crossover = population + crossover(parents)

        break
        # TODO control how many individuals will be mutated.
        ''' Adding some variations to the offspring using mutation. '''
        # offspring_mutation = mutation(population)

        ''' Creating the new population based on the parents and offspring. '''
        population = offspring_crossover 
    return population


def select_mating_pool(population, num_parents_mating):
    ''' Selecting the best individuals in the current generation as parents for producing the offspring of the next generation. '''
    population.sort(key=lambda x: x.fitness, reverse=True)

    parents = population[0:num_parents_mating]

    return parents


def crossover(parents):
    offspring = []
    for main_parent in parents:
        for sub_parent in parents:
            if main_parent == sub_parent:
                continue

            ''' Crossover '''
            # crossover
            print("cutting point: \n", main_parent.cuttingPoint)
            print("signature: \n", main_parent.signature)
            # find elements to be crossovered
            invalid_elements_start_index = []
            for signature in main_parent.signature:
                invalid_elements_start_index.append(signature[1]-1)
            relative_elements = []
            for elementGroup in main_parent.allElementGroups:
                elements = []
                for element in elementGroup:
                    elements.append(element[1]-1)
                relative_elements.append(elements)
            print("all signature: \n", main_parent.allElementGroups)
            while True:
                point = []
                indexOfSelectedElement = random.randint(0, len(main_parent.cuttingPoint)-2)
                cuttingPoint = main_parent.cuttingPoint
                if cuttingPoint[indexOfSelectedElement] not in invalid_elements_start_index:
                    for elements in relative_elements:
                        if cuttingPoint[indexOfSelectedElement] in elements:
                            for end in elements:
                                end_index = cuttingPoint.index(end)
                                start = 0 if end_index == 0 else cuttingPoint[end_index-1]+1
                                point.append((int(start), int(end)))
                            break
                    if point == []:
                        end = cuttingPoint[indexOfSelectedElement]
                        start = 0 if indexOfSelectedElement == 0 else cuttingPoint[indexOfSelectedElement-1]+1
                        point.append((int(start), int(end)))
                    break
            print("index to be crossovered: \n", point)

            # construct offspring based on main_parent
            temp_parsedMIDI = Preprocess.ProcessedMIDI(None, main_parent.parsedMIDI)
            
            # find suitable sequence for filler
            blank_length = int( sum( main_parent.parsedMIDI.noteSeq[C.DURATIONINDEX][point[0][0]:point[0][1]] ) )
            print("blank length: ", blank_length)
            filler_tree = MusicTree.findSolutionForBlank( blank_length, sub_parent.musicTree )
            print(filler_tree)

            # filling the blank
            # 1st part merge note sequence
            # for each gap, split original note sequence into 3 part: left + blank + right
            for gap in point:
                left_noteSeq_offspring = temp_parsedMIDI.noteSeq[:,:gap[0]]
                right_noteSeq_offspring = temp_parsedMIDI.noteSeq[:,gap[1]:]
            if len(filler_tree) == 1:
                filler_noteSeq = Preprocess.expandElementarySequence( filler_tree[0].pitchSeq, filler_tree[0].durationSeq ) 
            elif len(filler_tree) == 2:
                filler_noteSeq = np.concatenate([
                    Preprocess.expandElementarySequence( filler_tree[0].pitchSeq, filler_tree[0].durationSeq ),
                    Preprocess.expandElementarySequence( filler_tree[1].pitchSeq, filler_tree[1].durationSeq )
                ], axis=1 )
            
            print( "Father: \n",temp_parsedMIDI.noteSeq[0] )
            print( "Son:" )
            print( left_noteSeq_offspring[0] )
            print( right_noteSeq_offspring[0] )
            print( filler_noteSeq[0] )
            # 2nd part merge tree structure 


            return []

            # for i in range(len(mask)):
            #     if(mask[i] == 1):
            #         start = main_parent.cuttingPoint[i]
            #         end = main_parent.cuttingPoint[i+1]-1
            #         for i in range(start, end+1):
            #             move = random.randint(-4, 4)
            #             if temp.noteSeq[C.PITCHINDEX][i] != 0:
            #                 if temp.noteSeq[C.PITCHINDEX][i] + move <= 0:
            #                     break
            #                 temp.noteSeq[C.PITCHINDEX][i] = temp.noteSeq[C.PITCHINDEX][i] + move

            ####
            # offspring_parsedMIDI = Preprocess.ProcessedMIDI(None, main_parent.parsedMIDI)
            offspring_ancestor = main_parent.ancestor

            ####change to individual####
            # TODO: update cutting Point
            offspring.append(Individual(offspring_parsedMIDI,
                                        main_parent.cuttingPoint, main_parent.signature, False, offspring_ancestor))
    offspring.sort(key=lambda x: x.fitness, reverse=True)
    return offspring

# TODO preserve the original individual


def mutation(offspring_crossover):
    newPopulation = []
    # int(len(offspring_crossover)*0.3)
    mutation_size = len(offspring_crossover)
    count = 0
    for offspring in offspring_crossover:
        if count == mutation_size:
            break
        count = count+1
        new_parsedMIDI = Preprocess.ProcessedMIDI(None, offspring.parsedMIDI)
        newOffspring = Individual(new_parsedMIDI, offspring.cuttingPoint,
                                  offspring.signature, False, offspring.ancestor)
        # selected element can not be signature
        start = 0
        end = 0
        while (start, end+1) in newOffspring.signature or (start == 0 and end == 0):
            selected_elementIndex = random.randint(
                0, len(newOffspring.cuttingPoint)-1)
            start = 0 if selected_elementIndex == 0 else newOffspring.cuttingPoint[
                selected_elementIndex-1]+1
            end = newOffspring.cuttingPoint[selected_elementIndex]
        pitchShifting(start, end, newOffspring.parsedMIDI)
        # offspring.parsedMIDI.printMIDI()
        pitchOrderReverse(start, end, newOffspring.parsedMIDI)
        newOffspring.parsedMIDI.updateFieldVariable(newOffspring.parsedMIDI)
        newOffspring.calculateAllFeatures()
        newPopulation.append(newOffspring)

    return offspring_crossover + newPopulation


def pitchOrderReverse(start, end, target):
    # Pitch
    target.noteSeq[C.PITCHINDEX][start:end +
                                 1] = np.flipud(target.noteSeq[C.PITCHINDEX][start:end+1])
    # Duration
    target.noteSeq[C.DURATIONINDEX][start:end +
                                    1] = np.flipud(target.noteSeq[C.DURATIONINDEX][start:end+1])
    # Rest
    target.noteSeq[C.RESTINDEX][start:end +
                                1] = np.flipud(target.noteSeq[C.RESTINDEX][start:end+1])
    # Interval

    def calculateInterval(i):
        if i < 0 or i >= target.numberOfNotes-1:
            return
        if target.noteSeq[C.PITCHINDEX][i+1] == 0:
            if i + 2 < target.numberOfNotes:
                nextNextPitch = target.noteSeq[C.PITCHINDEX][i+2]
                target.noteSeq[C.INTERVALINDEX][i]\
                    = abs(nextNextPitch - target.noteSeq[C.PITCHINDEX][i])
                target.noteSeq[C.INTERVALINDEX][i+1]\
                    = abs(nextNextPitch - target.noteSeq[C.PITCHINDEX][i])
            else:
                target.noteSeq[C.INTERVALINDEX][i] = 0
        else:
            target.noteSeq[C.INTERVALINDEX][i]\
                = abs(target.noteSeq[C.PITCHINDEX][i+1] - target.noteSeq[C.PITCHINDEX][i])
    for i in range(start-2, end + 2):
        calculateInterval(i)

    # TODO reconstruct accumulative beat sequence( merge into segmentation? )


def pitchShifting(start, end, target):
    move = random.randint(-7, 7)
    newPitchSeq = []
    for i in range(start, end+1):
        if target.noteSeq[C.PITCHINDEX][i] != 0:
            newPitch = target.noteSeq[C.PITCHINDEX][i] + move
            if Utility.isValidPitch(newPitch):
                newPitchSeq.append(newPitch)
            else:
                return
        else:
            newPitchSeq.append(0)
    target.noteSeq[C.PITCHINDEX][start:end+1] = newPitchSeq


def findBestOffspring(population):
    population.sort(key=lambda x: x.fitness, reverse=True)
    for i in population:
        if i.isAncestor != True:
            return i
    return None


if __name__ == "__main__":

    try:
        paths = sys.argv[1:]
    except:
        print("Missing input MIDI file!")

    population = []

    for path in paths:
        db = ZODB(path)
        dbroot = db.dbroot
        print(dbroot.keys())
        for key in dbroot.keys():
            population.append(dbroot[key])
        db.close()

    new_population = startGA(50, 5, population, 100)
    bestOffspring = findBestOffspring(new_population)
    if bestOffspring != None:
        bestOffspring.parsedMIDI.printMIDI()
        mid_output = Demo.parsed2MIDI(bestOffspring.parsedMIDI)
        cur_time = str(time.strftime('%m_%d_%H_%M', time.localtime()))
        mid_output.save('../output/' + cur_time + ".mid")
