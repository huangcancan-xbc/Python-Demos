# 导入所需模块：requests用于网络请求，BeautifulSoup用于解析网页
import requests
from bs4 import BeautifulSoup

# 请求头：模拟浏览器访问，避免被豆瓣反爬识别
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

top = 1

with open("爬虫——豆瓣电影top250.txt", "w", encoding="utf-8") as f:
    # 遍历豆瓣Top250的10页数据（每页25条，start参数从0到225）
    for index in range(0, 250, 25):
        # 发送GET请求获取单页数据
        response = requests.get(f"https://movie.douban.com/top250?start={index}&filter=", headers = headers)
        # print(response) # 打印响应内容
        # print(response.status_code) # 打印响应状态码

        html = response.text        # 提取网页文本内容
        soup = BeautifulSoup(html, "html.parser")   # 解析网页内容（使用html.parser解析器）
        alltitles = soup.findAll("span", attrs={"class": "title"})  # 查找所有class为title的span标签（包含电影名称）
        
        # 遍历所有找到的标题，筛选纯中文标题（排除含/的外文标题）
        for title in alltitles:
            title_string = title.string
            # 过滤掉外文标题（含/的是外文别名）
            if "/" not in title_string:
                print(title_string)  # 控制台打印电影名
                f.write(f"豆瓣电影top{top}: {title_string}\n")  # 写入文件
                top += 1  # 排名自增