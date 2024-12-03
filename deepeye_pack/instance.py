"""
此文件定义了ViewPosition和Instance两个类：
ViewPosition类是用于枚举的辅助类，只有table_pos和view_pos两个数据成员，记录了一个图表对应的table的位置(table_pos)，
以及该图表在view列表中的位置
Instance类主要实现了对每个图表评分的工作，其中的getM, getW函数实现了论文中M值的归一化和W值的计算(注意：M值的计算位于
view.py文件中的getM函数)。随后机器学习排序算法通过加载相应的模型文件对图表进行评分，偏序关系排序算法通过论文中的图算法
对图表进行评分，这些评分功能分别在getScore_learning_to_rank和getScore函数中实现。
"""


import os
import time
from .features import Type

class ViewPosition(object):
    """
    Attributes:
        table_pos(int): the index of the table in the table list.
        view_pos(int): the index of the view in the view list.
    """
    def __init__(self, table_pos, view_pos):
        self.table_pos = table_pos
        self.view_pos = view_pos

class Instance(object):
    """
    Attributes:
        table_name(str): the name of the table corresponding to this instance.
        column_num(int): the number of columns.
        tuple_num(int): the number of columns after transformation.
        table_num(int): the number of tables after transformation.
        view_num(int): the number of views.
        tables(list): the list of tables.
        views(list): the list of views.
    """
    def __init__(self, table_name):
        self.table_name = table_name
        self.column_num = self.tuple_num = 0 # the number of the column and row of the original data
        self.table_num = self.view_num = 0
        self.tables = []
        self.views = []

    def addTable(self, table):
        self.tables.append(table)
        self.table_num += 1

    def addTables(self, tables):
        for table in tables:
            self.addTable(table)

    def getM(self):
        """
        Normalize M value: M(v) = M(v) / maxM
        (note: The calcualtion of M value is in the getM function of class View in view.py file)

        Args:
            None
            
        Returns:
            None
            
        """
        max_M = [0, 0, 0, 0] # 4 elements: pie, bar, scatter, line
        for table in self.tables: # to gain max_M
            for view in table.views:
                if view.M > max_M[view.chart]:
                    max_M[view.chart] = view.M
        for table in self.tables:
            for view in table.views:
                if max_M[view.chart] == 0:
                    view.M = 0
                else:
                    view.M = 1.0 * view.M / max_M[view.chart]
    
    def getW(self):
        """
        calculate W value in the paper

        Args:
            None
            
        Returns:
            None
            
        """
        if self.view_num == 0:
            return
        weight = [0 for i in range(self.column_num)]
        for table in self.tables:
            for view in table.views:
                weight[view.fx.origin] += 1
                weight[view.fy.origin] += 1
                if view.z_id != -1: # for 3D views
                    weight[view.z_id] += 1
        for i in range(self.column_num):
            weight[i] = 1.0 * weight[i] / self.view_num
        for table in self.tables:
            for view in table.views:
                view.W = weight[view.fx.origin] + weight[view.fy.origin]
                if view.z_id != -1:
                    view.W += weight[view.z_id]
        max_W = -1
        for table in self.tables:
            for view in table.views:
                if view.W > max_W:
                    max_W = view.W
        for table in self.tables:
            for view in table.views:
                view.W = view.W / max_W
    
    def getScore_learning_to_rank(self):
        """
        For learning_to_rank method, get score of each view and write to files

        Args:
            None
            
        Returns:
            None
            
        """
        path = os.path.dirname(__file__) # 此份代码的目录
        path2 = os.getcwd() + '/data/' # 运行python程序的目录
        if not os.path.exists(path2):
            os.mkdir(path2)
        f = open(path2 + self.table_name + '.ltr','w') #ltr = learn to rank
        for i in range(self.table_num):
            self.views.extend([ViewPosition(i,view_pos) for view_pos in range(self.tables[i].view_num)])
        for i in range(self.table_num):
            for j in range(self.tables[i].view_num):
                view = self.tables[i].views[j]
                f.write(view.output_score()+'\n')
        f.close()
        #create '.ltr' and '.score' file
        cmd = 'java -jar "'+path+'/jars/RankLib.jar" -load "'+path+'/jars/rank.model" -rank "'+ path2 + self.table_name+'.ltr" -score "'+ path2 + self.table_name + '.score"'
        os.popen(cmd)
        a = time.time()
        while not os.path.exists(path2 + self.table_name + '.score') and time.time() - a < 60:
            pass
        time.sleep(1)
        if os.path.exists(path2 + self.table_name + '.score'):
            f = open(path2 + self.table_name + '.score')
            i = 0
            line = f.readline() #read '.score' file and store the scores
            while line:
                self.tables[self.views[i].table_pos].views[self.views[i].view_pos].score = float(line.split()[-1])
                line = f.readline()
                i += 1
            f.close()
        else:
            print("Score file not found. You may run the program again to get the result.")
        #sort by scores
        self.views.sort(key=lambda view:self.tables[view.table_pos].views[view.view_pos].score,reverse=True)

    #for partial_order rank
    def getScore(self):
        """
        For partial_order method, get score of each view

        Args:
            None
            
        Returns:
            None
            
        """
        for i in range(self.table_num):
            self.views.extend([ViewPosition(i,view_pos) for view_pos in range(self.tables[i].view_num)])
        G = [[-1 for i in range(self.view_num)] for j in range(self.view_num)]
        out_edge_num = [0 for i in range(self.view_num)]
        score = [0 for i in range(self.view_num)]
        for i in range(self.view_num):
            for j in range(self.view_num):
                if i != j:
                    view_i = self.tables[self.views[i].table_pos].views[self.views[i].view_pos]
                    view_j = self.tables[self.views[j].table_pos].views[self.views[j].view_pos]
                    if view_i.M >= view_j.M and view_i.Q >= view_j.Q and view_i.W >= view_j.W:
                        if view_i.M == view_j.M and view_i.Q == view_j.Q and view_i.W == view_j.W:
                            continue
                        G[i][j] = (view_i.M - view_j.M + view_i.Q - view_j.Q + view_i.W - view_j.W) / 3.0
                        out_edge_num[i] += 1
        for remove_time in range(self.view_num-1):
            for i in range(self.view_num):
                if out_edge_num[i] == 0:
                    for j in range(self.view_num):
                        if G[j][i] >= 0:
                            score[j] += G[j][i] + score[i]
                            G[j][i] = -1
                            out_edge_num[i] = -1
                            out_edge_num[j] -= 1
                    break
        for i in range(self.view_num):
            self.tables[self.views[i].table_pos].views[self.views[i].view_pos].score = score[i]
            # print(i)
            # print("M =", self.tables[self.views[i].table_pos].views[self.views[i].view_pos].M)
            # print("Q =", self.tables[self.views[i].table_pos].views[self.views[i].view_pos].Q)
            # print("W =", self.tables[self.views[i].table_pos].views[self.views[i].view_pos].W)
            # print("score:", score[i])
        #sort by scores
        self.views.sort(key=lambda view:self.tables[view.table_pos].views[view.view_pos].score,reverse=True)
        # for i in range(self.view_num):
        #     print("score[i], ", self.tables[self.views[i].table_pos].views[self.views[i].view_pos].score)
