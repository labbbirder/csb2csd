# csb2csd
cocostudio csb反编成csd, forked from [lyzz0612/csb2csd](https://github.com/lyzz0612/csb2csd).

建议使用dev分支，master用来pr。dev分支在多个真实项目上测试通过。

## 使用说明
命令行输入：
```shell
$ python cli.py -h
```
输出：
```
usage: cli.py [-h] [-d] [-m] [-r {keep,cocos,blank,drop}] [-c {all,ref,no}]
              [-s SEARCH_PATH [SEARCH_PATH ...]] [-n]
              input output

反编译cocostudio的csb文件

positional arguments:
  input                 输入的csb文件或目录
  output                输出目录

optional arguments:
  -h, --help            show this help message and exit
  -d, --output-dependency
                        output information of dependencies to dependence.json
  -m, --output-missing-reference
                        output information of missing references to
                        missing.json
  -r {keep,cocos,blank,drop}, --refill {keep,cocos,blank,drop}
                        what to do with the missing references, especially the
                        image file. 'keep' is to let it be, 'cocos' is to
                        replace it with default resource of cocostudio,
                        'blank' is to replace it with a transparent image.
                        default is 'keep'.
  -c {all,ref,no}, --copy {all,ref,no}
                        which files in folder should be copied besides csd.
                        'all' means whatever, 'ref' means only those
                        referenced, 'no' means csd only. default is 'all'.
  -s SEARCH_PATH [SEARCH_PATH ...], --search-path SEARCH_PATH [SEARCH_PATH ...]
                        additional paths to search the missing references
  -n, --name-fix        rename the nodes whose name is illegal in lua.
```
输入可以是单个文件，也可以是一个目录。输出需要指定一个目录。

`-d` 表示输出资源依赖数据，可以用来分析资源依赖结构、自动划分图集等

`-m` 表示输出缺失资源数据，方便后期补图。

`-r` 如何处理缺失的资源。keep不处理，cocostudio导出时会报告资源丢失；cocos表示使用Default资源代替；blank使用一张透明图片代替原本位置；drop去掉缺图资源。默认是keep。

`-c` 复制哪些资源。all表示输入目录内的所有资源；ref只复制csd中引用到的资源，可以减少资源数量；no表示只处理csb，不复制其他资源。默认是all。

`-s` 找不到资源时，备用的搜索路径。适用于原工程设置了search_path的情况。

`-n` 重命名有非法lua名称的节点，不使用此命令会导致“01”等名称的节点导出lua失败。

## 例子
导出测试用资源：
```shell
$ python cli.py test out #只生成csd文件
```
```shell
$ # 只复制用到的素材，修复非法变量名，如果找不到素材，则到"path_to_cocostudio/images"
$ # 和"path_to_cocostudio/images_another"中再次查找，用默认素材代替缺失素材。
$ python cli.py --search-path "path_to_cocostudio/images" "path_to_cocostudio/images_another" \
--copy ref --name-fix --refill cocos path_to_cocostudio path_to_output
```

你将在out目录下看到生成的设计文件
