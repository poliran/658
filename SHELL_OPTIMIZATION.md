# Shell Optimization Documentation

## Overview

This document describes the shell prompt optimizations implemented to achieve sub-100ms latency and eliminate Starship pyenv timeout warnings.

## Problem

The original Starship configuration was causing:
- Timeout warnings when entering Python project directories
- Prompt latency exceeding 100ms in Python projects (131ms measured)
- Slow pyenv calls blocking prompt rendering

## Solution

Implemented a minimal Starship configuration with strict timeout enforcement and optimized module detection.

## Changes Made

### 1. Starship Configuration (`~/.config/starship.toml`)

**Backup Location:** `~/.config/starship.toml.backup`

#### Key Changes:
- **Timeout:** Reduced from 1000ms to 100ms (`command_timeout = 100`)
- **Modules:** Stripped to essentials (directory, git_branch, git_status, python, character)
- **Python Module:**
  - Disabled `pyenv_version_name` to avoid slow pyenv calls
  - Strict file detection: only activates with `pyproject.toml`, `requirements.txt`, `.python-version`, `Pipfile`, or `setup.py`
  - Disabled folder and extension detection to prevent false positives
  - Uses Python interpreter version instead of pyenv for speed

#### Removed Modules:
- nodejs, rust, golang, java (language modules)
- docker_context, kubernetes, aws (infrastructure)
- memory_usage, battery, time, status, jobs, shell, container (system info)
- username, hostname, git_commit, cmd_duration, package

### 2. Performance Improvements

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| Empty directory | 26ms | 24ms | 2ms faster |
| Git repository | 50ms | 48ms | 2ms faster |
| Python project | 131ms | 32ms | **99ms faster (75% reduction)** |
| Current project | 65ms | 61ms | 4ms faster |

**All scenarios now pass the sub-100ms target ✅**

### 3. Files Created

- `shell_benchmark.sh` - Benchmark script for measuring prompt performance
- `shell_performance.md` - Performance test results
- `SHELL_OPTIMIZATION.md` - This documentation

## Rollback Procedure

If you need to restore the original configuration:

```bash
# Restore original Starship config
cp ~/.config/starship.toml.backup ~/.config/starship.toml

# Restart your shell or reload config
exec zsh
```

## Testing

Run the benchmark script to verify performance:

```bash
cd ~/Documents/personal/projects/658
./shell_benchmark.sh
```

Expected results: All scenarios should complete in <100ms.

## Customization

### Re-enable Specific Modules

To add back a module (e.g., nodejs), edit `~/.config/starship.toml`:

1. Add module to format string:
```toml
format = """
$directory\
$git_branch\
$git_status\
$nodejs\
$python\
$line_break\
$character"""
```

2. Add module configuration:
```toml
[nodejs]
format = "via [$symbol($version )]($style)"
symbol = "⬢ "
style = "bold green"
detect_files = ["package.json"]
detect_folders = []
detect_extensions = []
```

3. Test performance impact:
```bash
./shell_benchmark.sh
```

### Adjust Timeout

If you need more time for certain operations:

```toml
# In ~/.config/starship.toml
command_timeout = 150  # Increase to 150ms
```

**Note:** Keep timeout as low as possible for responsive shell experience.

### Re-enable Pyenv Version Display

If you need pyenv version names and can accept slower performance:

```toml
[python]
pyenv_version_name = true
```

**Warning:** This will increase Python project prompt latency to ~130ms.

## Maintenance

### Periodic Performance Checks

Run the benchmark monthly to catch performance regressions:

```bash
cd ~/Documents/personal/projects/658
./shell_benchmark.sh
```

### Updating Starship

After updating Starship, verify performance hasn't regressed:

```bash
brew upgrade starship
./shell_benchmark.sh
```

## Technical Details

### Why Pyenv is Slow

The `pyenv version-name` command:
1. Searches for `.python-version` files up the directory tree
2. Checks multiple pyenv shims and versions
3. Executes shell scripts and subprocesses
4. Can take 100-130ms on average

### Alternative: Python Interpreter Detection

Starship can detect Python version directly from the interpreter:
- Faster: ~30ms vs ~130ms
- Still accurate for most use cases
- Doesn't require pyenv to be in PATH

### Benchmark Methodology

The `shell_benchmark.sh` script:
- Runs `starship prompt` 10 times per scenario
- Measures time using Python's `time.time()` (millisecond precision)
- Tests in isolated temporary directories
- Averages results to account for variance

## Troubleshooting

### Still Seeing Timeout Warnings

1. Check if pyenv is enabled:
```bash
grep pyenv_version_name ~/.config/starship.toml
```
Should show `pyenv_version_name = false`

2. Verify timeout setting:
```bash
grep command_timeout ~/.config/starship.toml
```
Should show `command_timeout = 100`

3. Restart shell:
```bash
exec zsh
```

### Prompt Missing Information

If you need more information displayed:
1. Identify which module you need from the backup config
2. Add it to the minimal config following the customization guide above
3. Test performance impact with benchmark script

### Performance Regression

If performance degrades over time:
1. Run benchmark to identify slow scenario
2. Check for new modules added to config
3. Verify pyenv_version_name is still false
4. Consider increasing timeout slightly if needed

## References

- [Starship Documentation](https://starship.rs/)
- [Starship Performance Guide](https://starship.rs/advanced-config/#performance)
- Original config backup: `~/.config/starship.toml.backup`

## Summary

✅ **Achieved sub-100ms prompt latency across all scenarios**  
✅ **Eliminated pyenv timeout warnings**  
✅ **Maintained essential prompt information (directory, git, python)**  
✅ **75% performance improvement in Python projects**  
✅ **Easy rollback available**
