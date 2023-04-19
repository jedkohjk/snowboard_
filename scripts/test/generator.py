#!/usr/bin/python3
import sys
import os
from collections import defaultdict
import re
import subprocess
import pickle
import time
from datetime import datetime
from executor import concurrent_executor
from Heap import Heap

def set_to_list():
    return set([])

def ins_list():
    return [0, [-1, []]]

def ins_new_dict():
    return defaultdict(ins_list)

def access_dict():
    return [[defaultdict(ins_new_dict), defaultdict(ins_new_dict), defaultdict(ins_new_dict)], [defaultdict(ins_new_dict), defaultdict(ins_new_dict), defaultdict(ins_new_dict)]]

verbose_debugging = True

# Find mem-dict-file and pmc folder
findCMD = 'find ' + sys.argv[1] + ' -name "mem-dict-*"'
out = subprocess.Popen(findCMD, shell=True,stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(stdout, stderr) = out.communicate()
mem_dict_filename = stdout.decode().strip()

findCMD = 'find ' + sys.argv[1] + ' -name "PMC-*" -type d'
out = subprocess.Popen(findCMD, shell=True,stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(stdout, stderr) = out.communicate()
pmc_dir = stdout.decode().strip()
print(mem_dict_filename, pmc_dir)
mem_dict_file = open(mem_dict_filename, 'rb')
print("Loading python dictionary into memory")
mem_dict = pickle.load(mem_dict_file)
f = open(pmc_dir+'/singles', 'rb')
singles = pickle.load(f)
f = open(pmc_dir+'/pairs', 'rb')
pairs = pickle.load(f)

def get_score(item):
    global singles, pairs
    return singles[0][item[0]][0] * singles[1][item[1]][0] * pairs[item][0]

queue = Heap(get_score)
for i in pairs.keys():
    pairs[i].append(queue.insert(i))

time_now = datetime.now()
timestamp = time_now.strftime("%Y-%m-%d-%H-%M-%S")
snowboard_storage = os.environ.get('SNOWBOARD_STORAGE')
if snowboard_storage is None:
    print("[Error] Please source scripts/setup.sh $FOLDER_TO_STORE_DATA first")
    exit(1)
log_filename = snowboard_storage + '/generator-log-' + timestamp + '.txt'
log_file = open(log_filename, 'w')
while queue.peek() is not None:
    testcase_pack = []
    while queue.peek() is not None and len(testcase_pack) < 512:
        test = queue.poll()[1]
        cluster = pairs[test][1].pop()[1]
        write_seed = mem_dict[cluster[0]][0][cluster[6].bit_length()-1][cluster[2]][cluster[4]][1]
        write_seed[0] = (write_seed[0] + 1) % len(write_seed[1])
        write_seed = write_seed[1][write_seed[0]]
        read_seed = mem_dict[cluster[1]][1][cluster[7].bit_length()-1][cluster[3]][cluster[5]][1]
        read_seed[0] = (read_seed[0] + 1) % len(read_seed[1])
        read_seed = read_seed[1][read_seed[0]]
        testcase_pack.append(list(cluster) + [write_seed, read_seed])
        print(*testcase_pack[-1], file=log_file)
        affected_ins = [set(), set()]
        affected_pairs = set()
        if len(pairs[test][1]):
            affected_pairs.add(test)
        for i in range(2):
            if test[i] not in affected_ins[i]:
                for ins in singles[i][test[i]][1]:
                    affectee = (test[i], ins)[::(-1)**i]
                    specs = pairs[affectee]
                    if queue.remove(specs[-1]):
                        affected_pairs.add(affectee)
                affected_ins[i].add(test[i])
            singles[i][test[i]][0] **= 2
        pairs[test][0] *= 2 * pairs[test][0]
        for i in affected_pairs:
            pairs[i][-1] = queue.insert(i)
    concurrent_executor(testcase_pack)
