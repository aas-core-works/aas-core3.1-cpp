"""Run all tests and re-record the golden data."""

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import uuid


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    print("Building and running all tests...")
    env = os.environ.copy()
    env["AAS_CORE_AAS_3_1_TEST_DATA_DIR"] = str(repo_root / "test_data")

    if "VCPKG_ROOT" not in os.environ:
        print(
            "The environment variable VCPKG_ROOT is not set -- we use VCPKG to install "
            "the dependencies in the development scripts. See the article "
            "Getting Started in documentation for more details how to install VCPKG "
            "or visit https://vcpkg.io.",
            file=sys.stderr,
        )
        return 1

    vcpkg_root = pathlib.Path(env["VCPKG_ROOT"])
    if not vcpkg_root.exists():
        print(
            f"The VCPKG directory pointed to by the environment variable VCPKG_ROOT "
            f"does not exist: {vcpkg_root}",
            file=sys.stderr,
        )
        return 1

    vcpkg_cmake = vcpkg_root / "scripts/buildsystems/vcpkg.cmake"
    if not vcpkg_cmake.exists():
        print(
            f"The vcpkg.cmake file does not exist: {vcpkg_cmake}. "
            f"Is your VCPKG properly set up?",
            file=sys.stderr,
        )
        return 1

    # NOTE (mristin):
    # We specify build ID in a separate statement in case we want to debug
    # the re-recording of tests and want to re-build in the same directory.
    build_id = str(uuid.uuid4())

    build_dir = repo_root / f"build-for-update-{build_id}"

    # NOTE (mristin):
    # When we debug this script, we usually override ``build_id`` so that we can
    # repeatedly run it. Hence, we allow the build directory to exist here.
    build_dir.mkdir(exist_ok=True)

    cmd = [
        "cmake",
        "-DBUILD_TESTS=ON",
        "-DCMAKE_BUILD_TYPE=Debug",
        f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_cmake}",
        "-S.",
        f"-B{build_dir}",
    ]
    cmd_joined = " ".join(cmd)
    print(f"Executing: {cmd_joined}")
    subprocess.check_call(
        cmd,
        env=env,
        cwd=repo_root,
    )

    cmd = ["cmake", "--build", str(build_dir), "-j", "8"]
    cmd_joined = " ".join(cmd)
    print(f"Executing: {cmd_joined}")
    subprocess.check_call(cmd, env=env, cwd=repo_root)

    cmd = ["ctest", "-C", "DEBUG"]
    cmd_joined = " ".join(cmd)
    print(f"Executing: {cmd_joined}")
    subprocess.check_call(cmd, env=env, cwd=build_dir)

    # NOTE (mristin):
    # We delete the build directory only if everything succeeded. Otherwise,
    # we leave it lingering so that we can investigate the issue.

    if build_dir.exists():
        shutil.rmtree(build_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
