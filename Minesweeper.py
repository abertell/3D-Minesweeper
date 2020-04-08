#Minesweeper Class for 3D Minesweeper 1.2.2
#Controls arbitrary storage in 3D space and game logic

import math,random,copy,itertools

#euclidean distance
def euclideanDistance(p1,p2):
    return ((p1[0]-p2[0])**2+(p1[1]-p2[1])**2+(p1[2]-p2[2])**2)**.5

#object for storing values indexed by arbitrary points in 3D space
class Store3D():
    def __init__(self,default,load,vals):
        self.default=default
        if load:
            self.mapTo,self.memory,self.n=vals
        else:
            self.mapTo={}
            self.memory=[]
            self.n=0

    #assign new value to a point
    def assign(self,xyz,v):
        if xyz in self.mapTo:
            self.memory[self.mapTo[xyz]]=v
        else:
            self.mapTo[xyz]=self.n
            self.n+=1
            self.memory.append(v)

    #retrieve value at a point
    def get(self,xyz):
        if xyz in self.mapTo:
            return self.memory[self.mapTo[xyz]]
        else:
            new=copy.copy(self.default)
            self.assign(xyz,new)
            return new

    #return all values in a given cuboid
    def inSlice(self,dims):
        mem=[]
        for x in range(dims[0],dims[1]+1):
            for y in range(dims[2],dims[3]+1):
                for z in range(dims[4],dims[5]+1):
                    if (x,y,z) in self.mapTo:
                        mem.append(((x,y,z),self.get((x,y,z))))
        return mem

#game class
class Minesweeper():
    
    #-1 is default (unchecked) value
    #0-26 are revealed squares with n adjacent mines
    #27 is unrevealed empty square
    #29 is unrevealed mine
    #31 is revealed mine
    #flagging is +1 (on last 3 only)

    def __init__(self,p,limit,load,vals):
        self.p=p
        self.temp=set()
        self.queue=set()
        self.newBlocks=set()
        self.removedBlocks=set()
        self.origin=(0,0,0)
        self.limit=limit
        self.cubes,self.goodFlags,self.badFlags=vals[0:3]
        self.board=Store3D(-1,load=load,vals=vals[3:])
        if not load:
            self.board.assign(self.origin,27)
            for i in self.adjacent(self.origin):
                self.board.assign(i,27)
            self.clearWrapper((0,0,0))

    #return all cubes adjacent to given one
    def adjacent(self,xyz):
        dx,dy,dz=zip(*(x for x in itertools.product([-1,0,1],repeat=3) if x!=(0,0,0)))
        return [(xyz[0]+dx[i],xyz[1]+dy[i],xyz[2]+dz[i])for i in range(26)]

    #iterative clearing
    def clear(self,xyz):
        self.temp.add(xyz)
        halt=False
        mines=0
        for i in self.adjacent(xyz):
            if euclideanDistance(i,self.origin)>self.limit:
                halt=True
            if self.board.get(i)==-1:
                newMine=(random.random()<self.p/100)
                mines+=newMine
                self.board.assign(i,27+2*newMine)
                self.newBlocks.add(i)
            elif self.board.get(i)>=29:
                mines+=1
        if not halt:
            self.board.assign(xyz,mines)
            self.cubes+=1
            self.removedBlocks.add(xyz)
            if mines==0:
                for i in self.adjacent(xyz):
                    if self.board.get(i)==27 and i not in self.temp:
                        self.queue.add(i)

    #wrapper function for iterative clearing
    def clearWrapper(self,xyz):
        self.newBlocks=set()
        self.removedBlocks=set()
        self.origin=xyz
        self.clear(xyz)
        while self.queue:
            block=self.queue.pop()
            self.clear(block)
        self.temp=set()
        return (self.newBlocks.difference(self.removedBlocks),self.removedBlocks)

    #clicking a cube
    def click(self,xyz):
        v=self.board.get(xyz)
        if v==29:
            self.board.assign(xyz,31)
            return -1
        elif v==27:
            return self.clearWrapper(xyz)

    #flagging a cube
    def flag(self,xyz):
        v=self.board.get(xyz)
        self.board.assign(xyz,v-1+2*(v%2))
        if v==27:self.badFlags+=1
        elif v==28:self.badFlags-=1
        elif v%2:self.goodFlags+=1
        else:self.goodFlags-=1
        return v-1+2*(v%2)
