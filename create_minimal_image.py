import subprocess
import sys

BUILD_DIR = "build-output"


def main(directory):
    find_command = ["find", directory, "-type", "f", "-perm", "/a+x", "-exec", "ldd", "{}", ";"]
    jvm_find_std_out = _run_popen_command(find_command)
    shared_objects = _std_out_to_shared_objects({}, jvm_find_std_out)
    _copy_files_to_build_output_directory(directory, shared_objects)
    return shared_objects


def _copy_files_to_build_output_directory(directory, shared_objects):
    build_output_dir = "{0}{1}".format(BUILD_DIR, directory)
    _run_popen_command(["mkdir", "-p", build_output_dir])
    _run_popen_command(["cp", "-rL", "{0}/.".format(directory), build_output_dir + "/"])
    output_dirs = set(build_output_dir)
    for file_name in sorted(shared_objects.values()):
        _mkdir_and_copy_file(file_name, output_dirs)


def _mkdir_and_copy_file(file_name, output_dirs):
    file_directory = "/".join(file_name.split("/")[:-1])
    build_output_dir = "{0}{1}/".format(BUILD_DIR, file_directory)
    if build_output_dir not in output_dirs:
        _run_popen_command(["mkdir", "-p", build_output_dir])
        output_dirs.add(build_output_dir)
    _run_popen_command(["cp", file_name, build_output_dir])
    return output_dirs


def _ldd_of_shared_object(shared_objects, executable):
    std_out = _run_popen_command(["ldd", str(executable).strip()])
    return _std_out_to_shared_objects(shared_objects, std_out)


def _std_out_to_shared_objects(shared_objects, std_out):
    for std_out_line in _convert_std_out_to_list(std_out):
        _find_dependencies(shared_objects, std_out_line)
    return shared_objects


def _convert_std_out_to_list(std_out):
    return std_out.replace("\t", "").strip().split("\n")


def _find_dependencies(shared_objects, std_out_line):
    shared_object_details = std_out_line.split(" ")
    shared_object_name = shared_object_details[0].strip()
    shared_object_location = shared_object_details[2] if len(shared_object_details) > 3 else shared_object_name
    if shared_objects.get(shared_object_name, None) is None and shared_object_location not in ["", "not", "statically"]:
        shared_objects[shared_object_name] = shared_object_location
        _ldd_of_shared_object(
                shared_objects,
                shared_objects[shared_object_name]
        )
    return shared_objects


def _run_popen_command(command):
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    std_out, std_err = popen.communicate("")
    return std_out


if __name__ == "__main__":
    for directory in sys.argv[1:]:
        main(directory)
