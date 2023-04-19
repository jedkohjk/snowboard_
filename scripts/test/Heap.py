#!/usr/bin/python3

class Heap:
    
    def __init__(self, f):
        self.data = [0]
        self.f = lambda x: float('inf') if x is None else f(x[1])

    def peek(self):
        if len(self.data) > 1:
            return self.data[1]

    def poll(self):
        m = self.peek()
        self.remove(m)
        return m

    def get(self, idx):
        if idx < len(self.data):
            return self.data[idx]

    def insert(self, item):
        idx = len(self.data)
        item = [idx, item]
        self.data.append(item)
        self.shift_up(idx)
        return item

    def remove(self, item):
        idx = item[0]
        if self.data[idx] is item:
            last = self.data.pop()
            if item is not last:
                self.data[idx] = last
                self.data[idx][0] = idx
                self.shift_up(idx)
                self.shift_down(idx)
            return True
        return False

    def shift_up(self, idx):
        if idx > 1:
            parent = idx >> 1
            if self.f(self.get(idx)) < self.f(self.get(parent)):
                self.data[idx], self.data[parent] = self.data[parent], self.data[idx]
                self.data[idx][0], self.data[parent][0] = idx, parent
                self.shift_up(parent)

    def shift_down(self, idx):
        child = idx << 1
        child = min([i for i in range(child, child+2)], key=lambda x: self.f(self.get(x)))
        if self.f(self.get(idx)) > self.f(self.get(child)):
            self.data[idx], self.data[child] = self.data[child], self.data[idx]
            self.data[idx][0], self.data[child][0] = idx, child
            self.shift_down(child)
