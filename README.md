# OHTTPS_TO_DogeCloud
使用OHTTPS的WebHook功能自动更新DogeCloud的证书

白嫖党肯定都知道DogeCloud吧，他可以提供免费的20G CDN流量，其中节点基本全是腾讯云的，用着是丝毫不拉胯，那么我们就可以通过OHTTPS的WebHook来自动部署，只不过这个就需要我们通过DogeCloud的API来自己写接口了。
人生苦短，我选择Python，官方提供的Python的SDK非常全面，完全足够我们写一个自动更新证书出来
先说用到了什么东东
Python 3.11.1
FastAPI
Uvicorn
DogeCloud API
MySQL
主要就是这些，MySQL主要是记录当前使用证书的ID，其实也可以通过API去查询需要替换证书的一堆域名中的一个域名绑定的ID也可以，这样就省去了MySQL，但是如果这个域名某天不用了，那就需要修改源代码了，所以我用了数据库，数据库只有一个字段ID，存的就是DogeCloud证书的ID，更新完域名证书之后再把数据库里面的ID改成最新的就可以了

启动方法
```
uvicorn main:app --host="0.0.0.0" --port=5543 --reload
```
其中host是IP，如果回环设置为127.0.0.1无法在公网访问，这个是需要让OHTTPS去访问的，所以是0.0.0.0，port为端口号，记得在防火墙打开
可以使用Supervisor来守护进程，我使用的是宝塔面板的进程管理器来运行的
