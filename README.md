# ZhihuCrawler
爬取知乎所有用户信息~仅供学习使用



#### 技术栈

* 支持账号池，多账号轮流爬取信息，登录参考[zhihu-py3](https://github.com/7sDream/zhihu-py3) 
* 社交关系爬取采用BFS，沿着关注关系爬取
* 采用redis存储搜索队列，支持断点续爬
* 采用mongodb存储用户信息
* 采用elasticsearch，kibana做数据分析(待完成)



#### 使用方式

* git clone https://github.com/happyfarmergo/ZhihuCrawler.git
* cd ZhihuCrawler
* python Zhihu.py



具体参考我的博客: [happyfarmer](http://www.happyfarmergo.xyz/)



