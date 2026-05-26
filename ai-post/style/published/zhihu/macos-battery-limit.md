# 基于 smcFanControl，优雅地限制 MacOS 电池充电上限

**作者**: Lord包包  
**身份**: 诺丁汉大学 电气工程博士在读  
**专栏**: 好奇与折腾  
**赞同**: 3 人  
**发布日期**: 2023年3月10日

---

## 目录

## 设备信息

- MacOS Big Sur 11.7.4
- Macbook pro 2019 (intel)

## 常见解法

### smcFanControl

为了限制 Macos充电上限，中文互联网上常见的方法往往是借助于开源工具 smcFanControl。

**安装步骤**:

1. 确保安装了Xcode commandline tools
2. `git clone https://github.com/hholtmann/smcFanControl.git`
3. `cd smcFanControl/smc-command`
4. `make`
5. `sudo ./smc -k BCLM -w 4D`（注：最后的值为充电限制的16进制值，必须小于64）
6. `./smc -k BCLM -r`（查看当前的设置）

**说明**:

- 比如设置：`sudo ./smc -k BCLM -w 32`，表示充电限制为50%
- 若你当前电量超过了50%就会停止充电，若低于50%就会充电至50%
- macbook电量百分比一般会标的高一点，比如设置为4D（77），实际电量会停在80%
- 恢复默认设置方法：`sudo ./smc -k BCLM -w 64`

### AlDente

要收钱，而且更加臃肿，直接pass。

## 次优解

基于 smcFanControl，可以简单写一个 shell 脚本，并设置为开机自启，实现自动化。

为了免去每次运行都要输密码，可以用管道实现自动输入密码：

```bash
echo [your passwd] |sudo -S [command]
```

为了提高可扩展性，在同文件夹下创建 `password.txt`，记录自己的管理员密码：

```bash
echo [your passwd]>./password.txt
```

然后用 `cat` 命令输出文档中的密码：

```bash
echo $(cat ./password.txt) |sudo -S [command]
```

用 `work_path=$(dirname $0)` 替换 `.`，整理为 shell 脚本：

```bash
#!/bin/sh
work_path=$(dirname $0)
echo $work_path
echo $(cat $work_path/password.txt) |sudo -S ~/smcFanControl/smc-command/smc -k BCLM -w 50
exit
```

## 优化

然而正如 smcFanControl 仓库 readme 首段所说，它是一个风扇控制工具，而不是电量控制工具：

> smcFanControl lets the user set a minimum speed for built-in fans. It allows you to increase your minimum fan speed to make your Intel Mac run cooler. In order to not damage your machine, smcFanControl does not let you set a minimum speed to a value below Apple's defaults.

尽管 smcFanControl 也只有 2.9 MB，但也留下了碍眼的风扇控制（我才不愿意被创造需求呢doge），很难看。

何不如直接把用到的可执行文件 `smc` 拎出来？

于是看着不顺眼的 smcFanControl 也可以删掉了：

```bash
brew uninstall smcfancontrol
```

**优化后的脚本**:

```bash
#!/bin/sh
work_path=$(dirname $0)
echo $work_path
echo $(cat $work_path/password.txt) |sudo -S $work_path/smc -k BCLM -w 50
exit
```

---

**本文写于**: 2023年3月10日

**标签**: macOS
