import sys
file = open(sys.argv[1], 'r')

dy = 0
for line in file.readlines():
    for dx in line.rstrip().split(","):
        print(f"do Screen.drawPixel(x + {dx}, y + {str(dy)});")
    dy += 1 