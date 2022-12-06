import numpy as np
import random
import os

class Player:
    def __init__ (self,name):
        self.name = name
        self.score = {}
        path = f'save{self.name}.txt'
        if os.path.exists(path):
            with open(path,'r') as f:
                store_key = None #will odd or even
                for line in f:
                    line = line.strip()
                    if not ',' in line: #getkey
                        self.score[line]= {}
                        store_key = line
                    else:
                        multi_qvalue = [item for item in line.split(',') if ':' in item]
                        small_dict = {}

                        for item in multi_qvalue:
                            nextact,qvalue = item.split(':')
                            small_dict.update({nextact:float(qvalue)})
                        self.score[store_key] = small_dict

        self.last_act = []

    def encode_map(self,map):
        encode = "".join([str(int(item)) for item in list(map.flatten())])
        return encode

    def takeplace(self,map,epsilon,mode):
        old_map = map.copy()

        #check and add score dict base
        old_encode = self.encode_map(old_map)
        if old_encode in self.score:
            pass
        else:
            self.score[old_encode] = {} #create stage dict

        #check availble map
        count_avil = np.count_nonzero(map) #count zeo

        if count_avil == 0: #mean start

            if mode == "Train":
                x = random.randint(0,2)
                y = random.randint(0,2)
                map[x,y] = self.name
                # save last action
                new_encode = self.encode_map(map)
                self.last_act = [old_encode,new_encode]

            elif mode == "TrainEx":
                action_dict = self.score[old_encode]
                encode_idx = None
                try:
                    encodeofmax = max(action_dict, key=action_dict.get)
                    for i in range(len(encodeofmax)):
                        if old_encode[i] != encodeofmax[i]:
                            encode_idx = i
                            break
                    #3x3 map
                    x = encode_idx//3
                    y = encode_idx%3
                    map[x, y] = self.name
                except ValueError:
                    x = random.randint(0, 2)
                    y = random.randint(0, 2)
                    map[x, y] = self.name
                # save last action
                new_encode = self.encode_map(map)
                self.last_act = [old_encode, new_encode]

            else: #check with table score find good start point #play mode
                action_dict = self.score[old_encode]
                encode_idx = None

                encodeofmax = max(action_dict, key=action_dict.get)

                for i in range(len(encodeofmax)):
                    if old_encode[i] != encodeofmax[i]:
                        encode_idx = i
                        break
                #3x3 map
                x = encode_idx//3
                y = encode_idx%3
                map[x, y] = self.name

        elif count_avil < 9: #full of map
            #find a index that still 0
            avil_place = np.argwhere(map==0).tolist()
            if mode == "Train":
                [x,y] = random.choice(avil_place) #random place
                map[x,y] = self.name
                # save last action
                new_encode = self.encode_map(map)
                self.last_act = [old_encode,new_encode]
            elif mode == "TrainEx":
                action_dict = self.score[old_encode]
                encode_idx = None

                try:
                    encodeofmax = max(action_dict, key=action_dict.get)
                    for i in range(len(encodeofmax)):
                        if old_encode[i] != encodeofmax[i]:
                            encode_idx = i
                            break
                    # 3x3 map
                    x = encode_idx // 3
                    y = encode_idx % 3
                    map[x, y] = self.name
                except ValueError:
                    [x, y] = random.choice(avil_place)  # random place
                    map[x, y] = self.name

                # save last action
                new_encode = self.encode_map(map)
                self.last_act = [old_encode, new_encode]
            else: #check with table score
                action_dict = self.score[old_encode]
                encode_idx = None
                encodeofmax = max(action_dict, key=action_dict.get)
                for i in range(len(encodeofmax)):
                    if old_encode[i] != encodeofmax[i]:
                        encode_idx = i
                        break
                # 3x3 map
                x = encode_idx // 3
                y = encode_idx % 3
                map[x, y] = self.name
        else:
            print("End Table")

        #create dict score for action was choosed
        new_encode = self.encode_map(map) #map already update
        if new_encode != old_encode: #action were take
            if new_encode in self.score[old_encode]:
                pass #alreay init
            else:
                self.score[old_encode][new_encode] = 0

        return map,epsilon #update map


    def getmaxfromfuture(self,mapplayeraction):
        future_score_list = []
        for i in range(len(mapplayeraction)): #find max of possible oppponent reaction
            if mapplayeraction[i] == '0':
                if self.name == 1:
                    map_afterresponsebyopponent = mapplayeraction[:i] + str(2) + mapplayeraction[i+1:]
                else:
                    map_afterresponsebyopponent = mapplayeraction[:i] + str(1) + mapplayeraction[i+1:]
                #find max of response
                pos_map_max = max(list(self.score[map_afterresponsebyopponent].values()))
                future_score_list.append(pos_map_max)

        return future_score_list

    def cal_score(self,name,status,old_map,new_map): #win +1 draw 0.1 loss -1
        numcode = self.encode_map(new_map)
        numstagecode = self.encode_map(old_map)

        lr = 0.5
        discountrate = 0.5

        #check if there gane or not
        if status: #mean still in game
            if numstagecode in self.score: #update only own game (only own stage)
                q_current = self.score[numstagecode][numcode]
                try:  # get from future
                    maxfuture_fromaction_value = max(self.getmaxfromfuture(numcode))
                except:  # not have future value yet
                    maxfuture_fromaction_value = 0
                q_current = q_current + lr *(0 + (discountrate*maxfuture_fromaction_value) - q_current)
                print('future reward: '+str(maxfuture_fromaction_value))
                print('q_value in action-stage: '+str(q_current))
                # update score_dict
                self.score[numstagecode][numcode] = q_current
                #fill unaction but possible in game only first time
                for i in range(len(numstagecode)):
                    if numstagecode[i] == '0':
                        # check that if this point action is in the dict or not
                        assume_stage = numstagecode[:i] + str(self.name) + numstagecode[i + 1:]
                        if assume_stage in self.score[numstagecode]:
                            pass
                        else:
                            print(assume_stage)
                            self.score[numstagecode][assume_stage] = 0  # init qvalue
        else: #endgame
            #draw case then find a winner
            if np.count_nonzero(new_map) == 9:
                #update both
                if name == self.name: #mean cuurent player
                    q_current = self.score[numstagecode][numcode]
                    try:  # get from future
                        maxfuture_fromaction_value = max(self.getmaxfromfuture(numcode))
                    except:  # not have future value yet
                        maxfuture_fromaction_value = 0

                    q_current = q_current + lr * (0.1 + (discountrate * maxfuture_fromaction_value) - q_current)
                    # update score_dict
                    self.score[numstagecode][numcode] = q_current
                elif name != self.name: #mean prev player
                    numstagecode = self.last_act[0]
                    numcode = self.last_act[1]
                    q_current = self.score[numstagecode][numcode]
                    try:  # get from future
                        maxfuture_fromaction_value = max(self.getmaxfromfuture(numcode))
                    except:  # not have future value yet
                        maxfuture_fromaction_value = 0
                    q_current = q_current + lr * (0.1 + (discountrate * maxfuture_fromaction_value) - q_current)
                    # update score_dict
                    self.score[numstagecode][numcode] = q_current

            else: #mean have a winner
                if name == self.name:  # mean winner
                    q_current = self.score[numstagecode][numcode]
                    try:  # get from future
                        maxfuture_fromaction_value = max(self.getmaxfromfuture(numcode))
                    except:  # not have future value yet future of winner
                        maxfuture_fromaction_value = 0
                    q_current = q_current + lr * (1 + (discountrate * maxfuture_fromaction_value) - q_current)
                    # update score_dict
                    self.score[numstagecode][numcode] = q_current
                elif name != self.name:  # mean loss use prev action to update score
                    numstagecode = self.last_act[0]
                    numcode = self.last_act[1]
                    q_current = self.score[numstagecode][numcode]
                    try:  # get from future
                        maxfuture_fromaction_value = max(self.getmaxfromfuture(numcode))
                    except:  # not have future value yet future of loss is loos
                        maxfuture_fromaction_value = 0
                    q_current = q_current + lr * (-1.2 + (discountrate * maxfuture_fromaction_value) - q_current)
                    print('loss q: ' + str(q_current))

                    #update score_dict
                    self.score[numstagecode][numcode] = q_current


    def train(self,map,epsilon,mode='exploit'):
        storemap = map.copy()
        print(f'player {self.name} choose')
        if mode == 'explore':
            new_map,new_esp = self.takeplace(storemap,epsilon,"Train")
        else:
            new_map, new_esp = self.takeplace(storemap, epsilon, "TrainEx")
        print(new_map)
        return new_map,new_esp

    def play(self,map,epsilon):
        storemap = map.copy()
        print(f'player {self.name} choose')
        new_map,new_esp = self.takeplace(storemap,epsilon, mode='play')
        print(new_map)
        return new_map

class Board:
    def __init__(self):
        self.map = np.zeros((3,3)).astype(np.int8)
        self.start = True
        self.player1 = Player(1)
        self.player2 = Player(2)
        self.epsilon = 0.2


    def check_winstatus(self,map):
        # check with number
        name_player = None
        game_status = self.start
        # loop to check all 1 case
        # hor case
        if game_status:
            for i in range(3):
                select_map = map[i, :]
                if select_map.sum() == 3 and not 0 in select_map:  # player 1 win
                    name_player = 1
                    game_status = False
                    break
                elif select_map.sum() == 6 and not 0 in select_map:  # player 2 win
                    name_player = 2
                    game_status = False
                    break
        # ver case
        if game_status:
            for i in range(3):
                select_map = map[:, i]
                if select_map.sum() == 3 and not 0 in select_map:  # player 1 win
                    name_player = 1
                    game_status = False
                    break
                elif select_map.sum() == 6 and not 0 in select_map:  # player 2 win
                    name_player = 2
                    game_status = False
                    break
        # cross case
        if game_status:
            for i in range(3):  # only 2 check due to 4corners
                if i == 0:  # top left
                    list_value = []
                    locki = i
                    for j in range(3):
                        list_value.append(map[locki, j])
                        locki += 1

                        if len(list_value) == 3:  # dynamic size of table
                            if sum(list_value) == 3 and not 0 in list_value:  # player 1 win
                                name_player = 1
                                game_status = False
                                break
                            elif sum(list_value) == 6 and not 0 in list_value:  # player 2 win
                                name_player = 2
                                game_status = False
                                break
                elif i == 2:  # botton left
                    list_value = []
                    locki = i
                    for j in range(3):
                        list_value.append(map[locki, j])
                        locki -= 1
                        if len(list_value) == 3:  # dynamic size of table
                            if sum(list_value) == 3 and not 0 in list_value:  # player 1 win
                                name_player = 1
                                game_status = False
                                break
                            elif sum(list_value) == 6 and not 0 in list_value:  # player 2 win
                                name_player = 2
                                game_status = False
                                break

        # all draw case
        if game_status:
            if np.count_nonzero(map) == 9:
                game_status = False
                print('draw case')

        return name_player, game_status

    def train(self,eporch):
        sum_explore = 0
        sum_exploit = 0
        decay_rate = 1/eporch
        for i in range(eporch):
            if self.epsilon > random.uniform(0, 1): #exploit epsilon limit to zero or every 100 game
                print('Exploit mode')
                while self.start:
                    map,self.epsilon = self.player1.train(self.map,self.epsilon)
                    name,self.start = self.check_winstatus(map)
                    self.player1.cal_score(name, self.start,self.map,map)
                    self.player2.cal_score(name, self.start, self.map, map)
                    self.map = map
                    print('end player1 train')
                    if not self.start: #player 1 win
                        if name:
                            print('player'+str(name)+' win')
                        else:
                            print('Draw')
                        break

                    map,self.epsilon = self.player2.train(self.map,self.epsilon)
                    name, self.start = self.check_winstatus(map)
                    self.player1.cal_score(name, self.start, self.map, map)
                    self.player2.cal_score(name, self.start, self.map, map)
                    self.map = map
                    print('end player2 train')
                    if not self.start: #player 2 win
                        if name:
                            print('player' + str(name) + ' win')
                        else:
                            print('Draw')
                        break
                #update greeddy
                self.epsilon = self.epsilon-(decay_rate*self.epsilon)
                sum_exploit += 1
            else: #explore
                print('Explore mode')
                while self.start:
                    map,self.epsilon = self.player1.train(self.map,self.epsilon,mode='explore')
                    name,self.start = self.check_winstatus(map)
                    self.player1.cal_score(name,self.start,self.map,map)
                    self.player2.cal_score(name, self.start, self.map, map)
                    self.map = map
                    print('end player1 train')
                    if not self.start: #player 1 win
                        if name:
                            print('player'+str(name)+' win')
                        else:
                            print('Draw')
                        break

                    map,self.epsilon = self.player2.train(self.map,self.epsilon,mode='explore')
                    name, self.start = self.check_winstatus(map)
                    self.player1.cal_score(name, self.start, self.map, map)
                    self.player2.cal_score(name, self.start, self.map, map)
                    self.map = map
                    print('end player2 train')
                    if not self.start: #player 2 win
                        if name:
                            print('player' + str(name) + ' win')
                        else:
                            print('Draw')
                        break
                sum_explore += 1
            print(f'epoch {i} done.')
            #init new game
            self.map = np.zeros((3, 3)).astype(np.int8)
            self.start = True
        print('All Explore eporch: '+str(sum_explore))
        print('All Exploit eporch: ' + str(sum_exploit))
        print(self.epsilon)

    def play(self):
        self.map = np.zeros((3, 3)).astype(np.int8)
        print('Game Start!!')
        print(self.map)
        while self.start:
            map = self.player1.play(self.map,self.epsilon)
            name, self.start = self.check_winstatus(map)
            self.map = map
            if not self.start:  # player 1 win
                if name:
                    print('player' + str(name) + ' win')
                else:
                    print('Draw')
                break

            map = self.player2.play(self.map,self.epsilon)
            name, self.start = self.check_winstatus(map)
            self.map = map
            print('end player2 turn')
            if not self.start:  # player 1 win
                if name:
                    print('player' + str(name) + ' win')
                else:
                    print('Draw')

                break
        print('End Game')
        with open('save1.txt','w') as f:
            for key,value in self.player1.score.items():
                f.write(f'{key}\n')
                long_str = []
                for subkey,qvalue in value.items():
                    long_str.append(f'{subkey}:{qvalue},')
                long_str.append('\n')
                long_text = "".join(long_str)
                f.write(long_text)
        with open('save2.txt','w') as f:
            for key,value in self.player2.score.items():
                f.write(f'{key}\n')
                long_str = []
                for subkey,qvalue in value.items():
                    long_str.append(f'{subkey}:{qvalue},')
                long_str.append('\n')
                long_text = "".join(long_str)
                f.write(long_text)

    def buildgame(self):
        num_play = input('Choose 1 or 2 player: ')
        num_play =int(num_play)

        self.map = np.zeros((3, 3)).astype(np.int8)
        print('Game Start')
        print(self.map)
        while self.start:
            if num_play == 1:
                xy = input('Place location(x,y): ')
                x,y = xy.split(',')
                x,y = int(x),int(y)
                self.map[x,y]=1
                print(self.map)
                #check win con
                name, self.start = self.check_winstatus(self.map)
                if not self.start:  # player 1 win
                    if name:
                        print('player' + str(name) + ' win')
                    else:
                        print('Draw')
                    break
                #bot play
                self.map = self.player2.play(self.map, self.epsilon)
                #check wincon
                name, self.start = self.check_winstatus(self.map)

                if not self.start:  # player 2 win
                    if name:
                        print('player' + str(name) + ' win')
                    else:
                        print('Draw')
                    break
            else:
                self.map = self.player1.play(self.map, self.epsilon)
                name, self.start = self.check_winstatus(self.map)
                if not self.start:  # player 1 win
                    if name:
                        print('player' + str(name) + ' win')
                    else:
                        print('Draw')
                    break
                xy = input('Place location(x,y): ')
                x, y = xy.split(',')
                x, y = int(x), int(y)
                self.map[x, y] = 2
                print(self.map)
                # check win con
                name, self.start = self.check_winstatus(self.map)
                if not self.start:  # player 1 win
                    if name:
                        print('player' + str(name) + ' win')
                    else:
                        print('Draw')
                    break

        print('Game end..')
#Run Hera
game = Board()
# game.train(500000) #50k game is smart enough
# game.play()
game.buildgame()