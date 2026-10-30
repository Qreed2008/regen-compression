import hashlib
from time import time
import os
from copy import deepcopy



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



def base64_custom(n):
  if n == 0:
    return "0"

  digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz~+"
  sign = "-" if n < 0 else ""
  n = abs(n)
  result = ""

  while n > 0:
    n, remainder = divmod(n, 64)
    result = digits[remainder] + result

  return sign + result



def base64_decode(n):
  result = 0
  digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz~+"
  for i in range(len(n)):
    result += digits.index(n[-i-1]) * (64**i)

  return result



def char_list_gen(data, mode = "normal"):
  results = {}
  start_time = time()
  for i in range(len(data)):
    if data[i] in results:
      results[data[i]]["main"] += 1
    else:
      results[data[i]] = {"main": 1}

    if i < len(data)-1:
      if data[i+1] in results[data[i]]:
        results[data[i]][data[i+1]] += 1
      else:
        results[data[i]][data[i+1]] = 1

    if i % 1000000 == 0:
      print(i, len(data), time()-start_time)

  finalstr = ""
  if mode == "normal":
    for item in results:
      finalstr += hex(item)[2:].zfill(2).upper() + ":" + base64_custom(results[item]["main"]) + "/"

  elif mode == "follow-up":
    for item in results:
      finalstr += hex(item)[2:].zfill(2).upper() + ":" + base64_custom(results[item]["main"]) + ",("
      for jtem in results[item]:
        if jtem != "main":
          finalstr += hex(jtem)[2:].zfill(2).upper() + ":" + base64_custom(results[item][jtem]) + ","

      if item == [x for x in results.keys()][-1] and len(results[item]) == 1:
        finalstr = finalstr[:-1]
      else:
        finalstr = finalstr[:-1] + ")/"

  return finalstr[:-1]



def hash_mode_num(list_of_hashes):
  mode_num_hash = 0
  for i in range(len(supported_hashes)):
    if supported_hashes[-i][0] in list_of_hashes:
      mode_num_hash += 2**i

  return mode_num_hash



file_name = input("Filename? - ")
output = input("Output file? - ")
supported_hashes = [["SHA1", hashlib.sha1], ["SHA256", hashlib.sha256], ["MD5", hashlib.md5]]

with open(file_name, "rb") as openFile:
  content = PartialFile(file_name, 64*1048576)
  settings = {"hashes": []}

  # ---------------------------------------------------------------------------------------------
  current = ""

  hashes = []
  while current != "next":
    current = input("Use which hashes? (SHA1, SHA256, MD5) - ")
    hashes.append(current)

  del hashes[-1]
  hash_check = False
  for item in supported_hashes:
    if item[0] in hashes:
      hash_check = True
      settings["hashes"].append(item)

  if hash_check == False:
    raise Exception("Can't have zero hashes")
  else:
    print(settings["hashes"])
  # ---------------------------------------------------------------------------------------------



  # ---------------------------------------------------------------------------------------------
  current = ""
  print("""
Other settings can be added here
f - Include "follow-up bytes" details (ex. if given 00 01, it
  will also be noted that one 01 appears after 00)
ch - Hashes for chunks (more questions will appear afterwards)
""")
# cb - Include byte details per chunk (will follow chunk hashes'
#     chunk size setting if you did that) (cbf to include
#     "follow-up"s, like seen above)
  while current != "next":
    current = input("Other settings? - ")

    if current == "f":
      settings["f"] = True
    elif current == "ch":
      settings["ch"] = []
      ch_temp = []

      if "c_size" not in settings:
        settings["c_size"] = int(input("Block size? "))

      while current != "next":
        current = input("Use which hashes? (SHA1, SHA256, MD5) - ")
        ch_temp.append(current)

      del ch_temp[-1]
      hash_check = False
      for item in supported_hashes:
        if item[0] in ch_temp:
          hash_check = True
          settings["ch"].append(item[0])

      if hash_check == False:
        raise Exception("Can't have zero hashes")
      else:
        print("this is the chunk hash portion")


  with open(output, "w") as openTwo:
    mode_num = 0

    if "f" in settings:
      mode_num += 1
    if "ch" in settings:
      mode_num += 2
    if "cb" in settings:
      mode_num += 4
    if "cbf" in settings:
      mode_num += 12

    openTwo.write(base64_custom(len(content)) + "-")
    openTwo.write(base64_custom(mode_num).zfill(2) + "-")

    if "c_size" in settings:
      openTwo.write(base64_custom(settings["c_size"]) + "-")

    openTwo.write(base64_custom(hash_mode_num(hashes)) + "/" + "/".join([base64_custom(int(supported_hashes[supported_hashes.index(j)][1](openFile.read()).hexdigest(), 16)) for j in settings["hashes"]]) + "-")
    openTwo.write(char_list_gen(content, "follow-up" if "f" in settings else "normal"))

    if "ch" in settings:
      openTwo.write("-" + base64_custom(hash_mode_num(settings["ch"])) + "/")

      for i in range(len(supported_hashes)):
        if supported_hashes[-i][0] in settings["ch"]:
          del settings["ch"][settings["ch"].index(supported_hashes[-i][0])]
          settings["ch"].append(supported_hashes[-i])

      for i in range(0, len(content), settings["c_size"]):
        for j in settings["ch"]:
          if j == settings["ch"][-1] and len(content) - i < settings["c_size"]:
            openTwo.write(base64_custom(int(supported_hashes[supported_hashes.index(j)][1](content[i:i+settings["c_size"]]).hexdigest(), 16)))
          else:
            openTwo.write(base64_custom(int(supported_hashes[supported_hashes.index(j)][1](content[i:i+settings["c_size"]]).hexdigest(), 16)) + "/")

        if i % (100*settings["c_size"]) == 0:
          print("chunk hash:", i, len(content))
