import os
import ffmpeg
import ctypes.wintypes

force_clean = False  # Default to false

CSIDL_PERSONAL = 5  # My Documents
SHGFP_TYPE_CURRENT = 0  # Get current, not default value

# Random crap to obtain Documents folder

buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetFolderPathW(
    None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
documents_path = buf.value.replace("\\", "/")

remote_db = list()
known_formats = [".mp3", ".flac", ".m4a", ".ogg"]
music_directories = []  # Your directories here as a list ["X:/Example", "X:/Example2"]

# Unsure about m4a but it's usually AAC stuff
# Not sure how RAGE deals with this format, never seen it in the game files
unsupported_formats = [".flac", ".m4a"]
music_path = documents_path + "/Rockstar Games/GTA V/User Music/"


# Util function to remove the "Database", unused
def clean():
    if os.path.exists(music_path + "trackdb.txt"):
        os.remove(music_path + "trackdb.txt")


# Sanitize inputs from files, removing escape sequences
# Useful for lists
def sanitize_file_input(f_input):
    output = list()
    for entry in f_input:
        entry = entry.strip('\n')
        output.append(entry)

    return output


# Check whether the "Database" is in sync with the actual files
def sync_db(musicdir_state, db_state):
    if musicdir_state == db_state:
        return True
    else:
        return False


# Create a symlink for supported formats
def create_symlink(path, filename):
    dest_path = music_path + filename
    if os.path.exists(dest_path):
        pass
    else:
        os.symlink(path, dest_path)


# Convert unsupported formats
def convert_format(path, filename):
    for fmat in unsupported_formats:
        if fmat in filename:
            # I tried strip but it did eat some track's names
            dest_path = music_path + filename.replace(fmat, "") + ".mp3"
            if os.path.exists(dest_path):
                pass
            else:
                try:
                    stream = ffmpeg.input(path)
                    stream = ffmpeg.output(stream, dest_path, f='mp3', acodec='libmp3lame',
                                           audio_bitrate=320000)
                    ffmpeg.run(stream)
                except Exception as e:
                    print("Could not convert due to: {}".format(e))


# Get a list of the tracks stored in the "Database"
def get_stored_db_list():
    with open(music_path + "trackdb.txt", "r") as f:
        music_list = f.readlines()
        music_list_fixed = sanitize_file_input(music_list)

    return music_list_fixed


# Do the main tasks of conversion and symlinking
def process_db(music_list_fixed):
    for x in range(len(music_list_fixed)):
        cur_track = music_list_fixed[x]
        try:
            track_name = music_list_fixed[x + 1]
        except Exception as e:
            break

        if not ":/" in cur_track:  # Look for drive path, shitty hack
            continue
        # TODO: Remove hardcoding
        if ".flac" or ".m4a" in cur_track:  # Is an unsupported file?
            convert_format(cur_track, track_name)
        else:
            try:
                if os.path.exists(cur_track):
                    create_symlink(cur_track, track_name)
            except Exception as e:
                print("Failed due to {}".format(e))


# Verify whether the "Database" exists or not
def check_db_existence():
    if os.path.exists(music_path + "trackdb.txt"):
        return True
    else:
        return False


# Walk over the source directories and return a list of the files and things
def seek_source_files():
    music_list = list()
    for directory in music_directories:
        for root, _, files in os.walk(directory):
            for file in files:
                # Fixes slashes, windows does support forward slash
                root = root.replace("\\", "/")

                for fmat in known_formats:
                    if file.endswith(fmat):
                        music_list.append(root + '/' + file)
                        music_list.append('\n' + file + '\n')
                    else:
                        continue

    return music_list


# Write the "Database" file with the list of tracks and files and things
def write_db_file(music_list):
    with open("X:/Documents/Rockstar Games/GTA V/User Music/trackdb.txt", "w") as f:
        for track in music_list:
            f.write(track)


# Verify the status of the database to write or not the "Database" file
def check_db_status(music_list):
    if check_db_existence():
        print("WARN: DB already exists")
        db_status = sync_db(sanitize_file_input(
            music_list), get_stored_db_list())
        if db_status:
            print("WARN: DB is in sync")
        else:
            print("WARN: DB is out of sync")
            write_db_file(music_list)
    else:
        print("WARN: Track DB does not exist.")
        write_db_file(music_list)


# Clean stale files
def clean_stale_files():
    stored_db = get_stored_db_list()
    for ext in known_formats:
        stored_db = [track.replace(ext, ".mp3") for track in stored_db]
    file_list = list()
    for _, _, files in os.walk(music_path):
        for file in files:
            file_list.append(file)

    # Bad GC? How are these variables still existing after the for loop execution? It's out of scope.
    del files, file

    if file_list == stored_db:
        print("No stale files! :D")
    else:
        print("Stale files detected. Removing...")
        for file in file_list:
            if file.endswith(".mp3"):
                if file not in stored_db:
                    print(file, "needs to be removed")
                    os.remove(
                        music_path + file)


def main():
    if force_clean:
        clean()
    check_db_status(seek_source_files())
    process_db(get_stored_db_list())
    clean_stale_files()


if __name__ == "__main__":
    main()
