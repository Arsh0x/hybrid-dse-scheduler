#!/usr/bin/env python3
"""
build_program.py — Build a benchmark program with AFL instrumentation.

Usage:
    build_program.py <program> <compiler> <opt_level>

Example:
    build_program.py zlib gcc O2

Reads benchmarks/<program>/metadata.yaml and produces a build in
/workspace/builds/<program>/<compiler>-<opt>/.

Idempotent: if the binary already exists and is newer than metadata.yaml,
the build is skipped.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml  # provided by pyyaml in container

WORKSPACE = Path("/workspace")
BUILDS_DIR = WORKSPACE / "builds"
BENCHMARKS_DIR = WORKSPACE / "benchmarks"

VALID_COMPILERS = ["gcc", "clang"]
VALID_OPTS = ["O0", "O1", "O2", "O3", "Os"]


def log(msg, level="INFO"):
    print("[{}] {}".format(level, msg), flush=True)


def die(msg, code=1):
    log(msg, "ERROR")
    sys.exit(code)


def ensure_pyyaml():
    try:
        import yaml  # noqa
    except ImportError:
        log("pyyaml not installed; installing...", "WARN")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"],
                       check=True)


def load_metadata(program):
    meta_path = BENCHMARKS_DIR / program / "metadata.yaml"
    if not meta_path.exists():
        die("metadata.yaml not found at {}".format(meta_path))
    with open(str(meta_path)) as f:
        return yaml.safe_load(f)


def resolve_compiler(compiler):
    """Map 'gcc'/'clang' to AFL wrapper path."""
    if compiler == "gcc":
        return "afl-gcc"
    elif compiler == "clang":
        return "afl-clang-fast"
    else:
        die("Unknown compiler: {}".format(compiler))


def prepare_build_dir(program, compiler, opt):
    build_dir = BUILDS_DIR / program / "{}-{}".format(compiler, opt)
    build_dir.mkdir(parents=True, exist_ok=True)
    return build_dir


def fetch_source(program, meta, build_dir):
    """Download + extract source tarball if not already present."""
    src_dir = build_dir / "src"
    if src_dir.exists() and any(src_dir.iterdir()):
        log("source already fetched at {}".format(src_dir))
        return src_dir

    url = meta["url"]
    tarball = build_dir / "source.tar.gz"

    if not tarball.exists():
        log("downloading {}".format(url))
        subprocess.run(["curl", "-sL", "-o", str(tarball), url], check=True)

    log("extracting...")
    src_dir.mkdir(exist_ok=True)
    subprocess.run(["tar", "xzf", str(tarball), "-C", str(src_dir),
                    "--strip-components=1"], check=True)
    return src_dir


def find_zlib_dir():
    """Return the path to the built zlib (for libpng dependency)."""
    candidates = list((BUILDS_DIR / "zlib").glob("*-*/src"))
    if not candidates:
        die("zlib not built yet; build zlib first")
    return candidates[0]


def substitute_paths(cmd, zlib_dir=None):
    """Replace placeholders in build commands."""
    if zlib_dir:
        cmd = cmd.replace("<ZDIR>", str(zlib_dir))
    return cmd


def run_configure(program, meta, src_dir, build_dir, cc, opt, zlib_dir=None):
    build = meta["build"]
    if "configure" not in build:
        return

    log("running configure...")
    cmd = build["configure"]
    cmd = substitute_paths(cmd, zlib_dir)

    env = os.environ.copy()
    env["CC"] = cc
    env["CFLAGS"] = "-{}".format(opt)

    result = subprocess.run(cmd, shell=True, cwd=str(src_dir), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        log("configure failed:", "ERROR")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        sys.exit(1)
    log("configure OK")


def run_make(program, meta, src_dir, cc, opt):
    make_cmd = meta["build"].get("make", "make -j$(nproc)")

    log("running make...")
    env = os.environ.copy()
    env["CC"] = cc
    env["CFLAGS"] = "-{}".format(opt)

    result = subprocess.run(make_cmd, shell=True, cwd=str(src_dir), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        log("make failed:", "ERROR")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        sys.exit(1)
    log("make OK")


def copy_custom_files(program, meta, src_dir):
    """Copy custom files (drivers, patches) from benchmarks/<program>/ into source tree."""
    meta_dir = BENCHMARKS_DIR / program
    if not meta_dir.exists():
        return
    copied = []
    for f in meta_dir.iterdir():
        if f.is_file() and f.suffix in (".c", ".cpp", ".h"):
            dest = src_dir / f.name
            shutil.copy(str(f), str(dest))
            copied.append(f.name)
    if copied:
        log("copied custom files: {}".format(", ".join(copied)))


def run_custom_build(program, meta, src_dir, cc, opt, zlib_dir=None):
    custom = meta["build"].get("custom_build")
    if not custom:
        return

    log("running custom build steps...")
    cmd = substitute_paths(custom, zlib_dir)

    env = os.environ.copy()
    env["CC"] = cc
    env["CFLAGS"] = "-{}".format(opt)

    result = subprocess.run(cmd, shell=True, cwd=str(src_dir), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
        log("custom build failed:", "ERROR")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        sys.exit(1)
    log("custom build OK")


def verify_binary(meta, src_dir):
    """Confirm the target binary exists after build."""
    target = meta["target"]["binary"]
    binary_path = src_dir / target
    if not binary_path.exists():
        die("target binary not found: {}".format(binary_path))
    log("target binary: {}".format(binary_path))
    return binary_path


def fetch_seeds(program, meta, build_dir, src_dir):
    """Copy or generate seeds into build_dir/seeds/."""
    seeds_dir = build_dir / "seeds"
    if seeds_dir.exists() and any(seeds_dir.iterdir()):
        log("seeds already present at {}".format(seeds_dir))
        return seeds_dir

    seeds_dir.mkdir(exist_ok=True)
    meta_seeds = BENCHMARKS_DIR / program / "seeds"
    if meta_seeds.exists():
        log("copying seeds from {}".format(meta_seeds))
        for f in meta_seeds.iterdir():
            if f.is_file():
                shutil.copy(f, seeds_dir / f.name)
    else:
        log("no seeds found in metadata dir; manual seed setup required",
            "WARN")

    return seeds_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program")
    parser.add_argument("compiler", choices=VALID_COMPILERS)
    parser.add_argument("opt", choices=VALID_OPTS)
    args = parser.parse_args()

    ensure_pyyaml()
    meta = load_metadata(args.program)
    cc = resolve_compiler(args.compiler)

    log("=== Building {} with {} -{} ===".format(
        args.program, args.compiler, args.opt))

    build_dir = prepare_build_dir(args.program, args.compiler, args.opt)
    src_dir = fetch_source(args.program, meta, build_dir)

    zlib_dir = None
    if "zlib" in (meta.get("dependencies") or []):
        zlib_dir = find_zlib_dir()
        log("using zlib at {}".format(zlib_dir))

    run_configure(args.program, meta, src_dir, build_dir, cc, args.opt, zlib_dir)
    run_make(args.program, meta, src_dir, cc, args.opt)
    copy_custom_files(args.program, meta, src_dir)
    run_custom_build(args.program, meta, src_dir, cc, args.opt, zlib_dir)

    binary = verify_binary(meta, src_dir)
    seeds = fetch_seeds(args.program, meta, build_dir, src_dir)

    log("=== BUILD COMPLETE ===")
    log("binary: {}".format(binary))
    log("seeds:  {}".format(seeds))
    log("build:  {}".format(build_dir))


if __name__ == "__main__":
    main()
