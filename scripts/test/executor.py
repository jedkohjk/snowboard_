#!/usr/bin/python3
import sys
import os

def concurrent_executor(testcase_list, testing_mode=False):
    main_home = os.environ.get('MAIN_HOME')
    if main_home is None:
        print("Please source setup.sh")
        exit(1)
    script = main_home + "/scripts/test/concurrent-test.sh"
    input1 = ['SKI_INPUT1_RANGE=%']
    input2 = ['SKI_INPUT2_RANGE=%']
    preemp1 = ['SKI_CPU1_PREEMPTION=']
    preemp2 = ['SKI_CPU2_PREEMPTION=']
    value1 = ['SKI_CPU1_PREEMPTION_VALUE=']
    value2 = ['SKI_CPU2_PREEMPTION_VALUE=']
    addr = ['SKI_CHANNEL_ADDR=']
    ski_mode = False
    if testing_mode:
        testcase_list = testcase_list[:50]
    for testcase in testcase_list:
        write_addr = testcase[0]
        if write_addr == -1:
            ski_mode = True
        if ski_mode:
            input1.append(str(testcase[8]) +',')
            input2.append(str(testcase[9]) +',')
            continue
        read_addr = testcase[1]
        write_byte = testcase[6]
        read_byte = testcase[7]
        write_value = testcase[4]
        read_value = testcase[5]
        write_addr_set = set([])
        read_addr_set = set([])
        for addr_tmp in range(write_addr, write_addr + write_byte):
            write_addr_set.add(addr_tmp)
        for addr_tmp in range(read_addr, read_addr + read_byte):
            read_addr_set.add(addr_tmp)
        addr_begin = min(list(write_addr_set & read_addr_set))
        input1.append(str(testcase[8]) +',')
        input2.append(str(testcase[9]) +',')
        preemp1.append(str(testcase[2]) +',')
        preemp2.append(str(testcase[3]) +',')
        value1.append(str(write_value) + ',')
        value2.append(str(read_value) + ',')
        addr.append(str(addr_begin) +',')
    if not ski_mode:
        test_cmd = ''.join(input1)[:-1] + ' ' + ''.join(input2)[:-1] + ' ' + ''.join(preemp1)[:-1] + ' ' + ''.join(preemp2)[:-1]+' '+''.join(addr)[:-1] + ' ' + \
                    ''.join(value1)[:-1] + ' ' + ''.join(value2)[:-1] + ' SKI_PREEMPTION_BY_ACCESS=1 SKI_FORKALL_CONCURRENCY=1 ' + script
    else:
        test_cmd = ''.join(input1)[:-1] + ' ' + ''.join(input2)[:-1] + ' SKI_PREEMPTION_BY_ACCESS=0 SKI_FORKALL_CONCURRENCY=1 ' + script
    print(test_cmd)
    os.system(test_cmd)
