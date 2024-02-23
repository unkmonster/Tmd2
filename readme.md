# Tmd2
Twitter Media Downloader 推特媒体下载器

## 功能

- 下载指定用户的所有媒体 (video, gif, image)
- 以列表为单位批量下载
- 关注中的用户批量下载
- 避免重复下载
- 1. 只会下载自上次运行脚本后用户更新的内容
  2. 当多个 List/Following 包含同一用户，本地只在首个包含此用户的列表目录中保存该用户的推文，其余列表只创建指向该用户目录的快捷方式
  3. 自动更新用户，列表名称，不会造成由用户更改用户/列表名造成的重复下载
- 进度显示
- 并发支持

## 立即使用

1. `git clone https://github.com/unkmonster/Tmd2.git`
1. `CD Tmd2`
1. `pip install -r requirements.txt`

### 首次运行

首次运行 `examples` 目录下的任意脚本需按提示填写配置

![z](https://github.com/unkmonster/Tmd2/blob/master/assets/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202024-02-23%20102915.png)

#### Cookie &  Authorization 获取

1. 使用Chrome 浏览器 打开 https://Twitter.com 
2. 按 `F12`打开开发者控制台
3. 选中`网络`以及 `Fetch/Xhr` 后按 `F5` 刷新网页
4. 左键单击选中列表中任意请求（**并不是每个请求的请求头都一定包含 Cookie 以及 Authorization，如果在当前选中的请求的请求头中没有找到 Cookie 或 Authorization，尝试多换几个试试，会有的**）
5. 在右侧边栏中找到请求标头中的 Cookie 以及 Authorization 双击选中并复制

![屏幕截图 2024-02-23 094641](https://github.com/unkmonster/Tmd2/blob/master/assets/屏幕截图%202024-02-23%20094641.png)

![屏幕截图 2024-02-23 095259](https://github.com/unkmonster/Tmd2/blob/master/assets/屏幕截图%202024-02-23%20095259.png)

### 单用户下载

`python examples\user_download.py 用户名（非昵称）`

>  用户名无需包含 ‘@’

![屏幕截图 2024-02-16 090611](https://github.com/unkmonster/Tmd2/blob/master/assets/屏幕截图%202024-02-16%20090611.png)

### 列表下载

`python examples\list_download.py 列表ID`

![屏幕截图 2024-02-16 090926](https://github.com/unkmonster/Tmd2/blob/master/assets/屏幕截图%202024-02-16%20090926.png)

### 关注用户下载

`python examples\following_download.py 用户名（非昵称）`
