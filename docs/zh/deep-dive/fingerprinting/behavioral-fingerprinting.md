# 行为指纹识别

本文档探讨行为指纹识别——最复杂的机器人检测层，它分析**用户如何交互**而不是**使用什么工具**。虽然网络和浏览器指纹可以通过足够的技术知识进行伪造，但人类行为却非常难以令人信服地复制。

!!! info "模块导航"
    - **[← 指纹识别概述](./index.md)** - 模块介绍和理念
    - **[← 网络指纹识别](./network-fingerprinting.md)** - 协议层指纹识别
    - **[← 浏览器指纹识别](./browser-fingerprinting.md)** - 应用层指纹识别
    - **[→ 规避技术](./evasion-techniques.md)** - 实用对策
    
    关于实用的类人自动化，请参阅**[类人交互](../../features/automation/human-interactions.md)**。

!!! danger "最后的前沿"
    行为指纹识别是对抗自动化的**最后一道防线**。即使拥有完美的网络和浏览器指纹，不自然的鼠标移动、即时文本插入或机器人滚动模式也能立即揭示自动化。

## 为什么存在行为指纹识别

传统的机器人检测专注于技术指纹——TLS 签名、HTTP 标头、JavaScript 属性。但随着自动化工具发展到可以伪造这些特征，反机器人系统需要一种新方法：**分析行为本身**。

基本洞察：**人类是混乱的，机器人是精确的**。

- 人类以略微弯曲的路径移动鼠标，加速度可变
- 人类以不规则的间隔打字，受手指灵巧性和双字母组合影响
- 人类滚动具有遵循物理定律的惯性和动量
- 人类会暂停、犹豫、纠正错误并有机地交互

默认情况下，机器人以机器精度执行操作——完美笔直的鼠标移动、恒定的打字速度、即时滚动和顺序操作，没有人类变异性。

!!! info "行业采用"
    领先的反机器人供应商已将重点转向行为分析：
    
    - **[DataDome](https://datadome.co/)**：在 25 亿+ 行为信号上使用机器学习
    - **[PerimeterX (Human Security)](https://www.humansecurity.com/)**：分析鼠标动态、触摸事件和交互模式
    - **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)**：结合 TLS 指纹识别与行为生物识别
    - **[Cloudflare Bot Management](https://www.cloudflare.com/application-services/products/bot-management/)**：使用在数十亿请求上训练的机器学习模型
    - **[Shape Security (F5)](https://www.f5.com/products/security/shape-defense)**：自 2011 年以来的行为分析先驱

## 鼠标移动分析

鼠标移动是最强大的行为指标之一，因为人类运动控制遵循机器人难以准确复制的**生物力学定律**。

### 菲茨定律和人类运动控制

[菲茨定律](https://en.wikipedia.org/wiki/Fitts%27s_law)（1954）描述了移动到目标所需的时间：

```
T = a + b × log₂(D/W + 1)
```

其中：
- `T` = 完成移动的时间
- `a` = 启动/停止时间（反应时间）
- `b` = 设备的固有速度
- `D` = 到目标的距离
- `W` = 目标的宽度

**机器人检测的关键含义：**

1. **加速/减速**：人类在移动开始时加速，在接近目标时减速
2. **过冲和校正**：人类经常略微过冲目标，然后校正
3. **子移动**：长距离移动由多个子移动组成，而不是一个连续运动
4. **可变性**：即使到达同一目标，没有两次移动是相同的

### 检测自动化鼠标移动

```python
class MouseMovementAnalyzer:
    """
    分析鼠标移动模式以检测自动化。
    """
    
    def analyze_trajectory(self, points: list[tuple[int, int, float]]) -> dict:
        """
        分析鼠标移动轨迹。
        
        Args:
            points: (x, y, timestamp) 元组列表
            
        Returns:
            带有检测标志的分析结果
        """
        import math
        
        if len(points) < 3:
            return {'error': 'Insufficient data points'}
        
        # 计算速度
        velocities = []
        for i in range(1, len(points)):
            x1, y1, t1 = points[i-1]
            x2, y2, t2 = points[i]
            
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            time_delta = t2 - t1
            
            if time_delta > 0:
                velocity = distance / time_delta
                velocities.append(velocity)
        
        # 计算加速度
        accelerations = []
        for i in range(1, len(velocities)):
            accel = velocities[i] - velocities[i-1]
            accelerations.append(abs(accel))
        
        # 计算路径曲率
        curvatures = []
        for i in range(1, len(points) - 1):
            x1, y1, _ = points[i-1]
            x2, y2, _ = points[i]
            x3, y3, _ = points[i+1]
            
            # 计算中间点的角度
            angle1 = math.atan2(y2 - y1, x2 - x1)
            angle2 = math.atan2(y3 - y2, x3 - x2)
            curve = abs(angle2 - angle1)
            curvatures.append(curve)
        
        # 检测标志
        flags = []
        
        # 标志 1：完美直线
        if len(curvatures) > 0 and max(curvatures) < 0.01:
            flags.append('PERFECTLY_STRAIGHT_LINE')
        
        # 标志 2：恒定速度（无加速/减速）
        if len(velocities) > 2:
            velocity_variance = self._variance(velocities)
            if velocity_variance < 10:  # 非常低的方差
                flags.append('CONSTANT_VELOCITY')
        
        # 标志 3：无子移动
        # 人类移动在速度上有多个"峰值"
        velocity_peaks = self._count_peaks(velocities)
        total_distance = sum(math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                      (points[i][1] - points[i-1][1])**2)
                           for i in range(1, len(points)))
        
        if total_distance > 200 and velocity_peaks < 2:
            flags.append('NO_SUBMOVEMENTS')
        
        # 标志 4：即时跳跃（瞬移）
        max_velocity = max(velocities) if velocities else 0
        if max_velocity > 10000:  # 像素/秒
            flags.append('INSTANT_JUMP')
        
        return {
            'total_points': len(points),
            'total_distance': total_distance,
            'avg_velocity': sum(velocities) / len(velocities) if velocities else 0,
            'max_velocity': max_velocity,
            'velocity_variance': self._variance(velocities),
            'avg_curvature': sum(curvatures) / len(curvatures) if curvatures else 0,
            'velocity_peaks': velocity_peaks,
            'detection_flags': flags,
            'is_suspicious': len(flags) > 1,
        }
    
    @staticmethod
    def _variance(values: list[float]) -> float:
        """计算列表的方差。"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean)**2 for x in values) / len(values)
    
    @staticmethod
    def _count_peaks(values: list[float], threshold: float = 0.8) -> int:
        """计算速度剖面中的峰值数量。"""
        if len(values) < 3:
            return 0
        
        max_val = max(values)
        peak_count = 0
        
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                if values[i] > max_val * threshold:
                    peak_count += 1
        
        return peak_count


# 示例用法
points = [
    (100, 100, 0.0),
    (200, 100, 0.1),    # 完美笔直的水平线
    (300, 100, 0.2),
    (400, 100, 0.3),
    (500, 100, 0.4),
]

analyzer = MouseMovementAnalyzer()
result = analyzer.analyze_trajectory(points)

print(f"检测标志: {result['detection_flags']}")
# 输出: ['PERFECTLY_STRAIGHT_LINE', 'CONSTANT_VELOCITY', 'NO_SUBMOVEMENTS']
# → 高度可疑！
```

### 贝塞尔曲线和人类运动模拟

**贝塞尔曲线**由法国工程师 [Pierre Bézier](https://en.wikipedia.org/wiki/Pierre_B%C3%A9zier) 于 1960 年代为雷诺的汽车车身设计开发，是参数曲线，可在两点之间生成平滑、自然的路径。

#### 为什么自动化工具使用贝塞尔曲线

机器人鼠标移动的基本问题：

```
机器人移动（线性）：
A ──────────────────────► B
（完美笔直，恒定速度）

人类移动（贝塞尔）：
A ─╮        ╭──► B
   ╰────────╯
（略微弯曲，可变速度）
```

**关于自然曲线的研究：**

- **Flash, T., & Hogan, N. (1985)**："The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model" - Journal of Neuroscience。证明人类到达运动遵循**最小加加速度轨迹**，可以用三次多项式很好地近似。

- **Abend, W., Bizzi, E., & Morasso, P. (1982)**："Human Arm Trajectory Formation" - Brain。表明两点之间的手部路径通常是弯曲的，而不是直线的，这是由于生物力学约束。

#### 控制点放置策略

逼真模拟的关键是**随机化控制点**，同时保持自然约束：

**几何约束：**

1. **距离成比例的偏差**：控制点的偏差应最多为总距离的 20-30%
   - 偏差过多 → 不自然的 S 曲线
   - 偏差过少 → 几乎线性（类似机器人）

2. **双边不对称**：P₁ 和 P₂ 不应对称
   - 人类不产生完全对称的曲线
   - 随机偏移打破镜像对称

3. **时间间距**：将 P₁ 放置在更靠近起点（t ≈ 0.33），P₂ 更靠近终点（t ≈ 0.66）
   - 模仿加速/减速阶段
   - 与菲茨定律预测一致

**实现示例：**

```python
import random
import math

def generate_realistic_control_points(start, end):
    """
    根据生物力学约束生成控制点。
    基于 Flash & Hogan (1985) 最小加加速度模型。
    """
    x1, y1 = start
    x4, y4 = end
    
    # 计算距离和角度
    distance = math.sqrt((x4 - x1)**2 + (y4 - y1)**2)
    angle = math.atan2(y4 - y1, x4 - x1)
    
    # 控制点 1：路径的 1/3 处带有垂直偏移
    t1 = 0.33
    offset_1 = random.uniform(-distance * 0.25, distance * 0.25)
    x2 = x1 + (x4 - x1) * t1 + offset_1 * math.sin(angle)
    y2 = y1 + (y4 - y1) * t1 - offset_1 * math.cos(angle)
    
    # 控制点 2：路径的 2/3 处带有不同偏移
    t2 = 0.66
    offset_2 = random.uniform(-distance * 0.2, distance * 0.2)
    x3 = x1 + (x4 - x1) * t2 + offset_2 * math.sin(angle)
    y3 = y1 + (y4 - y1) * t2 - offset_2 * math.cos(angle)
    
    return (x2, y2), (x3, y3)

# 使用 De Casteljau 算法的三次贝塞尔评估
def evaluate_bezier(t, p0, p1, p2, p3):
    """在参数 t 处评估三次贝塞尔。"""
    u = 1 - t
    x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
    return (x, y)
```

#### 速度剖面和缓动函数

除了曲线形状，沿曲线的**速度分布**也至关重要。人类运动遵循**钟形速度剖面**（加速 → 峰值 → 减速）。

**常见缓动函数：**

| 函数 | 公式 | 特征 |
|----------|---------|----------------|
| **线性** | f(t) = t | 恒定速度（机器人） |
| **缓入缓出** | f(t) = 3t² - 2t³ | 平滑加速/减速 |
| **三次** | f(t) = 4t³ (t < 0.5)<br/>1 - 4(1-t)³ (t ≥ 0.5) | 更明显的加速 |
| **指数** | f(t) = (e^(kt) - 1) / (e^k - 1) | 模仿生物运动 |

**速度剖面可视化：**

```
线性（机器人）：
V │    ████████████████
  │    
  └────────────────────► t
     （恒定速度）

人类（缓入缓出）：
V │        ╱╲
  │      ╱    ╲
  │    ╱        ╲
  └────────────────────► t
   （加速 → 减速）
```

#### De Casteljau 算法

虽然显式公式有效，但 **[De Casteljau 算法](https://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm)**（由 Paul de Casteljau 于 1959 年在雪铁龙开发）在数值上更稳定且几何上更直观：

**递归细分：**

```
给定点 P₀, P₁, P₂, P₃ 和参数 t：

级别 1（线性插值）：
Q₀ = (1-t)P₀ + tP₁
Q₁ = (1-t)P₁ + tP₂  
Q₂ = (1-t)P₂ + tP₃

级别 2：
R₀ = (1-t)Q₀ + tQ₁
R₁ = (1-t)Q₁ + tQ₂

级别 3（最终点）：
B(t) = (1-t)R₀ + tR₁
```

这种三级插值产生相同的结果，但避免了高次幂多项式，减少了浮点误差。

!!! warning "贝塞尔曲线检测"
    虽然贝塞尔曲线比直线产生更自然的路径，但复杂的反机器人系统可以**检测贝塞尔曲线的过度使用**：
    
    **检测技术：**
    
    1. **曲率一致性**：贝塞尔曲线具有**单调曲率**（曲率仅增加或减少，从不振荡）。真实的人类运动通常由于肌肉校正而具有**局部曲率变化**。
    
    2. **子移动分析**：人类执行运动作为一系列**重叠的子移动**（[Meyer et al., 1988](https://pubmed.ncbi.nlm.nih.gov/3411362/)）。纯贝塞尔曲线缺乏这些微校正。
    
    3. **统计指纹识别**：如果用户 90%+ 的鼠标移动遵循具有相似控制点分布的三次贝塞尔模式，这在统计上是可疑的。
    
    4. **速度过冲**：真实的人类经常**略微过冲**目标，然后校正。完美调整的贝塞尔+缓动组合缺乏这一点。
    
    **研究：**
    - **Chou, Y. et al. (2017)**："A Study of Web Bot Detection by Analyzing Mouse Trajectories" - 证明贝塞尔生成的移动在特征空间中的聚类与有机移动不同。

!!! tip "超越简单贝塞尔"
    生产级鼠标模拟需要：
    
    - **复合曲线**：链接多个具有不同控制点的贝塞尔段
    - **抖动注入**：添加小的随机垂直偏差（±2-5px）
    - **微暂停**：移动中偶尔短暂停止（50-150ms）
    - **过冲 + 校正**：故意过冲目标 5-15px，然后校正
    - **随机化缓动**：不要总是使用相同的缓动函数
    
    使用贝塞尔的流行工具：
    - **[Puppeteer Ghost Cursor](https://github.com/Xetera/ghost-cursor)**：将贝塞尔与随机过冲结合
    - **[Pyautogui](https://pyautogui.readthedocs.io/)**：基本补间（容易检测）
    - **[Humanize.js](https://github.com/HumanSignal/label-studio-frontend/blob/master/src/utils/utilities.js)**：高级复合曲线

### 鼠标移动熵

**在这种情况下什么是熵？**

在信息论中，**熵**衡量数据中的随机性或不可预测性量。应用于鼠标移动，它量化路径的"变化"或"不可预测"程度。

**为什么测量熵：**

- **高熵** = 大量变化，许多不同方向，不可预测的变化 → 类人
- **低熵** = 重复模式，可预测的移动，很少方向变化 → 类机器人

这样想：
- 完美直线具有**零熵**（完全可预测）
- 随机游走具有**高熵**（难以预测下一个点）
- 人类运动具有**中到高熵**（有点随机，但不完全混乱）

**香农熵公式（简化）：**

熵测量"惊喜"——如果每个方向都同样可能，熵就会最大化。如果移动总是朝同一方向，熵为零。

```
H = -Σ(p × log₂(p))

其中：
- p = 每个方向的概率
- 高 H = 许多不同方向（人类）
- 低 H = 很少方向或重复（机器人）
```

**实际检测：**

检测系统将路径分成段，测量每个点的角度，并计算每个角度出现的次数。直线移动的机器人每次都会有相同的角度（低熵），而人类会有变化的角度（高熵）。

```python
import math
from collections import Counter


def calculate_mouse_entropy(points: List[Tuple[int, int]]) -> float:
    """
    计算鼠标移动方向变化的香农熵。
    
    低熵 = 可预测/机器人移动
    高熵 = 自然的人类变异性
    """
    if len(points) < 3:
        return 0.0
    
    # 计算方向变化
    directions = []
    for i in range(1, len(points) - 1):
        x1, y1 = points[i-1]
        x2, y2 = points[i]
        x3, y3 = points[i+1]
        
        # 计算角度
        angle1 = math.atan2(y2 - y1, x2 - x1)
        angle2 = math.atan2(y3 - y2, x3 - x2)
        
        # 将角度变化量化为区间
        angle_diff = angle2 - angle1
        bin_index = int((angle_diff + math.pi) / (2 * math.pi / 8))  # 8 个区间
        directions.append(bin_index)
    
    # 计算香农熵
    total = len(directions)
    if total == 0:
        return 0.0
    
    freq = Counter(directions)
    entropy = -sum((count / total) * math.log2(count / total) 
                   for count in freq.values())
    
    return entropy


# 示例
human_points = [(i + random.randint(-5, 5), i + random.randint(-5, 5)) 
                for i in range(100)]
bot_points = [(i, i) for i in range(100)]  # 完美对角线

human_entropy = calculate_mouse_entropy(human_points)
bot_entropy = calculate_mouse_entropy(bot_points)

print(f"人类熵: {human_entropy:.3f}")  # ~2.5-3.0（高）
print(f"机器人熵: {bot_entropy:.3f}")      # ~0.0-0.5（低）
```

!!! info "鼠标动态研究"
    关于鼠标动态用于身份验证的学术研究：
    
    - **Ahmed, A. A. E., & Traore, I. (2007)**："A New Biometric Technology Based on Mouse Dynamics" - IEEE Transactions on Dependable and Secure Computing
    - **Gamboa, H., & Fred, A. (2004)**："A Behavioral Biometric System Based on Human-Computer Interaction" - International Society for Optical Engineering
    - **Zheng, N., Paloski, A., & Wang, H. (2011)**："An Efficient User Verification System via Mouse Movements" - ACM Conference on Computer and Communications Security
    
    这些论文确定鼠标动态可以实现 **90-98% 的身份验证准确性**。

## 击键动态（打字节奏）

击键动态——也称为**打字生物识别**——分析键盘输入的时间模式。这是最古老的行为生物识别技术之一，可追溯到 1850 年代的电报员，他们可以通过"莫尔斯电码拳"相互识别。

### 击键时间特征

现代击键动态系统测量：

| 特征 | 描述 | 检测价值 |
|---------|-------------|-----------------|
| **停留时间** | 按键按下和释放之间的时间（`keydown` → `keyup`） | 人类：50-200ms，机器人：通常 0ms 或恒定 |
| **飞行时间** | 释放一个键和按下下一个键之间的时间（`keyup` → `keydown`） | 因双字母而异（例如，"th" 比 "pz" 快） |
| **二元组延迟** | 两键序列的总时间 | 双字母依赖（运动记忆） |
| **三元组延迟** | 三键序列的时间 | 显示打字节奏 |
| **错误率** | 退格/删除的频率 | 人类会犯错，机器人不会 |
| **大写模式** | Shift 与 Caps Lock 的使用 | 揭示打字习惯 |

### 检测自动化打字

```python
from typing import List, Tuple
import statistics


class KeystrokeAnalyzer:
    """
    分析击键动态以检测自动化。
    """
    
    # 预期的人类打字速度（毫秒）
    HUMAN_DWELL_TIME = (50, 200)      # 按键持续时间
    HUMAN_FLIGHT_TIME = (80, 400)     # 按键之间的时间
    HUMAN_WPM_RANGE = (20, 120)       # 每分钟字数
    
    def analyze_typing(
        self,
        events: List[Tuple[str, str, float]]
    ) -> dict:
        """
        分析击键事件以进行机器人检测。
        
        Args:
            events: (event_type, key, timestamp) 元组列表
                   event_type: 'keydown' 或 'keyup'
                   
        Returns:
            带有检测标志的分析
        """
        if len(events) < 4:
            return {'error': 'Insufficient keystroke data'}
        
        dwell_times = []
        flight_times = []
        
        keydown_times = {}
        last_keyup_time = None
        
        for event_type, key, timestamp in events:
            if event_type == 'keydown':
                keydown_times[key] = timestamp
                
                # 计算飞行时间（自上次按键释放以来的时间）
                if last_keyup_time is not None:
                    flight_time = (timestamp - last_keyup_time) * 1000  # ms
                    flight_times.append(flight_time)
            
            elif event_type == 'keyup':
                if key in keydown_times:
                    # 计算停留时间
                    dwell_time = (timestamp - keydown_times[key]) * 1000  # ms
                    dwell_times.append(dwell_time)
                    
                    last_keyup_time = timestamp
                    del keydown_times[key]
        
        # 计算打字速度（WPM）
        if len(events) >= 2:
            total_time = events[-1][2] - events[0][2]  # 秒
            char_count = len([e for e in events if e[0] == 'keydown'])
            wpm = (char_count / 5) / (total_time / 60) if total_time > 0 else 0
        else:
            wpm = 0
        
        # 检测标志
        flags = []
        
        # 标志 1：零停留时间（即时按键释放）
        if dwell_times and min(dwell_times) < 1:
            flags.append('ZERO_DWELL_TIME')
        
        # 标志 2：恒定时间（无人类变异性）
        if len(dwell_times) > 3:
            dwell_variance = statistics.variance(dwell_times)
            if dwell_variance < 10:  # 非常一致
                flags.append('CONSTANT_DWELL_TIME')
        
        if len(flight_times) > 3:
            flight_variance = statistics.variance(flight_times)
            if flight_variance < 10:
                flags.append('CONSTANT_FLIGHT_TIME')
        
        # 标志 3：不可能的打字速度
        if wpm > 150:  # 世界纪录约为 170 WPM
            flags.append('SUPERHUMAN_SPEED')
        
        # 标志 4：过于一致（无错误，无暂停）
        if len(events) > 50:
            backspaces = sum(1 for e in events if e[1] in ['Backspace', 'Delete'])
            if backspaces == 0:
                flags.append('NO_TYPING_ERRORS')
        
        return {
            'total_keystrokes': len([e for e in events if e[0] == 'keydown']),
            'avg_dwell_time': statistics.mean(dwell_times) if dwell_times else 0,
            'avg_flight_time': statistics.mean(flight_times) if flight_times else 0,
            'dwell_variance': statistics.variance(dwell_times) if len(dwell_times) > 1 else 0,
            'flight_variance': statistics.variance(flight_times) if len(flight_times) > 1 else 0,
            'typing_speed_wpm': wpm,
            'detection_flags': flags,
            'is_suspicious': len(flags) >= 2,
        }


# 示例：机器人打字（恒定间隔）
bot_events = []
t = 0.0
for char in "automated_text":
    bot_events.append(('keydown', char, t))
    bot_events.append(('keyup', char, t + 0.001))  # 1ms 停留（过快）
    t += 0.05  # 完美的 50ms 间隔

analyzer = KeystrokeAnalyzer()
result = analyzer.analyze_typing(bot_events)
print(f"机器人检测标志: {result['detection_flags']}")
# 输出: ['ZERO_DWELL_TIME', 'CONSTANT_DWELL_TIME', 'CONSTANT_FLIGHT_TIME', 'SUPERHUMAN_SPEED']
```

### 二元组时间模式（双字母）

**什么是双字母？**

**双字母**（或二元组）只是一对连续字符。在打字分析中，双字母揭示了每个人独特的模式，简单的机器人无法复制。

**为什么双字母时间很重要：**

当你输入单词"the"时，你不是按下三个独立的键——你正在执行一个记忆的运动序列。你的大脑和手指已经学会"th"和"he"是常见模式，使它们比罕见的组合如"xq"或"zp"更快。

**背后的科学：**

运动学习研究表明：
- **频繁输入的双字母**（如"th"、"in"、"er"）作为**运动块**存储在程序记忆中
- **同手双字母**通常比交替手更快（需要更少的协调）
- **主行到主行**比到达远键更快
- **尴尬的手指组合**（如同一只手的无名指 → 小指）自然较慢

这为每个人创建了一个**独特的时间签名**，基于：
1. 他们的打字风格（触摸打字 vs 寻找和啄击）
2. 键盘布局熟悉度
3. 母语（葡萄牙语使用者与英语使用者有不同的双字母）
4. 身体手部特征

**时间差异示例：**

```python
# 常见英语双字母时间（毫秒）
BIGRAM_TIMINGS = {
    # 快速双字母（同手，常见序列）
    'th': 80,
    'he': 85,
    'in': 90,
    'er': 85,
    'an': 95,
    'ed': 100,
    
    # 中等双字母（手部交替）
    'to': 120,
    'es': 125,
    'or': 130,
    
    # 慢速双字母（尴尬的手指位置）
    'pz': 250,
    'qx': 280,
    'zq': 300,
    
    # 非常慢（需要手部重新定位）
    'ju': 180,
    'mp': 170,
}


def estimate_bigram_time(bigram: str) -> float:
    """
    估算双字母的实际时间。
    返回以秒为单位的时间，带有小的随机变化。
    """
    import random
    
    base_time = BIGRAM_TIMINGS.get(bigram.lower(), 150)  # 默认 150ms
    
    # 添加 10-20% 的随机变化
    variation = random.uniform(0.9, 1.2)
    
    return (base_time / 1000) * variation


def simulate_human_typing(text: str) -> List[Tuple[str, str, float]]:
    """
    使用双字母感知时间模拟逼真的人类打字。
    """
    events = []
    t = 0.0
    
    for i, char in enumerate(text):
        # keydown
        events.append(('keydown', char, t))
        
        # 停留时间（50-150ms 带变化）
        dwell = random.uniform(0.05, 0.15)
        
        # keyup
        events.append(('keyup', char, t + dwell))
        
        # 飞行时间（下一个 keydown）
        if i < len(text) - 1:
            bigram = text[i:i+2]
            flight = estimate_bigram_time(bigram)
            t += dwell + flight
        else:
            t += dwell
    
    return events
```

!!! info "击键动态参考"
    - **Monrose, F., & Rubin, A. D. (2000)**："Keystroke Dynamics as a Biometric for Authentication" - Future Generation Computer Systems
    - **Banerjee, S. P., & Woodard, D. L. (2012)**："Biometric Authentication and Identification using Keystroke Dynamics" - IEEE Survey
    - **Hu, J., Gingrich, D., & Sentosa, A. (2008)**："A k-Nearest Neighbor Approach for User Authentication through Biometric Keystroke Dynamics" - IEEE International Conference on Communications
    
    这些研究表明，击键动态只需 50-100 次击键就可以实现 **95%+ 的身份验证准确性**。

### "粘贴检测"问题

最简单的机器人指标之一是**没有键盘事件的文本插入**：

```javascript
// 服务器端检测（伪代码）
function detectPastedText(input_events) {
    // 检查输入字段是否在没有相应键事件的情况下更改
    
    if (input.value.length > 0 && key_events.length == 0) {
        return 'TEXT_PASTED';  // input.value = "text" 或粘贴事件
    }
    
    if (input.value.length > key_events.length * 2) {
        return 'MISSING_KEYSTROKES';  // 某些文本在没有键的情况下出现
    }
    
    return 'OK';
}
```

**机器人模式：**
- 使用 `element.send_keys("text")` 而没有单个键事件
- JavaScript `input.value = "text"` 注入
- 没有 `paste` 事件或前面的键事件的剪贴板粘贴

**人类模式：**
- 每个字符的单独 `keydown`/`keyup` 事件
- 偶尔的 `paste` 事件（Ctrl+V）带有相应的键盘修饰符
- 打字错误后跟退格

## 滚动模式和物理学

**为什么滚动难以伪造：**

当你用鼠标滚轮或触控板滚动时，你不仅仅是在移动像素——你正在向机械或电容式输入设备**施加物理力**。这种物理交互创建了遵循物理定律的自然模式。

**人类滚动的物理学：**

1. **初始动量**：当你轻弹鼠标滚轮或滑动触控板时，你传递动能
2. **摩擦/阻力**：系统施加虚拟"摩擦"，逐渐减慢滚动
3. **减速**：速度呈指数（而非线性）下降，直到停止
4. **惯性**：特别是在触控板上，手指离开后内容继续滚动一小段时间

这与在桌子上滑动物体相同——它开始很快，然后由于摩擦逐渐减慢。

**机器人滚动问题：**

```python
# 机器人滚动（即时跳跃）：
window.scrollTo(0, 1000)  # 瞬移！

# 或恒速滚动：
for i in range(10):
    window.scrollBy(0, 100)  # 相同增量，相同时间
    sleep(0.1)               # 完美间隔
```

两者对人类来说都是物理上不可能的——没有动量，没有减速，没有变化。

**可观察的差异：**

| 特征 | 人类 | 机器人 |
|----------------|-------|-----|
| **速度剖面** | 指数衰减 | 恒定或即时 |
| **事件间隔** | 可变（帧依赖） | 完美/可预测 |
| **滚动距离** | 每个事件可变 | 每个事件恒定 |
| **减速** | 渐进、平滑 | 突然停止或无 |
| **过冲** | 有时 | 从不 |

### 滚动事件分析

```python
import math
from typing import List, Tuple


class ScrollAnalyzer:
    """
    分析滚动行为以检测自动化。
    """
    
    def analyze_scroll_events(
        self,
        events: List[Tuple[float, int, float]]  # (timestamp, delta_y, velocity)
    ) -> dict:
        """
        分析滚动事件以进行机器人检测。
        
        Args:
            events: (timestamp, delta_y, velocity) 元组列表
                   delta_y: 滚动的像素
                   velocity: 该时刻的滚动速度
                   
        Returns:
            带有检测标志的分析
        """
        if len(events) < 3:
            return {'error': 'Insufficient scroll data'}
        
        # 提取特征
        deltas = [e[1] for e in events]
        velocities = [abs(e[2]) for e in events]
        timestamps = [e[0] for e in events]
        
        # 计算时间间隔
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        
        flags = []
        
        # 标志 1：恒定滚动增量（无滚轮动量）
        if len(set(deltas)) == 1 and len(deltas) > 5:
            flags.append('CONSTANT_SCROLL_DELTA')
        
        # 标志 2：即时滚动（无动量/惯性）
        # 人类滚动具有渐进减速
        if len(velocities) > 3:
            # 检查速度是否突然降至零（无惯性）
            has_inertia = any(velocities[i] < velocities[i-1] * 0.8 
                            for i in range(1, len(velocities)))
            
            if not has_inertia and max(velocities) > 100:
                flags.append('NO_SCROLL_INERTIA')
        
        # 标志 3：完美时间间隔
        if len(intervals) > 2:
            interval_variance = self._variance(intervals)
            if interval_variance < 0.001:  # 小于 1ms 方差
                flags.append('CONSTANT_SCROLL_TIMING')
        
        # 标志 4：不可能的滚动距离
        total_scroll = sum(abs(d) for d in deltas)
        total_time = timestamps[-1] - timestamps[0]
        
        if total_time > 0:
            scroll_speed = total_scroll / total_time  # 像素/秒
            if scroll_speed > 10000:  # 不切实际的快
                flags.append('IMPOSSIBLE_SCROLL_SPEED')
        
        # 标志 5：末尾无减速
        if len(velocities) > 3:
            # 最后 3 个速度应显示减速
            if velocities[-1] >= velocities[-3]:
                flags.append('NO_DECELERATION')
        
        return {
            'total_scroll_distance': sum(abs(d) for d in deltas),
            'scroll_event_count': len(events),
            'avg_scroll_delta': sum(abs(d) for d in deltas) / len(deltas),
            'avg_velocity': sum(velocities) / len(velocities),
            'detection_flags': flags,
            'is_suspicious': len(flags) >= 2,
        }
    
    @staticmethod
    def _variance(values: List[float]) -> float:
        """计算方差。"""
        if not values or len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean)**2 for x in values) / len(values)


# 示例：机器人滚动（即时跳跃）
bot_scroll = [
    (0.0, 1000, 1000),  # 即时 1000px 滚动
    (0.001, 0, 0),      # 立即停止
]

# 示例：人类滚动（动量 + 惯性）
human_scroll = [
    (0.0, 120, 800),    # 初始动量
    (0.05, 100, 650),   # 减速
    (0.1, 80, 520),
    (0.15, 60, 390),
    (0.2, 40, 250),
    (0.25, 20, 120),
    (0.3, 10, 50),      # 渐进停止
    (0.35, 0, 0),
]

analyzer = ScrollAnalyzer()
bot_result = analyzer.analyze_scroll_events(bot_scroll)
human_result = analyzer.analyze_scroll_events(human_scroll)

print(f"机器人标志: {bot_result['detection_flags']}")
# 输出: ['NO_SCROLL_INERTIA', 'NO_DECELERATION', 'IMPOSSIBLE_SCROLL_SPEED']

print(f"人类标志: {human_result['detection_flags']}")
# 输出: []  （自然滚动）
```

### 模拟逼真滚动

```python
def simulate_human_scroll(target_distance: int, direction: int = 1) -> List[Tuple[float, int, float]]:
    """
    模拟具有动量和惯性的类人滚动。
    
    Args:
        target_distance: 要滚动的总像素
        direction: 1 表示向下，-1 表示向上
        
    Returns:
        (timestamp, delta_y, velocity) 滚动事件列表
    """
    import random
    
    events = []
    
    # 初始速度（人类范围内的随机）
    velocity = random.uniform(500, 1200)  # 像素/秒
    
    # 减速率（摩擦）
    deceleration = random.uniform(800, 1500)  # 像素/秒²
    
    scrolled = 0
    t = 0.0
    dt = 0.016  # ~60 FPS
    
    while scrolled < target_distance and velocity > 10:
        # 计算此帧的滚动增量
        delta = int(velocity * dt) * direction
        
        # 添加小的随机变化
        delta += random.randint(-2, 2)
        
        events.append((t, delta, velocity))
        
        scrolled += abs(delta)
        
        # 应用减速（摩擦/惯性）
        velocity -= deceleration * dt
        velocity = max(0, velocity)
        
        # 添加小的随机速度波动
        velocity += random.uniform(-20, 20)
        
        t += dt
    
    return events
```

!!! tip "滚动物理学"
    真实的滚动行为遵循**"缓出"**模式：
    
    1. **初始动量**：来自用户输入（鼠标滚轮、触控板轻弹）的高速度
    2. **减速**：由于摩擦的指数衰减
    3. **微调整**：接近目标的小校正
    
    这在浏览器的平滑滚动中通过 CSS `scroll-behavior: smooth` 使用**贝塞尔缓动函数**实现。

## 事件序列分析

除了单独的操作，反机器人系统还分析事件的**序列和时间**。人类遵循可预测的交互模式，而机器人经常跳过步骤或以不自然的顺序执行它们。

### 自然交互序列

```python
class EventSequenceAnalyzer:
    """
    分析事件序列以检测不自然的交互模式。
    """
    
    # 自然的人类交互模式
    NATURAL_SEQUENCES = {
        'click': ['mousemove', 'mousedown', 'mouseup', 'click'],
        'text_input': ['focus', 'keydown', 'keypress', 'keyup', 'input'],
        'navigation': ['mousemove', 'mousedown', 'mouseup', 'click', 'unload'],
        'form_submit': ['focus', 'input', 'blur', 'submit'],
    }
    
    def analyze_click_sequence(self, events: List[Tuple[str, float]]) -> dict:
        """
        分析导致点击的事件。
        
        Args:
            events: (event_type, timestamp) 元组列表
            
        Returns:
            带有检测标志的分析
        """
        flags = []
        
        # 按顺序提取事件类型
        event_types = [e[0] for e in events]
        
        # 查找点击事件
        click_indices = [i for i, e in enumerate(event_types) if e == 'click']
        
        for click_idx in click_indices:
            # 分析点击前的事件
            start_idx = max(0, click_idx - 10)  # 查看最后 10 个事件
            preceding_events = event_types[start_idx:click_idx]
            
            # 标志 1：没有前面的 mousemove 的点击
            if 'mousemove' not in preceding_events:
                flags.append(f'CLICK_WITHOUT_MOUSEMOVE_at_{click_idx}')
            
            # 标志 2：没有 mousedown/mouseup 的点击
            if 'mousedown' not in preceding_events or 'mouseup' not in preceding_events:
                flags.append(f'INCOMPLETE_CLICK_SEQUENCE_at_{click_idx}')
            
            # 标志 3：即时点击（光标没有时间到达目标）
            if click_idx > 0:
                time_since_last_move = None
                for i in range(click_idx - 1, max(0, click_idx - 10), -1):
                    if event_types[i] == 'mousemove':
                        time_since_last_move = events[click_idx][1] - events[i][1]
                        break
                
                if time_since_last_move is not None and time_since_last_move < 0.05:
                    # 从 mousemove 到点击少于 50ms（太快）
                    flags.append(f'INSTANT_CLICK_at_{click_idx}')
        
        return {
            'total_events': len(events),
            'total_clicks': len(click_indices),
            'detection_flags': flags,
            'is_suspicious': len(flags) > 0,
        }
    
    def analyze_typing_sequence(self, events: List[Tuple[str, str, float]]) -> dict:
        """
        分析文本输入序列以查找不自然的模式。
        
        Args:
            events: (event_type, key, timestamp) 元组列表
        """
        flags = []
        
        # 按输入字段分组（简化）
        for i in range(len(events)):
            event_type, key, timestamp = events[i]
            
            if event_type == 'input':
                # 检查是否有前面的 keydown 事件
                preceding = events[max(0, i-5):i]
                has_keydown = any(e[0] == 'keydown' for e in preceding)
                
                if not has_keydown:
                    flags.append(f'INPUT_WITHOUT_KEYDOWN_at_{i}')
        
        # 检查打字前的焦点事件
        has_focus = any(e[0] == 'focus' for e in events[:10])
        has_typing = any(e[0] in ['keydown', 'keyup'] for e in events)
        
        if has_typing and not has_focus:
            flags.append('TYPING_WITHOUT_FOCUS')
        
        return {
            'detection_flags': flags,
            'is_suspicious': len(flags) > 0,
        }


# 示例：机器人点击（无 mousemove）
bot_click_events = [
    ('mousedown', 1.0),
    ('mouseup', 1.001),
    ('click', 1.002),  # 没有前面的 mousemove！
]

# 示例：人类点击（自然序列）
human_click_events = [
    ('mousemove', 0.5),
    ('mousemove', 0.55),
    ('mousemove', 0.6),
    ('mousemove', 0.7),
    ('mousedown', 0.85),
    ('mouseup', 0.95),
    ('click', 0.96),
]

analyzer = EventSequenceAnalyzer()
bot_result = analyzer.analyze_click_sequence(bot_click_events)
human_result = analyzer.analyze_click_sequence(human_click_events)

print(f"机器人标志: {bot_result['detection_flags']}")
# 输出: ['CLICK_WITHOUT_MOUSEMOVE_at_2', 'INCOMPLETE_CLICK_SEQUENCE_at_2']

print(f"人类标志: {human_result['detection_flags']}")
# 输出: []
```

### 时间分析：事件间间隔

**什么是事件间间隔？**

**事件间间隔**只是连续操作之间的时间——一次鼠标点击和下一次之间的间隙，或按下一个键和按下另一个键之间的间隙。

**为什么这很重要：**

人类在时间上具有自然变异性，因为：
- **认知处理**：思考下一步做什么（100-500ms）
- **视觉搜索**：在屏幕上找到下一个目标（200-800ms）
- **运动执行**：物理移动时间变化（菲茨定律：根据距离 100-1000ms）
- **疲劳和注意力**：疲劳时较慢，专注时较快
- **决策复杂性**：简单操作快速，复杂决策缓慢

**机器人泄露：**

1. **完美规律性**：事件以恰好 100ms 间隔间隔
2. **太快**：没有人类可以一致地每秒点击 10 次
3. **无方差**：标准偏差接近零（人类变化 20-50%）
4. **缺少"思考时间"**：机器人在前一个操作完成后立即执行下一个操作

**真实示例：**

```
人类点击 5 个按钮：
点击 1 → 0.0s
点击 2 → 0.8s   （变化：阅读，移动鼠标）
点击 3 → 1.3s   （0.5s 后）
点击 4 → 2.7s   （1.4s 后 - 犹豫？）
点击 5 → 3.2s   （0.5s 后）

机器人点击 5 个按钮：
点击 1 → 0.0s
点击 2 → 0.1s   （完美时间）
点击 3 → 0.2s   （完美时间）
点击 4 → 0.3s   （完美时间）
点击 5 → 0.4s   （完美时间）
```

机器人完美的 100ms 间隔对人类来说在统计上是不可能的。

```python
def analyze_event_timing(events: List[Tuple[str, float]]) -> dict:
    """
    分析事件之间的时间以检测机器人模式。
    """
    import statistics
    
    if len(events) < 3:
        return {'error': 'Insufficient events'}
    
    # 计算事件间间隔
    intervals = []
    for i in range(1, len(events)):
        interval = events[i][1] - events[i-1][1]
        intervals.append(interval)
    
    flags = []
    
    # 标志 1：完美时间（无方差）
    if len(intervals) > 3:
        variance = statistics.variance(intervals)
        if variance < 0.0001:  # 小于 0.1ms 方差
            flags.append('PERFECT_TIMING')
    
    # 标志 2：可疑的规律间隔
    # 检查间隔是否遵循模式
    if len(intervals) > 5:
        rounded = [round(i, 2) for i in intervals]
        unique_intervals = len(set(rounded))
        
        if unique_intervals < len(intervals) / 3:
            flags.append('REPETITIVE_TIMING')
    
    # 标志 3：不可能的速度（事件太接近）
    min_interval = min(intervals)
    if min_interval < 0.001:  # 小于 1ms
        flags.append('IMPOSSIBLE_SPEED')
    
    return {
        'avg_interval': statistics.mean(intervals),
        'interval_variance': statistics.variance(intervals) if len(intervals) > 1 else 0,
        'min_interval': min_interval,
        'max_interval': max(intervals),
        'detection_flags': flags,
        'is_suspicious': len(flags) > 1,
    }
```

!!! danger ""思考时间"检测器"
    高级反机器人系统测量**首次交互时间**：
    
    ```python
    # 从页面加载到首次用户操作的时间
    time_to_first_action = first_event_timestamp - page_load_timestamp
    
    if time_to_first_action < 0.5:  # 小于 500ms
        # 人类需要时间阅读、理解、定位元素
        return 'BOT_DETECTED'  # 太快不是人类
    ```
    
    **真实人类**：
    - 扫描页面（1-3 秒）
    - 阅读内容（2-10 秒）
    - 移动光标到目标（0.3-1 秒）
    - 点击（0.05-0.2 秒）
    
    **总计**：从页面加载到首次点击 3.5-14+ 秒
    
    **机器人**：
    - 在 DOMContentLoaded 后立即执行
    - 总时间：0.1-0.5 秒

## 行为检测中的机器学习

现代反机器人系统使用在数十亿交互上训练的**机器学习模型**来将行为分类为人类或机器人。这些系统不依赖简单的基于规则的检测——它们通过对大规模数据集的监督学习来学习模式。

### 基于 ML 的检测如何工作

**训练阶段：**

1. **数据收集**：数百万已确认的人类和机器人会话
2. **特征提取**：每个会话 100-500+ 个特征：
   - 鼠标：速度方差、曲率熵、加速度模式
   - 键盘：停留/飞行时间分布、双字母时间、错误率
   - 滚动：动量系数、减速曲线
   - 时间：事件间间隔、操作序列、犹豫模式
3. **模型训练**：随机森林、梯度提升、神经网络
4. **验证**：针对保留集进行测试以最小化误报

**检测阶段：**

1. **实时特征提取**：在浏览器中捕获用户交互
2. **模型推理**：特征馈送到训练模型（< 50ms）
3. **置信度分数**：机器人的概率（0.0-1.0）
4. **决策**：根据阈值阻止、挑战或允许

### 商业系统使用的特征类别

| 类别 | 示例特征 | 检测信号 |
|----------|-----------------|------------------|
| **鼠标动态** | 速度方差、轨迹熵、子移动计数 | 低方差 = 机器人 |
| **击键模式** | 停留时间标准差、双字母时间、错误率 | 完美时间 = 机器人 |
| **滚动行为** | 动量系数、减速率、惯性存在 | 即时滚动 = 机器人 |
| **事件序列** | 点击前的 mousemove、打字前的焦点、思考时间 | 缺少步骤 = 机器人 |
| **会话模式** | 总事件、会话持续时间、交互密度 | 太快 = 机器人 |
| **设备一致性** | 触摸 vs 鼠标一致性、屏幕方向变化 | 不一致 = 机器人 |

!!! info "基于 ML 的机器人检测系统"
    使用 ML 的商业机器人检测系统：
    
    - **DataDome**：声称使用在 25 亿+ 信号上训练的行为 ML 模型实现 **99.99% 的准确性**
    - **PerimeterX (Human Security)**："行为指纹识别™"，具有 400+ 行为信号
    - **Akamai Bot Manager**：每个会话分析 200+ 行为特征
    - **Castle.io**：实时 ML 推理，延迟低于 100ms
    - **Arkose Labs**：将行为分析与交互式 CAPTCHA 挑战结合
    - **Cloudflare Bot Management**：使用集成模型（随机森林 + 神经网络）
    
    **常见 ML 架构：**
    - **随机森林**：快速推理，可解释特征，适合表格数据
    - **梯度提升（XGBoost/LightGBM）**：高准确性，处理缺失值
    - **递归神经网络（LSTM/GRU）**：捕获时间序列（鼠标轨迹）
    - **集成方法**：组合多个模型以获得更高的准确性

**为什么 ML 有效：**

1. **自适应学习**：模型随着机器人技术的发展而更新
2. **高维度**：500+ 个特征不可能一致地伪造
3. **微妙模式**：检测人类看不到的相关性（例如，速度-曲率关系）
4. **低误报率**：在数百万真实用户上训练
5. **实时性能**：优化为 < 50ms 推理

**规避者的限制：**

你**不能**在本地复制基于 ML 的检测。这些模型是专有的，在大规模数据集上训练，并不断重新训练。你最好的方法是**专注于逼真的行为**，而不是试图逆向工程他们的模型。

## 结论

行为指纹识别代表了机器人检测的**前沿**。这是即使复杂的机器人也难以令人信服地克服的最后一道防线。

**关键要点：**

1. **人类是混乱的**：变异性、错误和犹豫是特征，而不是缺陷
2. **机器人是精确的**：恒定时间、直线和完美执行是危险信号
3. **物理学很重要**：运动遵循生物力学定律（菲茨定律、惯性、动量）
4. **上下文很重要**：操作必须以现实时间以自然序列发生
5. **ML 无处不在**：现代系统不使用基于规则的检测——它们学习模式

**Pydoll 的优势：**

与暴露 `navigator.webdriver` 并具有可检测的 CDP 特征的 Selenium/Puppeteer 不同，Pydoll 提供：

- **无 webdriver 标志**（更干净的指纹）
- **完整的 CDP 控制**（深度浏览器操作）
- **异步架构**（自然时间模式）
- **请求拦截**（标头一致性）

关于实用的规避技术和实现策略，请参阅[规避技术](./evasion-techniques.md)指南。

## 进一步阅读

### 学术研究

- **Ahmed, A. A. E., & Traore, I. (2007)**："A New Biometric Technology Based on Mouse Dynamics" - IEEE TDSC
- **Monrose, F., & Rubin, A. D. (2000)**："Keystroke Dynamics as a Biometric for Authentication" - Future Generation Computer Systems
- **Zheng, N., Paloski, A., & Wang, H. (2011)**："An Efficient User Verification System via Mouse Movements" - ACM CCS
- **Gamboa, H., & Fred, A. (2004)**："A Behavioral Biometric System Based on Human-Computer Interaction" - SPIE
- **Fitts, P. M. (1954)**："The Information Capacity of the Human Motor System" - Journal of Experimental Psychology

### 行业资源

- **[DataDome Bot Detection](https://datadome.co/)**：具有行为 ML 的商业机器人检测
- **[PerimeterX (Human Security)](https://www.humansecurity.com/)**：行为指纹识别和机器人管理
- **[Akamai Bot Manager](https://www.akamai.com/products/bot-manager)**：企业机器人检测
- **[Cloudflare Bot Management](https://www.cloudflare.com/application-services/products/bot-management/)**：基于 ML 的机器人检测
- **[F5 Shape Security](https://www.f5.com/products/security/shape-defense)**：行为分析先驱

### 技术文档

- **[菲茨定律维基百科](https://en.wikipedia.org/wiki/Fitts%27s_law)**：运动控制基础
- **[MDN: Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events)**：浏览器事件文档
- **[MDN: Keyboard Events](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent)**：键盘事件 API
- **[CSS Easing Functions](https://developer.mozilla.org/en-US/docs/Web/CSS/easing-function)**：滚动/动画时间

### 实用指南

- **[Pydoll: 类人交互](../../features/automation/human-interactions.md)**：实用的行为自动化
- **[Pydoll: 行为验证码绕过](../../features/advanced/behavioral-captcha-bypass.md)**：使用行为通过挑战
- **[规避技术](./evasion-techniques.md)**：完整的指纹识别规避指南
