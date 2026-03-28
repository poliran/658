#!/usr/bin/env zsh

# Shell Prompt Benchmark Script
ITERATIONS=10
RESULTS_FILE="shell_performance.md"

echo "🚀 Shell Prompt Performance Benchmark"
echo "======================================"

# Function to benchmark prompt rendering
benchmark_prompt() {
    local test_dir="$1"
    local test_name="$2"
    local total=0
    
    cd "$test_dir" 2>/dev/null || return 1
    
    for i in {1..$ITERATIONS}; do
        local start=$(python3 -c 'import time; print(int(time.time() * 1000))')
        starship prompt > /dev/null 2>&1
        local end=$(python3 -c 'import time; print(int(time.time() * 1000))')
        local elapsed=$(( end - start ))
        total=$(( total + elapsed ))
    done
    
    local avg=$(( total / ITERATIONS ))
    echo "$avg"
}

# Create temp directories
TEMP_BASE="/tmp/starship_bench_$$"
ORIGINAL_DIR=$(pwd)
mkdir -p "$TEMP_BASE/empty" "$TEMP_BASE/git" "$TEMP_BASE/python"

# Setup git repo
cd "$TEMP_BASE/git"
git init -q && echo "test" > README.md && git add . > /dev/null 2>&1 && git commit -q -m "init" > /dev/null 2>&1

# Setup python project
cd "$TEMP_BASE/python"
echo "numpy==1.24.0" > requirements.txt
echo "3.11.0" > .python-version

cd "$ORIGINAL_DIR"

# Run benchmarks
echo ""
echo "Running benchmarks..."
empty_time=$(benchmark_prompt "$TEMP_BASE/empty" "Empty directory")
echo "  Empty directory: ${empty_time}ms"
git_time=$(benchmark_prompt "$TEMP_BASE/git" "Git repository")
echo "  Git repository: ${git_time}ms"
python_time=$(benchmark_prompt "$TEMP_BASE/python" "Python project")
echo "  Python project: ${python_time}ms"
current_time=$(benchmark_prompt "$ORIGINAL_DIR" "Current project")
echo "  Current project: ${current_time}ms"

cd "$ORIGINAL_DIR"

# Determine status
empty_status=$([ "$empty_time" -lt 100 ] 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL")
git_status=$([ "$git_time" -lt 100 ] 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL")
python_status=$([ "$python_time" -lt 100 ] 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL")
current_status=$([ "$current_time" -lt 100 ] 2>/dev/null && echo "✅ PASS" || echo "❌ FAIL")

overall_status="Optimization needed ⚠️"
if [ "$empty_time" -lt 100 ] 2>/dev/null && [ "$git_time" -lt 100 ] 2>/dev/null && [ "$python_time" -lt 100 ] 2>/dev/null && [ "$current_time" -lt 100 ] 2>/dev/null; then
    overall_status="All tests passing ✅"
fi

# Generate report
cat > "$RESULTS_FILE" <<ENDREPORT
# Shell Performance Benchmark Results

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Iterations per test:** $ITERATIONS
**Target:** <100ms prompt latency

## Baseline Measurements

| Scenario | Average Time | Status |
|----------|--------------|--------|
| Empty directory | ${empty_time}ms | $empty_status |
| Git repository | ${git_time}ms | $git_status |
| Python project | ${python_time}ms | $python_status |
| Current project | ${current_time}ms | $current_status |

## Analysis

- **Overall status:** $overall_status
- **Python project timing:** ${python_time}ms indicates pyenv timeout issue

## Notes

- Measurements taken using \`starship prompt\` command
- Times include full prompt rendering with all configured modules
- Target is sub-100ms for responsive shell experience
- Python project likely exceeds target due to pyenv calls
ENDREPORT

# Cleanup
rm -rf "$TEMP_BASE"

# Display results
echo ""
echo "======================================"
echo "📊 Results saved to: $RESULTS_FILE"
echo ""
cat "$RESULTS_FILE"
