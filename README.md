# csb2csd
cocostudio csb反编成csd

建完工程搜了遍才发现已经有大佬实现了[csb2csd](https://github.com/DavidFeng/csb2csd)。可惜在windows系统折腾了几遍竟然没法编译成功(linux上一遍过了)。还是决定自己手撸一个好了。

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


如遇到转换过程报错或转换后格式错误的，欢迎反馈并尽量提供源文件。

## 配置相关
1. `CSParseBinary.fbs` 是基于`cocos/editor-support/cocostudio/fbs-files/CSParseBinary.fbs`，添加了一些其他结构，使用`flatc -p CSParseBinary.fbs`生成库结构，部分坑需要手动修改

2. `header_rule.json`和`child_rule.json`是导出csd的规则配置，其中`header_rule.json`是对应csd中类似`<AbstractNodeData Name="room_bg" ActionTag="-1313931908" Tag="1" ...`这样的格式，`child_rule.json`对应`<AnchorPoint ScaleX="0.5" ScaleY="0.5" />`的格式

   2.1 `header_rule.json`
   以Button为例, 
```
配置
"Button":[
    ["DisplayState", "Displaystate", false, ""],
    ["Scale9Enable", "Scale9Enabled", false, ""],
    ["LeftEage", "CapInsets.X", 0.0, ""],
    ["RightEage", "CapInsets.X", 0.0, ""],
    ["TopEage", "CapInsets.Y", 0.0, ""],
    ["BottomEage", "CapInsets.Y", 0.0, ""],
    ["Scale9OriginX", "CapInsets.X", 0.0, ""],
    ["Scale9OriginY", "CapInsets.Y", 0.0, ""],
    ["Scale9Width", "CapInsets.Width", 0.0, ""],
    ["Scale9Height", "CapInsets.Height", 0.0, ""],
    ["ShadowOffsetX", "ShadowOffsetX", 0.0, ""],
    ["ShadowOffsetY", "ShadowOffsetY", 0.0, ""],
    ["ButtonText", "Text", "", ""],
    ["FontSize", "FontSize", "", ""]
  ],
```
```
对应csd结构
<AbstractNodeData ... DisplayState="True" Scale9Enable="True" LeftEage="15" RightEage="15" 
   TopEage="11" BottomEage="11" Scale9OriginX="15" Scale9OriginY="11" Scale9Width="1" Scale9Height="9" 
   ShadowOffsetX="2" ShadowOffsetY="-2" ButtonText="Test" FontSize="14">
```
```
fbs结构
   table ButtonOptions
   {
       widgetOptions:WidgetOptions;

       normalData:ResourceData;
       pressedData:ResourceData;
       disabledData:ResourceData;
       fontResource:ResourceData;
       text:string;
       fontName:string;
       fontSize:int;
       textColor:Color;
       capInsets:CapInsets;
       scale9Size:FlatSize;
       scale9Enabled:bool;
       displaystate:bool;

       outlineEnabled:bool = false;
       outlineColor:Color;
       outlineSize:int = 1;
       shadowEnabled:bool = false;
       shadowColor:Color;
       shadowOffsetX:float = 2;
       shadowOffsetY:float = -2;
       shadowBlurRadius:int;
       isLocalized:bool = false;
   }
```
`["Scale9OriginY", "CapInsets.Y", 0.0, ""]`第一个为csd的字段名，第二个为根据fbs取值的字段路径, 第三个为默认值，等于默认值的将不写到csd中，第四个为重命名，如`["ProgressType", "Direction", 0, "0=Left_To_Right,1=Right_To_Left"]`就是值为0时，写入csd的是Left_To_Right，1时写入Right_To_Left

   2.2 `child_rule.json` 跟2.1类似
   
   `<Size X="100" Y="100" />`
   ``` fbs
   struct FlatSize
   {
       width:float;
       height:float;
   }
   ```
   `["Size", "Size", "X=Width,Y=Height", ""],` 第一个为csd的字段名，第二个为根据fbs取值的字段路径, 第三个为重命名，即将width的值以键X写入csd，第四个为特殊标记，不赋值的时候会按照fbs的字段格式导出，特殊值目前只有ImageData,代表这是文件路径格式

## 待完成
1. 支持粒子特效、骨骼动画
2. 支持动画曲线的points
3. ……

## 踩过的坑
1. 对比引擎用的CSParseBinary_generated.h和给出的CSParseBinary.fbs，发现fbs中的isLocalized位置有问题需要手动移至最后
2. 九宫格数据Scale9OriginX，Scale9OriginY，Scale9Width，Scale9Height必须是整数否则会解析错误，取出的浮点数要去除小数点和0
3. 编辑器里显示的九宫格用的是LeftEage、RightEage、TopEage、BottomEage，而不是2中的几个字段
4. 字段名不一致容易写错的：

   | fbs字段名   | 编辑器字段  |
   |------------|------------|
   | ClipEnabled | ClipAble  |
   | Scale9Enabled | Scale9Enable  |
   | TouchScaleEnable | TouchScaleChangeAble  |
   
5. flatc导出python时bool类型的默认值未生效，默认值全部都是false，一些默认值为true的会有问题，已手动修改
6. 骨骼动画、粒子特效的结构描述竟然不在CSParseBinary.fbs里面，暂只整合进了SketonNode

