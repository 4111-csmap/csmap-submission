while True:
    fp = open("courses.txt")
    s = input("Line: ")
    f = s.split("'")
    search = "'"+f[3]+"', '"+f[5]+"', '"+f[7]+"', '"+f[9]+"'"
    for line in fp:
        if search in line:
            print(line.split("'")[8][2:-2])
            break
    fp.close()
