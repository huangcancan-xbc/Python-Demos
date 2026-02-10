# 定义一个学生类
# 要求：
# 1. 属性包括学生姓名、学号，以及语数英三科的成绩
# 2. 能够设置学生某科目的成绩
# 3. 能够打印出该学生的所有科目成绩


class student:
    def __init__ (self, name, id):
        self.name = name
        self.id = id
        self.score = {'语文': 0, '数学': 0, '英语': 0}

    def set_score(self, course, score):
        if course in self.score:
            self.score[course] = score
        else:
            print('课程不存在！')

    def print_score(self):
        print(f"学生：{self.name}, 学号id：{self.id}, 他的成绩如下：")
        for course, score in self.score.items():
            print(f"{course}：{score}")

xxx = student("张三", 12345)
xxx.set_score('语文', 90)
xxx.set_score('数学', 85)
xxx.set_score("语文", 66)
xxx.print_score()
yyy = student("李四", 54321)
yyy.set_score('英语', 95)
yyy.print_score()