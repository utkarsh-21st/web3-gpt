from pathlib import Path

for path in Path("temp/0xAppl/contracts/contracts").rglob("*"):
    if path.is_file(): 
      # print(path)
      print(path.parts)
