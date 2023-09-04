#3D Minesweeper v1.3.0
#Author: Adam Bertelli (abertell@andrew.cmu.edu)

#main.py performs all the 3D graphics and rendering

#using "cube.egg" model from:
#https://github.com/treeform/panda3d-sample-models/blob/master/cube.egg

import math,sys,itertools
from Minesweeper import euclideanDistance,Store3D,Minesweeper
o=math.pi/180
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TransparencyAttrib
from panda3d.core import WindowProperties,TextNode
from panda3d.core import CollisionTraverser,CollisionNode,CollisionHandlerQueue
from panda3d.core import CollisionRay,CollisionBox,CollisionSphere
from panda3d.core import BitMask32,LVector3
from panda3d.core import KeyboardButton as KB

#game constants
GAME_PROB=[17]
LIVES=[1]
CAMERA_FOV=[120]
PLAYER_SPEED=[2]
NUM_DISP_PERCENTAGE=[75]
LOAD_LIMIT=[30]
CHUNK_SIZE=[4]
RENDER_DIST=[2]
NUM_CHUNK_SIZE=[0]
NUM_RENDER_DIST=[3]
DO_COLLIDE=[True]
DISP_GUI=[1]
WIPE_ON_DEATH=[False]
FULLSCREEN=[False]

INGAME=[GAME_PROB,LIVES,CAMERA_FOV,PLAYER_SPEED,NUM_DISP_PERCENTAGE,LOAD_LIMIT,
        CHUNK_SIZE,RENDER_DIST,NUM_RENDER_DIST,DISP_GUI]

#camera movement
class Player():
    def __init__(self,speed,pos):
        self.speed=speed
        self.angle=0
        self.incline=0
        self.vel=[0,0,0]
        self.limit=15
        self.pos=pos
    def accel(self,a):
        for i in range(3):self.vel[i]+=self.speed*a[i]
        mag=euclideanDistance(self.vel,(0,0,0))
        if mag>self.limit*self.speed:
            for i in range(3):self.vel[i]*=self.limit*self.speed/mag
    def accel3rd(self,c):
        self.accel([c*math.sin(o*self.incline)*math.sin(o*self.angle),
                    -c*math.sin(o*self.incline)*math.cos(o*self.angle),
                    c*math.cos(o*self.incline)])
    def accelPar(self,c):
        self.accel([-c*math.sin(o*self.angle)*math.cos(o*self.incline),
                    c*math.cos(o*self.angle)*math.cos(o*self.incline),
                    c*math.sin(o*self.incline)])
    def accelPerp(self,c):
        self.accel([c*math.cos(o*self.angle),c*math.sin(o*self.angle),0])
    def bounce(self,coll):
        for i in range(3):self.vel[i]*=2*(coll[i]*self.vel[0]>=0)-1
    def decel(self,c):
        for i in range(3):self.vel[i]*=c
    def dpos(self,dp):
        for i in range(3):self.pos[i]+=dp[i]
    def move(self,dt):
        self.pos[0]+=dt*self.vel[0]
        self.pos[1]+=dt*self.vel[1]
        self.pos[2]+=dt*self.vel[2]
    def turn(self,angle):
        self.angle+=angle
    def turnUp(self,angle):
        self.incline=max(-90,min(90,self.incline+angle))

#game rendering
class Renderer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.gameOver=False
        self.init=True
        self.firstStart=False
        self.size=20
        self.numSize=NUM_DISP_PERCENTAGE[0]/100

        #collisions
        self.mouseTraverser=CollisionTraverser()
        self.mouseQueue=CollisionHandlerQueue()
        self.mouseNode=CollisionNode('mouseNode')
        self.mouseAdd=camera.attachNewNode(self.mouseNode)
        self.mouseNode.setCollideMask(BitMask32(1))
        self.mouseRay=CollisionRay()
        self.mouseNode.addSolid(self.mouseRay)
        self.mouseTraverser.addCollider(self.mouseAdd,self.mouseQueue)
        #self.mouseTraverser.showCollisions(render)
        self.cameraTraverser=CollisionTraverser()
        self.cameraQueue=CollisionHandlerQueue()
        self.cameraNode=CollisionNode('cameraNode')
        self.cameraAdd=camera.attachNewNode(self.cameraNode)
        self.cameraNode.setCollideMask(BitMask32(2))
        self.cameraSphere=CollisionSphere(0,0,0,2)
        self.cameraNode.addSolid(self.cameraSphere)
        self.cameraTraverser.addCollider(self.cameraAdd,self.cameraQueue)
        #self.cameraTraverser.showCollisions(render)

        #interaction
        self.mouseSens=40
        self.disableMouse()
        window=WindowProperties()
        window.setMouseMode(WindowProperties.M_relative)
        window.setCursorHidden(True)
        window.setFullscreen(FULLSCREEN[0])
        self.win.requestProperties(window)
        self.oldx,self.oldy=0,0

        #key input
        self.accept('escape',sys.exit)
        self.accept('mouse1',self.click)
        self.accept('e',self.click)
        self.accept('mouse3',self.flag)
        self.accept('q',self.flag)
        self.accept('f',self.boom)
        self.accept('tab',self.save)
        
        self.accept('r',self.newGame,[False])
        self.accept('m',self.switchMenu2)
        self.accept('backspace',self.switchMenu1)
        self.accept('enter',self.startGame,[False])
        self.accept('l',self.startGame,[True])
        self.accept('arrow_left',self.modify,[-1])
        self.accept('arrow_right',self.modify,[1])
        self.accept('arrow_up',self.scroll,[-1])
        self.accept('arrow_down',self.scroll,[1])

        #number management
        self.centerScale=1000
        self.numStart=[(-3,-5),(-3,-7),(-3,-7),(-3,-5),(-3,-3),(-3,-5),(-3,-5),
                       (-1,-7),(-3,-5),(-3,-5),(-3,-7)]
        self.numShape=[[(1,-1),(2,-1),(3,0),(3,1),(3,2),(3,3),(3,4),(2,3),(1,2),
                        (0,1),(0,2),(0,3),(0,4),(1,5),(2,5)],
                       [(1,0),(2,0),(3,0),(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),
                        (1,5),(0,4)],
                       [(1,0),(2,0),(3,0),(0,1),(1,2),(2,3),(3,4),(3,5),(2,6),
                        (1,6),(0,5)],
                       [(1,-1),(2,-1),(3,0),(3,1),(2,2),(1,2),(3,3),(3,4),(2,5),
                        (1,5),(0,4)],
                       [(4,0),(3,0),(2,0),(1,0),(0,1),(1,2),(2,3),(3,4),(3,3),
                        (3,2),(3,1),(3,-1),(3,-2)],
                       [(1,-1),(2,-1),(3,0),(3,1),(2,2),(1,2),(0,2),(0,3),(0,4),
                        (0,5),(1,5),(2,5),(3,5)],
                       [(1,-1),(2,-1),(3,0),(3,1),(2,2),(1,2),(0,1),(0,2),(0,3),
                        (0,4),(1,5),(2,5),(3,4)],
                       [(0,1),(1,2),(1,3),(2,4),(2,5),(2,6),(1,6),(0,6),(-1,6)],
                       [(1,-1),(2,-1),(3,0),(3,1),(2,2),(1,2),(0,1),(0,3),(0,4),
                        (1,5),(2,5),(3,4),(3,3)],
                       [(1,-1),(2,-1),(3,0),(3,1),(3,2),(3,3),(3,4),(2,5),(1,5),
                        (0,4),(0,3),(1,2),(2,2)],
                       [(1,0),(2,0),(3,1),(3,2),(3,3),(3,4),(3,5),(2,6),(1,6),
                        (0,6),(0,5),(0,4),(0,3),(0,2),(0,1)]]

        #function input
        self.chunkConditions=lambda:(
            self.renderDistance,self.chunk,self.chunkWidth,self.chunkSize,
            self.curRange,self.chunkStorage,self.makeCube,self.removeCube,0)
        self.numConditions=lambda:(
            self.numRenderDistance,self.numChunk,self.numChunkWidth,
            self.numChunkSize,self.numCurRange,self.numChunkStorage,
            self.makeNum,self.removeNum,1)

        #main menu
        self.menu=1
        self.menu1Attributes=[]
        self.menu2Attributes=[]
        self.endAttributes=[]
        self.settingMsg=["Mine Density","Lives","FOV","Movement Speed",
                         "Number Size","Generation Limit","Chunk Size",
                         "Render Distance","Number Visibility","Ingame Overlay"]
        self.settingExp=[
            """
Percentage probability that a randomly generated cube is a mine.
            """,
            """
The amount of times the player can incorrectly click before losing.
            """,
            """
The first-person field of view angle on the camera.
            """,
            """
The speed at which the player can move.
            """,
            """
What percentage of the cube you want the size of the displayed
number to take up.
            """,
            """
How far the game is allowed to propogate outwards while clearing
new regions before manually halting, measured in euclidean distance.
The lower the number, the less time loading new regions will take.
            """,
            """
The size of each chunk, starting from the center and facing
any direction.
            """,
            """
The number of chunks being rendered in any direction.
            """,
            """
How far away numbers can be from you before they become invisible.
            """,
            """
Whether the ingame overlay (lives, statistics) is displayed.
            """]
        self.settingLowerBound=[0,0,40,0,0,4,-1,-1,-1,-1]
        self.settingUpperBound=[100,13,140,16,101,51,51,13,10,2]
        self.settingDelta=[1,1,5,1,1,1,1,1,1,1]
        self.isBool=[0,0,0,0,0,0,0,0,0,1]
        self.setpoint=0
        self.canLoad=0
        self.loadColor=(1,0,0,1)
        try:saveState=open("saves/saveState.txt")
        except FileNotFoundError:pass
        else:
            if saveState.read()!='blank':
                self.canLoad=1
                self.loadColor=(0,1,0,1)
            saveState.close()
        self.dispMenu1()
        self.taskMgr.add(self.titleTask,"titleTask")

    #clear all adjacent unflagged cubes ("chording")
    def boom(self):
        flags=self.sweep.board.get(self.numChunk)
        count=0
        clear=set()
        for xyz in self.sweep.adjacent(self.numChunk):
            if self.sweep.board.get(xyz) in {28,30,32}:
                count+=1
                if count>flags:
                    break
            elif self.sweep.board.get(xyz) in {27,29,31}:
                clear.add(xyz)
        if count==flags:
            for cube in clear:
                self.clear(cube)

    #clear a cube
    def clear(self,xyz):
        res=self.sweep.click(xyz)
        if res==-1:
            cube=self.currentCubes[self.mapToCubes[xyz]]
            cube.setTexture(self.mineTex)
            self.lives-=1
            if self.inGameGUI and self.hearts:self.hearts.pop(-1).destroy()
            if self.lives==0:
                self.endGame()
        elif res:
            for xyz in res[0]:
                place=((xyz[0]+self.chunkSize)//self.chunkWidth,
                       (xyz[1]+self.chunkSize)//self.chunkWidth,
                       (xyz[2]+self.chunkSize)//self.chunkWidth)
                chunk=self.chunkStorage.get(place)
                chunk.add(xyz)
                self.chunkStorage.assign(place,chunk)
                if place in self.curRange:
                    self.makeCube(xyz,self.sweep.board.get(xyz))
            for xyz in res[1]:
                place=((xyz[0]+self.chunkSize)//self.chunkWidth,
                       (xyz[1]+self.chunkSize)//self.chunkWidth,
                       (xyz[2]+self.chunkSize)//self.chunkWidth)
                chunk=self.chunkStorage.get(place)
                if xyz in chunk:
                    chunk.remove(xyz)
                    self.chunkStorage.assign(place,chunk)
                    if place in self.curRange:
                        self.removeCube(xyz)

                place=((xyz[0]+self.numChunkSize)//self.numChunkWidth,
                       (xyz[1]+self.numChunkSize)//self.numChunkWidth,
                       (xyz[2]+self.numChunkSize)//self.numChunkWidth)
                val=self.sweep.board.get(xyz)
                if val>0:
                    numChunk=self.numChunkStorage.get(place)
                    numChunk.add(xyz)
                    self.numChunkStorage.assign(place,numChunk)
                    if place in self.numCurRange:
                        self.makeNum(xyz,val)

    #uses ray collision to update board state
    def click(self):
        if not (self.gameOver or self.init):
            self.mouseRay.setFromLens(self.camNode,0,0)
            self.mouseTraverser.traverse(self.render)
            if self.mouseQueue.getNumEntries()>0:
                self.mouseQueue.sortEntries()
                name=self.mouseQueue.getEntry(0).getIntoNode().name
                xyz=tuple(map(int,name.split(',')))
                self.clear(xyz)

    #redraws new parts of the space
    def draw(self,conditions):
        distance,chunk,width,size,curRange,storage,make,remove,isNum=conditions
        newRange=set(itertools.product(
            range(-distance+chunk[0],distance+chunk[0]+1),
            range(-distance+chunk[1],distance+chunk[1]+1),
            range(-distance+chunk[2],distance+chunk[2]+1)))
        for place in newRange:
            if place not in curRange:
                if place in storage.mapTo:
                    getChunk=storage.get(place)
                    for xyz in getChunk:
                        make(xyz,self.sweep.board.get(xyz))
                else:
                    newChunk=set()
                    read=self.sweep.board.inSlice(
                        (place[0]*width-size,place[0]*width+size,
                         place[1]*width-size,place[1]*width+size,
                         place[2]*width-size,place[2]*width+size))
                    for i in read:
                        if (i[1]<27)==isNum and i[1]>0:
                            make(i[0],i[1])
                            newChunk.add(i[0])
                    storage.assign(place,newChunk)
        for place in curRange.difference(newRange):
            getChunk=storage.get(place)
            for xyz in getChunk:
                remove(xyz)
        return newRange

    def dispMenu1(self):
        self.titleNum=self.makeNum((0,3,.5),99,title=True)
        self.menu1Attributes.append(OnscreenText(
            text="[Enter] - New Game",pos=(0,-.1),scale=.1,fg=(0,1,0,1)))
        self.menu1Attributes.append(OnscreenText(
            text="[L] - Load Game",pos=(0,-.3),scale=.1,fg=self.loadColor))
        self.menu1Attributes.append(OnscreenText(
            text="[M] - Settings",pos=(0,-.5),scale=.1,fg=(0,1,0,1)))
        self.menu1Attributes.append(OnscreenText(
            text="Press [Esc] at any time to quit",scale=.1,pos=(0,-.9),
            fg=(0,1,0,1)))
        title=OnscreenImage(image="resources/title.png",scale=(1.04,1,0.16),
                            pos=(0,0,0.2))
        title.setTransparency(TransparencyAttrib.MAlpha)
        self.menu1Attributes.append(title)
    
    def dispMenu2(self):
        global INGAME
        for i in range(len(INGAME)):
            self.menu2Attributes.append(OnscreenText(
                text=self.msg(i),pos=(1,.3-.09*i),scale=.09,mayChange=1,
                fg=(0,1,0,1)))
            self.menu2Attributes.append(OnscreenText(
                text=self.settingMsg[i],pos=(-1,.3-.09*i),scale=.09,
                mayChange=1,align=TextNode.ALeft,fg=(0,1,0,1)))
        self.menu2Attributes.append(OnscreenText(
    text="Up/Down Arrows to select setting, Left/Right Arrows to change value",
            pos=(0,.8),scale=.08,fg=(0,1,0,1)))
        self.menu2Attributes.append(OnscreenText(
            text="[Backspace] - return to Main Menu",pos=(0,-.7),scale=.1,
            fg=(0,1,0,1)))
        self.menu2Attributes.append(OnscreenText(
            text="Press [Esc] at any time to quit",scale=.1,pos=(0,-.9),
            fg=(0,1,0,1)))
        self.menu2Attributes.append(OnscreenText(
            text=self.settingExp[self.setpoint],pos=(0,.7),scale=.07,
            fg=(0,1,0,1),mayChange=1))
        self.menu2Attributes[2*self.setpoint].setText(
            '> '+self.msg(self.setpoint)+' <')

    #game over
    def endGame(self):
        self.gameOver=True
        score=self.sweep.cubes+100*self.sweep.goodFlags
        score*=0.9**self.sweep.badFlags
        score=int(score)
        file=open('resources/highscore.txt')
        highscore=int(file.readline())
        file.close()
        if score>highscore:
            file=open('resources/highscore.txt','w')
            highscore=score
            file.write(str(highscore))
            file.close()
        if self.wipeOnDeath:
            saveState=open('saves/saveState.txt','w')
            saveState.write('blank')
            saveState.close()
        self.texList=[self.normalTex,self.flagTex,
                      self.mineTex,self.flagMineTex,
                      self.mineTex,self.flagMineTex]
        for place in self.curRange:
            chunk=self.chunkStorage.get(place)
            for xyz in chunk:
                val=self.sweep.board.get(xyz)
                if val in {29,30}:
                    self.removeCube(xyz)
                    self.makeCube(xyz,val)
        self.filter=OnscreenImage(image="resources/dead.png",scale=2)
        self.filter.setTransparency(TransparencyAttrib.MAlpha)
        self.endAttributes.append(self.filter)
        self.endAttributes.append(OnscreenText(
            text='GAME OVER',pos=(0,.3),scale=.3,fg=(1,1,1,1)))
        self.endAttributes.append(OnscreenText(
            text="[R] to restart",pos=(0,.1),scale=.1,fg=(1,1,1,1)))
        self.endAttributes.append(OnscreenText(
            text=f'Final Score: {score}',pos=(0,-0.3),scale=.15,fg=(1,1,1,1)))
        self.endAttributes.append(OnscreenText(
            text=f'Local Highscore: {highscore}',pos=(0,-0.5),scale=.15,
            fg=(1,1,1,1)))

    #uses ray collision to flag a cube
    def flag(self):
        if not (self.gameOver or self.init):
            self.mouseRay.setFromLens(self.camNode,0,0)
            self.mouseTraverser.traverse(self.render)
            if self.mouseQueue.getNumEntries()>0:
                self.mouseQueue.sortEntries()
                name=self.mouseQueue.getEntry(0).getIntoNode().name
                xyz=tuple(map(int,name.split(',')))
                res=self.sweep.flag(xyz)-27
                self.currentCubes[self.mapToCubes[xyz]].setTexture(
                    self.texList[res])

    #load existing game state
    def load(self):
        saveState=open("saves/saveState.txt")
        data=saveState.read().split('#')
        saveState.close()
        global GAME_PROB
        global LIVES
        GAME_PROB=[int(data[0])]
        LIVES=[int(data[1])]
        self.loadPos=list(map(float,data[2].split(', ')))
        self.loadVals=list(map(int,data[3:6]))
        n=int(data[6])
        mapTo={}
        memory=[]
        for i in range(n):
            key,ind=data[7+i].split('$')
            key=tuple(map(int,key.split(', ')))
            mapTo[key]=int(ind)
        for i in range(n):
            memory.append(int(data[7+n+i]))
        self.loadVals+=[mapTo,memory,n]

    #main loop
    def mainTask(self,task):
        #player movement
        game=self.mouseWatcherNode
        dt = min(globalClock.getDt(),1/self.sweeper.limit)
        vf,vb=(game.isButtonDown(key) for key in (KB.space(),KB.shift()))
        vl,vr,vu,vd=(game.isButtonDown(KB.asciiKey(key)) for key in 'adws')
        cl,cr,cu,cd=(game.isButtonDown(key) for key in (KB.left(),KB.right(),KB.up(),KB.down()))
        if (cl+cr)%2:
            self.sweeper.turn((cl-cr)*self.camAccel)
        if (cu+cd)%2:
            self.sweeper.turnUp((cu-cd)*self.camAccel)
        if (vf+vb)%2:
            self.sweeper.accelPar((vf-vb)*self.accel)
        if (vr+vl)%2:
            self.sweeper.accelPerp((vr-vl)*self.accel)
        if (vu+vd)%2:
            self.sweeper.accel3rd((vu-vd)*self.accel)
        self.sweeper.decel(self.ambientDecel)
        coll=[0,0,0]
        if self.collide:
            self.cameraTraverser.traverse(self.render)
            if self.cameraQueue.getNumEntries()>0:
                for entry in self.cameraQueue.getEntries():
                    norm=list(entry.getSurfaceNormal(self.render))
                    absnorm=[abs(i) for i in norm]
                    index=absnorm.index(max(absnorm))
                    sign=2*(norm[index]>0)-1
                    coll[index]=sign
                self.sweeper.dpos([norm[i]*self.bounce for i in range(3)])
        self.sweeper.bounce(coll)
        self.sweeper.move(dt)

        #text
        if self.saveSplash:
            self.saveSplash.setFg((1,1,1,1-self.saveTime))
            self.saveTime+=dt
            if self.saveTime>1:
                self.saveSplash.destroy()
                self.saveSplash=None
        if self.inGameGUI:
            self.displayDist.setText("Distance from origin: "+
                str(euclideanDistance((0,0,0),self.sweeper.pos)/self.size)[0:5])
            self.displayFlags.setText("Number of flags: "+
                str(self.sweep.goodFlags+self.sweep.badFlags))
            self.displayCubes.setText("Cubes uncovered: "+str(self.sweep.cubes))
        
        
        #chunk rendering
        self.chunk=(int((self.sweeper.pos[0]+self.size/2*self.chunkWidth)//
                        (self.size*self.chunkWidth)),
                    int((self.sweeper.pos[1]+self.size/2*self.chunkWidth)//
                        (self.size*self.chunkWidth)),
                    int((self.sweeper.pos[2]+self.size/2*self.chunkWidth)//
                        (self.size*self.chunkWidth)))
        if self.chunk!=self.oldChunk:
            self.curRange=self.draw(self.chunkConditions())
        self.oldChunk=self.chunk

        self.numChunk=(int((self.sweeper.pos[0]+self.size/2*self.numChunkWidth)//
                        (self.size*self.numChunkWidth)),
                       int((self.sweeper.pos[1]+self.size/2*self.numChunkWidth)//
                        (self.size*self.numChunkWidth)),
                       int((self.sweeper.pos[2]+self.size/2*self.numChunkWidth)//
                        (self.size*self.numChunkWidth)))
        if self.numChunk!=self.oldNumChunk:
            self.numCurRange=self.draw(self.numConditions())
        self.oldNumChunk=self.numChunk

        #mouse movement
        if game.hasMouse():
            x,y=game.getMouseX(),game.getMouseY()
            dx,dy=x-self.oldx,y-self.oldy
            self.sweeper.turn(-self.mouseSens*dx)
            self.sweeper.turnUp(self.mouseSens*dy)
        
        self.camera.setPosHpr(self.sweeper.pos[0],self.sweeper.pos[1],
                              self.sweeper.pos[2],self.sweeper.angle,
                              self.sweeper.incline,0)
        
        if self.numRotate:
            for num in self.currentNums:
                if num!=0:
                    num.setHpr(self.sweeper.angle,self.sweeper.incline,0)
                
        self.win.movePointer(0,
            int(self.win.getProperties().getXSize()/2),
            int(self.win.getProperties().getYSize()/2))
        return Task.cont

    #draw a new cube
    def makeCube(self,xyz,num):
        cube=loader.loadModel("resources/cube.egg")
        cube.setScale(self.size/2,self.size/2,self.size/2)
        cube.setPos(self.size*xyz[0],self.size*xyz[1],self.size*xyz[2])
        cube.setTexture(self.texList[num-27])
        coll=cube.attachNewNode(CollisionNode(','.join(map(str,xyz))))
        coll.node().addSolid(CollisionBox((0,0,0),1,1,1))
        coll.node().setIntoCollideMask(BitMask32(3))
        cube.reparentTo(self.render)
        if xyz in self.mapToCubes:
            self.currentCubes[self.mapToCubes[xyz]]=cube
        else:
            self.currentCubes.append(cube)
            self.mapToCubes[xyz]=self.currentN
            self.currentN+=1
            self.cubes+=1
    
    #draw a new number
    def makeNum(self,xyz,num,title=False):
        scale=self.centerScale*self.numSize
        center=loader.loadModel("resources/cube.egg")
        center.setScale(1/self.centerScale,1/self.centerScale,1/self.centerScale)
        center.setPos(self.size*xyz[0],self.size*xyz[1],self.size*xyz[2])
        if num<10:
            start=self.numStart[num]
            shape=self.numShape[num]
            tex=loader.loadTexture(f"resources/col{num}.png")
            aCube=loader.loadModel("resources/cube.egg")
            aCube.setTexture(tex)
            aCube.setScale(scale,scale,scale)
            aCube.setPos(scale*start[0],0,scale*start[1])
            aCube.reparentTo(center)
            for place in shape:
                cube=loader.loadModel("resources/cube.egg")
                cube.setTexture(tex)
                cube.setPos(place[0]*2,0,place[1]*2)
                cube.reparentTo(aCube)
        else:
            a,b=map(int,str(num)[0:2])
            tex=loader.loadTexture("resources/col0.png")
            if title:
                a,b=3,-1
                tex=loader.loadTexture("resources/col3.png")
            starta=self.numStart[a]
            startb=self.numStart[b]
            shapea=self.numShape[a]
            shapeb=self.numShape[b]
            offa=-6*scale
            offb=4*scale
            aCube=loader.loadModel("resources/cube.egg")
            aCube.setTexture(tex)
            aCube.setScale(scale,scale,scale)
            aCube.setPos(scale*starta[0]+offa,0,scale*starta[1])
            aCube.reparentTo(center)
            for place in shapea:
                cube=loader.loadModel("resources/cube.egg")
                cube.setTexture(tex)
                cube.setPos(place[0]*2,0,place[1]*2)
                cube.reparentTo(aCube)
            bCube=loader.loadModel("resources/cube.egg")
            bCube.setTexture(tex)
            bCube.setScale(scale,scale,scale)
            bCube.setPos(scale*startb[0]+offb,0,scale*startb[1])
            bCube.reparentTo(center)
            for place in shapeb:
                cube=loader.loadModel("resources/cube.egg")
                cube.setTexture(tex)
                cube.setPos(place[0]*2,0,place[1]*2)
                cube.reparentTo(bCube)
        center.reparentTo(self.render)
        if title:
            return center
        else:
            if xyz in self.mapToNums:
                self.currentNums[self.mapToNums[xyz]]=center
            else:
                self.currentNums.append(center)
                self.mapToNums[xyz]=self.currentNNum
                self.currentNNum+=1
                self.nums+=1

    def modify(self,direction):
        if self.menu==2:
            global INGAME
            point=self.setpoint
            old=INGAME[point][0]
            new=old+self.settingDelta[point]*direction
            if (new>self.settingLowerBound[point] and
                new<self.settingUpperBound[point]):
                INGAME[point][0]=new
                self.menu2Attributes[2*point].setText('> '+self.msg(point)+' <')

    def msg(self,index):
        if self.isBool[index]:
            return str(bool(INGAME[index][0]))
        return str(INGAME[index][0])[0:4]

    #restart in a new game
    def newGame(self,load):
        if self.gameOver or self.firstStart:
            if self.gameOver:
                self.wipe(self.endAttributes)
                for place in self.curRange:
                    chunk=self.chunkStorage.get(place)
                    for xyz in chunk:
                        self.removeCube(xyz)
                for place in self.numCurRange:
                    numChunk=self.numChunkStorage.get(place)
                    for xyz in numChunk:
                        self.removeNum(xyz)
            
            self.curRange=set()
            self.chunkStorage=Store3D(set(),False,None)
            self.currentCubes=[]
            self.cubes=0
            self.currentN=0
            self.mapToCubes={}
            
            self.numCurRange=set()
            self.numChunkStorage=Store3D(set(),False,None)
            self.currentNums=[]
            self.nums=0
            self.currentNNum=0
            self.mapToNums={}

            self.sweep=Minesweeper(GAME_PROB[0],LOAD_LIMIT[0],load,
                                   self.loadVals if load else [0,0,0])
            self.lives=LIVES[0]
            self.sweeper=Player(self.speed,self.loadPos if load else [0,0,0])
            self.texList=[self.normalTex,self.flagTex,
                      self.normalTex,self.flagTex,
                      self.mineTex,self.flagMineTex]
            if self.inGameGUI:
                self.hearts=[]
                for i in range(self.lives):
                    heart=OnscreenImage(image="resources/heart.png",
                                        pos=(-.95+.16*i,0,-.8),scale=.07)
                    heart.setTransparency(TransparencyAttrib.MAlpha)
                    self.hearts.append(heart)
            self.curRange=self.draw(self.chunkConditions())
            self.numCurRange=self.draw(self.numConditions())
            self.firstStart=False
            self.gameOver=False

    #remove a drawn cube
    def removeCube(self,xyz):
        val=self.mapToCubes[xyz]
        cube=self.currentCubes[val]
        cube.removeNode()
        self.currentCubes[val]=0
        self.cubes-=1

    #remove a drawn number
    def removeNum(self,xyz):
        val=self.mapToNums[xyz]
        num=self.currentNums[val]
        num.removeNode()
        self.currentNums[val]=0
        self.nums-=1

    #save current game state
    def save(self):
        if not (self.gameOver or self.init):
            saveState=open("saves/saveState.txt",'w')
            saveState.write(str(GAME_PROB[0])+'#')
            saveState.write(str(self.lives)+'#')
            saveState.write(str(self.sweeper.pos)[1:-1]+'#')
            saveState.write(str(self.sweep.cubes)+'#')
            saveState.write(str(self.sweep.goodFlags)+'#')
            saveState.write(str(self.sweep.badFlags)+'#')
            saveState.write(str(self.sweep.board.n)+'#')
            for key in self.sweep.board.mapTo:
                saveState.write(str(key)[1:-1]+'$'+
                                str(self.sweep.board.mapTo[key])+'#')
            for val in self.sweep.board.memory:
                saveState.write(str(val)+'#')
            saveState.close()
            if self.saveSplash:self.saveSplash.destroy()
            self.saveTime=0
            self.saveSplash=OnscreenText(text="Game Saved",scale=.2,fg=(1,1,1,1))

    def scroll(self,direction):
        if self.menu==2:
            old=self.setpoint
            new=(old+direction)%len(INGAME)
            self.menu2Attributes[2*new].setText('> '+self.msg(new)+' <')
            self.menu2Attributes[-1].setText(self.settingExp[new])
            self.menu2Attributes[2*old].setText(self.msg(old))
            self.setpoint=new
        
    #start the game for the first time
    def startGame(self,load):
        if self.init and self.menu==1 and load<=self.canLoad:
            self.wipe(self.menu1Attributes)
            self.menu=0
            self.taskMgr.remove("titleTask")
            self.titleNum.removeNode()
            self.titleNum=None
            
            if load:self.load()

            #gameplay
            self.speed=PLAYER_SPEED[0]
            self.accel=1
            self.camAccel=1
            self.collide=DO_COLLIDE[0]
            self.wipeOnDeath=WIPE_ON_DEATH[0]
            self.numRotate=True
            self.bounce=0.5
            self.ambientDecel=0.96
            self.camLens.setFov(CAMERA_FOV[0])
            self.inGameGUI=DISP_GUI[0]

            #render settings
            self.chunk=(0,0,0)
            self.oldChunk=(0,0,0)
            self.chunkSize=CHUNK_SIZE[0]
            self.chunkWidth=2*self.chunkSize+1
            self.renderDistance=RENDER_DIST[0]
            self.numChunk=(0,0,0)
            self.oldNumChunk=(0,0,0)
            self.numChunkSize=NUM_CHUNK_SIZE[0]
            self.numChunkWidth=2*self.numChunkSize+1
            self.numRenderDistance=NUM_RENDER_DIST[0]
            
            #textures/gui
            self.normalTex=loader.loadTexture("resources/normalcube.png")
            self.mineTex=loader.loadTexture("resources/minecube.png")
            self.flagTex=loader.loadTexture("resources/flagcube.png")
            self.flagMineTex=loader.loadTexture("resources/flagmine.png")
            self.saveSplash=None
            self.saveTime=0
            self.cross=OnscreenImage(image="resources/crosshair.png",scale=.02)
            self.cross.setTransparency(TransparencyAttrib.MAlpha)
            if self.inGameGUI:
                self.displayLives=OnscreenText(text='Lives:',
                    pos=(-1.26,-.8),scale=.07,mayChange=1,align=TextNode.ALeft,
                    fg=(1,.7,0,1))
                self.displayFlags=OnscreenText(text='Number of flags: 0',
                    pos=(-1.26,.88),scale=.07,mayChange=1,align=TextNode.ALeft,
                    fg=(1,.7,0,1),bg=(.5,.5,.5,1))
                self.displayCubes=OnscreenText(text='Cubes uncovered: 0',
                    pos=(-1.26,.8),scale=.07,mayChange=1,align=TextNode.ALeft,
                    fg=(1,.7,0,1),bg=(.5,.5,.5,1))
                self.displayDist=OnscreenText(text='Distance from origin: 0',
                    pos=(-1.26,.72),scale=.07,mayChange=1,align=TextNode.ALeft,
                    fg=(1,.7,0,1),bg=(.5,.5,.5,1))
            
            #main loop
            self.firstStart=True
            self.newGame(load)
            self.init=False
            self.taskMgr.add(self.mainTask,"mainTask")

    def switchMenu1(self):
        if self.menu==2:
            self.wipe(self.menu2Attributes)
            self.menu=1
            self.dispMenu1()

    def switchMenu2(self):
        if self.menu==1:
            self.wipe(self.menu1Attributes)
            self.titleNum.removeNode()
            self.titleNum=None
            self.menu=2
            self.dispMenu2()

    #manages 3D rendering in the title menu
    def titleTask(self,task):
        mouse=self.mouseWatcherNode
        if mouse.hasMouse():
            x,y=mouse.getMouseX(),mouse.getMouseY()
            dx,dy=x-self.oldx,y-self.oldy
            if self.titleNum:
                cur=self.titleNum.getHpr()
                self.titleNum.setHpr(cur[0]+self.mouseSens/2*dx,
                                     cur[1]-self.mouseSens/2*dy,0)
        self.win.movePointer(0,
            int(self.win.getProperties().getXSize()/2),
            int(self.win.getProperties().getYSize()/2))
        return Task.cont

    def wipe(self,menuAttr):
        n=len(menuAttr)
        for i in range(n):menuAttr.pop().destroy()

app=Renderer()
app.run()
