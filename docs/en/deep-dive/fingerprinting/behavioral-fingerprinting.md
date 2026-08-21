# Behavioral fingerprinting

Behavioral fingerprinting analyzes how a user interacts with a page rather than what tools they use. Network and browser fingerprints can be spoofed by setting the right values, but human behavior follows biomechanical patterns that are hard to replicate convincingly. Detection systems collect mouse movement, keystroke timing, scroll behavior, and interaction sequences, then use statistical models to separate humans from automation. This page explains those techniques, the science behind them, and how Pydoll's humanization addresses each one.

## Mouse movement analysis

Mouse movement is one of the strongest behavioral indicators, because human motor control follows biomechanical laws that simple automation does not reproduce. Detection systems collect `mousemove` events (each with x, y coordinates and a timestamp) and analyze the trajectory for properties that separate organic movement from programmatic cursor teleportation.

### Fitts's Law

Fitts's Law describes the time needed to move a pointer to a target. The Shannon formulation (MacKenzie, 1992) is the most widely used:

```
T = a + b * log2(D/W + 1)
```

`T` is the movement time, `a` is a start/reaction constant, `b` is the input device's inherent speed, `D` is the distance to the target, and `W` is the target width. The logarithm means that doubling the distance adds a fixed amount of time, and halving the target size adds the same fixed amount.

The implication for detection is direct. Humans take longer to reach small, distant targets and reach large, nearby targets quickly. They accelerate at the start, hit peak velocity around mid-path, and decelerate as they arrive. A bot that moves in constant time regardless of distance and target size violates Fitts's Law and is trivially detectable. Detection systems measure the movement time before each click, compute the time Fitts's Law predicts from the distance and target size, and flag movements that are far faster than predicted or show no correlation between distance/size and time.

### Trajectory shape

Human hand movements between two points are not straight lines. Abend, Bizzi, and Morasso (1982) showed that hand paths curve because of the arm's joints and muscles. Flash and Hogan (1985) showed that reaching movements follow minimum-jerk trajectories, minimizing the integral of jerk (the derivative of acceleration) over the movement. The velocity profile is bell-shaped, described by a quintic polynomial:

```
x(t) = x0 + (xf - x0) * (10t^3 - 15t^4 + 6t^5)
```

where `t` is normalized time from 0 to 1 and `x0`/`xf` are the start and end positions. This gives smooth acceleration from rest, peak velocity near mid-path, and smooth deceleration back to rest.

Detection systems analyze curvature, velocity, and acceleration for four tells:

- **Straight-line paths.** Zero curvature at every sample is the most obvious bot signal; human paths always curve because the arm rotates around joints.
- **Constant velocity.** Humans show a bell-shaped velocity profile. Constant velocity indicates linear interpolation, the default in most automation tools.
- **No sub-movements.** Long movements are built from overlapping sub-movements (Meyer et al., 1988), each with its own velocity peak. A 500-pixel move with a single smooth peak is suspicious; real ones show 2 to 4 peaks.
- **No overshoot.** Humans often overshoot by 5 to 15 pixels and correct back. Landing exactly on target every time is statistically improbable.

### Movement entropy

Entropy here measures how unpredictable the path is. Detection systems split the trajectory into segments, measure the direction change at each point, and compute Shannon entropy over the distribution of those changes. A straight line has zero entropy; a random walk has maximum entropy; human movement sits in between, combining intent with involuntary variability. Low entropy across many movements in a session is a strong bot signal, even when individual movements look plausibly curved.

### How Pydoll humanizes the mouse

With `humanize=True`, Pydoll generates movements that answer each of the tells above. The path follows a cubic Bezier curve with randomized control points, so it curves rather than running straight. The velocity along it follows the minimum-jerk profile (`10t^3 - 15t^4 + 6t^5`), giving the bell-shaped curve Fitts's Law predicts, and the duration is computed from Fitts's Law itself. Physiological tremor is added as position noise scaled inversely to velocity (more visible when the cursor moves slowly, matching real physiology), overshoot happens with a set probability before a correction, and occasional micro-pauses simulate brief hesitations.

```python
await element.click(humanize=True)
await tab.mouse.click(500, 300, humanize=True)   # coordinate form
```

The timing model is configurable through `MouseTimingConfig` assigned to `tab.mouse.timing`. See [Human-like interactions](../../stealth/human-like-interactions.md) for the practical guide.

!!! note "What this does not model"
    Pydoll's mouse path is a single Bezier segment; it does not split very long movements into multiple sub-movements. For typical web interactions (under about 500 pixels) that is enough. Full-screen diagonal traversals are the case where sub-movements would matter.

## Keystroke dynamics

Keystroke dynamics analyzes the timing of keyboard input. The idea is old: 1850s telegraph operators recognized each other by their Morse "fist", a characteristic timing pattern. Modern systems measure the same thing at millisecond precision through `keydown` and `keyup` events.

### Timing features

The two fundamental measurements are dwell time (from `keydown` to `keyup` on one key, usually 50 to 200ms) and flight time (from releasing one key to pressing the next, usually 80 to 400ms). The dwell and flight of a consecutive key pair is a digraph latency, and it is not uniform, because typing is a motor skill where common sequences live in procedural memory:

- **Hand alternation.** Bigrams typed with alternating hands (like "th" on QWERTY) are faster than same-hand ones (like "de"), because the second hand starts moving while the first is still finishing.
- **Finger travel.** Home-row to home-row transitions are fastest; reaching the top or bottom row costs time proportional to the distance.
- **Finger independence.** Ring and pinky combinations are slower than index and middle, because those fingers share tendons and move less independently.
- **Frequency.** Frequently typed bigrams ("th", "er", "in") run faster from motor memory, regardless of layout.

### Detection signals

- **Zero or constant dwell time.** Many tools dispatch `keydown` and `keyup` with near-zero delay; real presses have measurable, varying dwell.
- **Uniform flight time.** A fixed interval between keystrokes produces perfectly regular timing that is trivial to detect. Human flight times vary by bigram, fatigue, and load.
- **No typing errors.** In 50-plus characters, a total absence of backspace is unusual; humans err at roughly 1 to 5%.
- **Superhuman speed.** Sustained typing above 150 WPM is beyond all but elite typists, so anything faster is flagged.

### How Pydoll humanizes typing

With `type_text(humanize=True)`, keystroke delays are drawn from a distribution rather than a fixed interval. Punctuation gets extra delay, simulating the pause a typist takes at sentence structure; occasional thinking pauses and rarer distraction pauses simulate moments of thought or interruption. Realistic typos occur at roughly 2% per character across five error types weighted by real-world frequency (adjacent-key, transposition, double-press, skipped character, missed space), each followed by a natural correction sequence.

```python
await element.type_text('Hello, world!', humanize=True)
```

See [Human-like interactions](../../stealth/human-like-interactions.md) for how to tune it.

!!! note "What this does not model"
    Pydoll uses variable random delays, not bigram-aware timing, and does not model per-key dwell or hand-alternation differences. For form filling and search queries that is enough. Evading authentication-grade keystroke biometrics would need a custom timing model.

## Scroll behavior

Scroll fingerprinting analyzes how a user moves through page content. A programmatic `window.scrollTo()` is an instant, discrete jump, while a human scroll (wheel, trackpad, or touch) is a stream of small incremental events with momentum and deceleration.

Mouse wheels produce discrete `wheel` events with consistent deltas (often 100 or 120 pixels per notch) at irregular intervals. Trackpads produce many small events with decreasing deltas that simulate momentum. Touch is similar with larger initial deltas and a longer deceleration tail. Detection systems read the delta distribution, inter-event timing, and deceleration curve, and look for:

- **Instant scrolling.** `scrollTo`/`scrollBy` with large values changes the scroll position in a single frame, with no intermediate events.
- **Uniform deltas.** Constant delta values lack the 10 to 30% variation of real scrolling.
- **No deceleration.** Human scrolling, especially on trackpads, keeps moving after the finger lifts, with exponentially decreasing velocity. Automation that stops abruptly has no tail.
- **No direction changes.** Humans over-scroll and correct, or pause to read. One-directional constant-speed scrolling is suspicious.

Pydoll's humanized scroll answers these: it follows a Bezier easing curve for natural acceleration and deceleration, adds per-frame jitter to the deltas, inserts occasional micro-pauses, sometimes overshoots and corrects, and breaks long distances into multiple "flick" gestures rather than one continuous motion.

```python
from pydoll.constants import ScrollPosition

await tab.scroll.by(ScrollPosition.DOWN, 800, humanize=True)
```

## Other behavioral signals

Beyond mouse, keyboard, and scroll, some systems watch several more signals.

**Focus and visibility.** The Page Visibility API (`document.visibilityState`) and focus events reveal whether the user is actively viewing the page. A real session has tab switches, minimizations, and idle periods; a script that holds continuous focus for hours without a single blur is anomalous.

**Idle patterns.** Real users pause to read and think. A session where every action follows the previous one within 100 to 500ms, with no longer gaps, is statistically distinct from human browsing, where 2 to 30 second idles are normal.

**Event-sequence integrity.** A real click produces `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` in order, preceded by movement events approaching the target. Tools that dispatch a bare `click` with no preceding movement are detectable. Pydoll dispatches input through Chrome's own input simulation over CDP, so it generates the same complete event chain as real input.

## Machine-learning detection

Modern anti-bot systems (DataDome, Akamai Bot Manager, Cloudflare Bot Management, HUMAN Security) do not rely on threshold rules. They train models on millions of real and known-bot sessions, learning to separate them across 50-plus features at once: the joint distribution of speed and curvature, the correlation between typing speed and error rate, the relationship between scroll depth and reading time, the overall rhythm of a session. A run that passes every individual check but has subtly wrong correlations between features can still be flagged.

The practical consequence is that behavioral realism has to be consistent across interaction types, not just plausible one at a time. Pydoll's `humanize=True` gives a coherent humanization layer across mouse, keyboard, and scroll, but higher-level plausibility is still yours: add reading delays between page loads, vary the pace of a multi-page workflow, and include natural idle periods.

## Related

- [Network fingerprinting](network-fingerprinting.md): the protocol layer (TCP/IP, TLS, HTTP/2).
- [Browser fingerprinting](browser-fingerprinting.md): canvas, WebGL, fonts, and navigator.
- [Human-like interactions](../../stealth/human-like-interactions.md): the practical guide to `humanize=True`.

## References

- Fitts, P. M. (1954). The Information Capacity of the Human Motor System in Controlling the Amplitude of Movement. Journal of Experimental Psychology.
- MacKenzie, I. S. (1992). Fitts' Law as a Research and Design Tool in Human-Computer Interaction. Human-Computer Interaction.
- Flash, T., & Hogan, N. (1985). The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model. Journal of Neuroscience.
- Abend, W., Bizzi, E., & Morasso, P. (1982). Human Arm Trajectory Formation. Brain.
- Meyer, D. E., Abrams, R. A., Kornblum, S., Wright, C. E., & Smith, J. E. K. (1988). Optimality in Human Motor Performance. Psychological Review.
- Ahmed, A. A. E., & Traore, I. (2007). A New Biometric Technology Based on Mouse Dynamics. IEEE TDSC.
