
import dtwain
import struct
import multiprocessing
from ctypes import *
from dtwain.constants import DTWAIN_PT_DEFAULT, DTWAIN_USELONGNAME
from dtwain.dtwain import dtwain_source

SYS_ARCH = str(struct.calcsize("P")*8) + " bit"

print("This is a", SYS_ARCH, "system.")

def scan_image_process(process_number: int, image_name: str):
    log_label = f'[PROCESS #{process_number}]'
    twain_ref = dtwain.dtwain(debug=True)
    # source = twain_ref.selectSource()
    device_list = twain_ref.source_string_list
    print(log_label,"device_list:", device_list)
    assert(len(device_list) > 0)
    default_source = device_list[0]
    print(log_label, "default_source is selected as", default_source)
    source = twain_ref.getSourceByName(default_source)
    print(log_label, "Acquired scanner")
    scan_image(log_label, source, image_name)
    twain_ref.close()

def scan_image(log_label: str, data_source: dtwain_source, image_name: str):
    if not image_name.endswith(".bmp"):
        image_name += ".bmp"
    print(log_label, "Image name is ", image_name)
    data_source.acquire_and_write_file(image_name, dtwain.DTWAIN_BMP, DTWAIN_USELONGNAME, DTWAIN_PT_DEFAULT, False)

# scan_image_process(0, "out/SampleImage")

def main():
    processes: multiprocessing.Process = []
    for i in range(10):
        process = multiprocessing.Process(target=scan_image_process, args=[i, "out/SampleImage"+str(i)])
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

# print(processes)

if __name__ == '__main__':
    main()
