import os
import sys
import random
#filename = open(sys.argv[1], "rb")
Pair = {}
Pairincluded = {}
for i in range(1, 17):
    randomNumber =  random.randint(17, 32)
    while randomNumber in Pairincluded:
        randomNumber =  random.randint(17, 32)
    Pair[i] = randomNumber
    Pairincluded[randomNumber] =1
'''
link = {}
edgeCount =0

for line in filename:
    if line[0]!="#":
        edgeCount +=1
        switchList = line.split()
        tupleID = (int(switchList[0]), int(switchList[1]))
        link[tupleID]=edgeCount
for i in range(1, 9):
    for j in range(1, 5):
        edgeCount +=1
        link[(i, 16+i*4+j)]=edgeCount

'''

kvalue = int(sys.argv[1])

#print Pair

def printKthMatrix(k):
    #add the constraints first
    #add the objective part second
    FLOW = "X"+ str(k)
    line = 75 * (k-1)
    print "Aeq("+ str(1+line) +", [" + FLOW + "E33, " +FLOW+"E34, "+FLOW+"E35, "+FLOW +"E36, " + FLOW+"E1, " + FLOW + "E2 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(2+line) +", [" + FLOW + "E37, " +FLOW+"E38, "+FLOW+"E39, "+FLOW +"E40, " + FLOW+"E3, " + FLOW + "E4 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(3+line) +", [" + FLOW + "E41, " +FLOW+"E42, "+FLOW+"E43, "+FLOW +"E44, " + FLOW+"E9, " + FLOW + "E10 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(4+line) +", [" + FLOW + "E45, " +FLOW+"E46, "+FLOW+"E47, "+FLOW +"E48, " + FLOW+"E11, " + FLOW + "E12 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(5+line) +", [" + FLOW + "E49, " +FLOW+"E50, "+FLOW+"E51, "+FLOW +"E52, " + FLOW+"E17, " + FLOW + "E18 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(6+line) +", [" + FLOW + "E53, " +FLOW+"E54, "+FLOW+"E55, "+FLOW +"E56, " + FLOW+"E19, " + FLOW + "E20 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(7+line) +", [" + FLOW + "E57, " +FLOW+"E58, "+FLOW+"E59, "+FLOW +"E60, " + FLOW+"E25, " + FLOW + "E26 ])" + "= [1,1,1,1,-1,-1];"
    print "Aeq("+ str(8+line) +", [" + FLOW + "E61, " +FLOW+"E62, "+FLOW+"E63, "+FLOW +"E64, " + FLOW+"E27, " + FLOW + "E28 ])" + "= [1,1,1,1,-1,-1];"
    #########Above is for edge switches flow conservation#####################################

    print "Aeq("+ str(9+line) +", [" + FLOW + "E1, " +FLOW+"E3, "+FLOW+"E5, "+FLOW +"E6 ])" + "= [1,1,-1,-1];"
    print "Aeq("+ str(10+line) +", [" + FLOW + "E2, " +FLOW+"E4, "+FLOW+"E7, "+FLOW +"E8])" + "= [1,1,-1,-1];"
    print "Aeq("+ str(11+line) +", [" + FLOW + "E9, " +FLOW+"E11, "+FLOW+"E13, "+FLOW +"E14]) " + "= [1,1,-1,-1];"
    print "Aeq("+ str(12+line) +", [" + FLOW + "E10, " +FLOW+"E12, "+FLOW+"E15, "+FLOW +"E16]) " + "= [1,1,-1,-1];"

    print "Aeq("+ str(13+line) +", [" + FLOW + "E17, " +FLOW+"E19, "+FLOW+"E21, "+FLOW +"E22]) " + "= [1,1,-1,-1];"
    print "Aeq("+ str(14+line) +", [" + FLOW + "E18, " +FLOW+"E20, "+FLOW+"E23, "+FLOW +"E24]) " + "= [1,1,-1,-1];"
    print "Aeq("+ str(15+line) +", [" + FLOW + "E25, " +FLOW+"E27, "+FLOW+"E29, "+FLOW +"E30]) " + "= [1,1,-1,-1];"
    print "Aeq("+ str(16+line) +", [" + FLOW + "E26, " +FLOW+"E28, "+FLOW+"E31, "+FLOW +"E32]) " + "= [1,1,-1,-1];"

    print "Aeq("+ str(17+line) +", [" + FLOW + "E5, " +FLOW+"E13, "+FLOW+"E21, "+FLOW +"E29])" + "= [1,1,-1,-1];"
    print "Aeq("+ str(18+line) +", [" + FLOW + "E6, " +FLOW+"E14, "+FLOW+"E22, "+FLOW +"E30])" + "= [1,1,-1,-1];"
    print "Aeq("+ str(19+line) +", [" + FLOW + "E7, " +FLOW+"E15, "+FLOW+"E23, "+FLOW +"E31])" + "= [1,1,-1,-1];"
    print "Aeq("+ str(20+line) +", [" + FLOW + "E8, " +FLOW+"E16, "+FLOW+"E24, "+FLOW +"E32])" + "= [1,1,-1,-1];"


    print "Aeq(" + str(21+line) + ", [" + FLOW + "E"+ str(k +32)+"])=1;"
    print "Aeq(" + str(22+line) + ", [" + FLOW + "E"+ str(Pair[k] +32)+"])=1;"
    

    MB = "W"+ str(k)
    line =22+ 75 * (k-1)
    print "Aeq("+ str(1+line) +", [" + MB + "E33, " +MB+"E34, "+MB+"E35, "+MB +"E36, " + MB+"E1, " + MB + "E2, " + MB+  "P1  ])" + "= [1,1,1,1,-1,-1, -1];"
    print "Aeq("+ str(2+line) +", [" + MB + "E37, " +MB+"E38, "+MB+"E39, "+MB +"E40, " + MB+"E3, " + MB + "E4 , " + MB+  "P2 ])" + "= [1,1,1,1,-1,-1,-1];"
    print "Aeq("+ str(3+line) +", [" + MB + "E41, " +MB+"E42, "+MB+"E43, "+MB +"E44, " + MB+"E9, " + MB + "E10 , " + MB+  "P3 ])" + "= [1,1,1,1,-1,-1,-1];"
    print "Aeq("+ str(4+line) +", [" + MB + "E45, " +MB+"E46, "+MB+"E47, "+MB +"E48, " + MB+"E11, " + MB + "E12 , " + MB+  "P4 ])" + "= [1,1,1,1,-1,-1,-1];"
    print "Aeq("+ str(5+line) +", [" + MB + "E49, " +MB+"E50, "+MB+"E51, "+MB +"E52, " + MB+"E17, " + MB + "E18 , " + MB+  "P5 ])" + "= [1,1,1,1,-1,-1, 1];"
    print "Aeq("+ str(6+line) +", [" + MB + "E53, " +MB+"E54, "+MB+"E55, "+MB +"E56, " + MB+"E19, " + MB + "E20, " + MB+  "P6 ])" + "= [1,1,1,1,-1,-1, 1];"
    print "Aeq("+ str(7+line) +", [" + MB + "E57, " +MB+"E58, "+MB+"E59, "+MB +"E60, " + MB+"E25, " + MB + "E26 , " + MB+  "P7 ])" + "= [1,1,1,1,-1,-1, 1];"
    print "Aeq("+ str(8+line) +", [" + MB + "E61, " +MB+"E62, "+MB+"E63, "+MB +"E64, " + MB+"E27, " + MB + "E28 , " + MB+  "P8 ])" + "= [1,1,1,1,-1,-1, 1];"
    #########Above is for edge switches MB conservation#####################################

    print "Aeq("+ str(9+line) +", [" + MB + "E1, " +MB+"E3, "+MB+"E5, "+MB +"E6 , " + MB+  "P9])" + "= [1,1,-1,-1,-1];"
    print "Aeq("+ str(10+line) +", [" + MB + "E2, " +MB+"E4, "+MB+"E7, "+MB +"E8 , " + MB+  "P10 ])" + "= [1,1,-1,-1,-1];"
    print "Aeq("+ str(11+line) +", [" + MB + "E9, " +MB+"E11, "+MB+"E13, "+MB +"E14, " + MB+  "P11 ]) " + "= [1,1,-1,-1,-1];"
    print "Aeq("+ str(12+line) +", [" + MB + "E10, " +MB+"E12, "+MB+"E15, "+MB +"E16, " + MB+  "P12 ]) " + "= [1,1,-1,-1,-1];"

    print "Aeq("+ str(13+line) +", [" + MB + "E17, " +MB+"E19, "+MB+"E21, "+MB +"E22, " + MB+  "P13 ]) " + "= [1,1,-1,-1, 1];"
    print "Aeq("+ str(14+line) +", [" + MB + "E18, " +MB+"E20, "+MB+"E23, "+MB +"E24, " + MB+  "P14 ]) " + "= [1,1,-1,-1, 1];"
    print "Aeq("+ str(15+line) +", [" + MB + "E25, " +MB+"E27, "+MB+"E29, "+MB +"E30, " + MB+  "P15 ]) " + "= [1,1,-1,-1, 1];"
    print "Aeq("+ str(16+line) +", [" + MB + "E26, " +MB+"E28, "+MB+"E31, "+MB +"E32, " + MB+  "P16 ]) " + "= [1,1,-1,-1, 1];"

    print "Aeq("+ str(17+line) +", [" + MB + "E5, " +MB+"E13, "+MB+"E21, "+MB +"E29, " + MB+  "P17 ])" + "= [1,1,-1,-1,-1];"
    print "Aeq("+ str(18+line) +", [" + MB + "E6, " +MB+"E14, "+MB+"E22, "+MB +"E30, " + MB+  "P18 ])" + "= [1,1,-1,-1,-1];"
    print "Aeq("+ str(19+line) +", [" + MB + "E7, " +MB+"E15, "+MB+"E23, "+MB +"E31, " + MB+  "P19 ])" + "= [1,1,-1,-1,-1];"
    print "Aeq("+ str(20+line) +", [" + MB + "E8, " +MB+"E16, "+MB+"E24, "+MB +"E32, " + MB+  "P20 ])" + "= [1,1,-1,-1,-1];"

    print "Aeq(" + str(21+line) + ", [" + MB + "E"+ str(k +32)+", "+ FLOW+"E"+ str(k +32)+"])=[1,-1];"
    for i in range(1, 33):
        if i!=k:
            print "Aeq(" + str(21+line+i) + ", [" + MB + "E" + str(i+32)+ "])=1;"
 
    
    print "beq(" + str(21+75*(k-1))+", 1) = 0.4;" 
    print "beq(" + str(22+75*(k-1))+", 1) = 0.4;" 
    print " "
    return

#############################################################################################################################
#############################################################################################################################


def printKthIneqalityMatrix(k):
    #add the constraints first
    #add the objective part second
    FLOW = "X"+ str(k)
    WORK = "W" + str(k)
    line = 64 * (k-1) +52
    for j in range(1, 65):
        print "A("+str(j+line) +", [" + FLOW + "E"+str(j) + ", " + WORK + "E" + str(j)+ " ])" + "=[-1,1];"
    return


print "variables = {",
for i in range(1, kvalue+1):
    for j in range(1, 65):
        print "\'X"+ str(i)+"E"+str(j) +"\'",
        print ",",
        print "\'W"+ str(i)+"E"+str(j) +"\'",
        print ",",
    for j in range(1, 21):
        print "\'W"+ str(i) + "P" + str(j)+"\'",
        print ",",

print "\'U1\', \'U2\'",
print "};"
print "N = length(variables); "
print "% generate variables for flow, format is X or W means flow, and odd number is forwarding while even number is backward"
print "for v = 1:N "
print "\t eval([variables{v},\' = \', num2str(v),\';\']); "
print "end"
print "lb=zeros(size(variables))"
print "ub=ones(size(variables))"
print "ub([U1 U2]) = [1.5 1.5]"
print "f = zeros(size(variables));"

print "f([U1 U2]) = [1 100];"

print "Aeq = zeros(" + str(75*kvalue)+ ", N); beq=zeros(" +str(75*kvalue) + ", 1)"

for i in range(1, kvalue+1):
    printKthMatrix(i)


#arbitrary block, like 33-62, 34-63, 36-49...
# building flow conservation






print "A = zeros("+ str(52+64*kvalue) +", N); b=zeros("+ str(52+64*kvalue) +", 1)"

for i in range(1,33):
    print "A("+ str(i) +", [",
    for j in range(1, kvalue+1):
       FLOW = "X"+ str(j) +"E" + str(i) 
       print FLOW+", ",
    print "U1 ] ) = [",
    for j in range(1, kvalue +1):
        print  " 1 ,",
    print   "-1 ];"



for i in range(1,21):
    print "A("+ str(i+32) +", [",
    for j in range(1, kvalue+1):
       FLOW = "W"+ str(j) +"P" + str(i) 
       print FLOW+", ",
    print "U2 ] ) = [",
    for j in range(1, kvalue +1):
        print  " 1 ,",
    print   "-1 ];"
for i in range(1, kvalue +1):
    printKthIneqalityMatrix(i)


#intlinprog
print "[x fval] = linprog(f,A,b,Aeq,beq,lb, ub);"
#print "[x fval] =  linprog(f,A,b,Aeq,beq,lb, ub);"

print "for d = 1:N \n  fprintf(\'%4.5f \\t%s\\n\',x(d),variables{d}) \n end\n fval"

