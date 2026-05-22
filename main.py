import os
import subprocess
import kagglehub
import base64
import urllib.request
import re
import shutil

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

os.makedirs(os.path.expanduser("~/.kaggle"), exist_ok=True)

with open(os.path.expanduser("~/.kaggle/kaggle.json"), "w") as f:
    f.write(f"""{{
  "username": "{os.environ['KAGGLE_USERNAME']}",
  "key": "{os.environ['KAGGLE_KEY']}"
}}""")

os.chmod(os.path.expanduser("~/.kaggle/kaggle.json"), 0o600)

# -----------------------------
# 2. Install rclone
# -----------------------------
print("Installing rclone...")

url = "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
zip_path = "rclone.zip"

urllib.request.urlretrieve(url, zip_path)

subprocess.run(
    "rm -rf rclone-v1.74.1-linux-amd64 && unzip rclone.zip",
    shell=True,
    check=True
)

folder = [f for f in os.listdir() if f.startswith("rclone-")][0]
rclone_path = os.path.abspath(f"{folder}/rclone")

subprocess.run(
    f"chmod +x {rclone_path}",
    shell=True,
    check=True
)

subprocess.run(
    f"{rclone_path} version",
    shell=True,
    check=True
)

print("✅ Rclone ready")

# -----------------------------
# 3. Setup rclone config
# -----------------------------
print("Configuring rclone...")

os.makedirs(os.path.expanduser("~/.config/rclone"), exist_ok=True)

with open(os.path.expanduser("~/.config/rclone/rclone.conf"), "wb") as f:
    f.write(base64.b64decode(os.environ["RCLONE_CONFIG_BASE64"]))

# -----------------------------
# 4. Clean and create output folders
# -----------------------------
if os.path.exists(LOCAL_DIR):
    shutil.rmtree(LOCAL_DIR)

os.makedirs(f"{LOCAL_DIR}/Inter4K_png/Raw/Input", exist_ok=True)
os.makedirs(f"{LOCAL_DIR}/VCIP_png", exist_ok=True)

# -----------------------------
# 5. Read Inter4K file list and select videos 501-1000
# -----------------------------
print("Reading Inter4K files...")

result = subprocess.run(
    f"{rclone_path} lsf dataset:sevtone/Inter4K_png/Raw/Input -R",
    shell=True,
    capture_output=True,
    text=True,
    check=True
)

all_files = [
    x.strip()
    for x in result.stdout.splitlines()
    if x.strip()
]

selected = []

pattern = re.compile(r"Inter4K_vid_(\d+)_f(\d+)_in(\d+)\.png")

for file in all_files:
    filename = os.path.basename(file)
    m = pattern.match(filename)

    if m:
        vid = int(m.group(1))
        frame = int(m.group(2))
        in_num = int(m.group(3))

        if 501 <= vid <= 1000:
            selected.append((vid, frame, in_num, file))

selected.sort(key=lambda x: (x[0], x[1], x[2]))

with open("second_half.txt", "w") as f:
    for _, _, _, file in selected:
        f.write(file + "\n")

print(f"Selected Inter4K files: {len(selected)}")
print("First 20 selected files:")

with open("second_half.txt", "r") as f:
    for i, line in enumerate(f):
        if i >= 20:
            break
        print(line.strip())

# -----------------------------
# 6. Download Inter4K videos 501-1000 only
# -----------------------------
print("Downloading Inter4K videos 501-1000...")

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

print("✅ Inter4K download complete")

# -----------------------------
# 7. Download full VCIP
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
# 8. Upload to Kaggle
# -----------------------------
print("Uploading to Kaggle...")

kagglehub.dataset_upload(
    DATASET_HANDLE,
    LOCAL_DIR,
    version_notes="Inter4K videos 501-1000 only + complete VCIP_png"
)

print("🎉 Upload completed successfully!")
