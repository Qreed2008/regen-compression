from copy import deepcopy

class WeirdTreeThing:
  def __init__(self, settings):
    self.settings = settings
    self.branch = bytearray(settings["length"])
    self.current_state = deepcopy(self.settings["byte_details"])
    self.current_loc = 0
    self.backwards_record = bytearray(settings["length"])
    self.generate()

  def generate(self):
    current_byte = [x for x in self.settings["byte_details"].keys()][0]
    self.branch[self.current_loc] = current_byte
    self.backwards_record[self.current_loc] = current_byte
    self.current_state[current_byte]["main"] -= 1
    complete = False
    while not complete:
      self.step()
      if self.current_loc == len(self.branch)-1:
        complete = True

  def step(self):
    pass

  def backwards(self):
    if "f" in self.settings and self.settings["f"] == True:
      self.current_state[self.branch[self.current_loc]]["main"] += 1
      self.current_state[self.branch[self.current_loc-1]][self.branch[self.current_loc]] += 1

    self.branch[self.current_loc] = 0
    self.current_loc -= 1

  def next_byte(self):
    temp = self.current_state[self.branch[self.current_loc]]
    temp = temp[temp.index(self.backwards_record[self.current_loc])+1:]

# 54:1,(65:1)/65:4,(73:1,6E:2)/73:2,(74:1,65:1)/74:2,(20:1,65:1)/20:1,(73:1)/6E:2,(74:1,63:1)/63:1,(65:1)

"""
current is 54
insert 54 at first byte of branch
"""

thing = {
  0x54: {
    "main": 1, 0x65: 1
  }, 0x65: {
    "main": 4, 0x73: 1, 0x6E: 2
  }, 0x73: {
    "main": 2, 0x74: 1, 0x65: 1
  }, 0x74: {
    "main": 2, 0x20: 1, 0x65: 1
  }, 0x20: {
    "main": 1, 0x73: 1
  }, 0x6E: {
    "main": 2, 0x74: 1, 0x63: 1
  }, 0x63: {
    "main": 1, 0x65: 1
  }
}

WeirdTreeThing({"length": 13, "f": True, "byte_details": thing})

"""
elif mode == "e":
  content = PartialFile(file_name, 64*1048576)
  i = 0
  settings = {}
  settings_mode = "length"
  while i < len(content):
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
        settings_mode = "c_size"
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
      if "ch" in settings:
        settings_mode = "chunk-hashes"

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
      elif settings[settings_mode][-3] == "1":
        settings_mode = "chunk-hash-sha1"

      i += 1
    elif settings_mode == "chunk-hash-sha256":
      settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(64)
      if settings["chunk-hashes"][-1] == "1":
        settings_mode = "chunk-hash-md5"
      elif settings[settings_mode][-3] == "1":
        settings_mode = "chunk-hash-sha1"
      elif settings[settings_mode][-2] == "1":
        settings_mode = "chunk-hash-sha256"

      i += 1
    elif settings_mode == "chunk-hash-md5":
      settings[settings_mode] = hex(base64_decode(settings[settings_mode]))[2:].zfill(32)
      if settings[settings_mode][-3] == "1":
        settings_mode = "chunk-hash-sha1"
      elif settings[settings_mode][-2] == "1":
        settings_mode = "chunk-hash-sha256"
      elif settings[settings_mode][-1] == "1":
        settings_mode = "chunk-hash-md5"

      i += 1

  if type(settings["byte-details"]) == str:
    settings["byte-details"] = char_list_decode(settings["byte-details"])


  print(len(settings["byte-details"]))
  tree_thing = WeirdTreeThing(settings)
"""