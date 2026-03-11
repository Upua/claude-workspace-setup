---
name: performance-optimizer
description: Profile code, identify bottlenecks, analyze algorithmic complexity, detect memory leaks, and suggest caching/optimization strategies.
# No binary requirements - knowledge skill (profiling tools are ecosystem-specific)
# Context cost: ~74 lines (~1.5K tokens)
---

# Performance Optimizer Skill

## Trigger
Activated when asked about performance, optimization, speed, bottlenecks, profiling, or slow code.

## Capabilities
- Profile code execution and identify bottlenecks
- Analyze algorithmic complexity (Big O)
- Detect memory leaks and inefficient memory usage
- Identify N+1 queries and database performance issues
- Suggest caching strategies
- Optimize bundle sizes for web applications
- Analyze network request patterns

## Analysis Framework

### 1. Profiling Checklist
- [ ] CPU-bound vs I/O-bound identification
- [ ] Hot path analysis
- [ ] Memory allocation patterns
- [ ] Garbage collection pressure
- [ ] Thread/async utilization

### 2. Common Bottlenecks
| Pattern | Symptom | Solution |
|---------|---------|----------|
| N+1 Queries | Multiple DB calls in loop | Eager loading, batch queries |
| Synchronous I/O | Blocking main thread | Async/await, workers |
| Large bundles | Slow initial load | Code splitting, lazy loading |
| Memory leaks | Growing memory usage | Proper cleanup, weak refs |
| Inefficient loops | O(n²) or worse | Better algorithms, early exit |

### 3. Measurement Commands
```bash
# Node.js
node --prof app.js
node --prof-process isolate-*.log

# Python
python -m cProfile -s cumtime script.py
py-spy top --pid <PID>

# Web
lighthouse <url> --output json
```

## Output Format
```
PERFORMANCE ANALYSIS
====================
Overall Score: [1-100]
Critical Issues: [count]

BOTTLENECKS (by impact)
-----------------------
1. [HIGH] Description
   Location: file:line
   Current: [metric]
   Target: [metric]
   Fix: [specific recommendation]

2. [MEDIUM] ...

QUICK WINS
----------
- [Optimization that's easy to implement]

RECOMMENDATIONS
---------------
1. Short-term (immediate impact)
2. Medium-term (requires refactoring)
3. Long-term (architectural changes)
```
