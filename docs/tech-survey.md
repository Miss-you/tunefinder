# 音乐识别业界技术方案对比（audio fingerprinting）

> 目标：给一段包含音乐的音频，识别出「这是哪首歌」。
> 核心技术叫 **audio fingerprinting**（音频指纹）：从音频里抽出一段紧凑、抗噪、时移不变的"哈希序列"，去后端指纹库里做近邻匹配。

## 1. 核心原理简述

主流方案都基于同一套思路（Shazam 2003 论文奠基）：

1. STFT 得到时频谱图
2. 在时频域找到局部能量峰（peaks）——**抗噪、抗压缩、抗均衡的关键**
3. 把相邻 peak 配对为 (f1, f2, Δt)，量化后生成 **hash**
4. 每个 hash 关联 (track_id, offset)，入库
5. 查询时做同样的操作，用 (query_offset − db_offset) 的**直方图峰值**判定匹配

细节差别在于：hash 密度、峰选择策略、匹配阈值、库规模。

## 2. 主流方案对比

| 方案 | 类型 | 曲库规模 | 精度 | 延迟（识别 5s 片段） | 价格 | 适用场景 |
| --- | --- | --- | --- | --- | --- | --- |
| **Shazam 官方 (SDK)** | 商业闭源 | 2000w+ 首，含全球流行 | 极高（工业最强之一） | 云端 ~1-3s | 只对合作方开放 SDK | iOS Siri 内置、少量商业授权 |
| **Shazamio (逆向)** | 开源 Python，走 Shazam 公网 API | 同 Shazam | 同 Shazam | 云端 2-5s（含 HTTP） | 免费但 **非官方**，可能被限速/封禁 | 个人项目、CLI 工具、快速原型 |
| **ACRCloud** | 商业 SaaS | 7000w+，含广播、电视、UGC | 高，含 UGC 翻唱、直播流 | 云端 1-3s | 按识别次数付费（几分钱/次） | 广电监播、版权检测、直播识别 |
| **AudD** | 商业 SaaS | 6000w+ | 高 | 云端 2-4s | 有免费额度 + 订阅制 | 小规模商用、Discord 机器人 |
| **Chromaprint + AcoustID** | 开源 + 公益库 | ~500w，偏欧美古典/独立 | **匹配严格**：对干净原轨很高；对翻唱、直播、含噪几乎不识别 | 本地指纹几十 ms + HTTP 查库 <1s | 完全免费 | 音乐管理软件（Picard）、去重、原轨匹配 |
| **Dejavu / audfprint / olaf** | 开源自建 | 你自己灌多少 | 灌得好可以很高 | 本地纯 CPU：1-2s | 免费 | 私有曲库、封闭场景（比如自建的 BGM 库） |
| **Google Now Playing (Sound Search)** | 端上模型 | 数千万首 | 高 | 端上 1-2s，离线可用 | 仅 Pixel/Android 系统内置 | 手机原生 |
| **NeuralFP / 深度指纹** | 学术前沿（对比学习） | 由团队自训 | 抗噪、抗翻唱强 | GPU 推理 <100ms | 需自己训练 | 研究、抗攻击场景 |

## 3. 优劣与选型建议

### 3.1 我这次为什么选 Shazamio

- 只有一段 YouTube Shorts 的音频，需求是"识别是哪首歌"，典型的**主流商用曲库覆盖场景**
- Shazam 曲库最全，能识别到 J-Pop 冷门曲（如手嶌葵）
- Shazamio 免费，零 API Key，本地 pip install 即用
- 缺点：**依赖非官方接口**，Shazam 若更新反爬会失败；无 SLA；商用有法律风险

### 3.2 什么时候该换方案

| 需求 | 推荐 |
| --- | --- |
| 生产环境、有版权检测需求 | ACRCloud / AudD（商业授权，稳定） |
| 音乐管理软件、给用户本地曲库补 tag | Chromaprint + AcoustID |
| 内部私有 BGM 库、封闭场景 | Dejavu / audfprint 自建 |
| 边缘设备离线识别 | Google Sound Search（若能用）或自训练 NeuralFP |
| 直播流 7×24 监播 | ACRCloud broadcast monitoring |

### 3.3 精度 vs 延迟的权衡

- 若可接受**云端往返 + 3-5s 延迟**：Shazam 系列体验最好
- 若必须**离线本地**：Chromaprint（干净原轨）或 Dejavu（自建库）
- 若在**高噪 / DJ mix / 翻唱**场景：ACRCloud > Shazam > 其他
- 若在**实时低延迟**（<500ms）：只有端上模型能做到（Google / 自训 NeuralFP）

## 4. 通用架构：本工具的分层

```
   URL / 文件
       │
       ▼
┌─────────────────┐    ┌──────────────────┐
│  Downloader     │    │  Audio Loader    │
│ (yt-dlp)        │    │ (ffmpeg / pydub) │
└────────┬────────┘    └────────┬─────────┘
         └───────────┬──────────┘
                     ▼
           ┌───────────────────┐
           │  Recognizer (抽象) │
           └─┬──────┬─────┬────┘
             │      │     │
        Shazamio  AcoustID  Custom(Dejavu)
             │      │     │
             └──────▼─────┘
              统一 RecognitionResult
                     │
                     ▼
              CLI / Web API / 前端展示
```

后端切换通过配置 `TUNEFINDER_BACKEND=shazamio|acoustid|dejavu` 即可，业务层无感。
