import numpy as np
from ILBDM import ILBDM
import Constant as C
import copy
import random

# find a combination of one or more tree, which add up same length as blank_length
def findSolutionForBlank( blank_length, musicTrees ):
    # store all possible subsequence ( length < blank_length )
    possible_trees = {}
    for tree in musicTrees:
        for length in range( blank_length+1 ):
            if length in tree.hashTable:
                if length in possible_trees:
                    possible_trees[length] = possible_trees[length].union( tree.hashTable[length] )
                else:
                    possible_trees[length] =  tree.hashTable[length]
    # print( possible_trees )

    # randomly select 10 times
    for i in range(10):
        # key1 = blank_length 
        key1 = random.choice( list(possible_trees.keys() ) )
        key2 = blank_length-key1
        # case1: exactly fit in
        if key1 == blank_length:
            return random.sample( possible_trees[key1], 1 )
        elif key2 in possible_trees:
            return random.sample( possible_trees[key1], 1 ) + random.sample( possible_trees[key2], 1 )
        else:
            del possible_trees[key1]

    raise "no suitable combination. QQ~"



class treeNode:
    def __init__(self, _startIndex, _pitchSeq, _durationSeq, _LBDM=[]):
        if len(_pitchSeq) == len(_durationSeq) or len(_pitchSeq) == len(_LBDM):
            self.elementary_noteSeq = np.vstack( [_pitchSeq, _durationSeq] )
            self.pitchSeq = _pitchSeq
            self.durationSeq = _durationSeq
            self.startIndex = _startIndex
            self.LBDM = _LBDM
            self.length = int( sum(_durationSeq) )
            self.left = None
            self.right = None
            self.hashTable = {}

            # print(LBDM)
            if len(_LBDM) >= 2:
                if self.length not in self.hashTable:
                    self.hashTable[self.length] = set()
                self.hashTable[self.length].add(self)

                maxIndex = np.argmax(_LBDM[:-1])
                # print("left:")
                self.left = treeNode(
                    self.startIndex, _pitchSeq[:maxIndex+1], _durationSeq[:maxIndex+1], _LBDM[:maxIndex+1])
                # print("right:")
                self.right = treeNode(
                    self.startIndex + maxIndex+1, _pitchSeq[maxIndex+1:], _durationSeq[maxIndex+1:], _LBDM[maxIndex+1:])

                self.updateHashTable(self.left.hashTable)
                self.updateHashTable(self.right.hashTable)

    def __repr__(self):
        return "\nlength: " + str(self.length) + str(self.pitchSeq)

    def copyNode(self, otherNode):
        self.pitchSeq = otherNode.pitchSeq
        self.durationSeq = otherNode.durationSeq
        self.length = otherNode.length
        self.startIndex = otherNode.startIndex
        self.LBDM = otherNode.LBDM
        self.hashTable = copy.deepcopy(otherNode.hashTable)
        self.left = treeNode(0, [], [])
        self.right = treeNode(0, [], [])
        if otherNode.left != None:
            self.left.copyNode(otherNode.left)
        else:
            self.left = None
        if otherNode.right != None:
            self.right.copyNode(otherNode.right)
        else:
            self.right = None

    def updateHashTable(self, newHashTable):
        for k, v in newHashTable.items():
            if k not in self.hashTable:
                self.hashTable[k] = set()
            self.hashTable[k] = set.union(self.hashTable[k], v)

    def splitToThree(self, index1, index2, fill_in_None = False ):
        assert( 0<= index1<= index2 <= len(self.pitchSeq) )
        trees = [] #
        gap_index_split_trees = 0
        if index1 > 0 :
            trees.append( treeNode(0, self.pitchSeq[:index1], self.durationSeq[:index1], self.LBDM[:index1]) )
            gap_index_split_trees += 1

        if fill_in_None:
            trees.append( None )
        else:
            trees.append( treeNode(0, self.pitchSeq[index1:index2], self.durationSeq[index1:index2], self.LBDM[index1:index2]) )
        
        if index2 < len(self.pitchSeq) :
            trees.append( treeNode(0, self.pitchSeq[index2:], self.durationSeq[index2:], self.LBDM[index2:]) )

        return trees, gap_index_split_trees


if __name__ == "__main__":

    import sys
    from mido import MidiFile
    from Preprocess import ProcessedMIDI

    path = sys.argv[1]
    mid = MidiFile(path)
    parsedMIDI = ProcessedMIDI(mid)
    LBDM_result = ILBDM(parsedMIDI)
    pitchSeq = parsedMIDI.noteSeq[C.PITCHINDEX]
    durationSeq = parsedMIDI.noteSeq[C.DURATIONINDEX]
    test = treeNode(0, pitchSeq, durationSeq, LBDM_result)
    ''' test copyNode '''
    test2 = treeNode(0, [], [])
    test2.copyNode(test)
    ''' test hashTable '''
    print(test.hashTable)
    test2.hashTable.pop(103, None)
    print(103 in test.hashTable)
