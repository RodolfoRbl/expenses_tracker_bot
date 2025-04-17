from datetime import datetime, timezone, timedelta
import shutil
import zipfile
from .bot import Bot
import json
import os


def get_mx_time(format="%Y-%m-%d"):
    """Local time for Mexico city"""
    t_utc = datetime.now(timezone.utc)
    str_date = (t_utc - timedelta(hours=6)).strftime(format)
    return str_date


def zip_directory(directory_name: str) -> int:
    shutil.make_archive(directory_name, "zip", directory_name)
    return directory_name + ".zip"


def zip_files(output_name: str, *files: str) -> str:
    with zipfile.ZipFile(f"{output_name}.zip", "w") as zip_file:
        # Iterate over the list of files and add each to the archive
        for file in files:
            zip_file.write(file)
    return output_name + ".zip"


def add_files_to_zip(zipfile_path, files_to_add):
    # Open the existing zip file
    with zipfile.ZipFile(zipfile_path, "a") as zip_file:
        for file in files_to_add:
            # Get the base name of the file
            base_name = os.path.basename(file)
            # Add the file to the zip archive
            zip_file.write(file, arcname=base_name)


def zip_files_at_same_level(output_zip_path, files_and_dirs_to_zip):
    """
    Zip files and directories to a specific path, placing them at the same level.

    Args:
        output_zip_path (str): Path to the output zip file.
        files_and_dirs_to_zip (list): List of paths to files and directories to zip.
    """
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for item in files_and_dirs_to_zip:
            if os.path.isfile(item):
                zipf.write(item, arcname=os.path.basename(item))
            elif os.path.isdir(item):
                for root, _, files in os.walk(item):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(
                            os.path.basename(item), os.path.relpath(file_path, item)
                        )
                        zipf.write(file_path, arcname=arcname)
    return output_zip_path


def local_running(token, lambda_handler):
    bot = Bot(token)
    offset = -1
    while True:
        get_update = bot.get("getupdates", offset=offset)
        if get_update.get("result"):
            update_for_loop = get_update["result"][0]
            event = {"body": json.dumps(update_for_loop)}
            lambda_handler(event, context=0)
            new_offset = update_for_loop["update_id"] + 1
            offset = new_offset
