#!/usr/bin/env python3
import hashlib
import io
import os
import platform
import stat
import sys
import tarfile
import urllib.request

import gha

# Configuration
version = "v0.10.0"
url_base = f"https://github.com/mozilla/sccache/releases/download/{version}/"

platform = f"{platform.system()}-{platform.machine()}"
if platform == 'Windows-AMD64':
    expected_hash = "0d499d0f73fa575f805df014af6ece49b840195fb7de0c552230899d77186ceb"
    download_file_name = f"sccache-{version}-x86_64-pc-windows-msvc"
    binary_name = "sccache.exe"
elif platform == 'Windows-ARM64':
    expected_hash = "5fd6cd6dd474e91c37510719bf27cfe1826f929e40dd383c22a7b96da9a5458d"
    download_file_name = f"sccache-{version}-aarch64-pc-windows-msvc"
    binary_name = "sccache.exe"
elif platform == 'Linux-x86_64':
    expected_hash = "1fbb35e135660d04a2d5e42b59c7874d39b3deb17de56330b25b713ec59f849b"
    download_file_name = f"sccache-{version}-x86_64-unknown-linux-musl"
    binary_name = "sccache"
elif platform == 'Linux-aarch64':
    expected_hash = "d6a1ce4acd02b937cd61bc675a8be029a60f7bc167594c33d75732bbc0a07400"
    download_file_name = f"sccache-{version}-aarch64-unknown-linux-musl"
    binary_name = "sccache"
elif platform == 'Darwin-x86_64':
    expected_hash = "6d4a77802ec83607478df7b6338be28171e65e58a38a49497ebec1fbb300fce4"
    download_file_name = f"sccache-{version}-x86_64-apple-darwin"
    binary_name = "sccache"
elif platform == 'Darwin-arm64':
    expected_hash = "5aba39252e2efa26bd76144f87ac59787d60fe567ab785e27e2a8c8190892eac"
    download_file_name = f"sccache-{version}-aarch64-apple-darwin"
    binary_name = "sccache"
else:
    assert(False), f"Unknown platform '{platform}'"

sccache_url = f"{url_base}{download_file_name}.tar.gz"
name_in_tar = f"{download_file_name}/{binary_name}"

# Figure out the sccache directory paths and create it if necessary
# We assume our working directory is the repo root.
# The binary is placed in a subdirectory of its download hash to ensure we don't re-use an old version.
sccache_root = os.path.join(os.getcwd(), "bin", "tools", "sccache")
sccache_cache_directory = os.path.join(sccache_root, "cache")
sccache_cache_log_file_path = os.path.join(sccache_root, "sccache.log")

sccache_directory = os.path.join(sccache_root, expected_hash)
sccache_binary_location = os.path.join(sccache_directory, binary_name)
os.makedirs(sccache_directory, exist_ok=True)

# Add sccache to the workspace path and configure sccache's cache directory
gha.set_output('root-directory', sccache_root)
gha.set_output('log-file-path', sccache_cache_log_file_path)
gha.set_environment_variable('SCCACHE_DIR', sccache_cache_directory)
gha.set_environment_variable('SCCACHE_ERROR_LOG', sccache_cache_log_file_path)
gha.set_environment_variable('SCCACHE_LOG', 'info')
gha.add_path(sccache_directory)

# If the output path already exists, no need to download
# (This will happen automagically because the binary is going to be cached along with the cache its self.)
if os.path.exists(sccache_binary_location):
    print("sccache already downloaded, won't download again.")
    sys.exit()

# Download the sccache archive
print(f"Download sccache from '{sccache_url}'...")
response = urllib.request.urlopen(sccache_url)
file_data = response.read()

# Validate the file hash
file_hash = hashlib.sha256(file_data).hexdigest()
assert(file_hash == expected_hash), f"Failed to validate '{sccache_url}', expected SHA256 hash {expected_hash} (got {file_hash})"

# Extract the sccache binary
tar_stream = io.BytesIO(file_data)
with tarfile.open(fileobj=tar_stream) as tar_file:
    with tar_file.extractfile(name_in_tar) as file:
        with io.open(sccache_binary_location, mode='wb') as output_file:
            output_file.write(file.read())

# Mark the binary as executable
if sys.platform != 'win32':
    current_mode = os.stat(sccache_binary_location).st_mode
    os.chmod(sccache_binary_location, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Done
print("sccache downloaded.")
