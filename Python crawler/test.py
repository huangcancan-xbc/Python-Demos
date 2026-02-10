print("hello Python Crawler！")


print("Let\'s go'\ngogogo!")


print("""君不见，黄河之水天上来，奔流到海不复回。
君不见，高堂明镜悲白发，朝如青丝暮成雪。
人生得意须尽欢，莫使金樽空对月。""")


message = "hello "
print(message + "minbit")
print(type(message))


import math
a = 3; b = 4
print("第三边长是" + str(math.sqrt(a**2 + b**2)))


# BMI = 体重 / (身高 ** 2)
user_height = float(input("请输入您的身高(m)："))
user_weight = float(input("请输入您的体重(kg)："))
BMI = user_weight / (user_height ** 2)
print("您的BMI指数为：" + str(BMI))


index = int(input("请输入今天的心情指数："))
if index < 10:
    print("今天心情不好，奖励自己玩一天游戏")
elif index < 50:
    print("今天心情一般，努力学习")
else:
    print("今天心情很好，大吃特吃一顿！")


list = []
print(list)
list.append("a")
list.append("你好")
list.append(123)
print(list)
print(list[1])


vector = [1, 5, 2, 4, 6, 8, 3, 7]
print("当前的最大值：" + str(max(vector)) + "，当前的最小值：" + str(min(vector)))
sorted_vector = sorted(vector)
print("排序后的列表：" + str(sorted_vector))
hash_map = { "key":"value",
             "name":"minbit",
             "minbit":"2025",
             "小米里的大麦":"YYDS"}
k = input("请输入要查询的键：")
if k in hash_map:
    print(hash_map[k])
else:
    print("键不存在！")
