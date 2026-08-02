---
platform: wechat
slug: tone-chord-lab
published: 2026-08-02
title: 校音器只认单音？我从零写了个能看频谱、能认和弦的网页
---

# 校音器只认单音？我从零写了个能看频谱、能认和弦的网页

## 给乐器校个音，凭什么要先装个 App

要给吉他、钢琴、小提琴这些乐器校音，市面上的路数一般是：应用商店搜"调音器"，下载，注册，可能还要订阅。我只是想确认一下空弦准不准，却被要求先交一串个人信息。这不该是一个校音器该有的样子——校音是件很轻的小事，它就该打开网页、对准麦克风、立刻能用，而不是先付出一整套安装的代价。

所以我给自己写了一个：https://tone.mingyangbao.site/。打开就能给乐器校音，不用装 App、不用注册、音频全程留在本地。它还不止是校音器——弹和弦它能认出和弦，吹奏时它能画出实时频谱，压音滑动它追得上。吉他、钢琴、小提琴、口琴，一个网页全都能校。

这个网站的缘起，要从每天早晚从家到实验室的十几分钟里长出来的。

## 🎵 从家到实验室的十几分钟

每天从家走到实验室，有十几分钟没事干。别人刷短视频，我掏出布鲁斯口琴边走边练——拿自己的步伐当节拍器，一步一个四分音符，正好卡上拍子。路上练不了什么难的，压音（bend）这种不需要双手配合的活刚好合适。

最近我在练压音，把 C 孔那个音往下压小半度，再滑回原位。动作看着简单，麻烦的是：光靠耳朵，我根本分不清压出来的音是偏高、偏低，还是已经准准落在目标音上。新手耳朵靠不住，得找个校音工具帮我看一眼。

可我连校音 App 都不想下载。校音是件很轻的小事，我想要它尽可能轻便——在家用电脑打开网站，走到路上手机也能打开，随开随用。更何况一般的校音 App 和网站都只认单音，识别不了和弦；作为工科学生，我还想看看实时频谱。这几条加在一起，市面上的工具没一个能满足我。

所以我自己写了一个。

写着写着我就发现，它绝不该只给口琴用。吉他、钢琴、小提琴，泛音结构各不相同，可校音这个需求是共通的。最后它成了一个所有乐器通用的网页校音器：口琴是我的第一个用户，但不是唯一用户。

## 🔧 先用起来：三步，不装 App

别急着看原理，先玩三分钟。

1. 手机或电脑浏览器打开 https://tone.mingyangbao.site/
2. 点一下"启用麦克风"，在浏览器弹窗里选"允许"
3. 对着你的乐器吹奏或弹奏

吉他扫一根弦看音准，钢琴按下琴键看音名和 cent，小提琴拉弓看音高跟着走；吹口琴时能看实时频谱，弹个和弦它能整个认出来——校音器认不了和弦，这个认。音频全程留在本地，我保证它不会上传到任何地方。整个流程没有任何一步需要下载、登录或付费，手机和电脑的浏览器都行。

## 💡 我踩过的三个坑，都变成了设计

下面这段有代码。不用紧张，每段我都会先讲我为什么需要它。

### 坑一：泛音丰富的乐器，把 G 显示成 D

吉他、钢琴、口琴这类乐器泛音都很丰富，前几个分音往往比基频还响。校音器会锁住最响的那个峰，于是你弹 G，它告诉你这是 D——因为 D 正好是 G 的五度泛音。这个 bug 在各类校音器的差评里反复出现，我练琴第一天就撞上了。

我的解法是次谐波惩罚：打分时检查，如果某个候选频率的 1/2、1/3、1/4、1/5 处也有强峰，说明它大概率只是个泛音，得降权。真正干活的代码长这样：

```js
// dsp.js —— 次谐波惩罚：候选 f0 的分频处有强峰，说明它多半是泛音
let subharmonicPenalty = 0;
const divisors = [2, 3, 4, 5];
const divisorWeights = [0.85, 0.68, 0.56, 0.48];
for (let j = 0; j < divisors.length; j += 1) {
  const lower = f0 / divisors[j];
  if (lower < MIN_PITCH_HZ) continue;
  const lowerPeak = samplePeakDb(data, lower, sampleRate, fftSize, 28);
  subharmonicPenalty = Math.max(subharmonicPenalty,
    relativeAmplitude(lowerPeak.db) * divisorWeights[j]);
}
```

分数最后要乘上一个 `harmonicIndependence`，惩罚越重，候选被压得越低，基频才有机会浮上来。当我第一次看见 G 稳定地显示成 G 的时候，成就感比考级还强。

### 坑二：双路互补，YIN 管准、频谱管活

YIN 是公认最准的单音基频算法，抗噪强，但它是时域算法，追不上快速滑音。频谱打分则反过来：稳定、能追滑音，但对谐波又容易犯晕。两条路单独都靠不住，我干脆都跑，再合并：

```js
// app.js —— choosePitch：有和弦证据时强制走频谱，否则按置信度选路
function choosePitch(yinPitch, spectralPitch, polyphonic = false) {
  if (polyphonic && spectralPitch && spectralPitch.confidence >= 0.28) {
    return spectralPitch;           // 多音时不用 YIN：它会拿和弦的共同次谐波当基频
  }
  if (yinPitch && spectralPitch) {
    const distance = 1200 * Math.log2(yinPitch.frequency / spectralPitch.frequency);
    const octaveResidual = Math.abs(distance - Math.round(distance / 1200) * 1200);
    if (octaveResidual < 45) {      // 两路一致（±45 cent）才采信
      return yinPitch.confidence >= 0.55 ? yinPitch : spectralPitch;
    }
  }
  if (yinPitch && yinPitch.confidence >= 0.62) return yinPitch;
  if (spectralPitch && spectralPitch.confidence >= 0.34) return spectralPitch;
  return yinPitch || spectralPitch || null;
}
```

这里有个我自己很满意的细节：`polyphonic` 为真（识别到和弦）时直接强制走频谱，因为 YIN 会把和弦几个音的共同次谐波当成基频，锁出一个不存在的低音。单音时两路结果一致才采信，不一致就按置信度挑——这个"两票制"让吉他扫弦、口琴压音都被稳稳跟住，指针不至于乱抖。YIN 的塔乌估值我还用抛物线插值细化到小数样本，压音停在半途时，那个亚样本精度就是你能不能看出自己差几个 cent 的关键。

### 坑三：弹个和弦，它认不出来

这是校音器最容易让人上火的点：弹个 C 和弦，它要么不显示，要么随机锁一个音。我在键盘上随手按三根弦的时候，真希望屏幕上能跳出"这是 C 大三"。

我的解法是色度模板匹配：先把频谱收成一个 12 维色度向量（每格代表一个音级），再跟 10 种和弦模板 × 12 个根音做余弦相似度打分，取最高分。

```js
// chord.js —— detectChord：色度向量对模板做余弦匹配
const cosine = dot / (chromaNorm * templateNorm);
const missing = missingWeight / Math.max(weightSum, 1e-9);
const rootPresence = chroma[root] / maxValue;
const score = cosine - outside * 0.14 - missing * 0.06
            + rootPresence * 0.018
            - Math.max(0, type.intervals.length - 3) * 0.012;
```

光看余弦相似度还不够稳，我还会惩罚"模板该有的音却缺席"（missing）和"不该有的音却乱入"（outside），让匹配更准而不是哪个分高就瞎认。现在钢琴上弹个 Dm7，它标出来的是 Dm7，不是别的 D 开头的和弦。

### 为什么我敢把它写成一个静态站

你大概会问：又是 FFT 又是 YIN 又是模板匹配，这得挂几百个依赖吧？我当初也这么以为，结果写着写着发现，零依赖反而更省心。算法层（dsp.js、chord.js、music-theory.js）全是纯函数——所有输入显式传入、不碰 DOM、不碰全局状态，所以在 Node 里直接就能测。测试用的还是 `node --test` 内置工具，一个第三方包都不用装。

纯函数的好处不止是能测：同一份算法代码，浏览器里跑，Node 里也跑，我改了算法也不用担心把界面搞崩。UI 层只负责 Web Audio 取数和 `requestAnimationFrame` 画图，跟算法彻底分开。这一个决定，给我后来改错事省了不少心。也是因为零依赖、纯静态，它才真正做到"打开网页就能用、全平台免安装"——不用下载，就没有安装失败、没有磁盘占用、没有升级提醒，浏览器一关它就走，干净利落。

## 📌 全乐器通用，到底意味着什么

口琴压音时，我能看着频谱上那条能量峰值在几十音分里连续滑动，音名和 cent 偏差同步刷新，压过头了 cent 从 +30 一路掉到 -40，我就知道这口气使大了。

但同样的东西，给吉他、钢琴、小提琴用一样顺。吉他手对着屏幕扫 E 弦，看指针稳稳落在 E 上；钢琴生按和弦，色度图把根音和组成音一起点亮；小提琴手拉空弦，音高线跟着弓速走。校音这件小事，终于不用再下载一个沉重的 App，也不用纠结是不是只适用于我的乐器。一个网页，所有乐器，打开即用——这是校音器本该有的样子。

以前练琴靠耳朵猜，现在靠眼睛确认——不是替代耳朵，是给耳朵当参考。慢校音器追不上这个滑动，但频谱能。

## ✨ 回到最初

这个工具最早只有一个朴素的想法：让"校音器只认单音、追不上压音"这两个老大难，变成能在浏览器里亲眼看见的东西。做成之后我发现，它顺手也把"识别和弦"这件校音器做不到的事做了——而且是在一个零依赖、纯前端的静态站里，任何乐器都能用。

我把代码、算法和每一处设计的取舍都摊在 GitHub 上，你想看哪一段都能翻到它当初为什么这么写。想直接上手，点这里体验：https://tone.mingyangbao.site/

GitHub：https://github.com/DawnEver/tone-chord-lab
