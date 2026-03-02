# Behavioral Fingerprinting

Behavioral fingerprinting analyzes how users interact with web applications rather than what tools they use. While network and browser fingerprints can be spoofed by setting the right values, human behavior follows biomechanical patterns that are difficult to replicate convincingly. Detection systems collect mouse movements, keystroke timing, scroll behavior, and interaction sequences, then use statistical models to distinguish humans from automation.

This document covers the detection techniques, the science behind them, and how Pydoll's humanization features address each vector.

!!! info "Module Navigation"
    - [Network Fingerprinting](./network-fingerprinting.md): TCP/IP, TLS, HTTP/2 protocol fingerprinting
    - [Browser Fingerprinting](./browser-fingerprinting.md): Canvas, WebGL, navigator properties
    - [Evasion Techniques](./evasion-techniques.md): Practical countermeasures

## Mouse Movement Analysis

Mouse movement is one of the most powerful behavioral indicators because human motor control follows biomechanical laws that simple automation cannot replicate. Detection systems collect `mousemove` events (each containing x, y coordinates and a timestamp) and analyze the trajectory for properties that distinguish organic movement from programmatic cursor teleportation.

### Fitts's Law

Fitts's Law describes the time required to move a pointer to a target. The Shannon formulation (MacKenzie, 1992), which is the most widely used version, states:

```
T = a + b * log2(D/W + 1)
```

Where `T` is the movement time, `a` is a constant representing reaction/start time, `b` is a constant representing the inherent speed of the input device, `D` is the distance to the target, and `W` is the width (size) of the target. The logarithmic relationship means that doubling the distance adds a fixed amount of time, while halving the target size adds the same fixed amount.

The implications for bot detection are significant. Humans take longer to reach small, distant targets and reach large, nearby targets quickly. They accelerate at the start of a movement, reach peak velocity roughly mid-path, and decelerate as they approach the target. Bots that move the cursor in constant time regardless of distance and target size violate Fitts's Law and are trivially detectable.

Detection systems measure the movement time for each click event, compute the expected time from the distance and target size, and flag movements that are significantly faster than Fitts's Law predicts or that show no correlation between distance/size and movement time.

### Trajectory Shape

Human hand movements between two points are not straight lines. Research by Abend, Bizzi, and Morasso (1982) showed that hand paths are typically curved due to biomechanical constraints of the arm's joints and muscles. Flash and Hogan (1985) demonstrated that human reaching movements follow minimum-jerk trajectories, where the trajectory minimizes the integral of jerk (the derivative of acceleration) over the movement duration. The resulting velocity profile is bell-shaped and is described by a quintic (5th degree) polynomial:

```
x(t) = x0 + (xf - x0) * (10t^3 - 15t^4 + 6t^5)
```

where `t` is normalized time from 0 to 1, and `x0`/`xf` are the start and end positions. This produces smooth acceleration from rest, peak velocity at approximately mid-path, and smooth deceleration back to rest.

Detection systems analyze trajectory curvature, velocity profiles, and acceleration patterns. The specific signals they look for include:

**Straight-line detection.** A perfectly straight path between two points (zero curvature at every sample) is the most obvious bot signal. Human paths always have some curvature due to the arm's rotational joints.

**Constant velocity.** Humans show a bell-shaped velocity profile (accelerate, peak, decelerate). A constant velocity throughout the movement indicates linear interpolation, which is the default behavior of most automation tools.

**Absence of sub-movements.** Long movements are composed of multiple overlapping sub-movements (Meyer et al., 1988), each with its own velocity peak. A movement covering 500+ pixels with a single smooth velocity peak is suspicious; real movements of that distance typically show 2-4 velocity peaks.

**No overshoot.** Humans frequently overshoot the target slightly (by 5-15 pixels) and make a small correction back. Perfectly precise movements that land exactly on target every time are statistically improbable.

### Movement Entropy

Entropy, in this context, measures the unpredictability of the mouse path. Detection systems divide the trajectory into segments, measure the direction change at each point, and compute Shannon entropy over the distribution of direction changes. A straight line has zero entropy (every segment points the same direction). A random walk has maximum entropy. Human movement has moderate-to-high entropy, reflecting the combination of intentional direction and involuntary variability.

Low entropy across many mouse movements in a session is a strong bot signal, even if individual movements have plausible curvature.

### Pydoll's Mouse Humanization

Pydoll implements comprehensive mouse humanization through the `humanize=True` parameter on click operations. When enabled, the mouse module generates movements that address each of the detection vectors described above:

The path follows a cubic Bezier curve with randomized control points, producing natural curvature rather than straight lines. The velocity along the path follows a minimum-jerk profile (`10t^3 - 15t^4 + 6t^5`), producing the bell-shaped velocity curve that Fitts's Law predicts. Movement duration is calculated using Fitts's Law with configurable constants (`a=0.070`, `b=0.150` by default).

Physiological tremor is simulated by adding Gaussian noise to cursor positions, with amplitude scaled inversely to velocity (tremor is more visible when the hand moves slowly, which matches real physiology). Overshoot occurs with 70% probability, overshooting the target by 3-12% of the total distance before making a correction movement. Micro-pauses (15-40ms) occur with 3% probability during the movement, simulating brief hesitations.

```python
# Basic humanized click
await element.click(humanize=True)

# The Mouse class can also be used directly for more control
from pydoll.interactions.mouse import Mouse

mouse = Mouse(connection_handler)
await mouse.click(500, 300, humanize=True)
```

!!! note "What Pydoll Does Not Do"
    Pydoll's mouse humanization does not currently model sub-movements for very long distances (the path is a single Bezier segment). For most web interactions, where distances are under 500 pixels, this is sufficient. Extremely long movements (full-screen diagonal traversals) may benefit from future multi-segment support.

## Keystroke Dynamics

Keystroke dynamics analyzes the timing patterns of keyboard input. The technique dates back to telegraph operators in the 1850s, who could identify each other by their Morse code "fist" (characteristic timing pattern). Modern systems measure timing at millisecond precision through `keydown` and `keyup` events.

### Timing Features

The two fundamental measurements are dwell time (the duration between `keydown` and `keyup` for a single key, typically 50-200ms for humans) and flight time (the duration between releasing one key and pressing the next, typically 80-400ms). The combination of dwell and flight times for consecutive key pairs is called a digraph latency.

Digraph latencies are not uniform. They depend on the specific key pair (bigram) being typed, because typing is a motor skill where common sequences are stored as procedural memory. The key biomechanical factors are:

**Hand alternation.** Bigrams typed with alternating hands (like "th", where "t" is left hand and "h" is right hand on QWERTY) are generally faster than same-hand bigrams (like "de", where both keys are on the left hand). The alternating hand can begin its movement while the first hand is still completing its keystroke.

**Finger distance.** Home-row to home-row transitions are fastest. Reaching to the top or bottom row adds time proportional to the physical distance the finger must travel.

**Finger independence.** Ring finger and pinky combinations on the same hand are slower than index and middle finger combinations, because the ring and pinky fingers share tendons and have less independent motor control.

**Frequency effects.** Frequently typed bigrams (like "th", "er", "in" in English) are executed faster due to motor memory, regardless of their physical layout.

### Detection Signals

Detection systems look for several signals that distinguish human typing from automation:

**Zero or constant dwell time.** Many automation tools dispatch `keydown` and `keyup` events with zero or near-zero delay between them (under 5ms). Real key presses have measurable dwell times. Constant dwell time across all keys is equally suspicious.

**Uniform flight time.** Setting a fixed interval between keystrokes (such as `type_text("hello", interval=0.1)`) produces perfectly regular timing that is trivially detectable. Human flight times vary by bigram, fatigue, and cognitive load.

**No typing errors.** In extended text input (50+ characters), the complete absence of backspace or delete presses is unusual. Humans make mistakes at a rate of roughly 1-5% depending on typing proficiency and text complexity.

**Superhuman speed.** Sustained typing above 150 WPM is beyond the capability of all but elite competitive typists. Automation tools that dispatch characters faster than this are immediately flagged.

### Pydoll's Keyboard Humanization

Pydoll's `type_text(humanize=True)` addresses each detection vector with configurable parameters:

Keystroke delays are drawn from a uniform distribution (30-120ms by default) rather than a fixed interval. Punctuation characters (`.!?;:,`) receive additional delay (80-180ms), simulating the pause that occurs when a typist considers sentence structure. Thinking pauses (300-700ms) occur with 2% probability, simulating brief moments of thought. Distraction pauses (500-1200ms) occur with 0.5% probability, simulating the typist looking away or being briefly interrupted.

Realistic typos occur with approximately 2% probability per character, with five distinct error types weighted by their real-world frequency: adjacent key errors (55%, pressing a neighboring key on QWERTY), transpositions (20%, swapping two consecutive characters), double presses (12%, hitting a key twice), skipped characters (8%, hesitating before typing correctly), and missed spaces (5%, forgetting a space between words). Each error type includes a realistic recovery sequence (pause, backspace, correction) with appropriate timing.

```python
# Humanized typing
await element.type_text("Hello, world!", humanize=True)

# With custom timing configuration
from pydoll.interactions.keyboard import Keyboard, TimingConfig, TypoConfig

config = TimingConfig(
    keystroke_min=0.04,
    keystroke_max=0.15,
    thinking_probability=0.03,
)
keyboard = Keyboard(connection_handler, timing_config=config)
await keyboard.type_text("Custom timing example", humanize=True)
```

!!! note "What Pydoll Does Not Do"
    Pydoll's keyboard humanization uses uniform random delays rather than bigram-aware timing. It does not model per-key dwell time variation or hand-alternation speed differences. For most automation scenarios (form filling, search queries), uniform variation is sufficient to pass behavioral detection. Applications requiring authentication-level keystroke biometric evasion would need custom timing models.

## Scroll Behavior Analysis

Scroll fingerprinting analyzes how users navigate vertically (and horizontally) through page content. The distinction between human and automated scrolling is stark: programmatic `window.scrollTo()` calls produce instant, discrete jumps, while human scrolling via mouse wheel, trackpad, or touch produces a stream of small incremental events with momentum and deceleration.

### Physical Scroll Characteristics

Mouse wheel scrolling produces discrete `wheel` events with consistent delta values (typically 100 or 120 pixels per notch, depending on OS and browser). The events arrive at irregular intervals reflecting how quickly the user turns the wheel. Trackpad scrolling produces many small events with decreasing deltas, simulating physical momentum. Touch scrolling is similar to trackpad but with larger initial deltas and longer deceleration tails.

Detection systems analyze the delta distribution, inter-event timing, and deceleration curve. A `scrollTo(0, 5000)` call produces a single jump with no intermediate events, which is fundamentally different from the hundreds of incremental events that a human scroll generates.

### Detection Signals

**Instant scrolling.** Using `window.scrollTo()` or `window.scrollBy()` with large values produces zero intermediate scroll events. Detection systems that listen for `scroll` events see the scroll position change in a single frame.

**Uniform deltas.** Programmatic scroll simulation that dispatches wheel events with constant delta values (e.g., always 100 pixels) lacks the natural variation in human scrolling, where delta values fluctuate by 10-30% due to inconsistent finger pressure.

**No deceleration.** Human scrolling, especially on trackpads, has a momentum phase where the scroll continues after the user lifts their finger, with exponentially decreasing velocity. Automated scrolling that stops abruptly lacks this deceleration tail.

**Absence of direction changes.** Humans frequently over-scroll and scroll back slightly, or pause partway down a page to read content. Automated scrolling that moves in one direction at constant speed without pauses or reversals is suspicious.

### Pydoll's Scroll Humanization

Pydoll's scroll module implements humanized scrolling through `scroll.by(position, distance, humanize=True)`:

The scroll follows a cubic Bezier easing curve (control points `0.645, 0.045, 0.355, 1.0` by default), producing natural acceleration and deceleration. Per-frame jitter of ±3 pixels adds variation to delta values. Micro-pauses (20-50ms) occur with 5% probability, simulating brief reading stops. Overshoot occurs with 15% probability, scrolling 2-8% past the target and correcting back. For large distances, the scroll is broken into multiple "flick" gestures (100-1200 pixels each), simulating how a real user scrolls through a long page with repeated swipes rather than a single continuous motion.

```python
from pydoll.interactions.scroll import Scroll, ScrollPosition

scroll = Scroll(connection_handler)

# Humanized scroll down by 800 pixels
await scroll.by(ScrollPosition.Y, 800, humanize=True)

# Scroll to top/bottom uses multiple human-like flicks
await scroll.to_bottom(humanize=True)
```

## Additional Detection Vectors

Beyond mouse, keyboard, and scroll analysis, sophisticated detection systems monitor several other behavioral signals.

### Focus and Visibility

The Page Visibility API (`document.visibilityState`) and focus events (`window.onfocus`, `window.onblur`) reveal whether the user is actively viewing the page. A real user's session includes tab switches, window minimizations, and periods of inactivity. An automation script that maintains continuous focus for hours without a single blur event is behaviorally anomalous. Similarly, `document.hasFocus()` returning `true` continuously for extended periods is unusual.

### Idle Patterns

Real users have natural idle periods: reading content, thinking before acting, being distracted. Detection systems measure the distribution of idle times between interactions. A session where every action follows the previous one within 100-500ms with no longer pauses follows a pattern that is statistically distinct from human browsing, where idle periods of 2-30 seconds between actions are normal.

### Event Sequence Integrity

Browsers generate specific event sequences for user interactions. A mouse click produces `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` in that order, preceded by `pointermove`/`mousemove` events showing the cursor approaching the click target. Automation tools that dispatch a bare `click` event without the preceding movement and pointer events are detectable through event sequence analysis.

Pydoll's CDP-based event dispatch generates complete event sequences because it uses Chrome's input simulation, which produces the same event chain as real user input.

## Machine Learning Detection

Modern anti-bot systems (DataDome, Akamai Bot Manager, Cloudflare Bot Management, PerimeterX/HUMAN Security) do not use simple threshold rules. They train machine learning models on millions of real user sessions and millions of known bot sessions, learning to distinguish humans from automation based on 50+ features simultaneously.

These models capture statistical properties that are hard to enumerate as individual rules: the joint distribution of movement speed and curvature, the correlation between typing speed and error rate, the relationship between scroll depth and reading time, and the overall "rhythm" of a browsing session. A system that passes every individual check but has subtly wrong correlations between features can still be flagged by a well-trained model.

The practical implication is that behavioral evasion must be consistent across all interaction types, not just individually plausible. Pydoll's `humanize=True` parameter provides a coherent humanization layer across mouse, keyboard, and scroll interactions, but the developer is still responsible for higher-level behavioral plausibility: adding reading delays between page loads, varying the pace of a multi-page workflow, and including natural idle periods.

## References

- Fitts, P. M. (1954). The Information Capacity of the Human Motor System in Controlling the Amplitude of Movement. Journal of Experimental Psychology.
- MacKenzie, I. S. (1992). Fitts' Law as a Research and Design Tool in Human-Computer Interaction. Human-Computer Interaction.
- Flash, T., & Hogan, N. (1985). The Coordination of Arm Movements: An Experimentally Confirmed Mathematical Model. Journal of Neuroscience.
- Abend, W., Bizzi, E., & Morasso, P. (1982). Human Arm Trajectory Formation. Brain.
- Meyer, D. E., Abrams, R. A., Kornblum, S., Wright, C. E., & Smith, J. E. K. (1988). Optimality in Human Motor Performance. Psychological Review.
- Ahmed, A. A. E., & Traore, I. (2007). A New Biometric Technology Based on Mouse Dynamics. IEEE TDSC.
