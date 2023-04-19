#!/usr/bin/python3
import sys
import random
import os
from collections import defaultdict
import pickle
import time
from datetime import datetime
import struct

def ins_list():
    return [0, [-1, []]]

def ins_new_dict():
    return defaultdict(ins_list)

def access_dict():
    return [[defaultdict(ins_new_dict), defaultdict(ins_new_dict), defaultdict(ins_new_dict)], [defaultdict(ins_new_dict), defaultdict(ins_new_dict), defaultdict(ins_new_dict)]]

def counting_frequency(shared_mem_addr_list, result_path):
    if verbose_mode:
        log_filename = result_path + '/PMC.txt'
        raw_pmc_list_file = open(log_filename, 'w')
    access_index_to_byte = [1, 2, 4]
    num_pmc = 0
    finished_mem_addr = 0
    channel_freq = defaultdict(int)
    num_shared_mem_addr = len(shared_mem_addr_list)
    for write_addr in shared_mem_addr_list:
        if write_addr < 0xC0000000:
            finished_mem_addr += 1
            continue
        write_access_dict = mem_dict[write_addr][0]
        num_new_pmc = 0
        for write_length_index in range(0, 3):
            # map the length index to real bytes
            write_byte = access_index_to_byte[write_length_index]
            # if the length is 4 bytes, then the following address would be accessed
            # addr, addr+1, addr+2, addr+3
            write_addr_begin = write_addr
            write_addr_end = write_addr + write_byte - 1
            # Now we know the write address and write length
            write_ins_dict = write_access_dict[write_length_index]
            # enumerate all possible addressed that could overlap with the write access
            for read_addr in range(write_addr_begin - 3, write_addr_end + 1):
                if read_addr not in shared_mem_addr_set:
                    continue
                read_access_dict = mem_dict[read_addr][1]
                for read_length_index in range(0, 3):
                    read_byte = access_index_to_byte[read_length_index]
                    read_addr_begin = read_addr
                    read_addr_end = read_addr + read_byte - 1
                    write_addr_set = set([])
                    read_addr_set = set([])
                    for addr in range(write_addr_begin, write_addr_end + 1):
                        write_addr_set.add(addr)
                    for addr in range(read_addr_begin, read_addr_end + 1):
                        read_addr_set.add(addr)
                    # check if two memory access could overlap
                    if len(write_addr_set & read_addr_set) == 0:
                        continue
                    read_ins_dict = read_access_dict[read_length_index]
                    addr_begin = min(list(write_addr_set & read_addr_set))
                    addr_end = max(list(write_addr_set & read_addr_set))
                    read_begin_offset = addr_begin - read_addr_begin
                    read_end_offset = addr_end - read_addr_begin + 1
                    write_begin_offset = addr_begin - write_addr_begin
                    write_end_offset = addr_end - write_addr_begin + 1
                    for write_ins in write_ins_dict:
                        for read_ins in read_ins_dict:
                            write_value_dict = write_ins_dict[write_ins]
                            read_value_dict = read_ins_dict[read_ins]
                            for write_value in write_value_dict:
                                write_bytes_value = struct.pack('<I', write_value)
                                write_actual_value = write_bytes_value[write_begin_offset: write_end_offset]
                                for read_value in read_value_dict:
                                    read_bytes_value = struct.pack('<I', read_value)
                                    read_actual_value = read_bytes_value[read_begin_offset:read_end_offset]
                                    if write_actual_value != read_actual_value:
                                        write_num = write_value_dict[write_value][0]
                                        read_num = read_value_dict[read_value][0]
                                        freq = write_num * read_num
                                        if freq:
                                            channel = (write_ins, read_ins)
                                            if channel not in channel_freq:
                                                channel_freq[channel] = [0, list()]
                                            channel_freq[channel][0] += freq
                                            channel_freq[channel][1].append((freq, (write_addr, read_addr, write_ins, read_ins, write_value, read_value, write_byte, read_byte)))
                                            num_new_pmc += 1
                                            num_pmc += 1
        finished_mem_addr += 1
        print("Process analyzed %f (%d/%d) addresses, added %d new PMCs, %d in total" % (finished_mem_addr/num_shared_mem_addr, finished_mem_addr, num_shared_mem_addr, num_new_pmc, num_pmc))
    return channel_freq


def pmc_analysis(output, testing_mode):
    time_now = datetime.now()
    timestamp = time_now.strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = output + '/PMC-' + timestamp + '/'
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    time_start = time.time()
    shared_mem_addr_list = list(mem_dict.keys())
    random.shuffle(shared_mem_addr_list)
    if testing_mode:
        shared_mem_addr_list = shared_mem_addr_list[0:50000]
    # divide the task into even pieces
    num_shared_mem_addr = len(shared_mem_addr_list)
    task_list = list(shared_mem_addr_list)
    # launch several processes running the task in paralle
    raw_multiprocess_output_dir = output_dir + '/raw/'
    if verbose_mode and not os.path.isdir(raw_multiprocess_output_dir):
        os.makedirs(raw_multiprocess_output_dir)
    channel_freq = counting_frequency(task_list, raw_multiprocess_output_dir)
    # sort all communications based on their frequency
    sorted_channel = channel_freq.items()

    freqs = [{}, {}]
    for item in sorted_channel:
        channel = list(item[0])
        for i in range(2):
            ins = channel[i]
            if ins not in freqs[i]:
                freqs[i][ins] = [0, []]
            freqs[i][ins][0] += item[1][0]
            freqs[i][ins][1].append(channel[not i])
        item[1][1].sort(key=lambda x: -x[0])

    print('Saving singles')
    f = open(output_dir + '/singles','wb')
    pickle.dump(freqs, f, pickle.HIGHEST_PROTOCOL)

    print('Saving pairs')
    f = open(output_dir + '/pairs','wb')
    pickle.dump(channel_freq, f, pickle.HIGHEST_PROTOCOL)

    return



'''
# argument 1 memory dictionary file
# argument 2 path where to store the result
'''
verbose_mode = False 
mem_dict_file = open(sys.argv[1], 'rb')
print("Loading python dictionary into memory")
mem_dict = pickle.load(mem_dict_file)
print("Memory dictionary is loaded")
shared_mem_addr_set = set(mem_dict.keys())
testing_mode = False
pmc_analysis(sys.argv[2], testing_mode)
