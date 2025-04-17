import os
import shutil
import subprocess
import zipfile


def create_layer():
    """
    Create a Lambda layer for gspread.
    """

    layer_path = "python"
    if os.path.exists(layer_path):
        shutil.rmtree(layer_path)
    os.makedirs(layer_path)

    # Install packages to layer
    subprocess.check_call(["pip", "install", "gspread==6.1.2", "-t", layer_path])

    # Create ZIP file
    with zipfile.ZipFile("gspread_layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(layer_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(layer_path))
                zipf.write(file_path, arcname)

    shutil.rmtree(layer_path)
    print("Layer zip created successfully: gspread_layer.zip")


if __name__ == "__main__":
    create_layer()
