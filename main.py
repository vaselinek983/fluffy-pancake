import os
import subprocess
import kagglehub
import base64
import urllib.request

DATASET_HANDLE = "tonmoyk983/sevtone-half-inter4k-vcip"
LOCAL_DIR = "sevtone"

# -----------------------------
# 0. Install required tools
# -----------------------------
print("Installing system tools...")

subprocess.run(
    "apt update && apt install -y unzip ca-certificates",
    shell=True,
    check=True
)

# -----------------------------
# 1. Setup Kaggle credentials
# -----------------------------
print("Setting up Kaggle credentials...")

os.makedirs(
    os.path.expanduser("~/.kaggle"),
    exist_ok=True
)

with open(
    os.path.expanduser("~/.kaggle/kaggle.json"),
    "w"
) as f:

    f.write(f"""{{
  "username": "{os.environ['KAGGLE_USERNAME']}",
  "key": "{os.environ['KAGGLE_KEY']}"
}}""")

os.chmod(
    os.path.expanduser("~/.kaggle/kaggle.json"),
    0o600
)

# -----------------------------
# 2. Install rclone
# -----------------------------
print("Installing rclone...")

url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
zip_path = "rclone.zip"

urllib.request.urlretrieve(
    url,
    zip_path
)

subprocess.run(
    "rm -rf rclone-v1.74.1-linux-amd64 && unzip rclone.zip",
    shell=True,
    check=True
)

folder = [
    f for f in os.listdir()
    if f.startswith("rclone-")
][0]

rclone_path = os.path.abspath(
    f"{folder}/rclone"
)

subprocess.run(
    f"chmod +x {rclone_path}",
    shell=True,
    check=True
)

print("✅ Rclone ready")

# -----------------------------
# 3. Setup rclone config
# -----------------------------
print("Configuring rclone...")

os.makedirs(
    os.path.expanduser("~/.config/rclone"),
    exist_ok=True
)

with open(
    os.path.expanduser(
        "~/.config/rclone/rclone.conf"
    ),
    "wb"
) as f:

    f.write(
        base64.b64decode(
            os.environ["RCLONE_CONFIG_BASE64"]
        )
    )

# -----------------------------
# Create output folders
# -----------------------------
os.makedirs(
    f"{LOCAL_DIR}/Inter4K_png/Raw/Input",
    exist_ok=True
)

os.makedirs(
    f"{LOCAL_DIR}/VCIP_png",
    exist_ok=True
)

# -----------------------------
# 4. Read Inter4K file list
# -----------------------------
print("Reading Inter4K files...")

result = subprocess.run(
    f"{rclone_path} lsf dataset:sevtone/Inter4K_png/Raw/Input -R",
    shell=True,
    capture_output=True,
    text=True,
    check=True
)

files = sorted([
    x.strip()
    for x in result.stdout.splitlines()
    if x.strip()
])

total_files = len(files)
half = total_files // 2

print(f"Total Inter4K files: {total_files}")
print(f"Downloading SECOND half: {half+1} → {total_files}")

with open(
    "second_half.txt",
    "w"
) as f:

    for file in files[half:]:
        f.write(file + "\n")

# -----------------------------
# 5. Download SECOND HALF
# -----------------------------
print("Downloading second half of Inter4K...")

subprocess.run(
    f"{rclone_path} copy "
    f"dataset:sevtone/Inter4K_png/Raw/Input "
    f"{LOCAL_DIR}/Inter4K_png/Raw/Input "
    f"--files-from second_half.txt "
    f"--progress "
    f"--transfers 8 "
    f"--checkers 8 "
    f"--retries 5",
    shell=True,
    check=True
)

print("✅ Inter4K second half complete")

# -----------------------------
# 6. Download FULL VCIP
# -----------------------------
print("Downloading complete VCIP...")

subprocess.run(
    f"{rclone_path} copy "
    f"dataset:sevtone/VCIP_png "
    f"{LOCAL_DIR}/VCIP_png "
    f"--progress "
    f"--transfers 8 "
    f"--checkers 8 "
    f"--retries 5",
    shell=True,
    check=True
)

print("✅ VCIP complete")

# -----------------------------
# 7. Upload to Kaggle
# -----------------------------
print("Uploading to Kaggle...")

kagglehub.dataset_upload(
    DATASET_HANDLE,
    LOCAL_DIR,
    version_notes=(
        "Second half of Inter4K_png Raw Input and VCIP "
    )
)

print("🎉 Upload completed successfully!")
