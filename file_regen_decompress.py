import os
from copy import deepcopy
import hashlib

class WeirdTreeThing:
  def __init__(self, settings):
    self.settings = settings
    self.branch = bytearray(settings["length"])
    self.current_state = deepcopy(self.settings["byte-details"])
    self.current_loc = 0
    self.going_back = False
    self.backwards_record = bytearray(settings["length"])
    self.branch_num = 0

    if "f" not in settings:
      raise Exception("\"Follow-up bytes\" not included - Decode not available yet (not that it would be that useful I imagine...)")

    self.generate()

  def generate(self):
    current_byte = [x for x in self.settings["byte-details"].keys()][0]
    self.branch[self.current_loc] = current_byte
    self.backwards_record[self.current_loc] = current_byte
    self.current_state[current_byte]["main"] -= 1
    self.current_loc += 1

    complete = False
    while not complete:
      self.step()
      if self.current_loc == len(self.branch) and self.hash_check():
        complete = True

  def step(self):
    temp = self.get_next_byte_option()
    if temp == None or self.current_loc >= self.settings["length"]:
      #with open("temp.ug", "wb") as openFile:
        #openFile.write(self.branch)
        #openFile.write(self.backwards_record)
      self.backwards()
    else:
      self.branch[self.current_loc] = temp
      self.backwards_record[self.current_loc] = temp
      self.current_state[self.branch[self.current_loc]]["main"] -= 1
      self.current_state[self.branch[self.current_loc-1]][self.branch[self.current_loc]] -= 1
      self.current_loc += 1
      if self.going_back == True:
        if self.branch_num % 10000 == 0:
          print(f"End of branch {self.branch_num} | {self.branch}")
        self.branch_num += 1

      self.going_back = False

  def backwards(self):
    self.backwards_loc = self.current_loc
    self.current_loc -= 1
    self.current_state[self.branch[self.current_loc]]["main"] += 1
    self.current_state[self.branch[self.current_loc-1]][self.branch[self.current_loc]] += 1
    self.branch[self.current_loc] = 0
    self.going_back = True

  def get_next_byte_option(self):
    temp = [x for x in self.current_state[self.branch[self.current_loc-1]].keys()][1:]

    if self.going_back:
      temp = temp[temp.index(self.backwards_record[self.current_loc])+1:]

    temp = [x for x in temp if self.current_state[self.branch[self.current_loc-1]][x] != 0]

    unused = 0
    i = 0
    while unused < 1 and i < len(temp):
      if self.current_state[self.branch[self.current_loc-1]][temp[i]] == self.settings["byte-details"][self.branch[self.current_loc-1]][temp[i]]:
        unused += 1

      i += 1

    temp = temp[:i]
    return temp[0] if len(temp) > 0 else None

  def hash_check(self):
    for item in [["md5", hashlib.md5], ["sha1", hashlib.sha1], ["sha256", hashlib.sha256]]:
      if f"file-hash-{item[0]}" in self.settings:
        if item[1](self.branch).hexdigest() != self.settings[f"file-hash-{item[0]}"]:
          return False

  def chunk_hash_check(self):
    for item in [["md5", hashlib.md5], ["sha1", hashlib.sha1], ["sha256", hashlib.sha256]]:
      if f"file-hash-{item[0]}" in self.settings:
        if item[1](self.branch).hexdigest() != self.settings[f"file-hash-{item[0]}"]:
          return False





class PartialFile: # Load a file in pieces to not destroy the poor RPi this is for
  def __init__(self, file_name, segment_size):
    self.file_name = file_name
    self.segment_size = segment_size
    self.file = open(file_name, "rb")
    self.file_length = os.path.getsize(self.file_name)
    self.current_block = 0

    self.current_block_data = self.file.read(segment_size)

  def __getitem__(self, number):
    if type(number) == slice:
      start, stop, step = number.indices(len(self))
      return bytearray([self[i] for i in range(start, stop)])
    else:
      if self.current_block != number//self.segment_size:
        self.current_block = number//self.segment_size

        self.file.seek(self.current_block * self.segment_size)
        self.current_block_data = self.file.read(self.segment_size)

      return self.current_block_data[number % self.segment_size]

  def __len__(self):
    return self.file_length



def char_list_decode(string):
  parts = string.split("/")
  result = {}
  for i in range(len(parts)):
    if "(" in parts[i]:
      parts[i] = parts[i].split(",")

      result[int(parts[i][0].split(":")[0], 16)] = {}
      result[int(parts[i][0].split(":")[0], 16)]["main"] = base64_decode(parts[i][0].split(":")[1])

      for j in range(1, len(parts[i])):
        if parts[i][j][0] == "(" and parts[i][j][-1] == ")":
          part_num = parts[i][j][1:-1].split(":")
        elif parts[i][j][-1] == ")":
          part_num = parts[i][j][:-1].split(":")
        elif parts[i][j][0] == "(":
          part_num = parts[i][j][1:].split(":")
        else:
          part_num = parts[i][j].split(":")

        result[int(parts[i][0].split(":")[0], 16)][int(part_num[0], 16)] = base64_decode(part_num[1])

    else:
      result[int(parts[i].split(":")[0], 16)] = {"main": base64_decode(parts[i].split(":")[1])}

  return result



def base64_decode(n):
  result = 0
  digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz~+"
  for i in range(len(n)):
    result += digits.index(n[-i-1]) * (64**i)

  return result



file_name = input("Filename? - ")
out_name = input("Output file? - ")

content = PartialFile(file_name, 64*1048576)
i = 0
settings = {}
settings_mode = "length"
while i < len(content) and settings_mode != "end":
  if content[i] != 45 and ((content[i] != 47 and (settings_mode.startswith("file-hash-") or settings_mode.startswith("chunk-hash-") or settings_mode == "file-hashes" or settings_mode == "chunk-hashes")) or (settings_mode == "length" or settings_mode == "mode" or settings_mode == "byte-details")):
    if settings_mode in settings:
      settings[settings_mode] += chr(content[i])
    else:
      settings[settings_mode] = chr(content[i])

    i += 1
  elif settings_mode == "length":
    settings[settings_mode] = base64_decode(settings[settings_mode])
    settings_mode = "mode"

    i += 1
  elif settings_mode == "mode":
    settings[settings_mode] = bin(base64_decode(settings[settings_mode]))[2:]
    if settings[settings_mode][-1] == "1":
      settings["f"] = True
    elif settings[settings_mode][-2] == "1":
      settings["ch"] = []
    elif settings[settings_mode][-4:-2] == "11":
      settings["cbf"] = []
    elif settings[settings_mode][-3] == "1":
      settings["cb"] = []
    
    if "1" in settings[settings_mode][-4:-1]:
      settings_mode = "chunk-hash-size"
    else:
      settings_mode = "file-hashes"

    i += 1
  elif settings_mode == "file-hashes":
    settings[settings_mode] = bin(base64_decode(settings[settings_mode]))[2:]
    if settings[settings_mode][-3] == "1":
      settings_mode = "file-hash-sha1"
    elif settings[settings_mode][-2] == "1":
      settings_mode = "file-hash-sha256"
    elif settings[settings_mode][-1] == "1":
      settings_mode = "file-hash-md5"

    i += 1
  elif settings_mode == "file-hash-sha1":
    settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(40)
    if settings["file-hashes"][-2] == "1":
      settings_mode = "file-hash-sha256"
    elif settings["file-hashes"][-1] == "1":
      settings_mode = "file-hash-md5"
    else:
      settings_mode = "byte-details"

    i += 1
  elif settings_mode == "file-hash-sha256":
    settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(64)
    if settings["file-hashes"][-1] == "1":
      settings_mode = "file-hash-md5"
    else:
      settings_mode = "byte-details"

    i += 1
  elif settings_mode == "file-hash-md5":
    settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(32)
    settings_mode = "byte-details"

    i += 1
  elif settings_mode == "byte-details":
    settings["byte-details"] = char_list_decode(settings["byte-details"])
    #if "ch" in settings:
      #settings_mode = "chunk-hashes"
    settings_mode = "end"

    i += 1
  elif settings_mode == "chunk-hashes":
    settings[settings_mode] = bin(base64_decode(settings[settings_mode]))[2:]
    if settings[settings_mode][-3] == "1":
      settings_mode = "chunk-hash-sha1"
    elif settings[settings_mode][-2] == "1":
      settings_mode = "chunk-hash-sha256"
    elif settings[settings_mode][-1] == "1":
      settings_mode = "chunk-hash-md5"

    i += 1
  elif settings_mode == "chunk-hash-sha1":
    settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(40)
    if settings["chunk-hashes"][-2] == "1":
      settings_mode = "chunk-hash-sha256"
    elif settings["chunk-hashes"][-1] == "1":
      settings_mode = "chunk-hash-md5"
    else:
      settings_mode = "byte-details"

    i += 1
  elif settings_mode == "chunk-hash-sha256":
    settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(64)
    if settings["chunk-hashes"][-1] == "1":
      settings_mode = "chunk-hash-md5"
    else:
      settings_mode = "byte-details"

    i += 1
  elif settings_mode == "chunk-hash-md5":
    settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(32)
    settings_mode = "byte-details"

    i += 1
  elif settings_mode == "chunk-hash-size":
    settings[settings_mode] = base64_decode(settings[settings_mode])
    settings_mode = "file-hashes"
    i += 1

  elif settings_mode == "chunk-hashes-section":
    if settings_mode not in settings:
      settings[settings_mode] = {}

if type(settings["byte-details"]) == str:
  settings["byte-details"] = char_list_decode(settings["byte-details"])



print(len(settings["byte-details"]))
tree_thing = WeirdTreeThing(settings)

with open(out_name, "wb") as openFile:
  openFile.write(tree_thing.branch)
