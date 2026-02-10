# 文件操作

f = open("test.py", "r", encoding="utf-8")
print(f.read())
f.close()


f = open("test.txt", "w", encoding="utf-8")
for i in range(3):
    f.write("hello Python Crawler！\n")
    f.write("Let\'s go'\ngogogo!\n")
f.close()
f = open("test.txt", "r", encoding="utf-8")
for line in f:  # 读取每行
    print(f.read())  # 读取一行
f.close()


count = 0
# with是Python的上下文管理器，可以自动关闭文件，as表示取别名（相当于进行赋值）
with open("test1.txt", "w", encoding = "utf-8") as ff:
    for i in range(20):
        ff.write(f"这是第{count}行\n")
        count += 1
with open("test1.txt", "r", encoding = "utf-8") as ff:
    line = ff.readline()
    while line != "":
        print(line)           # 优化：strip()去掉换行符，输出更整洁
        line = ff.readline()  # 关键修复：读取下一行，避免死循环
